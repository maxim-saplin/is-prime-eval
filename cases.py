"""Deterministic, balanced case generation for the primality benchmark."""

from dataclasses import dataclass
from math import isqrt
import random
from typing import Iterable, Literal


Label = Literal["PRIME", "COMPOSITE"]
PRIME: Label = "PRIME"
COMPOSITE: Label = "COMPOSITE"
CASE_GENERATOR_VERSION = "v1"
MAX_SUPPORTED_DEPTH = 10
MAX_SUPPORTED_NUMBER = 10**MAX_SUPPORTED_DEPTH - 1


@dataclass(frozen=True)
class Case:
    """One integer classification item and its ground-truth label."""

    case_id: str
    depth: int
    number: int
    label: Label


def is_prime(number: int) -> bool:
    """Return exact primality for integers in the supported (at most 10-digit) range.

    Trial division through ``isqrt(number)`` is deterministic and simple to audit;
    the largest supported input requires checking only odd divisors below 100,000.
    """
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError("number must be an integer")
    if number > MAX_SUPPORTED_NUMBER:
        raise ValueError(
            f"number exceeds the supported {MAX_SUPPORTED_DEPTH}-digit maximum"
        )
    if number < 2:
        return False
    if number % 2 == 0:
        return number == 2
    for divisor in range(3, isqrt(number) + 1, 2):
        if number % divisor == 0:
            return False
    return True


def _validate_depths(depths: Iterable[int]) -> list[int]:
    try:
        requested = list(depths)
    except TypeError as exc:
        raise TypeError("depths must be an iterable of integers") from exc
    if not requested:
        raise ValueError("depths must not be empty")
    for depth in requested:
        if isinstance(depth, bool) or not isinstance(depth, int):
            raise TypeError("each depth must be an integer")
        if not 1 <= depth <= MAX_SUPPORTED_DEPTH:
            raise ValueError(f"depths must be between 1 and {MAX_SUPPORTED_DEPTH}")
    if len(set(requested)) != len(requested):
        raise ValueError("depths must not contain duplicates")
    return requested


def generate_cases(
    depths: Iterable[int], samples_per_class: int, seed: int
) -> list[Case]:
    """Generate seeded, class-balanced cases by uniform rejection sampling.

    Within each digit band, candidates are drawn uniformly at random and accepted
    only for the class currently being sampled. Duplicate values are discarded.
    IDs are derived from depth and number, so they remain stable if output order
    changes or the cases are regenerated with the same values.
    """
    validated_depths = _validate_depths(depths)
    if (
        isinstance(samples_per_class, bool)
        or not isinstance(samples_per_class, int)
    ):
        raise TypeError("samples_per_class must be an integer")
    if samples_per_class <= 0:
        raise ValueError("samples_per_class must be positive")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    rng = random.Random(seed)
    cases: list[Case] = []

    for depth in validated_depths:
        lower = 10 ** (depth - 1)
        upper = 10**depth - 1
        used_numbers: set[int] = set()
        depth_cases: list[Case] = []
        max_draws = max(10_000, samples_per_class * 1_000)

        for target_label in (PRIME, COMPOSITE):
            accepted = 0
            for _ in range(max_draws):
                number = rng.randint(lower, upper)
                if number in used_numbers:
                    continue
                actual_label = PRIME if is_prime(number) else COMPOSITE
                if actual_label != target_label:
                    continue
                used_numbers.add(number)
                depth_cases.append(
                    Case(
                        case_id=f"d{depth}-{number}",
                        depth=depth,
                        number=number,
                        label=target_label,
                    )
                )
                accepted += 1
                if accepted == samples_per_class:
                    break
            else:
                raise RuntimeError(
                    f"could not sample {samples_per_class} unique {target_label} "
                    f"numbers at depth {depth} after {max_draws} draws; "
                    "reduce the sample count or use a larger digit depth"
                )

        # Avoid presenting all cases for a depth grouped by class.
        rng.shuffle(depth_cases)
        cases.extend(depth_cases)

    return cases
