import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.report import (
    render_compact_leaderboard,
    render_leaderboard,
    summarize_run,
    update_readme_leaderboard,
    wilson_95_ci,
)


TEST_COMPACT_DEPTHS = tuple(range(7, 16))


def _fake_summary(
    model,
    effort,
    run_id,
    correct_by_depth,
    attempts=None,
    complete=True,
    depths=None,
    by_depth_extra=None,
):
    depths = tuple(depths) if depths is not None else TEST_COMPACT_DEPTHS
    by_depth = {}
    for depth in depths:
        correct = correct_by_depth.get(depth, 0)
        by_depth[depth] = {
            "scheduled": 30, "correct": correct, "wrong_label": 0,
            "invalid": 0, "truncated": 0, "no_response": 0, "pending": 0,
            "not_attempted": 0, "primes_scheduled": 15, "primes_correct": 0,
            "nonprimes_scheduled": 15, "nonprimes_correct": 0, "incorrect": 0,
        }
    by_depth.update(by_depth_extra or {})
    return {
        "model_id": model, "reasoning_effort": effort, "run_id": run_id,
        "complete": complete, "depths": list(depths), "by_depth": by_depth,
        "attempts": attempts or {},
    }


def _attempt(case_id, depth, *, status="response", prompt=10, completion=100, cost="0.01",
             normalized="0.02", latency=5.0):
    usage = {"prompt_tokens": prompt, "completion_tokens": completion,
             "estimate_prompt_tokens": prompt, "estimate_completion_tokens": completion}
    return {
        "attempt_id": f"att-{case_id}", "case_id": case_id, "depth": depth,
        "status": status, "provider_reported_usd": cost,
        "normalized_uncached_usd": normalized, "latency_seconds": latency,
        "usage": usage,
    }


class WilsonIntervalTests(unittest.TestCase):
    def test_interval_handles_empty_zero_all_and_low_counts(self):
        self.assertIsNone(wilson_95_ci(0, 0))
        zero_low, zero_high = wilson_95_ci(0, 20)
        self.assertEqual(zero_low, 0.0)
        self.assertGreater(zero_high, 0.0)
        all_low, all_high = wilson_95_ci(20, 20)
        self.assertLess(all_low, 1.0)
        self.assertEqual(all_high, 1.0)
        low_n, low_n_high = wilson_95_ci(1, 1)
        self.assertGreater(low_n, 0.0)
        self.assertEqual(low_n_high, 1.0)
        with self.assertRaises(ValueError):
            wilson_95_ci(2, 1)


