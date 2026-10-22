"""Allow `python -m is_prime_eval` to run the evaluator CLI."""

from .cli import entrypoint

if __name__ == "__main__":
    raise SystemExit(entrypoint())
