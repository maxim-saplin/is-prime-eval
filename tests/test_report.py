import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from report import render_leaderboard, summarize_run


class OptionalEffortReportTests(unittest.TestCase):
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
                    self.assertEqual(
                        text.count(f"| provider/model | {label} |"),
                        3 if complete else 1,
                    )


if __name__ == "__main__":
    unittest.main()
