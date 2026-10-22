"""Integrity checks for the checked-in publication, without API calls or Matplotlib."""

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent


class PublicationTests(unittest.TestCase):
    def test_local_document_links_resolve(self):
        documents = [
            ROOT / "README.md", ROOT / "analysis.md", ROOT / "leaderboard.md",
            ROOT / "results/README.md", *ROOT.glob("docs/*.md"),
            *ROOT.glob("graphs/*.md"),
        ]
        for document in documents:
            self.assertTrue(document.is_file(), document)
            for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", document.read_text()):
                if "://" in link or link.startswith("#"):
                    continue
                with self.subTest(document=document, link=link):
                    self.assertTrue((document.parent / link.split("#")[0]).exists())

    def test_readme_and_leaderboard_tables_match(self):
        readme = (ROOT / "README.md").read_text()
        start, end = "<!-- leaderboard:start -->", "<!-- leaderboard:end -->"
        self.assertEqual(readme.count(start), 1)
        self.assertEqual(readme.count(end), 1)
        embedded = readme.split(start)[1].split(end)[0].strip()
        leaderboard = (ROOT / "leaderboard.md").read_text()
        table = "\n".join(line for line in leaderboard.splitlines() if line.startswith("|"))
        self.assertEqual(embedded, table)
        self.assertIn("7–15", leaderboard)
        self.assertIn("| Cost |", table)
        self.assertNotIn("Partial", table)
        self.assertNotIn("*", table)
        self.assertNotIn("attempts", table)
        for line in table.splitlines()[2:]:
            cost = line.split("|")[4].strip()
            if cost not in ("Unknown", "—"):
                self.assertRegex(cost, r"^\$\d+\.\d{3}$")

    def test_plot_source_fingerprints_match_current_results(self):
        data = json.loads((ROOT / "graphs/plot-data.json").read_text())
        expected_sources = {
            str(p.relative_to(ROOT / "results"))
            for p in (ROOT / "results").rglob("*")
            if p.is_file() and p.suffix in (".json", ".jsonl")
        }
        self.assertEqual(set(data["source_sha256"]), expected_sources)
        for source, fingerprint in data["source_sha256"].items():
            with self.subTest(source=source):
                self.assertEqual(
                    hashlib.sha256((ROOT / "results" / source).read_bytes()).hexdigest(),
                    fingerprint,
                )

    def test_plot_points_intervals_and_usage_are_consistent(self):
        data = json.loads((ROOT / "graphs/plot-data.json").read_text())
        self.assertEqual([p["depth"] for p in data["points"]], list(range(4, 16)))
        self.assertIn(data["best_run"], data["runs"])
        for point in data["points"]:
            self.assertEqual(len(point["usage_coverage"]), len(data["runs"]))
            for coverage in point["usage_coverage"]:
                self.assertGreater(coverage["scheduled_cases"], 0)
                self.assertLessEqual(coverage["known_final_responses"], coverage["scheduled_cases"])
            for metric in ("best_accuracy", "average_accuracy", "best_tokens", "average_tokens"):
                with self.subTest(depth=point["depth"], metric=metric):
                    value, band = point[metric], point[metric + "_ci"]
                    if value is None:
                        self.assertIsNone(band)
                        continue
                    self.assertGreaterEqual(value, 0)
                    self.assertLessEqual(band[0], band[1])
                    if metric.endswith("accuracy"):
                        self.assertLessEqual(value, 1)
                        self.assertGreaterEqual(band[0], 0)
                        self.assertLessEqual(band[1], 1)
                    if metric == "best_accuracy":
                        self.assertLessEqual(band[0], value)
                        self.assertGreaterEqual(band[1], value)


if __name__ == "__main__":
    unittest.main()
