"""Deterministic, balanced case generation for the primality benchmark."""

from dataclasses import dataclass
import random
from typing import Iterable, Literal


Label = Literal["PRIME", "COMPOSITE"]
PRIME: Label = "PRIME"
COMPOSITE: Label = "COMPOSITE"
CASE_GENERATOR_VERSION = "v1"
MAX_SUPPORTED_DEPTH = 15
MAX_SUPPORTED_NUMBER = 10**MAX_SUPPORTED_DEPTH - 1
_DETERMINISTIC_MR64_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
_SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


@dataclass(frozen=True)
class Case:
    """One integer classification item and its ground-truth label."""

    case_id: str
    depth: int
    number: int
    label: Label


def is_prime(number: int) -> bool:
    """Return exact primality for integers in the supported (at most 15-digit) range.

    The seven deterministic Miller-Rabin witnesses below are proven for every
    unsigned 64-bit integer; the supported maximum (10**15 - 1) is in that range.
    Small-prime division handles trivial factors before modular exponentiation.
    """
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError("number must be an integer")
    if number > MAX_SUPPORTED_NUMBER:
        raise ValueError(
            f"number exceeds the supported {MAX_SUPPORTED_DEPTH}-digit maximum"
        )
    if number < 2:
        return False
    for prime in _SMALL_PRIMES:
        if number % prime == 0:
            return number == prime

    odd_part = number - 1
    powers_of_two = 0
    while odd_part % 2 == 0:
        powers_of_two += 1
        odd_part //= 2

    for witness in _DETERMINISTIC_MR64_BASES:
        base = witness % number
        if base in (0, 1):
            continue
        value = pow(base, odd_part, number)
        if value in (1, number - 1):
            continue
        for _ in range(powers_of_two - 1):
            value = (value * value) % number
            if value == number - 1:
                break
        else:
            return False
    return True


def generate_supplemental_cases(
    parent_cases: Iterable[Case],
    *,
    target_depth: int,
    existing_depths_per_class: int,
    new_depths_per_class: int,
    seed: int,
) -> tuple[list[Case], list[Case]]:
    """Generate disjoint top-ups for parent depths and cases for missing deeper bands.

    The returned pair is ``(top_up_cases, new_depth_cases)``. Parent values are
    excluded at their depth; one RNG stream is shared across both groups so the
    supplement is frozen reproducibly from a single extension seed.
    """
    parents = list(parent_cases)
    if not parents:
        raise ValueError("parent case set must not be empty")
    if isinstance(target_depth, bool) or not isinstance(target_depth, int):
        raise TypeError("target_depth must be an integer")
    if not 1 <= target_depth <= MAX_SUPPORTED_DEPTH:
        raise ValueError(f"target_depth must be between 1 and {MAX_SUPPORTED_DEPTH}")
    for name, value in (
        ("existing_depths_per_class", existing_depths_per_class),
        ("new_depths_per_class", new_depths_per_class),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
    if existing_depths_per_class < 0:
        raise ValueError("existing_depths_per_class cannot be negative")
    if new_depths_per_class <= 0:
        raise ValueError("new_depths_per_class must be positive")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    parent_depths = sorted({case.depth for case in parents})
    if target_depth < max(parent_depths):
        raise ValueError("target_depth cannot be below the parent's maximum depth")
    if any(not 1 <= depth <= MAX_SUPPORTED_DEPTH for depth in parent_depths):
        raise ValueError("parent cases contain an unsupported digit depth")
    parent_ids = [case.case_id for case in parents]
    if len(set(parent_ids)) != len(parent_ids):
        raise ValueError("parent case IDs must be unique")

    existing_numbers: dict[int, set[int]] = {}
    for case in parents:
        expected = PRIME if is_prime(case.number) else COMPOSITE
        if case.label != expected or len(str(case.number)) != case.depth:
            raise ValueError("parent case labels/depths do not match the exact oracle")
        existing_numbers.setdefault(case.depth, set()).add(case.number)

    new_depths = [
        depth
        for depth in range(min(parent_depths), target_depth + 1)
        if depth not in existing_numbers
    ]
    rng = random.Random(seed)

    def draw_for_depth(depth: int, count_per_class: int) -> list[Case]:
        if count_per_class == 0:
            return []
        lower, upper = 10 ** (depth - 1), 10**depth - 1
        used = set(existing_numbers.get(depth, set()))
        generated: list[Case] = []
        max_draws = max(10_000, count_per_class * 1_000)
        for target_label in (PRIME, COMPOSITE):
            accepted = 0
            for _ in range(max_draws):
                number = rng.randint(lower, upper)
                if number in used:
                    continue
                actual_label = PRIME if is_prime(number) else COMPOSITE
                if actual_label != target_label:
                    continue
                used.add(number)
                generated.append(
                    Case(case_id=f"d{depth}-{number}", depth=depth, number=number, label=target_label)
                )
                accepted += 1
                if accepted == count_per_class:
                    break
            else:
                raise RuntimeError(
                    f"could not sample {count_per_class} unique {target_label} "
                    f"numbers at depth {depth} after {max_draws} draws"
                )
        rng.shuffle(generated)
        return generated

    top_up_cases: list[Case] = []
    for depth in parent_depths:
        top_up_cases.extend(draw_for_depth(depth, existing_depths_per_class))
    new_depth_cases: list[Case] = []
    for depth in new_depths:
        new_depth_cases.extend(draw_for_depth(depth, new_depths_per_class))
    return top_up_cases, new_depth_cases


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
