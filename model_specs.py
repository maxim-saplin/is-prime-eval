"""Load explicit model/run settings from a JSON manifest."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal


ReasoningEffort = Literal["low", "medium"]
_REQUIRED_FIELDS = frozenset({"model_id", "reasoning_effort"})
_ALLOWED_EFFORTS = frozenset({"low", "medium"})


@dataclass(frozen=True)
class ModelSpec:
    """One explicitly configured model run."""

    model_id: str
    reasoning_effort: ReasoningEffort


def _validate_model_id(value: object, *, index: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"model_specs[{index}].model_id must be a non-empty string")
    if value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(f"model_specs[{index}].model_id must not contain whitespace")
    if "/" not in value or value.startswith("/") or value.endswith("/") or "//" in value:
        raise ValueError(
            f"model_specs[{index}].model_id must be a fully qualified ID containing '/'"
        )
    return value


def _validate_effort(value: object, *, index: int) -> ReasoningEffort:
    if not isinstance(value, str) or value not in _ALLOWED_EFFORTS:
        raise ValueError(
            f"model_specs[{index}].reasoning_effort must be exactly 'low' or 'medium'"
        )
    return value  # type: ignore[return-value]


def load_model_specs(path: str | Path) -> list[ModelSpec]:
    """Load model specs from a JSON file, preserving order and rejecting duplicate runs.

    The document must be a non-empty JSON array. Each element must be an object
    containing exactly ``model_id`` and ``reasoning_effort``. Model IDs must be
    fully qualified (include a non-empty provider and model path separated by
    ``/``), and effort must be explicitly ``low`` or ``medium``.
    """
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid model specs JSON in {source}: {exc.msg}") from exc

    if not isinstance(data, list):
        raise ValueError("model specs file must contain a JSON array")
    if not data:
        raise ValueError("model specs array must not be empty")

    specs: list[ModelSpec] = []
    identities: set[tuple[str, str]] = set()
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"model_specs[{index}] must be an object")
        fields = set(row)
        if fields != _REQUIRED_FIELDS:
            missing = sorted(_REQUIRED_FIELDS - fields)
            extra = sorted(fields - _REQUIRED_FIELDS)
            details = []
            if missing:
                details.append(f"missing fields: {', '.join(missing)}")
            if extra:
                details.append(f"unexpected fields: {', '.join(extra)}")
            raise ValueError(f"model_specs[{index}] has invalid fields ({'; '.join(details)})")
        spec = ModelSpec(
            model_id=_validate_model_id(row["model_id"], index=index),
            reasoning_effort=_validate_effort(
                row["reasoning_effort"], index=index
            ),
        )
        identity = (spec.model_id, spec.reasoning_effort)
        if identity in identities:
            raise ValueError(
                f"duplicate model run identity at model_specs[{index}]: "
                f"{spec.model_id} with reasoning_effort={spec.reasoning_effort}"
            )
        identities.add(identity)
        specs.append(spec)
    return specs
