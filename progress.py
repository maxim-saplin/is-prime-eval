"""Thread-safe terminal progress bars for one or more model runs."""

from __future__ import annotations

from dataclasses import dataclass, field
import shutil
import sys
import threading
import time
from typing import Any, TextIO

ProgressKey = tuple[str, str]  # (fully qualified model ID, explicit effort)


def _duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@dataclass
class _ModelProgress:
    total: int
    started_at: float
    initial_completed: int = 0
    completed: int = 0
    output_tokens: int = 0
    correct: int = 0
    incorrect: int = 0
    seen_case_ids: set[str] = field(default_factory=set)
    active_case: str | None = None
    active_attempt: int | None = None
    active_max_attempts: int | None = None
    status: str = "starting"


class ProgressReporter:
    """Render an in-place multi-model dashboard on TTY; throttle piped logs.

    Requests are non-streaming: completion tokens become observable only after
    a response. The output tokens/s number is measured completion tokens
    (including reasoning, when reported) divided by this model run's elapsed
    wall time; it is not token-by-token generation speed.
    """

    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        heartbeat_interval: float = 5.0,
        force_tty: bool | None = None,
    ) -> None:
        # Keep progress on stderr so stdout remains suitable for piping reports.
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

    def __enter__(self) -> "ProgressReporter":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        self._heartbeat_stop.set()
        thread = self._heartbeat_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=self._heartbeat_interval + 1)

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
        reasoning_effort: str,
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
                if any(state.active_case is not None for state in self._models.values()):
                    self._render_locked("waiting for model response")

    def model_finished(
        self, model_id: str, reasoning_effort: str, *, success: bool
    ) -> None:
        """Report batch elapsed separately when one model worker exits."""
        key = (model_id, reasoning_effort)
        with self._lock:
            if key in self._finished_models:
                return
            self._finished_models.add(key)
            status = "complete" if success else "failed/incomplete"
            model_state = self._models.get(key)
            if model_state is not None:
                model_state.active_case = None
                model_state.status = status
            total = self._batch_total if self._batch_total is not None else len(self._models)
            if total > 0 and len(self._finished_models) >= total:
                self._heartbeat_stop.set()
            self._render_locked(status)

    def __call__(self, event: dict[str, Any]) -> None:
        model_id = str(event.get("model_id", "model"))
        effort = str(event.get("reasoning_effort", ""))
        key = (model_id, effort)
        with self._lock:
            state = self._models.get(key)
            if state is None:
                total = int(event.get("total_cases", 0))
                state = _ModelProgress(total=total, started_at=time.monotonic())
                self._models[key] = state

            event_type = event.get("event")
            if event_type == "run_progress_init":
                state.total = int(event.get("total_cases", state.total))
                state.initial_completed = int(event.get("completed_cases", 0))
                state.completed = state.initial_completed
                state.correct = int(event.get("correct", 0))
                state.incorrect = int(event.get("incorrect", 0))
                state.started_at = time.monotonic()
                state.active_case = None
                state.status = "run state loaded"
                self._render_locked(state.status)
                return

            if event_type == "attempt_started":
                state.active_case = str(event.get("case_id", "request"))
                state.active_attempt = int(event.get("attempt_number") or 1)
                state.active_max_attempts = int(event.get("max_attempts") or 1)
                state.status = f"request {state.active_attempt}/{state.active_max_attempts} started"
                self._start_heartbeat_locked()
                self._render_locked(state.status)
                return

            if event_type == "attempt_cancelled_before_dispatch":
                state.active_case = None
                state.status = "cancelled before dispatch"
                self._render_locked(state.status)
                return

            if event_type == "attempt_failed":
                count = event.get("completion_tokens")
                if isinstance(count, int) and count >= 0:
                    state.output_tokens += count
                attempt = event.get("attempt_number", "?")
                maximum = event.get("max_attempts", "?")
                state.active_case = str(event.get("case_id", state.active_case or "request"))
                state.active_attempt = int(attempt) if isinstance(attempt, int) else None
                state.active_max_attempts = int(maximum) if isinstance(maximum, int) else None
                state.status = f"attempt {attempt}/{maximum} failed; retry/backoff if allowed"
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
            state.completed = min(state.total, state.completed + 1)
            count = event.get("completion_tokens")
            if isinstance(count, int) and count >= 0:
                state.output_tokens += count
            outcome = str(event.get("outcome", "unknown"))
            if outcome == "correct":
                state.correct += 1
            elif outcome in {"wrong_label", "invalid_response", "no_response"}:
                state.incorrect += 1
            state.status = outcome
            self._render_locked(outcome)

    def _model_line(self, key: ProgressKey, state: _ModelProgress) -> str:
        model_id, effort = key
        model_label = model_id if len(model_id) <= 32 else model_id[:29] + "..."
        effort_label = effort if len(effort) <= 12 else effort[:9] + "..."
        elapsed = max(0.0, time.monotonic() - state.started_at)
        completed_this_session = max(0, state.completed - state.initial_completed)
        remaining_cases = max(0, state.total - state.completed)
        eta = (
            _duration(elapsed * remaining_cases / completed_this_session)
            if completed_this_session > 0
            else "--:--:--"
        )
        rate = state.output_tokens / elapsed if elapsed > 0 else 0.0
        ratio = state.completed / state.total if state.total else 0.0
        bar_width = 12
        filled = min(bar_width, int(ratio * bar_width))
        bar = "█" * filled + "░" * (bar_width - filled)
        return (
            f"{model_label} | {effort_label} | [{bar}] {state.completed}/{state.total} "
            f"{ratio * 100:.0f}% | elapsed {_duration(elapsed)} | ETA {eta} | "
            f"out {rate:.1f} tok/s | C{state.correct} W{state.incorrect}"
        )

    def _render_locked(self, status: str) -> None:
        total = self._batch_total if self._batch_total is not None else len(self._models)
        batch_elapsed = _duration(time.monotonic() - self._batch_started)
        header_status = self._batch_notice or status
        lines = [
            f"Prime eval | model runs {len(self._finished_models)}/{total} complete "
            f"| batch elapsed {batch_elapsed} | {header_status}"
        ]
        lines.extend(self._model_line(key, state) for key, state in self._models.items())

        if self._is_tty:
            if self._rendered_lines:
                self.stream.write(f"\x1b[{self._rendered_lines}A")
            width = max(40, shutil.get_terminal_size((120, 24)).columns - 1)
            for line in lines:
                rendered = line[:width]
                self.stream.write("\r\x1b[2K" + rendered + "\n")
            self.stream.flush()
            self._rendered_lines = len(lines)
            return

        # A redirected log cannot be redrawn in place; emit only an initial,
        # periodic-case, terminal or interrupted summary rather than every call.
        emit = (
            status in {"starting", "complete", "incomplete", "run state loaded", "attempt_cancelled_before_dispatch"}
            or status.startswith("attempt ")
            or bool(self._batch_notice)
        )
        for state in self._models.values():
            interval = max(1, state.total // 20)
            if state.completed and state.completed % interval == 0:
                emit = True
        if emit:
            for line in lines:
                print(line, file=self.stream, flush=True)
