#!/usr/bin/env python3
"""Run the prompt-only prime evaluation through OpenRouter."""

from __future__ import annotations

import argparse
from pathlib import Path
import os
import sys
from typing import Sequence

from openrouter import OpenRouterClient, OpenRouterError
from runner import (
    DEFAULT_DEPTHS,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_COMPLETION_TOKENS,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_SAMPLES_PER_CLASS,
    DEFAULT_SEED,
    DEFAULT_TIMEOUT_SECONDS,
    RunConfig,
    create_dry_run_plan,
    resume_run,
    run_new,
)
from settings import PROJECT_ROOT, get_openrouter_key, load_dotenv


def parse_depths(value: str) -> tuple[int, ...]:
    """Parse an inclusive depth range (``4-10``) or comma-separated list."""
    text = value.strip()
    if not text:
        raise argparse.ArgumentTypeError("depths must not be empty")
    try:
        if "-" in text and "," not in text:
            start_text, end_text = text.split("-", 1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ValueError
            depths = tuple(range(start, end + 1))
        else:
            depths = tuple(int(part.strip()) for part in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "depths must be an inclusive range like 4-10 or a list like 4,6,8"
        ) from exc
    if not depths or any(depth < 1 or depth > 10 for depth in depths):
        raise argparse.ArgumentTypeError("depths must be between 1 and 10")
    if len(set(depths)) != len(depths):
        raise argparse.ArgumentTypeError("depths must not contain duplicates")
    return depths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask an OpenRouter model whether seeded 4–10 digit integers are prime."
    )
    parser.add_argument("--model", help="OpenRouter model ID or unique short model name")
    parser.add_argument("--model-alias", help="Short name shown in the leaderboard")
    parser.add_argument(
        "--reasoning-effort",
        choices=("low", "medium"),
        help="Reasoning effort (default: low); supports low and medium for the requested run",
    )
    parser.add_argument("--depths", type=parse_depths, help="e.g. 4-10 or 4,6,8 (default: 4-10)")
    parser.add_argument(
        "--samples-per-class",
        type=int,
        help="Prime and non-prime cases per digit depth (default: 10 each)",
    )
    parser.add_argument("--seed", type=int, help="Reproducible case-generation seed (default: 2026)")
    parser.add_argument("--max-attempts", type=int, help="Maximum API attempts per case (default: 3)")
    parser.add_argument("--retry-delay", type=float, help="Initial retry delay in seconds (default: 1)")
    parser.add_argument("--timeout", type=float, help="OpenRouter request timeout in seconds (default: 90)")
    parser.add_argument(
        "--max-completion-tokens",
        type=int,
        help="Maximum response tokens per request (default: 512)",
    )
    parser.add_argument("--results-dir", default=str(PROJECT_ROOT / "results"))
    parser.add_argument("--output", help="Explicit path for the JSONL event ledger")
    parser.add_argument("--resume", help="Resume a JSONL event ledger using its saved manifest")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the model/prices and print the planned cases; send no chat completions",
    )
    return parser


def _display_name(model: str, effort: str | None) -> str:
    short_name = model.strip().rsplit("/", 1)[-1]
    return f"{short_name}-{effort}" if effort else short_name


def _dry_run_text(plan: dict) -> str:
    rows = [
        "DRY RUN — no chat-completion inference will be sent",
        f"Display name: {plan['display_model']}",
        f"Requested model: {plan['requested_model']}",
        f"OpenRouter model: {plan['model_id']}",
        f"Reasoning effort: {plan['reasoning_effort'] or 'provider default'}",
        f"Digit depths: {', '.join(map(str, plan['depths']))}",
        f"Cases per depth: {plan['samples_per_class']} prime + {plan['samples_per_class']} non-prime",
        f"Total cases / inference requests: {plan['case_count']}",
        f"Seed: {plan['seed']}",
        f"Dataset SHA-256: {plan['dataset_sha256']}",
        f"Uncached input price: ${plan['prompt_rate_usd_per_million']} / 1M tokens",
        f"Output price: ${plan['completion_rate_usd_per_million']} / 1M tokens",
        f"Output-only cap estimate at token/attempt limits (input excluded): ${plan['max_output_cost_bound_usd']}",
        f"Maximum attempts per case: {plan['max_attempts']}",
        f"Maximum completion tokens per request: {plan['max_completion_tokens']}",
        f"Pricing source: {plan['pricing_source']} ({plan['pricing_retrieved_at']})",
        "Requests by depth: " + ", ".join(
            f"{depth}d={count}" for depth, count in plan["cases_by_depth"].items()
        ),
    ]
    return "\n".join(rows)


