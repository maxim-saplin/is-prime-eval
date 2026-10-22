"""Crash-aware append-only JSONL event ledger."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


class LedgerCorruptionError(ValueError):
    """Raised when a complete (newline-terminated) event is invalid JSON."""


class LedgerLockedError(OSError):
    """Raised when another process currently owns a run ledger."""


@contextmanager
def ledger_lock(path: str | Path):
    """Hold an OS advisory lock for the full run/enrichment mutation window.

    The `.lock` file may remain after exit or a crash; ownership is determined
    only by `flock`, so stale files never strand a run.
    """
    ledger = Path(path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(f"{ledger}.lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    locked = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except BlockingIOError:
            raise LedgerLockedError(f"run ledger is already owned: {ledger}") from None
        os.ftruncate(fd, 0)
        os.write(fd, f"pid={os.getpid()}\n".encode("ascii"))
        os.fsync(fd)
        yield
    finally:
        if locked:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_events(
    path: str | Path, *, repair_torn_tail: bool = False
) -> tuple[list[dict[str, Any]], int]:
    """Read newline-terminated events and optionally remove an incomplete tail.

    The runner fsyncs every event before its next action. Therefore a final
    unterminated line is not a committed event. When resuming, its exact bytes
    are preserved in ``<ledger>.torn`` before the ledger is truncated. Invalid
    JSON in a complete line is treated as corruption rather than skipped.
    Returns (events, number_of_discarded_tail_bytes).
    """
    ledger = Path(path)
    if not ledger.exists():
        return [], 0
    raw = ledger.read_bytes()
    if not raw:
        return [], 0

    discarded = 0
    if not raw.endswith(b"\n"):
        last_newline = raw.rfind(b"\n")
        keep_length = last_newline + 1
        tail = raw[keep_length:]
        discarded = len(tail)
        if not repair_torn_tail:
            raise LedgerCorruptionError(
                f"ledger has an unterminated trailing record ({discarded} bytes)"
            )
        torn_path = Path(f"{ledger}.torn")
        if tail:
            with torn_path.open("ab") as torn_file:
                torn_file.write(tail)
                torn_file.flush()
                os.fsync(torn_file.fileno())
        with ledger.open("r+b") as ledger_file:
            ledger_file.truncate(keep_length)
            ledger_file.flush()
            os.fsync(ledger_file.fileno())
        raw = raw[:keep_length]

    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerCorruptionError(
                f"invalid JSON event at line {line_number}"
            ) from exc
        if not isinstance(event, dict):
            raise LedgerCorruptionError(
                f"event at line {line_number} must be a JSON object"
            )
        events.append(event)
    return events, discarded


def append_event(path: str | Path, event: Mapping[str, Any]) -> dict[str, Any]:
    """Append and fsync one event before returning it to the caller."""
    ledger = Path(path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    record = dict(event)
    record.setdefault("event_id", uuid4().hex)
    record.setdefault("timestamp", _utc_now())
    encoded = (json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str) + "\n").encode("utf-8")

    fd = os.open(ledger, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        view = memoryview(encoded)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("failed to append event ledger record")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    return record
