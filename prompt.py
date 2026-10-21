"""The fixed prompt used for primality classification."""

from cases import MAX_SUPPORTED_NUMBER


def make_prompt(number: int) -> str:
    """Format a supported positive integer as a PRIME/COMPOSITE task."""
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError("number must be an integer")
    if not 1 <= number <= MAX_SUPPORTED_NUMBER:
        raise ValueError("number must be a positive integer of at most 15 digits")
    return f"Is {number} prime? Reply with only PRIME or COMPOSITE."
