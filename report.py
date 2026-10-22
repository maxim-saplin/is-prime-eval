"""Plain-language per-model leaderboard derived from saved run ledgers."""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from costs import as_decimal
from events import load_events
from runner import _manifest_path, _load_dataset


def _percentage(count: int, denominator: int) -> str:
    if denominator <= 0:
        return f"{count}/0 (—)"
    return f"{count}/{denominator} ({count / denominator * 100:.1f}%)"


def wilson_95_ci(successes: int, trials: int) -> tuple[float, float] | None:
    """Approximate 95% Wilson item-level interval; not a population CI."""
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("Wilson interval counts must satisfy 0 <= successes <= trials")
    if trials == 0:
        return None
    z = 1.959963984540054
    proportion = successes / trials
    z2 = z * z
    denominator = 1 + z2 / trials
    center = (proportion + z2 / (2 * trials)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / trials + z2 / (4 * trials * trials)
        )
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def _ci_cell(successes: int, trials: int) -> str:
    interval = wilson_95_ci(successes, trials)
    if interval is None:
        return "—"
    low, high = interval
    return f"{low * 100:.1f}–{high * 100:.1f}%"


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    return sum(values, Decimal("0"))


def _cost_cell(total: Decimal, known: int, attempts: int) -> str:
    if attempts == 0 or known == 0:
        return f"Unknown ({known}/{attempts} requests priced)"
    amount = f"${total:.6f}"
    if known < attempts:
        return f"Partial {amount} ({known}/{attempts} requests priced)"
    return amount


