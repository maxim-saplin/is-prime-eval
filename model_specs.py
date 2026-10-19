"""Parse model qualifiers for repeatable, parallel evaluation runs."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


_ALLOWED_EFFORTS = frozenset({"low", "medium", "high"})
_EFFORT_SUFFIX = re.compile(r"^(?P<model>.+)-(?P<effort>low|medium|high)$", re.IGNORECASE)
_ALIAS_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


@dataclass(frozen=True)
class ModelSpec:
    """One model request and the label/effort used to run it."""

    requested_model: str
    display_model: str
    reasoning_effort: str | None


def _normalize_effort(value: str | None, *, parameter_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{parameter_name} must be a string or None")
    effort = value.strip().lower()
    if effort not in _ALLOWED_EFFORTS:
        allowed = ", ".join(sorted(_ALLOWED_EFFORTS))
        raise ValueError(f"{parameter_name} must be one of: {allowed}")
    return effort


def _split_model_effort(model_text: str) -> tuple[str, str | None]:
    """Separate a recognized final ``:effort`` or ``-effort`` qualifier."""
    if ":" in model_text:
        if model_text.count(":") != 1:
            raise ValueError("model qualifier may contain only one effort separator ':'")
        model, effort_text = model_text.rsplit(":", 1)
        effort = _normalize_effort(effort_text, parameter_name="reasoning effort")
        if effort is None:
            raise ValueError("reasoning effort must not be empty")
        if _EFFORT_SUFFIX.fullmatch(model):
            raise ValueError("specify reasoning effort only once")
    else:
        match = _EFFORT_SUFFIX.fullmatch(model_text)
        if match is None:
            model, effort = model_text, None
        else:
            model = match.group("model")
            effort = match.group("effort").lower()
            if _EFFORT_SUFFIX.fullmatch(model):
                raise ValueError("specify reasoning effort only once")

    if not model:
        raise ValueError("model ID must not be empty")
    return model, effort


def parse_model_qualifier(
    text: str, default_effort: str | None = "low"
) -> ModelSpec:
    """Parse one model ID, optional effort suffix, and optional display alias.

    Supported forms include ``gpt-6-luna-low``,
    ``openai/gpt-6-luna:medium``, and ``baseline=openai/gpt-6-luna:medium``.
    A missing effort uses ``default_effort``. An explicit alias replaces the
    automatically derived short display name but does not change the API model ID.
    """
    normalized_default = _normalize_effort(
        default_effort, parameter_name="default_effort"
    )
    if not isinstance(text, str):
        raise TypeError("model qualifier must be a string")
    qualifier = text.strip()
    if not qualifier:
        raise ValueError("model qualifier must not be empty")

    alias: str | None = None
    if "=" in qualifier:
        if qualifier.count("=") != 1:
            raise ValueError("model qualifier may contain only one '='")
        alias_text, qualifier = qualifier.split("=", 1)
        alias = alias_text.strip()
        qualifier = qualifier.strip()
        if not alias:
            raise ValueError("model alias must not be empty")
        if not _ALIAS_RE.fullmatch(alias):
            raise ValueError(
                "model alias must start with a letter or digit and contain only "
                "letters, digits, '.', '_' or '-'"
            )

    if not qualifier:
        raise ValueError("model ID must not be empty")
    if any(character.isspace() for character in qualifier):
        raise ValueError("model ID must not contain whitespace")

    requested_model, explicit_effort = _split_model_effort(qualifier)
    effort = explicit_effort if explicit_effort is not None else normalized_default
    short_model_name = requested_model.rsplit("/", 1)[-1]
    display_model = alias or (
        f"{short_model_name}-{effort}" if effort is not None else short_model_name
    )
    return ModelSpec(
        requested_model=requested_model,
        display_model=display_model,
        reasoning_effort=effort,
    )


def parse_model_qualifiers(
    texts: Iterable[str], default_effort: str | None = "low"
) -> list[ModelSpec]:
    """Parse a repeatable qualifier list and reject duplicate display names.

    Distinct explicit aliases may deliberately refer to the same model and effort;
    repeated implicit names or aliases are rejected so leaderboard entries remain
    distinguishable. Duplicate detection is case-insensitive.
    """
    _normalize_effort(default_effort, parameter_name="default_effort")
    if isinstance(texts, str):
        raise TypeError("model qualifiers must be an iterable of strings, not a string")
    try:
        qualifiers = list(texts)
    except TypeError as exc:
        raise TypeError("model qualifiers must be an iterable of strings") from exc

    specs: list[ModelSpec] = []
    names_seen: set[str] = set()
    for text in qualifiers:
        spec = parse_model_qualifier(text, default_effort=default_effort)
        normalized_name = spec.display_model.casefold()
        if normalized_name in names_seen:
            raise ValueError(
                f"duplicate model display name or alias: {spec.display_model!r}; "
                "supply distinct aliases for repeated models"
            )
        names_seen.add(normalized_name)
        specs.append(spec)
    return specs
