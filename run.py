#!/usr/bin/env python3
"""Run explicit OpenRouter model-ID/reasoning-effort pairs."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import math
from pathlib import Path
import secrets
import signal
import sys
from typing import Sequence

from extensions import (
    load_extension_parents,
    locked_parents,
    prepare_extension_plan,
    select_parent_ledgers,
)
from model_specs import ModelSpec, parse_model_specs
from multi_run import ModelRunSpec, run_many
from openrouter import OpenRouterClient, OpenRouterError
from progress import ProgressReporter
from request_gate import AccountRequestGate
from runner import (
    DEFAULT_DEPTHS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MIN_REQUEST_INTERVAL_SECONDS,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_SAMPLES_PER_CLASS,
    EvaluationInterrupted,
    RunConfig,
    create_dry_run_plan,
    resume_run,
    run_new,
)
from settings import PROJECT_ROOT, get_openrouter_key, load_dotenv

DEFAULT_CLI_TIMEOUT_SECONDS = 600.0


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
    if not depths or any(depth < 1 or depth > 15 for depth in depths):
        raise argparse.ArgumentTypeError("depths must be between 1 and 15")
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
        help="Optional effort (default: provider default); when supplied, pair one per --model-id; 'omit' uses provider default",
    )
    parser.add_argument("--parallelism", type=int, default=4)
    parser.add_argument("--depths", type=parse_depths, help="e.g. 4-15 or 4,6,8 (default: 4-15)")
    parser.add_argument(
        "--extend-through",
        type=int,
        help="Extend selected complete base runs through this digit depth",
    )
    parser.add_argument("--parent-ledger", action="append", help="Explicit extension parent ledger; repeat per run")
    parser.add_argument("--top-up-existing-per-class", type=int, default=5)
    parser.add_argument("--new-depths-per-class", type=int, default=15)
    parser.add_argument("--samples-per-class", type=int, help="Prime and non-prime cases per depth (default: 15)")
    parser.add_argument(
        "--seed",
        type=int,
        help="Explicit reproducible seed; unset chooses and saves a system-random seed",
    )
    parser.add_argument("--max-retries", type=int, help="Retries after initial request (default: 5)")
    parser.add_argument("--retry-delay", type=float, help="Exponential backoff base in seconds (default: 1)")
    parser.add_argument("--requests-per-minute", type=float, help="Shared completion rate limit (default: 15)")
    parser.add_argument(
        "--timeout",
        type=float,
        help="urllib socket inactivity timeout in seconds (default: 600 for new runs; resume/extension inherit saved settings)",
    )
    parser.add_argument(
        "--max-completion-tokens",
        type=int,
        help="Explicit completion-token cap; unset sends no token cap",
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
        "seed": args.seed,
        "max_attempts": (
            (args.max_retries if args.max_retries is not None else DEFAULT_MAX_RETRIES) + 1
        ),
        "min_request_interval_seconds": (
            60.0 / args.requests_per_minute
            if args.requests_per_minute is not None
            else DEFAULT_MIN_REQUEST_INTERVAL_SECONDS
        ),
        "retry_delay_seconds": (
            args.retry_delay
            if args.retry_delay is not None
            else DEFAULT_RETRY_DELAY_SECONDS
        ),
        "timeout_seconds": (
            args.timeout if args.timeout is not None else DEFAULT_CLI_TIMEOUT_SECONDS
        ),
        "max_completion_tokens": args.max_completion_tokens,
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
    output_cap = plan["max_output_cost_bound_usd"]
    cap_line = (
        f"Output-only cap estimate at explicit token/attempt limits (input excluded): ${output_cap}"
        if output_cap is not None
        else "Output-only cap estimate: unbounded (no completion-token cap is set; input excluded)"
    )
    token_limit_line = (
        f"Completion token cap: {plan['max_completion_tokens']}"
        if plan["max_completion_tokens"] is not None
        else "Completion token cap: none (no max_completion_tokens or max_tokens parameter sent)"
    )
    rows = [
        "DRY RUN — no chat-completion inference will be sent",
        f"Model ID: {plan['model_id']}",
        f"Reasoning effort: {plan['reasoning_effort'] if plan['reasoning_effort'] is not None else 'omitted (provider default)'}",
        f"Resolved model name: {plan['resolved_model_name']}",
        f"Digit depths: {', '.join(map(str, plan['depths']))}",
        f"Cases per depth: {plan['samples_per_class']} prime + {plan['samples_per_class']} non-prime",
        f"Total cases / first attempts: {plan['case_count']}",
        f"Maximum completion attempts including retries: {plan['max_total_inference_attempts']}",
        f"Sampling seed: {plan['seed']} ({plan['seed_source']})",
        f"Dataset SHA-256: {plan['dataset_sha256']}",
        f"Uncached input price: ${plan['prompt_rate_usd_per_million']} / 1M tokens",
        f"Output price: ${plan['completion_rate_usd_per_million']} / 1M tokens",
        cap_line,
        f"Maximum retries per case: {plan['max_retries']} ({plan['max_attempts']} total attempts)",
        f"Retry backoff: {plan['retry_delay_seconds']:.2f}s exponential base with "
        f"bounded ±{plan['retry_jitter_fraction']:.0%} jitter",
        f"Request timeout: {plan['timeout_seconds']:.1f}s",
        f"Shared maximum request rate: {60.0 / plan['min_request_interval_seconds']:.2f} per minute "
        f"({plan['min_request_interval_seconds']:.2f}s minimum spacing)",
        f"429 cooldown: max(Retry-After, {plan['default_429_cooldown_seconds']:.0f}s safety floor)",
        token_limit_line,
        f"Pricing source: {plan['pricing_source']} ({plan['pricing_retrieved_at']})",
        "Requests by depth: " + ", ".join(
            f"{depth}d={count}" for depth, count in plan["cases_by_depth"].items()
        ),
    ]
    return "\n".join(rows)


def _print_run_result(model_id: str, effort: str | None, result: dict) -> None:
    print(f"Run {'complete' if result['complete'] else 'incomplete'}")
    print(f"Model ID: {model_id}")
    print(f"Reasoning effort: {effort if effort is not None else 'omitted (provider default)'}")
    print(f"Ledger: {result['ledger_path']}")
    print(f"Manifest: {result['manifest_path']}")
    counts = result["summary"]
    print(
        f"Correct: {counts['correct']}/{result['scheduled_cases']}  "
        f"Incorrect: {counts['incorrect']}/{result['scheduled_cases']}"
    )


def _run_depth_extension(
    *,
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    api_key: str,
) -> int:
    if args.output:
        parser.error("--output cannot be used with --extend-through")
    if args.depths is not None or args.samples_per_class is not None:
        parser.error("extensions inherit parent depths; do not supply --depths or --samples-per-class")
    if args.max_completion_tokens is not None:
        parser.error("extensions inherit the parent's token-cap policy; no cap override is allowed")
    if args.parent_ledger and (args.model_id or args.reasoning_effort):
        parser.error("use either --parent-ledger or Model ID/Effort selectors")

    model_specs = None if args.parent_ledger else _load_model_specs(args, parser)
    try:
        parent_paths = select_parent_ledgers(
            results_dir=args.results_dir,
            model_specs=model_specs,
            parent_ledgers=args.parent_ledger,
        )
        result_root = Path(args.results_dir).resolve()
        if any(Path(path).resolve().parent != result_root for path in parent_paths):
            raise ValueError("all extension parents must be in --results-dir")
        initial_parents = load_extension_parents(parent_paths)
        with locked_parents(initial_parents):
            parents = load_extension_parents(parent_paths)
            for parent in parents:
                if args.timeout is not None and parent.config.timeout_seconds != args.timeout:
                    raise ValueError(f"timeout mismatch for parent {parent.ledger_path.name}")
                if args.max_retries is not None and parent.config.max_attempts != args.max_retries + 1:
                    raise ValueError(f"max-retries mismatch for parent {parent.ledger_path.name}")
                if args.retry_delay is not None and parent.config.retry_delay_seconds != args.retry_delay:
                    raise ValueError(f"retry-delay mismatch for parent {parent.ledger_path.name}")
                if args.requests_per_minute is not None and not math.isclose(
                    parent.config.min_request_interval_seconds,
                    60.0 / args.requests_per_minute,
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                ):
                    raise ValueError(f"request-rate mismatch for parent {parent.ledger_path.name}")

            plan = prepare_extension_plan(
                results_dir=result_root,
                parents=parents,
                target_depth=args.extend_through,
                top_up_per_class=args.top_up_existing_per_class,
                new_depths_per_class=args.new_depths_per_class,
                requested_seed=args.seed,
            )
            timeout_seconds = parents[0].config.timeout_seconds
            catalog = OpenRouterClient(api_key, timeout=timeout_seconds)
            current_models = {}
            for parent in parents:
                identity = (parent.config.model_id, parent.config.reasoning_effort)
                if identity in current_models:
                    continue
                model_info = catalog.resolve_model(parent.config.model_id)
                OpenRouterClient.validate_reasoning_effort(model_info, parent.config.reasoning_effort)
                if model_info.prompt_rate_usd_per_million is None or model_info.completion_rate_usd_per_million is None:
                    raise ValueError(f"OpenRouter catalog lacks input/output rates for {model_info.model_id}")
                current_models[identity] = model_info
            specs = [
                spec
                if spec.resume_ledger_path is not None
                else replace(
                    spec,
                    model_info=current_models[(spec.config.model_id, spec.config.reasoning_effort)],
                )
                for spec in plan.specs
            ]
            if args.dry_run:
                batch = plan.manifest
                print("DEPTH EXTENSION DRY RUN — no chat-completion inference will be sent")
                print(f"Extension batch: {plan.batch_id}")
                print(f"Parent runs: {len(parents)} complete base runs")
                print(f"Parent depths: {', '.join(map(str, parents[0].config.depths))}")
                print(f"Target depths: {', '.join(map(str, plan.target_depths))}")
                print(
                    f"Added cases per model: {batch['added_case_count']}; "
                    f"cumulative cases per model: {batch['target_case_count']}"
                )
                print(f"Supplement sampling seed: {batch['sampling_seed']} ({batch['seed_source']})")
                print(
                    "Supplement per depth (primes + composites): "
                    + ", ".join(
                        f"{depth}d={count}+{count}"
                        for depth, count in sorted(
                            batch["added_samples_per_class_by_depth"].items(),
                            key=lambda item: int(item[0]),
                        )
                    )
                )
                print(f"Cumulative dataset SHA-256: {batch['target_dataset_sha256']}")
                print("Completion token cap: none; output-only cost bound is unbounded")
                attempts = parents[0].config.max_attempts
                print(
                    f"Maximum completion attempts per case: {attempts} "
                    f"({attempts - 1} retries); backoff base: "
                    f"{parents[0].config.retry_delay_seconds:g}s"
                )
                interval = parents[0].config.min_request_interval_seconds
                rate = "disabled" if interval <= 0 else f"{60.0 / interval:.2f} requests/min"
                print(
                    f"Timeout: {timeout_seconds}s socket inactivity · Parallelism: {args.parallelism} · "
                    f"Rate gate: {rate}"
                )
                for parent in parents:
                    info = current_models[(parent.config.model_id, parent.config.reasoning_effort)]
                    print(
                        f"{parent.config.model_id} / {parent.config.reasoning_effort or 'omitted'}: "
                        f"input=${info.prompt_rate_usd_per_million}/1M output=${info.completion_rate_usd_per_million}/1M"
                    )
                return 0

            reporter = ProgressReporter(stream=sys.stderr)
            rows = run_many(
                specs,
                client_factory=lambda timeout: OpenRouterClient(api_key, timeout=timeout),
                results_dir=result_root,
                parallelism=args.parallelism,
                on_progress=reporter,
                prepared_dataset=plan.prepared_dataset,
                shared_request_gate=AccountRequestGate(
                    parents[0].config.min_request_interval_seconds
                ),
            )
            reporter.close()
            exit_code = 0
            for row in rows:
                spec = row["spec"]
                if row.get("error"):
                    print(
                        f"[model_id={spec.config.model_id} effort={spec.config.reasoning_effort}] "
                        f"failed: {row['error']}",
                        file=sys.stderr,
                    )
                    exit_code = 1
                    continue
                result = row["result"]
                _print_run_result(spec.config.model_id, spec.config.reasoning_effort, result)
                if not result["complete"] and exit_code == 0:
                    exit_code = 2
            if any(row.get("batch_interrupted") for row in rows):
                return 130
            return exit_code
    except (ValueError, OSError, OpenRouterError) as exc:
        parser.error(str(exc))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.parallelism <= 0:
        parser.error("--parallelism must be positive")
    if args.timeout is not None and (
        not math.isfinite(args.timeout) or args.timeout <= 0
    ):
        parser.error("--timeout must be finite and positive")
    if args.max_retries is not None and args.max_retries < 0:
        parser.error("--max-retries cannot be negative")
    if args.extend_through is not None and not 1 <= args.extend_through <= 15:
        parser.error("--extend-through must be between 1 and 15")
    if args.extend_through is None and args.parent_ledger:
        parser.error("--parent-ledger requires --extend-through")
    if args.top_up_existing_per_class < 0:
        parser.error("--top-up-existing-per-class cannot be negative")
    if args.new_depths_per_class <= 0:
        parser.error("--new-depths-per-class must be positive")
    if (
        args.requests_per_minute is not None
        and (not math.isfinite(args.requests_per_minute) or args.requests_per_minute <= 0)
    ):
        parser.error("--requests-per-minute must be finite and positive")
    run_settings = (
        args.output,
        args.dry_run,
        args.extend_through is not None,
        args.parent_ledger,
        args.model_id,
        args.reasoning_effort,
        args.depths is not None,
        args.samples_per_class is not None,
        args.seed is not None,
        args.max_retries is not None,
        args.retry_delay is not None,
        args.requests_per_minute is not None,
        args.timeout is not None,
        args.max_completion_tokens is not None,
    )
    if args.resume and (any(run_settings) or args.extend_through is not None):
        parser.error("--resume uses its saved model/effort/config; do not supply run settings")
    if args.extend_through is not None and args.output:
        parser.error("--output cannot be used with --extend-through")

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
        effort = saved_model.get("reasoning_effort", saved_config.get("reasoning_effort"))
        if not model_id:
            parser.error("saved run manifest does not contain an explicit model ID")
        saved_timeout = saved_config.get("timeout_seconds")
        if (
            not isinstance(saved_timeout, (int, float))
            or isinstance(saved_timeout, bool)
            or not math.isfinite(saved_timeout)
            or saved_timeout <= 0
        ):
            parser.error("saved run manifest does not contain an explicit finite timeout")
        client = OpenRouterClient(api_key, timeout=float(saved_timeout))
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

    if args.extend_through is not None:
        return _run_depth_extension(args=args, parser=parser, api_key=api_key)

    specs = _load_model_specs(args, parser)
    if args.output and len(specs) > 1:
        parser.error("--output can only be used with one model ID/effort pair")
    settings = _settings(args)
    if settings["seed"] is None:
        settings["seed"] = secrets.randbits(64)
        settings["seed_source"] = "system_random"
    else:
        settings["seed_source"] = "explicit"
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

    for spec in run_specs:
        config = spec.config
        effort = config.reasoning_effort if config.reasoning_effort is not None else "provider default"
        cap = config.max_completion_tokens if config.max_completion_tokens is not None else "none"
        print(
            f"Run settings: {config.model_id} | reasoning: {effort} | "
            f"socket timeout: {config.timeout_seconds:g}s | token cap: {cap}",
            flush=True,
        )
    reporter = ProgressReporter(stream=sys.stderr)
    if len(run_specs) == 1:
        spec = run_specs[0]
        total = spec.config.scheduled_case_count
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


def _raise_sigterm_as_keyboard_interrupt(signum, _frame):
    raise KeyboardInterrupt(f"received {signal.Signals(signum).name}")


def _install_cli_signal_handlers() -> None:
    # Background shells can propagate SIG_IGN for SIGINT; override it so the
    # runner's cooperative cancellation path can drain in-flight requests.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _raise_sigterm_as_keyboard_interrupt)


if __name__ == "__main__":
    _install_cli_signal_handlers()
    raise SystemExit(main())