def _merge_attempts(events: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    attempts: dict[str, dict[str, Any]] = {}
    for event in events:
        attempt_id = event.get("attempt_id")
        event_type = event.get("event_type")
        if not attempt_id:
            continue
        state = attempts.setdefault(str(attempt_id), {"attempt_id": str(attempt_id)})
        if event_type == "attempt_started":
            state.update(event)
            state["status"] = "started"
        elif event_type in {"attempt_response", "attempt_failed", "attempt_interrupted", "attempt_cancelled_before_dispatch"}:
            state.update(event)
            state["status"] = event_type.removeprefix("attempt_")
        elif event_type == "attempt_cost_update":
            for key, value in event.items():
                if key not in {"event_type", "event_id", "timestamp"} and value is not None:
                    state[key] = value
        elif event_type == "cost_lookup_failed":
            state["cost_lookup_failed"] = True
            state["cost_lookup_error_type"] = event.get("error_type")

    # A request with an attempt-start event but no finish is attempted with an
    # unknown outcome/spend, even before a resume has written a recovery event.
    for state in attempts.values():
        state.setdefault("status", "outcome_unknown")
        state.setdefault("provider_reported_usd", None)
        state.setdefault("normalized_uncached_usd", None)
        if state["status"] in {"started", "interrupted"}:
            state["spend_status"] = "unknown"
    return attempts


def _case_outcomes(
    manifest: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    attempts: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    dataset = manifest.get("dataset")
    if not isinstance(dataset, Mapping):
        raise ValueError("run manifest has no dataset metadata")
    cases = _load_dataset(_manifest_path_from_manifest(manifest, events), dataset)
    response_by_case: dict[str, Mapping[str, Any]] = {}
    no_response_by_case: dict[str, Mapping[str, Any]] = {}
    for event in events:
        case_id = str(event.get("case_id", ""))
        if event.get("event_type") == "attempt_response":
            response_by_case[case_id] = event
        elif event.get("event_type") == "case_terminal" and event.get("outcome") == "no_response":
            no_response_by_case[case_id] = event

    attempts_by_case: dict[str, list[Mapping[str, Any]]] = {}
    for state in attempts.values():
        if state.get("status") == "cancelled_before_dispatch":
            continue
        case_id = str(state.get("case_id", ""))
        attempts_by_case.setdefault(case_id, []).append(state)

    outcomes = []
    for case in cases:
        response = response_by_case.get(case.case_id)
        failure = no_response_by_case.get(case.case_id)
        case_attempts = attempts_by_case.get(case.case_id, [])
        if response is not None:
            outcome = str(response.get("outcome", "invalid_response"))
            terminal = True
        elif failure is not None:
            outcome = "no_response"
            terminal = True
        elif case_attempts:
            outcome = "pending"
            terminal = False
        else:
            outcome = "not_attempted"
            terminal = False
        outcomes.append(
            {
                "case_id": case.case_id,
                "depth": case.depth,
                "number": case.number,
                "gold_label": case.label,
                "outcome": outcome,
                "terminal": terminal,
                "attempted": bool(case_attempts),
                "answered": response is not None,
                "invalid_reason": response.get("invalid_reason") if response is not None else None,
            }
        )
    complete = all(item["terminal"] for item in outcomes)
    return outcomes, complete


def _manifest_path_from_manifest(
    manifest: Mapping[str, Any], events: Sequence[Mapping[str, Any]]
) -> Path:
    # The ledger path is injected by load_run_summary to avoid relying on
    # machine-specific absolute paths stored inside a manifest.
    path = manifest.get("_manifest_path")
    if not path:
        raise ValueError("internal report error: missing manifest path")
    return Path(path)


def summarize_run(ledger_path: str | Path) -> dict[str, Any]:
    ledger = Path(ledger_path).resolve()
    manifest_path = _manifest_path(ledger)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"run manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["_manifest_path"] = str(manifest_path)
    events, torn_bytes = load_events(ledger, repair_torn_tail=False)
    attempts = {
        attempt_id: state
        for attempt_id, state in _merge_attempts(events).items()
        if state.get("status") != "cancelled_before_dispatch"
    }
    outcomes, complete = _case_outcomes(manifest, events, attempts)
    scheduled = len(outcomes)
    counts = {
        "correct": sum(1 for row in outcomes if row["outcome"] == "correct"),
        "wrong_label": sum(1 for row in outcomes if row["outcome"] == "wrong_label"),
        "invalid": sum(1 for row in outcomes if row["outcome"] == "invalid_response"),
        "truncated": sum(
            1 for row in outcomes
            if row["outcome"] == "invalid_response"
            and row.get("invalid_reason") == "completion_truncated"
        ),
        "no_response": sum(1 for row in outcomes if row["outcome"] == "no_response"),
        "pending": sum(1 for row in outcomes if row["outcome"] == "pending"),
        "not_attempted": sum(1 for row in outcomes if row["outcome"] == "not_attempted"),
    }
    counts["other_invalid"] = counts["invalid"] - counts["truncated"]
    counts["incorrect"] = counts["wrong_label"] + counts["invalid"] + counts["no_response"]
    counts["attempted_cases"] = sum(1 for row in outcomes if row["attempted"])
    counts["answered_cases"] = sum(1 for row in outcomes if row["answered"])
    counts["terminal_cases"] = counts["correct"] + counts["incorrect"]

    by_depth: dict[int, dict[str, int]] = {}
    for row in outcomes:
        cell = by_depth.setdefault(
            row["depth"],
            {
                "scheduled": 0,
                "correct": 0,
                "wrong_label": 0,
                "invalid": 0,
                "truncated": 0,
                "no_response": 0,
                "pending": 0,
                "not_attempted": 0,
                "primes_scheduled": 0,
                "primes_correct": 0,
                "nonprimes_scheduled": 0,
                "nonprimes_correct": 0,
            },
        )
        cell["scheduled"] += 1
        outcome = row["outcome"]
        if outcome == "correct":
            cell["correct"] += 1
        elif outcome == "wrong_label":
            cell["wrong_label"] += 1
        elif outcome == "invalid_response":
            cell["invalid"] += 1
            if row.get("invalid_reason") == "completion_truncated":
                cell["truncated"] += 1
        elif outcome == "no_response":
            cell["no_response"] += 1
        elif outcome == "pending":
            cell["pending"] += 1
        else:
            cell["not_attempted"] += 1
        if row["gold_label"] == "PRIME":
            cell["primes_scheduled"] += 1
            if outcome == "correct":
                cell["primes_correct"] += 1
        else:
            cell["nonprimes_scheduled"] += 1
            if outcome == "correct":
                cell["nonprimes_correct"] += 1
    for cell in by_depth.values():
        cell["incorrect"] = cell["wrong_label"] + cell["invalid"] + cell["no_response"]

    attempt_count = len(attempts)
    provider_costs = [
        parsed
        for attempt in attempts.values()
        if (parsed := as_decimal(attempt.get("provider_reported_usd"))) is not None
    ]
    normalized_costs = [
        parsed
        for attempt in attempts.values()
        if (parsed := as_decimal(attempt.get("normalized_uncached_usd"))) is not None
    ]
    prompt_token_values = [
        int(attempt["usage"]["prompt_tokens"])
        for attempt in attempts.values()
        if isinstance(attempt.get("usage"), Mapping)
        and isinstance(attempt["usage"].get("prompt_tokens"), int)
    ]
    completion_token_values = [
        int(attempt["usage"]["completion_tokens"])
        for attempt in attempts.values()
        if isinstance(attempt.get("usage"), Mapping)
        and isinstance(attempt["usage"].get("completion_tokens"), int)
    ]
    provider_total = _sum_decimals(provider_costs)
    normalized_total = _sum_decimals(normalized_costs)
    provider_known = len(provider_costs)
    normalized_known = len(normalized_costs)
    model = manifest.get("model", {})
    config = manifest.get("config", {})
    dataset = manifest.get("dataset", {})
    return {
        "ledger_path": str(ledger),
        "manifest_path": str(manifest_path),
        "run_id": manifest.get("run_id"),
        "model_id": model.get("model_id") or model.get("requested_id") or manifest.get("display_model", "unknown"),
        "reasoning_effort": model.get("reasoning_effort", "unknown"),
        "dataset_id": dataset.get("dataset_id"),
        "dataset_sha256": dataset.get("sha256"),
        "config_sha256": manifest.get("config_sha256"),
        "extension": manifest.get("extension"),
        "prompt_version": manifest.get("prompt", {}).get("version"),
        "depths": list(dataset.get("depths", [])),
        "samples_per_class": dataset.get("samples_per_class"),
        "samples_per_class_by_depth": dataset.get("samples_per_class_by_depth"),
        "scheduled": scheduled,
        "complete": complete,
        "counts": counts,
        "by_depth": by_depth,
        "attempt_count": attempt_count,
        "prompt_tokens": sum(prompt_token_values),
        "completion_tokens": sum(completion_token_values),
        "token_usage_known_attempts": sum(
            1
            for attempt in attempts.values()
            if isinstance(attempt.get("usage"), Mapping)
            and isinstance(attempt["usage"].get("prompt_tokens"), int)
            and isinstance(attempt["usage"].get("completion_tokens"), int)
        ),
        "provider_cost_total": provider_total,
        "provider_cost_known_attempts": provider_known,
        "normalized_cost_total": normalized_total,
        "normalized_cost_known_attempts": normalized_known,
        "provider_cost_cell": _cost_cell(provider_total, provider_known, attempt_count),
        "normalized_cost_cell": _cost_cell(normalized_total, normalized_known, attempt_count),
        "pricing": manifest.get("pricing", {}),
        "config": config,
        "attempts": attempts,
        "provider_routes": sorted(
            {
                str(attempt.get("provider_route"))
                for attempt in attempts.values()
                if attempt.get("provider_route")
            }
        ),
        "torn_tail_bytes": torn_bytes,
        "outcomes": outcomes,
    }


def _markdown_cell(value: Any) -> str:
    """Escape user/provider-controlled values before inserting them in a table."""
    text = str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _effort_label(summary: Mapping[str, Any]) -> str:
    effort = summary.get("reasoning_effort", "unknown")
    return _markdown_cell("omitted (provider default)" if effort is None else effort or "unknown")


def _samples_label(summary: Mapping[str, Any]) -> str:
    by_depth = summary.get("samples_by_depth") or summary.get("samples_per_class_by_depth") or {}
    if by_depth:
        counts = sorted((int(depth), int(count)) for depth, count in by_depth.items())
        if len({count for _depth, count in counts}) == 1:
            count = counts[0][1]
            return f"{count}+{count} per digit"
        bands = []
        start = previous = counts[0][0]
        current = counts[0][1]
        for depth, count in counts[1:]:
            if depth == previous + 1 and count == current:
                previous = depth
                continue
            label = f"{start}–{previous}d" if start != previous else f"{start}d"
            bands.append(f"{current}+{current} at {label}")
            start = previous = depth
            current = count
        label = f"{start}–{previous}d" if start != previous else f"{start}d"
        bands.append(f"{current}+{current} at {label}")
        return "; ".join(bands)
    per_class = summary.get("samples_per_class")
    if per_class is not None:
        return f"{per_class}+{per_class} per digit"
    return "unknown"


def _route_label(summary: Mapping[str, Any]) -> str:
    routes = summary.get("provider_routes", [])
    return _markdown_cell(", ".join(routes) if routes else "unknown")


def _incorrect_breakdown(counts: Mapping[str, int]) -> str:
    return (
        f"wrong label {counts['wrong_label']}, invalid {counts['invalid']} "
        f"(truncated {counts['truncated']}, other {counts['other_invalid']}), "
        f"no response {counts['no_response']}"
    )


def _coverage_label(summary: Mapping[str, Any]) -> str:
    depths = sorted(int(depth) for depth in summary.get("depths", []))
    if not depths:
        depth_label = "depths unknown"
    elif depths == list(range(depths[0], depths[-1] + 1)):
        depth_label = f"{depths[0]}–{depths[-1]}"
    else:
        depth_label = ",".join(map(str, depths))
    return f"{depth_label} / {summary['scheduled']} cases"


def _policy_label(summary: Mapping[str, Any]) -> str:
    config = summary.get("config", {})
    timeout = config.get("timeout_seconds", "?")
    attempts = config.get("max_attempts", "?")
    retry = config.get("retry_delay_seconds", "?")
    cap = config.get("max_completion_tokens")
    interval = config.get("min_request_interval_seconds", 4.0)
    rate = "unpaced" if not interval else f"{60.0 / float(interval):g} RPM"
    cap_label = "no cap" if cap is None else f"cap {cap}"
    return f"{timeout}s · {attempts} attempts · {retry}s retry · {cap_label} · {rate}"


def render_leaderboard(summaries: Sequence[Mapping[str, Any]]) -> str:
    if not summaries:
        return "No evaluation runs found.\n"

    complete_runs = sorted(
        (run for run in summaries if run["complete"]),
        key=lambda run: (
            -run["counts"]["correct"] / max(1, run["scheduled"]),
            run["model_id"].casefold(),
            str(run.get("reasoning_effort") or ""),
            str(run.get("run_id") or ""),
        ),
    )
    incomplete_runs = sorted(
        (run for run in summaries if not run["complete"]),
        key=lambda run: (
            run["model_id"].casefold(),
            str(run.get("reasoning_effort") or ""),
            str(run.get("run_id") or ""),
        ),
    )
    lines = [
        "# Prime-eval leaderboard",
        "",
        "All discovered results are listed together; each row is one run (a completed parent+extension is shown once). "
        "Depth coverage, sample counts, and request policy are shown per run. Rankings sort by raw accuracy; runs with different frozen questions are not paired comparisons.",
        "",
    ]
    if complete_runs:
        lines.extend(
            [
                "## Completed runs",
                "",
                "| Rank | Model ID | Effort | Run (parent+child) | Depths / cases | Samples | Request policy | Provider route | Answered / scheduled | Correct | Approx. 95% Wilson CI | Incorrect | Incorrect reasons |",
                "|---:|---|---|---|---:|---|---|---|---:|---:|---:|---:|---|",
            ]
        )
        for rank, run in enumerate(complete_runs, start=1):
            counts = run["counts"]
            total = run["scheduled"]
            lines.append(
                f"| {rank} | {_markdown_cell(run['model_id'])} | {_effort_label(run)} | "
                f"{_run_label(run)} | {_coverage_label(run)} | {_samples_label(run)} | "
                f"{_policy_label(run)} | "
                f"{_route_label(run)} | {counts['answered_cases']}/{total} | "
                f"{_percentage(counts['correct'], total)} | {_ci_cell(counts['correct'], total)} | "
                f"{_percentage(counts['incorrect'], total)} | {_incorrect_breakdown(counts)} |"
            )
        lines.extend(
            [
                "",
                "## Results by digit",
                "",
                "| Model ID | Effort | Run (parent+child) | Digits | Correct | Approx. 95% Wilson CI | Incorrect | Truncated | Primes correctly identified | Non-primes correctly identified |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for run in complete_runs:
            for depth in run["depths"]:
                cell = run["by_depth"][depth]
                scheduled = cell["scheduled"]
                lines.append(
                    f"| {_markdown_cell(run['model_id'])} | {_effort_label(run)} | "
                    f"{_run_label(run)} | {depth} | {_percentage(cell['correct'], scheduled)} | "
                    f"{_ci_cell(cell['correct'], scheduled)} | "
                    f"{_percentage(cell['incorrect'], scheduled)} | {cell['truncated']} | "
                    f"{cell['primes_correct']}/{cell['primes_scheduled']} | "
                    f"{cell['nonprimes_correct']}/{cell['nonprimes_scheduled']} |"
                )
        lines.extend(
            [
                "",
                "## Cost per run",
                "",
                "| Model ID | Effort | Run (parent+child) | Prompt / completion tokens | Provider-reported cost (USD) | Estimated cost without cache discounts (USD) |",
                "|---|---|---|---:|---:|---:|",
            ]
        )
        for run in complete_runs:
            lines.append(
                f"| {_markdown_cell(run['model_id'])} | {_effort_label(run)} | {_run_label(run)} | "
                f"{run['prompt_tokens']:,} / {run['completion_tokens']:,} "
                f"({run['token_usage_known_attempts']}/{run['attempt_count']} attempts with token counts) | "
                f"{run['provider_cost_cell']} | {run['normalized_cost_cell']} |"
            )

    if incomplete_runs:
        lines.extend(
            [
                "",
                "## Incomplete runs (provisional, not ranked)",
                "",
                "| Model ID | Effort | Run (parent+child) | Depths / cases | Samples | Request policy | Provider route | Correct | Incorrect terminal items | Attempted | Answered | No response | Pending | Never attempted | Provider-reported cost (USD) | Estimated cost without cache discounts (USD) |",
                "|---|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for run in incomplete_runs:
            counts = run["counts"]
            total = run["scheduled"]
            lines.append(
                f"| {_markdown_cell(run['model_id'])} | {_effort_label(run)} | {_run_label(run)} | "
                f"{_coverage_label(run)} | {_samples_label(run)} | {_policy_label(run)} | {_route_label(run)} | "
                f"{_percentage(counts['correct'], total)} | {_percentage(counts['incorrect'], total)} | "
                f"{counts['attempted_cases']} | {counts['answered_cases']} | {counts['no_response']} | "
                f"{counts['pending']} | {counts['not_attempted']} | {run['provider_cost_cell']} | "
                f"{run['normalized_cost_cell']} |"
            )

    lines.extend(
        [
            "",
            "Incorrect includes wrong labels, invalid responses, and retry-exhausted no-response items. "
            "Truncated is a sub-count of invalid responses. Percentages use every scheduled case. "
            "Approximate 95% Wilson intervals are per-run item-level summaries, not population, session-to-session, or model-difference intervals; incomplete runs have no interval. "
            "Runs with different question sets or sample counts are shown together for inventory, but their rankings are descriptive, not paired comparisons. "
            "Costs cover all request attempts; partial/unknown coverage is labeled, never treated as $0.",
            "",
        ]
    )
    return "\n".join(lines)


def _merge_extension_summary(
    parent: Mapping[str, Any], child: Mapping[str, Any]
) -> dict[str, Any]:
    extension = child.get("extension") or {}
    summaries = (parent, child)
    attempts = dict(parent.get("attempts", {}))
    for attempt_id, attempt in child.get("attempts", {}).items():
        if attempt_id in attempts:
            raise ValueError(f"duplicate attempt ID across parent/extension: {attempt_id}")
        attempts[attempt_id] = attempt

    counts = {
        key: int(parent["counts"].get(key, 0)) + int(child["counts"].get(key, 0))
        for key in set(parent["counts"]) | set(child["counts"])
    }
    by_depth: dict[int, dict[str, int]] = {}
    for summary in summaries:
        for raw_depth, values in summary["by_depth"].items():
            cell = by_depth.setdefault(int(raw_depth), {})
            for key, value in values.items():
                cell[key] = cell.get(key, 0) + int(value)

    attempt_count = sum(int(summary["attempt_count"]) for summary in summaries)
    provider_total = sum(
        (as_decimal(summary.get("provider_cost_total")) or Decimal("0"))
        for summary in summaries
    )
    normalized_total = sum(
        (as_decimal(summary.get("normalized_cost_total")) or Decimal("0"))
        for summary in summaries
    )
    provider_known = sum(int(summary["provider_cost_known_attempts"]) for summary in summaries)
    normalized_known = sum(int(summary["normalized_cost_known_attempts"]) for summary in summaries)
    token_known = sum(int(summary["token_usage_known_attempts"]) for summary in summaries)
    target_depths = list(extension.get("target_depths", []))
    raw_target_samples = extension.get("target_samples_per_class")
    target_samples = int(raw_target_samples) if raw_target_samples is not None else None
    target_samples_by_depth = {
        int(depth): int(count)
        for depth, count in extension.get("target_samples_by_depth", {}).items()
    }
    parent_run_id = str(parent.get("run_id"))
    batch_id = str(extension.get("extension_batch_id", "extension"))
    merged = dict(parent)
    merged.update(
        {
            "run_id": f"{parent_run_id[:8]}+{batch_id[:8]}",
            "parent_run_id": parent_run_id,
            "extension_child_run_ids": [str(child.get("run_id"))],
            "extension_batch_id": batch_id,
            "extension_complete": True,
            "dataset_id": extension.get("target_dataset_id"),
            "dataset_sha256": extension.get("target_dataset_sha256"),
            "depths": target_depths,
            "samples_per_class": target_samples,
            "samples_by_depth": target_samples_by_depth,
            "scheduled": int(parent["scheduled"]) + int(child["scheduled"]),
            "complete": True,
            "counts": counts,
            "by_depth": by_depth,
            "attempt_count": attempt_count,
            "attempts": attempts,
            "prompt_tokens": sum(int(summary["prompt_tokens"]) for summary in summaries),
            "completion_tokens": sum(int(summary["completion_tokens"]) for summary in summaries),
            "token_usage_known_attempts": token_known,
            "provider_cost_total": provider_total,
            "provider_cost_known_attempts": provider_known,
            "normalized_cost_total": normalized_total,
            "normalized_cost_known_attempts": normalized_known,
            "provider_cost_cell": _cost_cell(provider_total, provider_known, attempt_count),
            "normalized_cost_cell": _cost_cell(normalized_total, normalized_known, attempt_count),
            "provider_routes": sorted(
                set(parent.get("provider_routes", [])) | set(child.get("provider_routes", []))
            ),
            "outcomes": [*parent["outcomes"], *child["outcomes"]],
        }
    )
    merged_config = dict(parent.get("config", {}))
    merged_config.update({"depths": target_depths, "samples_per_class": target_samples})
    merged["config"] = merged_config
    return merged


def _run_label(summary: Mapping[str, Any]) -> str:
    parent_id = summary.get("parent_run_id")
    child_ids = summary.get("extension_child_run_ids")
    if parent_id and child_ids:
        return f"{str(parent_id)[:8]}+{str(child_ids[0])[:8]}"
    extension = summary.get("extension")
    if isinstance(extension, Mapping) and extension.get("parent_run_id"):
        return f"{str(extension['parent_run_id'])[:8]}+{str(summary.get('run_id') or '')[:8]}"
    return str(summary.get("run_id") or "")[:8]


def _load_extension_parent(child: Mapping[str, Any]) -> dict[str, Any]:
    extension = child.get("extension")
    if not isinstance(extension, Mapping):
        raise ValueError("extension child manifest lacks parent provenance")
    child_ledger = Path(str(child["ledger_path"]))
    parent_ledger = child_ledger.with_name(str(extension.get("parent_ledger_file", "")))
    if not parent_ledger.is_file():
        raise FileNotFoundError(
            f"extension parent ledger is missing for run {child.get('run_id')}: {parent_ledger}"
        )
    if hashlib.sha256(parent_ledger.read_bytes()).hexdigest() != extension.get("parent_ledger_sha256"):
        raise ValueError(f"extension parent ledger hash mismatch: {parent_ledger}")
    parent_manifest_path = _manifest_path(parent_ledger)
    if not parent_manifest_path.is_file():
        raise FileNotFoundError(f"extension parent manifest is missing: {parent_manifest_path}")
    if hashlib.sha256(parent_manifest_path.read_bytes()).hexdigest() != extension.get("parent_manifest_sha256"):
        raise ValueError(f"extension parent manifest hash mismatch: {parent_manifest_path}")
    parent = summarize_run(parent_ledger)
    if parent.get("run_id") != extension.get("parent_run_id"):
        raise ValueError("extension parent run ID mismatch")
    if parent.get("config", {}).get("config_sha256") not in (None, extension.get("parent_config_sha256")):
        raise ValueError("extension parent config hash mismatch")
    return parent


def load_summaries(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    summaries_by_path: dict[Path, dict[str, Any]] = {}
    pending = [Path(path).resolve() for path in paths]
    while pending:
        path = pending.pop()
        if path in summaries_by_path:
            continue
        summary = summarize_run(path)
        summaries_by_path[path] = summary
        extension = summary.get("extension")
        if isinstance(extension, Mapping):
            parent_summary = _load_extension_parent(summary)
            parent_path = Path(parent_summary["ledger_path"]).resolve()
            if parent_path not in summaries_by_path:
                pending.append(parent_path)

    summaries = list(summaries_by_path.values())
    by_run_id = {str(summary.get("run_id")): summary for summary in summaries}
    extensions: dict[tuple[str, str], dict[str, Any]] = {}
    for child in summaries:
        metadata = child.get("extension")
        if not isinstance(metadata, Mapping):
            continue
        key = (str(metadata.get("extension_batch_id")), str(metadata.get("parent_run_id")))
        if key in extensions:
            raise ValueError(f"multiple extension children found for parent {key[1]}")
        extensions[key] = child

    parent_counts: dict[str, int] = {}
    for _batch_id, parent_id in extensions:
        parent_counts[parent_id] = parent_counts.get(parent_id, 0) + 1
    if any(count > 1 for count in parent_counts.values()):
        raise ValueError("a base run has multiple extension children; merge one explicit child at a time")

    suppressed_ids: set[str] = set()
    extension_rows: list[dict[str, Any]] = []
    for (batch_id, parent_id), child in extensions.items():
        parent = by_run_id.get(parent_id)
        if parent is None:
            raise ValueError(f"extension parent run is missing: {parent_id}")
        if not parent["complete"]:
            raise ValueError(f"extension parent run is incomplete: {parent_id}")
        metadata = child["extension"]
        if metadata.get("parent_run_id") != parent_id:
            raise ValueError(f"extension parent mismatch for batch {batch_id}")
        if child["complete"]:
            extension_rows.append(_merge_extension_summary(parent, child))
            suppressed_ids.add(parent_id)
        else:
            provisional = dict(child)
            provisional["complete"] = False
            provisional["extension_complete"] = False
            provisional["extension_progress"] = "supplemental child incomplete"
            extension_rows.append(provisional)
        suppressed_ids.add(str(child["run_id"]))

    output = [
        summary
        for summary in summaries
        if str(summary.get("run_id")) not in suppressed_ids
    ]
    output.extend(extension_rows)
    return output


def discover_ledgers(results_dir: str | Path) -> list[Path]:
    root = Path(results_dir)
    if not root.is_dir():
        raise NotADirectoryError(root)
    return sorted(
        path
        for path in root.glob("*.jsonl")
        if _manifest_path(path).is_file()
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print a plain-language prime-eval leaderboard from saved JSONL runs."
    )
    parser.add_argument("ledgers", nargs="*", help="run JSONL ledgers; defaults to --results-dir")
    parser.add_argument("--results-dir", default="results", help="directory to scan when no ledgers are supplied")
    parser.add_argument("--output", help="also write the Markdown leaderboard to this path")
    args = parser.parse_args(argv)
    paths = [Path(value) for value in args.ledgers] if args.ledgers else discover_ledgers(args.results_dir)
    if not paths:
        print(f"No evaluation ledgers found in {args.results_dir}")
        return 0
    text = render_leaderboard(load_summaries(paths))
    print(text, end="")
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"\nWrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
