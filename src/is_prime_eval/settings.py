"""Small project-local environment loader (no dotenv dependency)."""

from __future__ import annotations

import os
import re
from pathlib import Path

WORKSPACE_ROOT = Path.cwd()
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_dotenv(path: str | Path | None = None, *, override: bool = False) -> bool:
    """Load simple KEY=value entries; existing process environment wins by default.

    Values may be unquoted or wrapped in matching single/double quotes. This is
    intentionally not a shell parser; it supports the project's `.env` format.
    Returns whether the file existed. Secret values are never printed.
    """
    env_path = Path(path) if path is not None else WORKSPACE_ROOT / ".env"
    if not env_path.is_file():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not _ENV_NAME.fullmatch(name):
            continue
        value = value.strip()
        if value and value[0] in "\"'":
            quote = value[0]
            closing = value.find(quote, 1)
            suffix = value[closing + 1 :].strip() if closing >= 0 else "invalid"
            if closing >= 0 and (not suffix or suffix.startswith("#")):
                value = value[1:closing]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if override:
            os.environ[name] = value
        else:
            os.environ.setdefault(name, value)
    return True


def get_openrouter_key() -> str | None:
    """Return the configured key without exposing it to logs or manifests."""
    return os.environ.get("OR_KEY") or os.environ.get("OPENROUTER_API_KEY")
