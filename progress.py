"""Thread-safe in-place per-model progress bars and batch elapsed status."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import shutil
import sys
import threading
import time
from typing import Any, Iterable, Mapping, TextIO

from costs import as_decimal, decimal_text

ProgressKey = tuple[str, str | None]  # (fully qualified model ID, optional effort)


def _duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _terminal_text(value: str, max_chars: int) -> str:
    printable = "".join(character if character.isprintable() else "?" for character in value)
    if len(printable) <= max_chars:
        return printable
    if max_chars <= 3:
        return printable[:max_chars]
    return printable[: max_chars - 3] + "..."


def _cost_lines(
    attempts: Iterable[Mapping[str, Any]], *, prefix: str = ""
) -> tuple[str, str]:
    rows = list(attempts)
    lines = []
    for field, label in (
        ("provider_reported_usd", "Provider-reported USD"),
        ("normalized_uncached_usd", "Uncached estimate USD"),
    ):
        values = [value for row in rows if (value := as_decimal(row.get(field))) is not None]
        known, total = len(values), len(rows)
        if total == 0:
            amount = "$0.000000 (no requests yet)"
        elif known == 0:
            amount = f"unknown (0/{total} requests priced)"
        else:
            partial = "partial " if known < total else ""
            amount = f"{partial}${sum(values, Decimal('0')):.6f} ({known}/{total} priced)"
        lines.append(f"{prefix}{label}: {amount}")
    return lines[0], lines[1]


@dataclass
class _ModelProgress:
    total: int
    started_at: float
    finished_at: float | None = None
    initial_completed: int = 0
    completed: int = 0
    output_tokens: int = 0
    correct: int = 0
    incorrect: int = 0
    seen_case_ids: set[str] = field(default_factory=set)
    cost_attempts: dict[str, dict[str, str | None]] = field(default_factory=dict)
    active_case: str | None = None
    active_attempt: int | None = None
    active_max_attempts: int | None = None
    status: str | None = None


class ProgressReporter:
    """Render stable progress and persisted-cost rows per model on a TTY.

    Non-streaming responses expose token usage only when they finish. The shown
    token rate is observed completion tokens (reasoning included when reported)
    divided by wall-clock elapsed time, not live generation speed.
    """

    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        heartbeat_interval: float = 5.0,
        force_tty: bool | None = None,
    ) -> None:
        self.stream = stream or sys.stderr
        detected_tty = getattr(self.stream, "isatty", lambda: False)()
        self._is_tty = detected_tty if force_tty is None else force_tty
        self._lock = threading.Lock()
        self._models: dict[ProgressKey, _ModelProgress] = {}
        self._batch_started = time.monotonic()
        self._batch_total: int | None = None
        self._finished_models: set[ProgressKey] = set()
        self._batch_notice = ""
        self._heartbeat_interval = max(0.1, heartbeat_interval)
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._rendered_lines = 0
        self._active_model_limit: int | None = None
        self._non_tty_last_completed: dict[ProgressKey, int] = {}

    def __enter__(self) -> "ProgressReporter":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        self._heartbeat_stop.set()
        thread = self._heartbeat_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=self._heartbeat_interval + 1)

    def set_active_model_limit(self, limit: int) -> None:
        if limit <= 0:
            raise ValueError("active model limit must be positive")
        with self._lock:
            self._active_model_limit = limit

    def set_batch_total(self, total: int) -> None:
        if total < 0:
            raise ValueError("batch model count cannot be negative")
        with self._lock:
            self._batch_total = total
            self._render_locked("batch prepared")

    def set_batch_status(self, notice: str) -> None:
        with self._lock:
            self._batch_notice = notice
            self._render_locked(notice)

    def register_model(
        self,
        model_id: str,
        reasoning_effort: str | None,
        total: int,
        *,
        initial_completed: int = 0,
        initial_correct: int = 0,
        initial_incorrect: int = 0,
    ) -> None:
        key = (model_id, reasoning_effort)
        with self._lock:
            if key in self._models:
                raise ValueError(
                    f"duplicate progress identity: model_id={model_id}, "
                    f"reasoning_effort={reasoning_effort}"
                )
            self._models[key] = _ModelProgress(
                total=total,
                started_at=time.monotonic(),
                initial_completed=initial_completed,
                completed=initial_completed,
                correct=initial_correct,
                incorrect=initial_incorrect,
            )
            self._render_locked("starting")

    def _start_heartbeat_locked(self) -> None:
        if not self._is_tty:
            return
        if self._heartbeat_thread is None or not self._heartbeat_thread.is_alive():
            self._heartbeat_stop.clear()
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                name="prime-eval-progress",
                daemon=True,
            )
            self._heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        while not self._heartbeat_stop.wait(self._heartbeat_interval):
            with self._lock:
                active_states = [
                    state for state in self._models.values()
                    if state.active_case is not None
                ]
                if active_states:
                    status = next(
                        (state.status for state in active_states if state.status),
                        "waiting for model response",
                    )
                    self._render_locked(status)

    def model_finished(
        self, model_id: str, reasoning_effort: str | None, *, success: bool
    ) -> None:
        key = (model_id, reasoning_effort)
        with self._lock:
            if key in self._finished_models:
                return
            self._finished_models.add(key)
            if key in self._models:
                self._models[key].active_case = None
                self._models[key].status = None
                self._models[key].finished_at = time.monotonic()
            total = self._batch_total if self._batch_total is not None else len(self._models)
            if total > 0 and len(self._finished_models) >= total:
                self._heartbeat_stop.set()
            self._render_locked("model complete" if success else "model incomplete")

    def __call__(self, event: dict[str, Any]) -> None:
        model_id = str(event.get("model_id", "model"))
        effort = event.get("reasoning_effort")
        key = (model_id, effort)
        with self._lock:
            state = self._models.get(key)
            if state is None:
                total = int(event.get("total_cases", 0))
                state = _ModelProgress(total=total, started_at=time.monotonic())
                self._models[key] = state

            event_type = event.get("event")
            attempt_id = event.get("attempt_id")
            if attempt_id and event_type == "attempt_cancelled_before_dispatch":
                state.cost_attempts.pop(str(attempt_id), None)
            elif attempt_id and event_type in {
                "attempt_started", "attempt_failed", "case_finished", "attempt_cost_update"
            }:
                costs = state.cost_attempts.setdefault(
                    str(attempt_id),
                    {"provider_reported_usd": None, "normalized_uncached_usd": None},
                )
                for cost_field in costs:
                    value = as_decimal(event.get(cost_field))
                    if value is not None:
                        costs[cost_field] = decimal_text(value)
            if event_type == "run_progress_init":
                state.cost_attempts = {
                    str(key): dict(value)
                    for key, value in event.get("cost_attempts", {}).items()
                }
                state.total = int(event.get("total_cases", state.total))
                state.initial_completed = int(event.get("completed_cases", 0))
                state.completed = state.initial_completed
                state.correct = int(event.get("correct", 0))
                state.incorrect = int(event.get("incorrect", 0))
                state.started_at = time.monotonic()
                state.active_case = None
                state.status = None
                self._render_locked("run state loaded")
                return

            if event_type == "attempt_cost_update":
                self._render_locked("cost updated")
                return

            if event_type == "rate_limit_wait":
                state.active_case = str(event.get("case_id", "request"))
                state.active_attempt = int(event.get("attempt_number") or 1)
                state.active_max_attempts = int(event.get("max_attempts") or 1)
                state.status = "waiting for shared request gate"
                self._start_heartbeat_locked()
                if self._is_tty:
                    self._render_locked(state.status)
                return

            if event_type == "attempt_started":
                state.active_case = str(event.get("case_id", "request"))
                state.active_attempt = int(event.get("attempt_number") or 1)
                state.active_max_attempts = int(event.get("max_attempts") or 1)
                state.status = "waiting for model response"
                self._start_heartbeat_locked()
                self._render_locked("request started")
                return

            if event_type == "attempt_cancelled_before_dispatch":
                state.active_case = None
                state.status = None
                self._render_locked("cancelled before dispatch")
                return

            if event_type == "attempt_failed":
                count = event.get("completion_tokens")
                if isinstance(count, int) and count >= 0:
                    state.output_tokens += count
                state.active_case = str(event.get("case_id", state.active_case or "request"))
                state.active_attempt = int(event.get("attempt_number") or 1)
                state.active_max_attempts = int(event.get("max_attempts") or 1)
                state.status = f"attempt {state.active_attempt}/{state.active_max_attempts} failed; retry/backoff if allowed"
                self._render_locked(state.status)
                return

            if event_type != "case_finished":
                return

            case_id = str(event.get("case_id", ""))
            if case_id and case_id in state.seen_case_ids:
                return
            if case_id:
                state.seen_case_ids.add(case_id)
            state.active_case = None
            state.status = None
            state.completed = min(state.total, state.completed + 1)
            count = event.get("completion_tokens")
            if isinstance(count, int) and count >= 0:
                state.output_tokens += count
            outcome = str(event.get("outcome", "unknown"))
            if outcome == "correct":
                state.correct += 1
            elif outcome in {"wrong_label", "invalid_response", "no_response"}:
                state.incorrect += 1
            self._render_locked(outcome)

    def _model_lines(self, key: ProgressKey, state: _ModelProgress, width: int) -> tuple[str, ...]:
        model_id, effort = key
        end_time = state.finished_at if state.finished_at is not None else time.monotonic()
        elapsed = max(0.0, end_time - state.started_at)
        completed_this_session = max(0, state.completed - state.initial_completed)
        remaining_cases = max(0, state.total - state.completed)
        eta = (
            _duration(elapsed * remaining_cases / completed_this_session)
            if completed_this_session > 0
            else "--:--:--"
        )
        rate = state.output_tokens / elapsed if elapsed > 0 else 0.0
        ratio = state.completed / state.total if state.total else 0.0

        # Preserve the useful counters and rate at narrow widths by shortening
        # labels/bar first, rather than slicing off ETA or tokens/second.
        effort_label = _terminal_text(effort if effort is not None else "default", 12)
        bar_width = min(12, max(4, width // 10))
        suffix = f" | [{('█' * min(bar_width, int(ratio * bar_width))) + ('░' * (bar_width - min(bar_width, int(ratio * bar_width))))}] {state.completed}/{state.total} ({ratio:.0%})"
        middle = f" | Effort: {effort_label}"
        model_budget = max(4, width - len("Model ID: ") - len(middle) - len(suffix))
        model_label = _terminal_text(model_id, model_budget)
        first_line = f"Model ID: {model_label}{middle}{suffix}"
        if len(first_line) > width:
            first_line = first_line[:width]

        second_line = (
            f"Elapsed {_duration(elapsed)} | ETA {eta} | Output {rate:.1f} tok/s | "
            f"Correct {state.correct} | Incorrect {state.incorrect}"
        )
        if len(second_line) > width:
            second_line = second_line[:width]
        costs = _cost_lines(state.cost_attempts.values())
        return first_line, second_line, *(_terminal_text(line, width) for line in costs)

    def _render_locked(self, status: str) -> None:
        total = self._batch_total if self._batch_total is not None else len(self._models)
        batch_elapsed = _duration(time.monotonic() - self._batch_started)
        header_status = self._batch_notice or status
        terminal = shutil.get_terminal_size((120, 24))
        width = max(40, terminal.columns - 1)
        header = (
            f"Prime eval | {len(self._finished_models)}/{total} done "
            f"| batch elapsed {batch_elapsed} | {header_status}"
        )
        # A long cancellation/error notice must not wrap and shift the cursor
        # accounting used by the in-place TTY redraw.
        lines = [_terminal_text(header, width)]
        lines.extend(
            _terminal_text(line, width)
            for line in _cost_lines(
                (cost for state in self._models.values() for cost in state.cost_attempts.values()),
                prefix="Batch ",
            )
        )

        if self._is_tty:
            active_models = [
                (key, state)
                for key, state in self._models.items()
                if key not in self._finished_models
            ]
            available_model_lines = max(0, terminal.lines - len(lines) - 1)
            requested_limit = (
                self._active_model_limit
                if self._active_model_limit is not None
                else len(active_models)
            )
            model_limit = min(requested_limit, available_model_lines // 4)
            hidden_count = 0
            if len(active_models) > model_limit:
                model_limit = min(model_limit, max(0, (available_model_lines - 1) // 4))
                hidden_count = len(active_models) - model_limit
            for key, state in active_models[:model_limit]:
                lines.extend(self._model_lines(key, state, width))
            visible_count = min(len(active_models), model_limit)
            lines.extend([""] * (4 * (model_limit - visible_count)))
            if hidden_count:
                lines.append(_terminal_text(
                    f"{hidden_count} active model(s) not shown", width
                ))

            # Reserve a fixed dashboard height so starting/finishing workers
            # never leaves stale rows or grows a scrollable list of completed runs.
            reserved_lines = max(self._rendered_lines, len(lines))
            if reserved_lines > terminal.lines - 1:
                reserved_lines = max(1, terminal.lines - 1)
                lines = lines[:reserved_lines]
            if self._rendered_lines:
                self.stream.write(f"\x1b[{self._rendered_lines}A")
            for index in range(reserved_lines):
                line = lines[index] if index < len(lines) else ""
                self.stream.write("\r\x1b[2K" + line + "\n")
            self.stream.flush()
            self._rendered_lines = reserved_lines
            return

        for key, state in self._models.items():
            lines.extend(self._model_lines(key, state, width))

        # A redirected log cannot be redrawn in place; emit periodic summaries.
        emit = (
            status in {"starting", "model complete", "model incomplete", "run state loaded", "cancelled before dispatch"}
            or "failed" in status
            or bool(self._batch_notice)
        )
        for key, state in self._models.items():
            interval = max(1, state.total // 10)
            last = self._non_tty_last_completed.get(key, -1)
            if state.completed and state.completed % interval == 0 and state.completed != last:
                self._non_tty_last_completed[key] = state.completed
                emit = True
        if emit:
            for line in lines:
                print(line, file=self.stream, flush=True)