class OptionalEffortReportTests(unittest.TestCase):
    def test_different_datasets_share_one_results_table_without_dataset_ids(self):
        runs = (
            ("run-a", "provider/mercury", "dataset-a", "correct"),
            ("run-b", "provider/other", "dataset-b", "wrong_label"),
        )
        with tempfile.TemporaryDirectory() as directory:
            summaries = []
            for run_id, model_id, dataset_id, outcome_name in runs:
                ledger = Path(directory) / f"{run_id}.jsonl"
                ledger.write_text("", encoding="utf-8")
                ledger.with_suffix(".manifest.json").write_text(
                    json.dumps({
                        "run_id": run_id,
                        "model": {"model_id": model_id, "reasoning_effort": None},
                        "config": {"timeout_seconds": 600, "max_attempts": 6, "retry_delay_seconds": 1},
                        "dataset": {"dataset_id": dataset_id, "depths": [4], "samples_per_class": 1},
                    }),
                    encoding="utf-8",
                )
                outcome = {
                    "depth": 4,
                    "outcome": outcome_name,
                    "gold_label": "PRIME",
                    "attempted": True,
                    "answered": True,
                }
                with patch("scripts.report._case_outcomes", return_value=([outcome], True)):
                    summaries.append(summarize_run(ledger))

        text = render_leaderboard(summaries)
        self.assertEqual(text.count("## Completed runs"), 1)
        self.assertNotIn("## Dataset `", text)
        self.assertNotIn("dataset-a", text)
        self.assertNotIn("dataset-b", text)
        self.assertIn("provider/mercury", text)
        self.assertIn("provider/other", text)
        self.assertIn("different frozen questions are not paired comparisons", text)

    def test_missing_and_null_effort_remain_distinct_in_all_report_tables(self):
        examples = (
            ({}, "unknown"),
            ({"reasoning_effort": None}, "omitted (provider default)"),
            ({"reasoning_effort": "none"}, "none"),
            ({"reasoning_effort": "custom|effort"}, "custom\\|effort"),
        )
        for model_effort, label in examples:
            for complete in (False, True):
                with self.subTest(model_effort=model_effort, complete=complete):
                    with tempfile.TemporaryDirectory() as directory:
                        ledger = Path(directory) / "run.jsonl"
                        ledger.write_text("", encoding="utf-8")
                        ledger.with_suffix(".manifest.json").write_text(json.dumps({
                            "model": {"model_id": "provider/model", **model_effort},
                            "dataset": {"depths": [4]},
                        }), encoding="utf-8")
                        outcome = {
                            "depth": 4,
                            "outcome": "correct" if complete else "not_attempted",
                            "gold_label": "PRIME",
                            "attempted": complete,
                            "answered": complete,
                        }
                        with patch("scripts.report._case_outcomes", return_value=([outcome], complete)):
                            summary = summarize_run(ledger)
                    self.assertEqual(summary["reasoning_effort"], model_effort.get("reasoning_effort", "unknown"))
                    text = render_leaderboard([summary])
                    if complete:
                        self.assertEqual(text.count("Approx. 95% Wilson CI"), 2)
                    self.assertEqual(
                        text.count(f"| provider/model | {label} |"),
                        3 if complete else 1,
                    )


if __name__ == "__main__":
    unittest.main()


