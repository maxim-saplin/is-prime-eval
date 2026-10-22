import importlib.util
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from scripts.plot_results import DEPTHS, depth_statistics, draw_graphs, observations, select_runs


def cases(prefix, correct, tokens):
    return {
        f"{prefix}-{i}": {"label": "PRIME" if i % 2 else "COMPOSITE", "accuracy": float(value), "tokens": tokens[i]}
        for i, value in enumerate(correct)
    }


class PlotStatisticsTests(unittest.TestCase):
    def test_mean_weights_runs_equally_and_missing_usage_is_not_zero(self):
        data = [cases("a", [1, 1], [10, None]), cases("b", [0] * 6, [50] * 6)]
        stats = depth_statistics(data, repetitions=100, rng=random.Random(2))
        self.assertEqual(stats["average_accuracy"], 0.5)
        self.assertEqual(stats["best_tokens"], 10)
        self.assertEqual(stats["average_tokens"], 30)
        self.assertEqual(stats["usage_coverage"][0]["known_final_responses"], 1)
        self.assertLess(stats["best_accuracy_ci"][0], 1)
        self.assertEqual(stats["best_accuracy_ci"][1], 1)

    def test_shared_questions_do_not_become_independent_replications(self):
        records = cases("shared", [0, 1, 1, 0, 1, 1], [2, 4, 9, 10, 30, 40])
        single = depth_statistics([records], repetitions=300, rng=random.Random(12))
        duplicate = depth_statistics([records, records], repetitions=300, rng=random.Random(12))
        self.assertEqual(single["average_accuracy_ci"], duplicate["average_accuracy_ci"])
        self.assertEqual(single["average_tokens_ci"], duplicate["average_tokens_ci"])
        self.assertEqual(single["best_tokens_ci"], duplicate["best_tokens_ci"])

    def test_absent_tokens_remain_unavailable(self):
        stats = depth_statistics([cases("a", [0, 1], [None, None])], repetitions=30, rng=random.Random(1))
        self.assertIsNone(stats["best_tokens"])
        self.assertIsNone(stats["best_tokens_ci"])
        self.assertIsNone(stats["average_tokens"])
        self.assertIsNone(stats["average_tokens_ci"])

    def test_tokens_use_final_response_not_failed_attempt_or_double_reasoning(self):
        run = {
            "attempts": {
                "failed": {"case_id": "a", "status": "failed", "usage": {"completion_tokens": 1000}},
                "response": {"case_id": "a", "status": "response", "usage": {"completion_tokens": 5, "estimate_completion_tokens": 7, "reasoning_tokens": 4}},
            },
            "outcomes": [
                {"case_id": "a", "depth": 4, "gold_label": "PRIME", "outcome": "correct"},
                {"case_id": "b", "depth": 4, "gold_label": "COMPOSITE", "outcome": "no_response"},
            ],
        }
        data = observations(run)[4]
        self.assertEqual(data["a"]["tokens"], 7)
        self.assertIsNone(data["b"]["tokens"])
        self.assertEqual(data["b"]["accuracy"], 0)

    def test_winner_is_selected_globally_once_and_unsupported_runs_excluded(self):
        def run(model, correct, complete=True, depths=DEPTHS, cap=None):
            return {"model_id": model, "reasoning_effort": None, "run_id": model,
                    "complete": complete, "depths": list(depths), "scheduled": 360,
                    "counts": {"correct": correct}, "config": {"max_completion_tokens": cap}}
        selected = select_runs([run("b", 200), run("a", 300), run("unfinished", 360, False), run("partial-range", 20, depths=[4]), run("capped", 360, cap=512)])
        self.assertEqual([item["model_id"] for item in selected], ["a", "b"])

    @unittest.skipUnless(importlib.util.find_spec("matplotlib"), "optional plotting dependency")
    def test_each_saved_plot_has_two_lines_two_gray_bands_and_both_formats(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        axes = []
        original = plt.subplots
        def capture(*args, **kwargs):
            fig, ax = original(*args, **kwargs)
            axes.append(ax)
            return fig, ax
        points = [{"depth": depth, **depth_statistics([cases("a", [0, 1], [10, 30]), cases("b", [1, 1], [20, 40])], repetitions=30, rng=random.Random(depth))} for depth in (4, 5)]
        with tempfile.TemporaryDirectory() as folder, patch.object(plt, "subplots", side_effect=capture):
            draw_graphs(points, Path(folder), "provider/model / high", 2)
            for stem in ("tokens-vs-depth", "accuracy-vs-depth"):
                self.assertTrue((Path(folder) / f"{stem}.png").read_bytes().startswith(b"\x89PNG"))
                svg = (Path(folder) / f"{stem}.svg").read_text()
                self.assertIn("<svg", svg)
                self.assertTrue(all(line == line.rstrip() for line in svg.splitlines()))
        self.assertEqual(len(axes), 2)
        self.assertTrue(all(len(ax.lines) == 2 and len(ax.collections) == 2 for ax in axes))
        for ax in axes:
            for band in ax.collections:
                red, green, blue, _ = band.get_facecolor()[0]
                self.assertEqual(red, green)
                self.assertEqual(green, blue)


if __name__ == "__main__":
    unittest.main()
