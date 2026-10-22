"""Fair run-wide pacing and cooldown for completion dispatches."""

from __future__ import annotations

from collections import deque
import math
import threading
import time
from typing import Any, Callable


class AccountRequestGate:
    """Serialize request starts across workers with spacing and shared cooldowns.

    One instance must be shared by every model worker in a batch. It coordinates
    workers in this process; other processes or clients using the same API key
    must be quiescent or use an equivalent shared gate.
    """

    def __init__(
        self,
        min_interval_seconds: float,
        *,
        default_429_cooldown_seconds: float = 60.0,
    ) -> None:
        if not math.isfinite(min_interval_seconds) or min_interval_seconds <= 0:
            raise ValueError("minimum request interval must be a finite positive number")
        if (
            not math.isfinite(default_429_cooldown_seconds)
            or default_429_cooldown_seconds <= 0
        ):
            raise ValueError("default 429 cooldown must be a finite positive number")
        self.min_interval_seconds = float(min_interval_seconds)
        self.default_429_cooldown_seconds = float(default_429_cooldown_seconds)
        self._condition = threading.Condition()
        self._waiters: deque[object] = deque()
        self._next_allowed_at = 0.0
        self._cooldown_until = 0.0

    def acquire(
        self,
        cancel_event: Any = None,
        *,
        on_admitted: Callable[[], bool] | None = None,
    ) -> bool:
        """Wait fairly for a dispatch slot; invoke the start callback at admission."""
        ticket = object()
        with self._condition:
            self._waiters.append(ticket)

        while True:
            with self._condition:
                if cancel_event is not None and cancel_event.is_set():
                    self._waiters.remove(ticket)
                    self._condition.notify_all()
                    return False

                is_first = bool(self._waiters) and self._waiters[0] is ticket
                now = time.monotonic()
                if is_first:
                    delay = max(self._next_allowed_at, self._cooldown_until) - now
                    if delay <= 0:
                        try:
                            admitted = on_admitted is None or on_admitted()
                        except BaseException:
                            self._waiters.popleft()
                            self._condition.notify_all()
                            raise
                        self._waiters.popleft()
                        if not admitted:
                            self._condition.notify_all()
                            return False
                        self._next_allowed_at = (
                            time.monotonic() + self.min_interval_seconds
                        )
                        self._condition.notify_all()
                        return True
                else:
                    delay = 0.25

                timeout = min(0.1, delay) if cancel_event is not None else delay
                self._condition.wait(timeout=max(0.0, timeout))

    def cool_down(self, retry_after_seconds: float | None = None) -> float:
        """Pause every worker after a 429 and return the cooldown applied."""
        try:
            requested = float(retry_after_seconds) if retry_after_seconds is not None else 0.0
        except (TypeError, ValueError):
            requested = 0.0
        if not math.isfinite(requested):
            requested = 0.0
        cooldown = max(
            self.default_429_cooldown_seconds,
            requested,
            self.min_interval_seconds,
        )
        with self._condition:
            deadline = time.monotonic() + cooldown
            self._cooldown_until = max(self._cooldown_until, deadline)
            self._next_allowed_at = max(self._next_allowed_at, self._cooldown_until)
            self._condition.notify_all()
        return cooldown