class CompactLeaderboardTests(unittest.TestCase):
    def test_compact_scopes_to_depths_7_15_and_sorts_descending(self):
        high = _fake_summary(
            "provider/model-a", "high", "run-a",
            {7: 30, 8: 25, 9: 20, 4: 30, 5: 30, 6: 30},
        )  # scope 75/270
        low = _fake_summary(
            "provider/model-b", None, "run-b",
            {7: 20, 8: 20, 9: 20, 4: 30, 5: 30, 6: 30},
        )  # scope 60/270
        text = render_compact_leaderboard([low, high])
        self.assertLess(text.index("model-a-high"), text.index("model-b"))
        self.assertIn("27.8%", text)  # 75/270
        self.assertIn("22.2%", text)  # 60/270
        self.assertIn("Depths 7–15 only", text)

    def test_compact_strips_provider_and_appends_effort_suffix(self):
        runs = [
            _fake_summary("openai/gpt-6-luna", "high", "r1", {7: 30, 8: 30, 9: 30}),
            _fake_summary("inception/mercury-3", None, "r2", {7: 29, 8: 29, 9: 29}),
            _fake_summary("deepseek/deepseek-v4.1-flash-1017", "low", "r3", {7: 28, 8: 28, 9: 28}),
        ]
        text = render_compact_leaderboard(runs)
        self.assertIn("gpt-6-luna-high", text)
        self.assertNotIn("openai/gpt-6-luna", text)
        self.assertIn("mercury-3", text)
        self.assertNotIn("mercury-3-", text)
        self.assertIn("deepseek-v4.1-flash-1017-low", text)

    def test_compact_uses_provider_reported_cost_only(self):
        attempts = {
            "c1": _attempt("c1", 7, cost="0.10", normalized="0.99", latency=3.0),
            "c2": _attempt("c2", 8, cost="0.20", normalized="0.99", latency=4.0),
            "c3": _attempt("c3", 9, cost=None, normalized="0.50", latency=None),
            "c4": _attempt("c4", 4, cost="9.99", normalized="9.99", latency=9.0),  # out of scope
        }
        summary = _fake_summary("provider/model", "high", "r", {7: 30, 8: 30, 9: 30}, attempts=attempts)
        text = render_compact_leaderboard([summary])
        self.assertIn("$0.300", text)  # 2/3 attempts priced, clean numeric cell
        self.assertNotIn("0.99", text)  # estimated cost never shown
        self.assertNotIn("Estimated", text)
        self.assertNotIn("9.99", text)  # out-of-scope cost excluded
        self.assertIn("never used", text)
        self.assertIn("Tokens/cost are reported subtotals where usage is missing; not complete bills.", text)
        self.assertIn("Coverage: model-high: cost 2/3, API 2/3.", text)
        self.assertNotIn("*", text)  # no sidenote markers in cells

    def test_compact_tokens_total_prompt_plus_completion_within_scope(self):
        attempts = {
            "a1": _attempt("a1", 7, prompt=10, completion=100),  # 110
            "a2": _attempt("a2", 8, prompt=10, completion=200),  # 210
            "a3": _attempt("a3", 9, prompt=None, completion=None, cost=None, latency=None),
            "a4": _attempt("a4", 9, status="failed", prompt=10, completion=9999, cost="0.01"),
            "a5": _attempt("a5", 4, prompt=10, completion=9999),  # out of scope
        }
        summary = _fake_summary("provider/model", None, "r", {7: 30, 8: 30, 9: 30}, attempts=attempts)
        text = render_compact_leaderboard([summary])
        # scoped total = 110 + 210 + failed 10009 = 10329 over 3/4 attempts
        self.assertIn("| 10,329 |", text)
        self.assertNotIn("9999", text)
        self.assertNotIn("10,009", text)
        self.assertIn("Coverage: model: tokens 3/4, cost 3/4, API 3/4.", text)
        self.assertNotIn("*", text)

    def test_compact_api_time_sums_scoped_request_latency_and_marks_missing(self):
        attempts = {
            "c1": _attempt("c1", 7, latency=10.0),
            "c2": _attempt("c2", 8, latency=20.0),
            "c3": _attempt("c3", 9, latency=None),
            "c4": _attempt("c4", 4, latency=9999.0),
        }
        summary = _fake_summary("provider/model", None, "r", {7: 30, 8: 30, 9: 30}, attempts=attempts)
        text = render_compact_leaderboard([summary])
        self.assertIn("| 30s |", text)
        self.assertNotIn("9999", text)
        self.assertIn("Coverage: model: API 2/3.", text)
        self.assertNotIn("*", text)

    def test_compact_omits_api_time_column_when_no_scoped_latency(self):
        no_time = _fake_summary("provider/model", None, "r", {7: 30, 8: 30, 9: 30},
                                attempts={"c1": _attempt("c1", 7, latency=None)})
        text = render_compact_leaderboard([no_time])
        self.assertNotIn("| API time |", text)
        self.assertNotIn("API time =", text)
        self.assertNotIn("n/a", text)
        self.assertIn("API time column omitted", text)
        self.assertIn("$0.010", text)  # remaining columns stay intact

    def test_compact_excludes_runs_missing_requested_depths(self):
        full = _fake_summary("provider/full", None, "r1", {7: 30, 8: 30, 9: 30})
        easy_only = _fake_summary(
            "provider/easy", None, "r2", {4: 30, 5: 30, 6: 30},
            depths=(4, 5, 6),
        )
        partial = _fake_summary(
            "provider/short", None, "r3", {7: 30, 8: 30}, depths=(7, 8),
        )
        text = render_compact_leaderboard([easy_only, partial, full])
        self.assertNotIn("| easy |", text)
        self.assertNotIn("| short |", text)
        self.assertIn("| full |", text)
        self.assertEqual(text.count("| 1 |"), 0)  # no rank column
        self.assertIn("Scope: 1 complete runs", text)

    def test_compact_excludes_incomplete_runs(self):
        complete = _fake_summary("provider/model", None, "r1", {7: 30, 8: 30, 9: 30})
        incomplete = _fake_summary("provider/other", None, "r2", {7: 30, 8: 30, 9: 30}, complete=False)
        text = render_compact_leaderboard([complete, incomplete])
        self.assertNotIn("other", text)
        self.assertIn("model", text)
        self.assertEqual(text.count("| model |"), 1)

    def test_compact_documents_scope_and_independent_winner_selection(self):
        summary = _fake_summary(
            "provider/model", None, "r", {7: 30, 8: 30, 9: 30},
            attempts={"c1": _attempt("c1", 7, latency=1.0)},
        )
        text = render_compact_leaderboard([summary])
        self.assertIn("computed independently within 7–15", text)
        self.assertIn("analysis.md", text)
        self.assertIn("retries included", text)
        self.assertIn("rate-gate waits", text)
        self.assertIn("never used", text)
        self.assertIn("prompt + completion", text)
        self.assertIn("Tokens/cost are reported subtotals where usage is missing; not complete bills.", text)
        self.assertNotIn("| Rank |", text)
        self.assertNotIn("Provider-reported cost (USD)", text)

    def test_wilson_endpoints_exact_for_all_or_none_successes(self):
        none_low, none_high = wilson_95_ci(0, 30)
        self.assertEqual(none_low, 0.0)
        all_low, all_high = wilson_95_ci(30, 30)
        self.assertEqual(all_high, 1.0)
        self.assertLess(all_low, 1.0)
        # n=20 regression: all-success upper bound must be exactly 1.0
        _, n20_all_high = wilson_95_ci(20, 20)
        self.assertEqual(n20_all_high, 1.0)
        n20_none_low, _ = wilson_95_ci(0, 20)
        self.assertEqual(n20_none_low, 0.0)

    def test_update_readme_leaderboard_requires_markers_and_file(self):
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(
                "# Header\n\n<!-- leaderboard:start -->\nold table\n<!-- leaderboard:end -->\n\nTail.\n",
                encoding="utf-8",
            )
            table = "| Rank | Model | Accuracy |\n|---:|---|---|\n| 1 | m | 100% |"
            update_readme_leaderboard(readme, table)
            updated = readme.read_text(encoding="utf-8")
            self.assertIn("# Header", updated)
            self.assertIn("Tail.", updated)
            self.assertIn("| 1 | m | 100% |", updated)
            self.assertNotIn("old table", updated)
            # missing markers must fail loudly, leaving the file untouched
            plain = Path(directory) / "plain.md"
            plain.write_text("no markers here\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                update_readme_leaderboard(plain, table)
            self.assertEqual(plain.read_text(encoding="utf-8"), "no markers here\n")
            with self.assertRaises(FileNotFoundError):
                update_readme_leaderboard(Path(directory) / "absent.md", table)
            # duplicated markers must be refused without mutation
            dup = Path(directory) / "dup.md"
            dup_text = (
                "<!-- leaderboard:start -->\n<!-- leaderboard:start -->\n"
                "body\n<!-- leaderboard:end -->\n< leaderboard:end -->\n"
            )
            dup.write_text(dup_text, encoding="utf-8")
            with self.assertRaises(ValueError):
                update_readme_leaderboard(dup, table)
            self.assertEqual(dup.read_text(encoding="utf-8"), dup_text)
            # end-before-start must be refused without mutation
            inverted = Path(directory) / "inverted.md"
            inverted_text = (
                "<!-- leaderboard:end -->\nbody\n<!-- leaderboard:start -->\n"
            )
            inverted.write_text(inverted_text, encoding="utf-8")
            with self.assertRaises(ValueError):
                update_readme_leaderboard(inverted, table)
            self.assertEqual(inverted.read_text(encoding="utf-8"), inverted_text)
