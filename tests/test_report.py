import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from report import render_leaderboard, summarize_run, wilson_95_ci


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
                with patch("report._case_outcomes", return_value=([outcome], True)):
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
                        with patch("report._case_outcomes", return_value=([outcome], complete)):
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
