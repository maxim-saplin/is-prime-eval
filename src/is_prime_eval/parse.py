"""Strict parser for the benchmark's PRIME/COMPOSITE response contract."""

import re
from typing import Literal


Label = Literal["PRIME", "COMPOSITE"]
_RESPONSE_RE = re.compile(r"\s*(PRIME|COMPOSITE)[.!?]?\s*", re.IGNORECASE)


def parse_response(raw_response: str | None) -> Label | None:
    """Return a label only for an otherwise bare, unambiguous model response.

    Case and surrounding whitespace are ignored; one optional terminal period,
    exclamation mark, or question mark is accepted. Explanations, refusals,
    extra labels, and malformed output return ``None``.
    """
    if not isinstance(raw_response, str):
        return None
    match = _RESPONSE_RE.fullmatch(raw_response)
    if match is None:
        return None
    if match.group(1).upper() == "PRIME":
        return "PRIME"
    return "COMPOSITE"
