"""Create offline depth plots from saved ledgers, not the Markdown leaderboard."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import random
from statistics import fmean
from typing import Any, Mapping, Sequence

from .report import discover_ledgers, load_summaries, wilson_95_ci
from .settings import WORKSPACE_ROOT

DEPTHS = tuple(range(4, 16))


def select_runs(summaries: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Use complete, uncapped 4–15 runs; composed parent+child counts once."""
    runs = [
        run for run in summaries
        if run["complete"] and tuple(run["depths"]) == DEPTHS
        and run["config"].get("max_completion_tokens", False) is None
    ]
    if not runs:
        raise ValueError("no complete uncapped 4–15 runs found")
    return sorted(runs, key=lambda run: (
        -run["counts"]["correct"] / run["scheduled"], run["model_id"],
        str(run.get("reasoning_effort")), str(run["run_id"]),
    ))


def observations(run: Mapping[str, Any]) -> dict[int, dict[str, dict[str, Any]]]:
    """Final-response output tokens only; unknown usage is never imputed as zero."""
    responses = {}
    for attempt in run["attempts"].values():
        if attempt.get("status") != "response":
            continue
        case_id = attempt["case_id"]
        if case_id in responses:
            raise ValueError(f"multiple final responses for {case_id}")
        usage = attempt.get("usage") or {}
        tokens = usage.get("estimate_completion_tokens")
        if tokens is None:
            tokens = usage.get("completion_tokens")
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
            tokens = None
        responses[case_id] = tokens
    by_depth: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for outcome in run["outcomes"]:
        case_id, depth = outcome["case_id"], outcome["depth"]
        if case_id in by_depth[depth]:
            raise ValueError(f"duplicate scored case {case_id}")
        by_depth[depth][case_id] = {
            "label": outcome["gold_label"],
            "accuracy": float(outcome["outcome"] == "correct"),
            "tokens": responses.get(case_id),
        }
    return dict(by_depth)


def _mean_known(values: Sequence[float | int | None]) -> float | None:
    known = [value for value in values if value is not None]
    return fmean(known) if known else None


def _interval(values: Sequence[float]) -> list[float] | None:
    if not values:
        return None
    ordered = sorted(values)
    def quantile(p: float) -> float:
        at = p * (len(ordered) - 1)
        low, high = math.floor(at), math.ceil(at)
        return ordered[low] + (ordered[high] - ordered[low]) * (at - low)
    return [quantile(0.025), quantile(0.975)]


def depth_statistics(
    data: Sequence[dict[str, dict[str, Any]]], *, repetitions: int, rng: random.Random
) -> dict[str, Any]:
    """Paired, class-stratified question bootstrap, with the run roster fixed."""
    if repetitions <= 0:
        raise ValueError("bootstrap repetitions must be positive")
    groups: dict[tuple[str, tuple[str, ...]], list[tuple[int, list[dict[str, Any]]]]] = defaultdict(list)
    for index, cases in enumerate(data):
        if not cases:
            raise ValueError("every selected run must have cases at every depth")
        for label in ("PRIME", "COMPOSITE"):
            ids = tuple(sorted(key for key, row in cases.items() if row["label"] == label))
            if not ids:
                raise ValueError("each run/depth must contain both classes")
            groups[(label, ids)].append((index, [cases[key] for key in ids]))

    accuracy = [fmean(row["accuracy"] for row in cases.values()) for cases in data]
    tokens = [_mean_known([row["tokens"] for row in cases.values()]) for cases in data]
    bootstrap: dict[str, list[float]] = {
        "best_tokens": [], "average_tokens": [], "average_accuracy": [],
    }
    for _ in range(repetitions):
        correct, total = [0.0] * len(data), [0] * len(data)
        token_sum, token_n = [0] * len(data), [0] * len(data)
        for (_label, ids), members in groups.items():
            # The same sampled question indices are used by every run that
            # answered this shared stratum; separate case sets draw independently.
            picks = [rng.randrange(len(ids)) for _ in ids]
            for index, records in members:
                for pick in picks:
                    row = records[pick]
                    correct[index] += row["accuracy"]
                    total[index] += 1
                    if row["tokens"] is not None:
                        token_sum[index] += row["tokens"]
                        token_n[index] += 1
        run_tokens = [token_sum[i] / token_n[i] if token_n[i] else None for i in range(len(data))]
        if run_tokens[0] is not None:
            bootstrap["best_tokens"].append(run_tokens[0])
        mean_tokens = _mean_known(run_tokens)
        if mean_tokens is not None:
            bootstrap["average_tokens"].append(mean_tokens)
        bootstrap["average_accuracy"].append(fmean(correct[i] / total[i] for i in range(len(data))))

    best_n = len(data[0])
    best_k = sum(row["accuracy"] == 1 for row in data[0].values())
    return {
        "best_accuracy": accuracy[0],
        "best_accuracy_ci": list(wilson_95_ci(best_k, best_n)),
        "average_accuracy": fmean(accuracy),
        "average_accuracy_ci": _interval(bootstrap["average_accuracy"]),
        "best_tokens": tokens[0],
        "best_tokens_ci": _interval(bootstrap["best_tokens"]),
        "average_tokens": _mean_known(tokens),
        "average_tokens_ci": _interval(bootstrap["average_tokens"]),
        "token_runs_with_usage": sum(value is not None for value in tokens),
        "usage_coverage": [
            {"known_final_responses": sum(row["tokens"] is not None for row in cases.values()),
             "scheduled_cases": len(cases)}
            for cases in data
        ],
    }


