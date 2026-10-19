"""Thread-safe per-model progress, elapsed/ETA and output-token throughput."""

from __future__ import annotations

from dataclasses import dataclass, field
import sys
import threading
import time
from typing import Any, TextIO


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
    active_status: str = "waiting for response"


class ProgressReporter:
    """Write independent per-model progress lines and a separate batch clock.

    OpenRouter calls are non-streaming: completion tokens are added to the
    observed rate only after usage arrives. Token counts include reasoning when
    it is part of the provider's completion total.
    """

    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        heartbeat_interval: float = 5.0,
    ) -> None:
        # Keep progress on stderr so stdout remains suitable for piping reports.
        self.stream = stream or sys.stderr
        self._lock = threading.Lock()
        self._models: dict[str, _ModelProgress] = {}
        self._batch_started = time.monotonic()
        self._batch_total: int | None = None
        self._finished_models: set[str] = set()
        self._heartbeat_interval = max(0.1, heartbeat_interval)
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

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

    def register_model(
        self,
        model: str,
        total: int,
        *,
        initial_completed: int = 0,
        initial_correct: int = 0,
        initial_incorrect: int = 0,
    ) -> None:
        with self._lock:
            if model in self._models:
                raise ValueError(f"duplicate progress display name: {model}")
            self._models[model] = _ModelProgress(
                total=total,
                started_at=time.monotonic(),
                initial_completed=initial_completed,
                completed=initial_completed,
                correct=initial_correct,
                incorrect=initial_incorrect,
            )
            self._print_locked(model, self._models[model], "starting")

    def _start_heartbeat_locked(self) -> None:
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
                for model, state in self._models.items():
                    if state.active_case is None or model in self._finished_models:
                        continue
                    attempt = state.active_attempt or 1
                    maximum = state.active_max_attempts or 1
                    self._print_locked(
                        model,
                        state,
                        f"{state.active_status} {state.active_case} attempt {attempt}/{maximum}",
                    )

    def model_finished(self, model: str, *, success: bool) -> None:
        """Report batch elapsed separately when one model worker exits."""
        with self._lock:
            if model in self._finished_models:
                return
            self._finished_models.add(model)
            model_state = self._models.get(model)
            if model_state is not None:
                model_state.active_case = None
            total = self._batch_total if self._batch_total is not None else len(self._models)
            elapsed = _duration(time.monotonic() - self._batch_started)
            status = "complete" if success else "failed/incomplete"
            print(
                f"[batch] {len(self._finished_models)}/{total} model runs finished "
                f"| batch elapsed {elapsed} | {model}: {status}",
                file=self.stream,
                flush=True,
            )
            if total > 0 and len(self._finished_models) >= total:
                self._heartbeat_stop.set()

    def __call__(self, event: dict[str, Any]) -> None:
        model = str(event.get("display_model", "model"))
        with self._lock:
            state = self._models.get(model)
            if state is None:
                total = int(event.get("total_cases", 0))
                state = _ModelProgress(total=total, started_at=time.monotonic())
                self._models[model] = state

            event_type = event.get("event")
            if event_type == "run_progress_init":
                state.total = int(event.get("total_cases", state.total))
                state.initial_completed = int(event.get("completed_cases", 0))
                state.completed = state.initial_completed
                state.correct = int(event.get("correct", 0))
                state.incorrect = int(event.get("incorrect", 0))
                state.started_at = time.monotonic()
                state.active_case = None
                self._print_locked(model, state, "run state loaded")
                return
            if event_type == "attempt_started":
                state.active_case = str(event.get("case_id", "request"))
                state.active_attempt = int(event.get("attempt_number") or 1)
                state.active_max_attempts = int(event.get("max_attempts") or 1)
                state.active_status = "waiting for response to"
                self._start_heartbeat_locked()
                self._print_locked(
                    model,
                    state,
                    f"request {state.active_attempt}/{state.active_max_attempts} started for {state.active_case}",
                )
                return

            if event_type == "attempt_cancelled_before_dispatch":
                state.active_case = None
                self._print_locked(model, state, "cancelled before dispatch")
                return

            if event_type == "attempt_failed":
                count = event.get("completion_tokens")
                if isinstance(count, int) and count >= 0:
                    state.output_tokens += count
                attempt = event.get("attempt_number", "?")
                total_attempts = event.get("max_attempts", "?")
                reason = event.get("reason", "request failed")
                state.active_case = str(event.get("case_id", state.active_case or "request"))
                state.active_attempt = int(attempt) if isinstance(attempt, int) else None
                state.active_max_attempts = int(total_attempts) if isinstance(total_attempts, int) else None
                state.active_status = "retrying after failure"
                self._print_locked(model, state, f"attempt {attempt}/{total_attempts} failed: {reason}")
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
            self._print_locked(model, state, outcome)

    def _print_locked(self, model: str, state: _ModelProgress, status: str) -> None:
        elapsed = max(0.0, time.monotonic() - state.started_at)
        completed_this_session = max(0, state.completed - state.initial_completed)
        remaining_cases = max(0, state.total - state.completed)
        eta = (
            _duration(elapsed * remaining_cases / completed_this_session)
            if completed_this_session > 0
            else "--:--:--"
        )
        token_rate = state.output_tokens / elapsed if elapsed > 0 else 0.0
        percent = (100.0 * state.completed / state.total) if state.total else 0.0
        print(
            f"[{model}] {state.completed}/{state.total} ({percent:.1f}%) "
            f"elapsed {_duration(elapsed)} ETA {eta} "
            f"observed output {token_rate:.1f} tok/s "
            f"correct {state.correct}, incorrect {state.incorrect} [{status}]",
            file=self.stream,
            flush=True,
        )