def _progress(event: dict) -> None:
    if event.get("event") == "case_finished":
        print(
            f"[{event['completed_cases']}/{event['total_cases']}] "
            f"{event['case_id']}: {event['outcome']}",
            flush=True,
        )


def _new_config(args: argparse.Namespace) -> tuple[RunConfig, str]:
    requested_model = args.model or os.environ.get("MODEL", "gpt-6-luna")
    effort = args.reasoning_effort or os.environ.get("REASONING_EFFORT", "low")
    alias = args.model_alias or _display_name(requested_model, effort)
    config = RunConfig(
        requested_model=requested_model,
        display_model=alias,
        reasoning_effort=effort,
        depths=args.depths or DEFAULT_DEPTHS,
        samples_per_class=(
            args.samples_per_class
            if args.samples_per_class is not None
            else DEFAULT_SAMPLES_PER_CLASS
        ),
        seed=args.seed if args.seed is not None else DEFAULT_SEED,
        max_attempts=args.max_attempts if args.max_attempts is not None else DEFAULT_MAX_ATTEMPTS,
        retry_delay_seconds=(
            args.retry_delay
            if args.retry_delay is not None
            else DEFAULT_RETRY_DELAY_SECONDS
        ),
        timeout_seconds=args.timeout if args.timeout is not None else DEFAULT_TIMEOUT_SECONDS,
        max_completion_tokens=(
            args.max_completion_tokens
            if args.max_completion_tokens is not None
            else DEFAULT_MAX_COMPLETION_TOKENS
        ),
    )
    return config, requested_model


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.resume and args.output:
        parser.error("--output cannot be combined with --resume")
    if args.resume and args.dry_run:
        parser.error("--dry-run cannot be combined with --resume")

    load_dotenv()
    api_key = get_openrouter_key()
    if not api_key:
        parser.error("OpenRouter key missing; set OR_KEY in .env or the environment")

    if args.resume:
        manifest_path = Path(args.resume).with_name(
            f"{Path(args.resume).stem}.manifest.json"
        )
        if not manifest_path.is_file():
            parser.error(f"run manifest not found: {manifest_path}")
        # The saved manifest supplies timeout and all frozen run settings.
        import json

        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        saved_config = saved.get("config", {})
        client = OpenRouterClient(
            api_key,
            timeout=float(saved_config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
        )
        overrides = {
            "model": args.model,
            "model_alias": args.model_alias,
            "reasoning_effort": args.reasoning_effort,
            "depths": args.depths,
            "samples_per_class": args.samples_per_class,
            "seed": args.seed,
            "max_attempts": args.max_attempts,
            "max_completion_tokens": args.max_completion_tokens,
        }
        try:
            result = resume_run(
                client=client,
                ledger_path=args.resume,
                overrides=overrides,
                on_progress=_progress,
            )
        except (ValueError, OSError, OpenRouterError) as exc:
            parser.error(str(exc))
        print(f"Run {'complete' if result['complete'] else 'incomplete'}: {result['ledger_path']}")
        print(f"Manifest: {result['manifest_path']}")
        return 0 if result["complete"] else 2

    config, requested_model = _new_config(args)
    try:
        client = OpenRouterClient(api_key, timeout=config.timeout_seconds)
        model_info = client.resolve_model(requested_model)
        OpenRouterClient.validate_reasoning_effort(model_info, config.reasoning_effort)
        if model_info.prompt_rate_usd_per_million is None or model_info.completion_rate_usd_per_million is None:
            parser.error("OpenRouter model catalog has no input/output rates for this model")
        if args.dry_run:
            plan = create_dry_run_plan(config=config, model_info=model_info)
            print(_dry_run_text(plan))
            return 0
        result = run_new(
            client=client,
            config=config,
            model_info=model_info,
            results_dir=args.results_dir,
            ledger_path=args.output,
            on_progress=_progress,
        )
    except (ValueError, OSError, OpenRouterError) as exc:
        parser.error(str(exc))

    print(f"Run {'complete' if result['complete'] else 'incomplete'}: {result['ledger_path']}")
    print(f"Manifest: {result['manifest_path']}")
    print(
        f"Correct: {result['summary']['correct']}/{result['scheduled_cases']}  "
        f"Incorrect: {result['summary']['incorrect']}/{result['scheduled_cases']}"
    )
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