def build_statistics(
    runs: Sequence[Mapping[str, Any]], *, repetitions: int = 2000, bootstrap_seed: int = 1729
) -> list[dict[str, Any]]:
    data = [observations(run) for run in runs]
    rng = random.Random(bootstrap_seed)
    return [
        {"depth": depth, **depth_statistics([run[depth] for run in data], repetitions=repetitions, rng=rng)}
        for depth in DEPTHS
    ]


def draw_graphs(points: Sequence[Mapping[str, Any]], output: Path, best_label: str, run_count: int) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    matplotlib.rcParams["svg.hashsalt"] = "is-prime-eval-depth-plots"
    specs = (
        ("tokens", "Mean completion tokens per recorded final response", "tokens-vs-depth", 1.0),
        ("accuracy", "Correct answers (%)", "accuracy-vs-depth", 100.0),
    )
    x = [point["depth"] for point in points]
    for metric, ylabel, filename, scale in specs:
        fig, ax = plt.subplots(figsize=(11, 6.5))
        for key, label, color, style in (
            ("best", f"Best overall: {best_label}", "#1565c0", "-"),
            ("average", f"Mean of all {run_count} runs (equal weight)", "#d45a00", "--"),
        ):
            y = [point[f"{key}_{metric}"] for point in points]
            ci = [point[f"{key}_{metric}_ci"] for point in points]
            values = [value * scale if value is not None else math.nan for value in y]
            lower = [band[0] * scale if band is not None else math.nan for band in ci]
            upper = [band[1] * scale if band is not None else math.nan for band in ci]
            ax.fill_between(x, lower, upper, color="gray", alpha=0.20, linewidth=0)
            ax.plot(x, values, style, marker="o", color=color, linewidth=2, label=label)
        ax.set(xlabel="Depth (decimal digits)", ylabel=ylabel, xticks=x)
        ax.set_title(f"{'Completion tokens' if metric == 'tokens' else 'Accuracy'} by depth")
        ax.grid(alpha=0.22)
        ax.set_ylim(bottom=0)
        if metric == "accuracy":
            ax.set_ylim(0, 103)
        else:
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend([*handles, Patch(facecolor="gray", alpha=0.25)], [*labels, "Pointwise 95% CI"], loc="best", fontsize=9)
        note = "Accuracy: winner Wilson CI; mean paired, class-stratified question-bootstrap CI."
        if metric == "tokens":
            missing: dict[tuple[int, int], list[int]] = defaultdict(list)
            for point in points:
                coverage = point["usage_coverage"][0]
                known, total = coverage["known_final_responses"], coverage["scheduled_cases"]
                if known < total:
                    missing[(known, total)].append(point["depth"])
            if missing:
                details = "; ".join(
                    f"{known}/{total} at depths {','.join(map(str, depths))}"
                    for (known, total), depths in sorted(missing.items())
                )
                note = f"Reasoning included; winner usage {details}; full elsewhere. All-run coverage: plot-data.json."
            else:
                note = "Reasoning included; winner usage complete at every depth. All-run coverage: plot-data.json."
        fig.text(0.5, 0.045, note, ha="center", fontsize=8)
        fig.text(0.5, 0.02, "Fixed saved-run roster; not model-population or session-to-session uncertainty. Winner selected overall.", ha="center", fontsize=8)
        fig.tight_layout(rect=(0, 0.08, 1, 1))
        fig.savefig(output / f"{filename}.png", dpi=180)
        svg_path = output / f"{filename}.svg"
        fig.savefig(svg_path, metadata={"Date": None})
        # Matplotlib emits trailing spaces inside multiline SVG path attributes.
        # Newlines already separate coordinates; trim spaces for clean diffs.
        svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
        plt.close(fig)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=WORKSPACE_ROOT / "results")
    parser.add_argument("--output-dir", type=Path, default=WORKSPACE_ROOT / "graphs")
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=1729, help="Plot CI reproducibility only; never changes evaluation inputs")
    args = parser.parse_args(argv)
    if args.bootstrap_samples < 200:
        parser.error("use at least 200 bootstrap samples")
    runs = select_runs(load_summaries(discover_ledgers(args.results_dir)))
    points = build_statistics(runs, repetitions=args.bootstrap_samples, bootstrap_seed=args.bootstrap_seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    best = runs[0]
    best_label = f"{best['model_id']} / {best.get('reasoning_effort') or 'provider default'}"
    payload = {
        "best_run": {key: best.get(key) for key in ("model_id", "reasoning_effort", "run_id")},
        "runs": [{key: run.get(key) for key in ("model_id", "reasoning_effort", "run_id")} for run in runs],
        "bootstrap_samples": args.bootstrap_samples, "bootstrap_seed": args.bootstrap_seed,
        "matplotlib_version": version("matplotlib"),
        "token_metric": "Mean final-response completion tokens, including reported reasoning; failed/retry-failure attempts excluded; missing usage excluded, not zero.",
        "ci_method": "Pointwise 95%: best accuracy Wilson; token means and mean accuracy percentile question bootstrap, class-stratified. Identical per-depth/class question cohorts resampled jointly; distinct cohorts independently (including incidental partial overlap). Fixed run roster; conditional on selecting the winner; no session/model-population inference or multiplicity adjustment.",
        "source_sha256": {
            str(path.relative_to(args.results_dir)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(args.results_dir.rglob("*"))
            if path.is_file() and path.suffix in (".json", ".jsonl")
        },
        "points": points,
    }
    (args.output_dir / "plot-data.json").write_text(json.dumps(payload, indent=2) + "\n")
    draw_graphs(points, args.output_dir, best_label, len(runs))
    print(f"Created two PNG/SVG graphs in {args.output_dir}; {len(runs)} runs; winner {best_label}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
