"""Validate repeated, separately specified model-ID/effort CLI options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ModelSpec:
    """One OpenRouter model ID and its explicitly provided reasoning effort."""

    model_id: str
    reasoning_effort: str


def parse_model_specs(
    model_ids: Sequence[str] | None,
    reasoning_efforts: Sequence[str] | None,
) -> list[ModelSpec]:
    """Pair repeated CLI values by order; never infer effort from the model ID.

    Every `--model-id` must have one corresponding `--reasoning-effort`.
    Effort values are passed through as supplied, allowing the selected provider
    and model to determine which non-empty levels they accept.
    """
    if isinstance(model_ids, str) or isinstance(reasoning_efforts, str):
        raise TypeError("model IDs and efforts must be supplied as repeated CLI values")
    ids = list(model_ids or [])
    efforts = list(reasoning_efforts or [])
    if not ids:
        raise ValueError("provide at least one --model-id")
    if len(ids) != len(efforts):
        raise ValueError(
            "provide exactly one --reasoning-effort for each --model-id, in the same order"
        )

    specs: list[ModelSpec] = []
    identities: set[tuple[str, str]] = set()
    for index, (model_id, effort) in enumerate(zip(ids, efforts)):
        if not isinstance(model_id, str) or not model_id:
            raise ValueError(f"model_id at position {index + 1} must be non-empty")
        if model_id != model_id.strip() or any(character.isspace() for character in model_id):
            raise ValueError(f"model_id at position {index + 1} must not contain whitespace")
        if "/" not in model_id or model_id.startswith("/") or model_id.endswith("/") or "//" in model_id:
            raise ValueError(
                f"model_id at position {index + 1} must be fully qualified (author/model)"
            )
        if not isinstance(effort, str) or not effort or effort != effort.strip():
            raise ValueError(
                f"reasoning_effort at position {index + 1} must be explicit and non-empty"
            )
        if any(character.isspace() for character in effort):
            raise ValueError(
                f"reasoning_effort at position {index + 1} must not contain whitespace"
            )
        identity = (model_id, effort)
        if identity in identities:
            raise ValueError(
                f"duplicate model_id/reasoning_effort pair at position {index + 1}: "
                f"{model_id} / {effort}"
            )
        identities.add(identity)
        specs.append(ModelSpec(model_id, effort))
    return specs
