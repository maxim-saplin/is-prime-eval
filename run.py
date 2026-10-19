#!/usr/bin/env python3
"""Run explicit OpenRouter model-ID/reasoning-effort pairs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from model_specs import ModelSpec, parse_model_specs
from multi_run import ModelRunSpec, run_many
from openrouter import OpenRouterClient, OpenRouterError
from progress import ProgressReporter
from runner import (
    DEFAULT_DEPTHS,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_COMPLETION_TOKENS,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_SAMPLES_PER_CLASS,
    DEFAULT_SEED,
    DEFAULT_TIMEOUT_SECONDS,
    EvaluationInterrupted,
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
        description="Evaluate explicit OpenRouter model IDs and reasoning efforts on prime classification.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--model-id",
        action="append",
        help="Fully qualified OpenRouter ID (author/model); repeat for parallel runs",
    )
    parser.add_argument(
        "--reasoning-effort",
        action="append",
        help="Explicit provider effort paired by order with each --model-id; repeat for parallel runs",
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=4,
        help="Maximum model runs in flight when options are repeated (default: 4)",
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
    parser.add_argument("--output", help="Explicit JSONL ledger path (single run only)")
    parser.add_argument("--resume", help="Resume one JSONL event ledger using its saved manifest")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve model IDs/rates and print the plan; send no chat completions",
    )
    return parser


def _settings(args: argparse.Namespace) -> dict:
    return {
        "depths": args.depths or DEFAULT_DEPTHS,
        "samples_per_class": (
            args.samples_per_class
            if args.samples_per_class is not None
            else DEFAULT_SAMPLES_PER_CLASS
        ),
        "seed": args.seed if args.seed is not None else DEFAULT_SEED,
        "max_attempts": args.max_attempts if args.max_attempts is not None else DEFAULT_MAX_ATTEMPTS,
        "retry_delay_seconds": (
            args.retry_delay
            if args.retry_delay is not None
            else DEFAULT_RETRY_DELAY_SECONDS
        ),
        "timeout_seconds": args.timeout if args.timeout is not None else DEFAULT_TIMEOUT_SECONDS,
        "max_completion_tokens": (
            args.max_completion_tokens
            if args.max_completion_tokens is not None
            else DEFAULT_MAX_COMPLETION_TOKENS
        ),
    }


def _load_model_specs(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[ModelSpec]:
    try:
        return parse_model_specs(args.model_id, args.reasoning_effort)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))


def _config_for(spec: ModelSpec, values: dict) -> RunConfig:
    return RunConfig(
        model_id=spec.model_id,
        reasoning_effort=spec.reasoning_effort,
        **values,
    )


def _dry_run_text(plan: dict) -> str:
    rows = [
        "DRY RUN — no chat-completion inference will be sent",
        f"Model ID: {plan['model_id']}",
        f"Reasoning effort: {plan['reasoning_effort']}",
        f"Resolved model name: {plan['resolved_model_name']}",
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


def _print_run_result(model_id: str, effort: str, result: dict) -> None:
    print(f"Run {'complete' if result['complete'] else 'incomplete'}")
    print(f"Model ID: {model_id}")
    print(f"Reasoning effort: {effort}")
    print(f"Ledger: {result['ledger_path']}")
    print(f"Manifest: {result['manifest_path']}")
    counts = result["summary"]
    print(
        f"Correct: {counts['correct']}/{result['scheduled_cases']}  "
        f"Incorrect: {counts['incorrect']}/{result['scheduled_cases']}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.parallelism <= 0:
        parser.error("--parallelism must be positive")
    run_settings = (
        args.output,
        args.dry_run,
        args.model_id,
        args.reasoning_effort,
        args.depths is not None,
        args.samples_per_class is not None,
        args.seed is not None,
        args.max_attempts is not None,
        args.retry_delay is not None,
        args.timeout is not None,
        args.max_completion_tokens is not None,
    )
    if args.resume and any(run_settings):
        parser.error("--resume uses its saved model/effort/config; do not supply run settings")

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
        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        saved_config = saved.get("config", {})
        saved_model = saved.get("model", {})
        model_id = str(saved_model.get("model_id") or saved_config.get("model_id") or saved_config.get("requested_model") or "")
        effort = str(saved_model.get("reasoning_effort") or saved_config.get("reasoning_effort") or "")
        if not model_id or not effort:
            parser.error("saved run manifest does not contain an explicit model ID and effort")
        client = OpenRouterClient(
            api_key,
            timeout=float(saved_config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
        )
        reporter = ProgressReporter(stream=sys.stderr)
        try:
            reporter.set_batch_total(1)
            reporter.register_model(model_id, effort, int(saved.get("dataset", {}).get("case_count", 0)))
            result = resume_run(
                client=client,
                ledger_path=args.resume,
                overrides={},
                on_progress=reporter,
            )
        except EvaluationInterrupted as exc:
            reporter.model_finished(model_id, effort, success=False)
            print(f"Run paused; resume with: .venv/bin/python run.py --resume {exc.ledger_path}", file=sys.stderr)
            return 130
        except (ValueError, OSError, OpenRouterError) as exc:
            reporter.model_finished(model_id, effort, success=False)
            parser.error(str(exc))
        reporter.model_finished(model_id, effort, success=result["complete"])
        _print_run_result(model_id, effort, result)
        return 0 if result["complete"] else 2

    specs = _load_model_specs(args, parser)
    if args.output and len(specs) > 1:
        parser.error("--output can only be used with one model ID/effort pair")
    settings = _settings(args)
    configs = [_config_for(spec, settings) for spec in specs]
    catalog_client = OpenRouterClient(api_key, timeout=settings["timeout_seconds"])
    run_specs: list[ModelRunSpec] = []
    try:
        # Resolve every model and price before dispatching any paid inference.
        for config in configs:
            model_info = catalog_client.resolve_model(config.model_id)
            OpenRouterClient.validate_reasoning_effort(model_info, config.reasoning_effort)
            if model_info.prompt_rate_usd_per_million is None or model_info.completion_rate_usd_per_million is None:
                raise ValueError(f"OpenRouter catalog has no input/output rates for {model_info.model_id}")
            run_specs.append(ModelRunSpec(config=config, model_info=model_info))
        if args.dry_run:
            for index, spec in enumerate(run_specs, start=1):
                print(f"Run spec {index}/{len(run_specs)}")
                print(_dry_run_text(create_dry_run_plan(config=spec.config, model_info=spec.model_info)))
                print()
            return 0
    except (ValueError, OSError, OpenRouterError) as exc:
        parser.error(str(exc))

    reporter = ProgressReporter(stream=sys.stderr)
    if len(run_specs) == 1:
        spec = run_specs[0]
        total = len(spec.config.depths) * spec.config.samples_per_class * 2
        reporter.set_batch_total(1)
        reporter.register_model(spec.config.model_id, spec.config.reasoning_effort, total)
        client = OpenRouterClient(api_key, timeout=spec.config.timeout_seconds)
        try:
            result = run_new(
                client=client,
                config=spec.config,
                model_info=spec.model_info,
                results_dir=args.results_dir,
                ledger_path=args.output,
                on_progress=reporter,
            )
        except EvaluationInterrupted as exc:
            reporter.model_finished(spec.config.model_id, spec.config.reasoning_effort, success=False)
            print(f"Run paused; resume with: .venv/bin/python run.py --resume {exc.ledger_path}", file=sys.stderr)
            return 130
        except (ValueError, OSError, OpenRouterError) as exc:
            reporter.model_finished(spec.config.model_id, spec.config.reasoning_effort, success=False)
            parser.error(str(exc))
        reporter.model_finished(spec.config.model_id, spec.config.reasoning_effort, success=result["complete"])
        _print_run_result(spec.config.model_id, spec.config.reasoning_effort, result)
        return 0 if result["complete"] else 2

    results = run_many(
        run_specs,
        client_factory=lambda timeout: OpenRouterClient(api_key, timeout=timeout),
        results_dir=args.results_dir,
        parallelism=args.parallelism,
        on_progress=reporter,
    )
    exit_code = 130 if any(row.get("batch_interrupted") for row in results) else 0
    if exit_code == 130:
        print(
            "Batch interrupted. Resume each incomplete model ledger with `run.py --resume <ledger>`.",
            file=sys.stderr,
        )
    for row in results:
        spec = row["spec"]
        if row["error"]:
            print(f"[model_id={spec.config.model_id} effort={spec.config.reasoning_effort}] failed: {row['error']}", file=sys.stderr)
            if exit_code != 130:
                exit_code = 1
            continue
        result = row["result"]
        _print_run_result(spec.config.model_id, spec.config.reasoning_effort, result)
        if not result["complete"] and exit_code == 0:
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())