"""Token and dollar accounting for OpenRouter requests."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

MILLION = Decimal(1_000_000)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if number < 0:
        return None
    # Avoid silently truncating values such as 1.5.
    if isinstance(value, float) and not value.is_integer():
        return None
    if isinstance(value, str) and value.strip() != str(number):
        return None
    return number


def as_decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not result.is_finite() or result < 0:
        return None
    return result


def extract_usage(response: Mapping[str, Any], generation: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize token counts and preserve OpenRouter/provider token variants.

    OpenRouter's completion `usage` counts are the first choice. Generation
    metadata also exposes normalized `tokens_*` and upstream-reported
    `native_tokens_*`; when native counts are available they are preferred for
    the uncached rate estimate. Reasoning tokens are a breakdown of completion
    tokens and are never added a second time.
    """
    usage = _mapping(response.get("usage"))
    gen_data = _mapping(_mapping(generation).get("data"))
    if not gen_data and generation:
        gen_data = _mapping(generation)

    api_prompt = _as_nonnegative_int(usage.get("prompt_tokens"))
    api_completion = _as_nonnegative_int(usage.get("completion_tokens"))
    generation_prompt = _as_nonnegative_int(gen_data.get("tokens_prompt"))
    generation_completion = _as_nonnegative_int(gen_data.get("tokens_completion"))
    native_prompt = _as_nonnegative_int(gen_data.get("native_tokens_prompt"))
    native_completion = _as_nonnegative_int(gen_data.get("native_tokens_completion"))

    prompt_tokens = api_prompt if api_prompt is not None else generation_prompt
    completion_tokens = api_completion if api_completion is not None else generation_completion
    if native_prompt is not None and native_completion is not None:
        estimate_prompt = native_prompt
        estimate_completion = native_completion
        estimate_source = "generation.native_tokens"
    elif api_prompt is not None and api_completion is not None:
        estimate_prompt = api_prompt
        estimate_completion = api_completion
        estimate_source = "completion.usage"
    elif generation_prompt is not None and generation_completion is not None:
        estimate_prompt = generation_prompt
        estimate_completion = generation_completion
        estimate_source = "generation.tokens"
    else:
        estimate_prompt = None
        estimate_completion = None
        estimate_source = None

    prompt_details = _mapping(usage.get("prompt_tokens_details"))
    if not prompt_details:
        prompt_details = _mapping(usage.get("input_tokens_details"))
    completion_details = _mapping(usage.get("completion_tokens_details"))
    if not completion_details:
        completion_details = _mapping(usage.get("output_tokens_details"))

    cached_tokens = None
    for key in ("cached_tokens", "cache_read_tokens", "cached_prompt_tokens"):
        cached_tokens = _as_nonnegative_int(prompt_details.get(key))
        if cached_tokens is not None:
            break
    if cached_tokens is None:
        cached_tokens = _as_nonnegative_int(usage.get("cached_tokens"))
    if cached_tokens is None:
        cached_tokens = _as_nonnegative_int(gen_data.get("native_tokens_cached"))

    reasoning_tokens = None
    for key in ("reasoning_tokens", "reasoning"):
        reasoning_tokens = _as_nonnegative_int(completion_details.get(key))
        if reasoning_tokens is not None:
            break
    if reasoning_tokens is None:
        reasoning_tokens = _as_nonnegative_int(gen_data.get("native_tokens_reasoning"))

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "native_prompt_tokens": native_prompt,
        "native_completion_tokens": native_completion,
        "estimate_prompt_tokens": estimate_prompt,
        "estimate_completion_tokens": estimate_completion,
        "estimate_token_source": estimate_source,
        "cached_prompt_tokens": cached_tokens,
        "reasoning_tokens": reasoning_tokens,
    }


def estimate_uncached_cost_usd(
    usage: Mapping[str, Any],
    input_rate_usd_per_million: Decimal | str | int | None,
    output_rate_usd_per_million: Decimal | str | int | None,
) -> Decimal | None:
    """Estimate normal uncached list-rate cost from reported token totals.

    All prompt tokens are priced at the regular input rate, including cache hits.
    """
    prompt_value = usage.get("estimate_prompt_tokens")
    completion_value = usage.get("estimate_completion_tokens")
    prompt_tokens = _as_nonnegative_int(
        prompt_value if prompt_value is not None else usage.get("prompt_tokens")
    )
    completion_tokens = _as_nonnegative_int(
        completion_value if completion_value is not None else usage.get("completion_tokens")
    )
    input_rate = as_decimal(input_rate_usd_per_million)
    output_rate = as_decimal(output_rate_usd_per_million)
    if None in (prompt_tokens, completion_tokens, input_rate, output_rate):
        return None
    return (
        Decimal(prompt_tokens) * input_rate
        + Decimal(completion_tokens) * output_rate
    ) / MILLION


def extract_provider_cost_usd(
    response: Mapping[str, Any], generation: Mapping[str, Any] | None = None
) -> Decimal | None:
    """Extract a dollar amount explicitly reported by OpenRouter, if present."""
    response = _mapping(response)
    usage = _mapping(response.get("usage"))
    top_level = _mapping(response.get("data"))
    gen_data = _mapping(_mapping(generation).get("data"))
    if not gen_data and generation:
        gen_data = _mapping(generation)

    candidates = (
        usage.get("cost"),
        response.get("cost"),
        top_level.get("total_cost"),
        top_level.get("cost"),
        gen_data.get("total_cost"),
        gen_data.get("cost"),
        _mapping(gen_data.get("usage")).get("cost"),
    )
    for candidate in candidates:
        parsed = as_decimal(candidate)
        if parsed is not None:
            return parsed
    return None


def decimal_text(value: Decimal | None) -> str | None:
    """Serialize a Decimal as an exact, non-exponent USD string."""
    if value is None:
        return None
    return format(value, "f")
