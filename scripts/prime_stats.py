#!/usr/bin/env python3
"""Generate exact prime counts for 4–15 digit integers in docs/prime-stats.md.

Setup and run from the repository root:
    python3 -m venv .venv
    .venv/bin/python -m pip install -e '.[stats]'
    .venv/bin/python scripts/prime_stats.py

Uses libprimecount through primecountpy; does not enumerate or store primes.
"""

from decimal import Decimal
from pathlib import Path

from primecountpy import prime_pi


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "prime-stats.md"


def generate_report() -> str:
    """Count primes in each inclusive band using differences of exact π(x)."""
    lines = [
        "# Prime statistics: 4–15 digits",
        "",
        "Exact counts for all positive integers in each inclusive digit band.",
        "Percentages use all integers in the band as the denominator and are",
        "rounded to eight decimal places (not sampled or estimated).",
        "",
        "| Digits | Minimum | Maximum | Integers | Primes | Prime percentage |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    previous_count = prime_pi(10**3 - 1)
    for digits in range(4, 16):
        lower = 10 ** (digits - 1)
        upper = 10**digits - 1
        cumulative_count = prime_pi(upper)
        prime_count = cumulative_count - previous_count
        total = upper - lower + 1
        percentage = Decimal(prime_count) * 100 / Decimal(total)
        lines.append(
            f"| {digits} | {lower:,} | {upper:,} | {total:,} "
            f"| {prime_count:,} | {percentage:.8f}% |"
        )
        previous_count = cumulative_count
        print(f"{digits} digits: {prime_count:,} primes ({percentage:.8f}%)", flush=True)
    lines.extend([
        "",
        "## Method",
        "",
        "Computed with `primecountpy` (libprimecount's exact prime-counting algorithm).",
        "For a band `[L, U]`, the count is `π(U) − π(L − 1)`, where `π(x)` counts",
        "primes less than or equal to `x`. The percentage is `100 × count / (U − L + 1)`.",
        "No individual primes are enumerated or saved.",
        "",
        "Regenerate from the repository root:",
        "",
        "```sh",
        ".venv/bin/python scripts/prime_stats.py",
        "```",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    report = generate_report()
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
