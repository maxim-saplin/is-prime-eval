"""Entrypoint smoke tests: every runnable CLI must work from *outside* the repo.

These guard the published layout: library modules stay at the repository root,
runnable entrypoints live at root (`run.py`) or under `scripts/`, and each
entrypoint must resolve its imports without relying on the working directory.
`--help` is used because it exercises argument parsing, imports, and exit
behavior without making any API/network calls.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCRIPTS = (
    "run.py",
    "scripts/report.py",
    "scripts/plot_results.py",
    "scripts/enrich_generations.py",
)


def _run_help(script: str) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env.pop("OR_KEY", None)
    env.pop("OPENROUTER_API_KEY", None)
    with tempfile.TemporaryDirectory(prefix="is-prime-eval-entrypoint-") as outside:
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / script), "--help"],
            cwd=outside,
            env=env,
            capture_output=True,
            timeout=120,
        )


class EntrypointTests(unittest.TestCase):
    def test_help_works_from_outside_cwd(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                result = _run_help(script)
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"{script} --help failed from outside cwd\n"
                    f"stdout:\n{result.stdout.decode(errors='replace')}\n"
                    f"stderr:\n{result.stderr.decode(errors='replace')}",
                )
                combined = (result.stdout + result.stderr).decode(errors="replace")
                self.assertIn("usage:", combined.lower(), msg=f"{script}: no usage text")

    def test_prime_stats_module_imports_and_targets_docs(self):
        # prime_stats.py has no CLI; it only needs to import cleanly and point
        # at the published output location. primecountpy is an optional
        # dependency, so stub it out and assert import does not leak extra
        # modules into sys.modules (no real primecountpy import attempt).
        import importlib
        import sys
        import types
        from unittest import mock

        fake_primecountpy = types.ModuleType("primecountpy")
        fake_primecountpy.prime_pi = lambda n: 0
        before = set(sys.modules)
        with mock.patch.dict(sys.modules, {"primecountpy": fake_primecountpy}):
            module = importlib.import_module("scripts.prime_stats")
            self.assertIs(sys.modules["primecountpy"], fake_primecountpy)
            self.assertEqual(
                module.OUTPUT_PATH, PROJECT_ROOT / "docs" / "prime-stats.md"
            )
        added = set(sys.modules) - before
        # Only the module under test (and its package, if not already loaded)
        # may be newly imported; nothing else, and certainly not the real
        # optional dependency.
        self.assertTrue(added <= {"scripts.prime_stats", "scripts"}, msg=f"unexpected sys.modules additions: {added}")
        sys.modules.pop("scripts.prime_stats", None)

    def test_published_layout_anchors(self):
        # Guard the agreed layout: core entrypoint at root, utilities under
        # scripts/, docs under docs/, results README present.
        for expected in (
            PROJECT_ROOT / "run.py",
            PROJECT_ROOT / "scripts" / "__init__.py",
            PROJECT_ROOT / "scripts" / "prime_stats.py",
            PROJECT_ROOT / "scripts" / "enrich_generations.py",
            PROJECT_ROOT / "docs" / "prime-stats.md",
            PROJECT_ROOT / "results" / "README.md",
        ):
            with self.subTest(path=expected):
                self.assertTrue(expected.is_file(), msg=f"missing {expected}")


if __name__ == "__main__":
    unittest.main()
