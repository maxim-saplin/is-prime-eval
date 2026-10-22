"""Entrypoint smoke tests for the packaged layout.

The evaluator is a proper package (`is_prime_eval`) installed under `src/`
with a `__main__.py` that forwards to the CLI. These tests guard that:
- `python -m is_prime_eval --help` works from *outside* the repository;
- installed console scripts (`is-prime-eval`, `is-prime-report`,
  `is-prime-plot`, `is-prime-enrich`) exist in the active venv and work
  (installation is mandatory — failure, never skip);
- defaults (`--results-dir`, `.env`) resolve from the process cwd, never
  from the installed package location;
- the published layout anchors are in place: no root `*.py` shims, and
  `scripts/` holds only the standalone `prime_stats.py` utility;
- `scripts/prime_stats.py` still imports cleanly with the optional
  `primecountpy` dependency stubbed out, without polluting `sys.modules`.

`--help` exercises argument parsing, imports, and exit behavior without any
API/network calls. All temp directories use `TemporaryDirectory` contexts so
nothing leaks after the process and assertions complete.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "is_prime_eval"

# Console entrypoints installed by pyproject into the active venv.
INSTALLED_COMMANDS = (
    "is-prime-eval",
    "is-prime-report",
    "is-prime-plot",
    "is-prime-enrich",
)


def _run_from_outside(argv: list[str], *, executable: str | None = None) -> subprocess.CompletedProcess[bytes]:
    with tempfile.TemporaryDirectory(prefix="is-prime-eval-entrypoint-") as outside:
        env = dict(os.environ)
        env.pop("OR_KEY", None)
        env.pop("OPENROUTER_API_KEY", None)
        return subprocess.run(
            [executable or sys.executable, *argv],
            cwd=outside,
            env=env,
            capture_output=True,
            timeout=120,
        )


class InstalledModuleTests(unittest.TestCase):
    def test_python_dash_m_help_works_from_outside_cwd(self):
        result = _run_from_outside(["-m", PACKAGE, "--help"])
        self.assertEqual(
            result.returncode, 0,
            msg=f"python -m {PACKAGE} --help failed\n"
            f"stdout:\n{result.stdout.decode(errors='replace')}\n"
            f"stderr:\n{result.stderr.decode(errors='replace')}",
        )
        combined = (result.stdout + result.stderr).decode(errors="replace")
        self.assertIn("usage:", combined.lower())

    def test_installed_console_commands_exist_and_work(self):
        # Installation is mandatory for the imported package; resolve commands
        # only from the active venv (sys.prefix/bin), never from PATH, which
        # could point at a different install.
        venv_bin = Path(sys.prefix) / "bin"
        for command in INSTALLED_COMMANDS:
            path = venv_bin / command
            with self.subTest(command=command):
                self.assertTrue(
                    path.is_file(),
                    msg=f"missing installed entrypoint: {path} "
                    f"(is the editable install complete?)",
                )
                result = _run_from_outside(["--help"], executable=str(path))
                self.assertEqual(
                    result.returncode, 0,
                    msg=f"{command} --help failed\n{result.stderr.decode(errors='replace')}",
                )
                combined = (result.stdout + result.stderr).decode(errors="replace")
                self.assertIn("usage:", combined.lower())

    def test_python_dash_m_installs_signal_handlers(self):
        # Regression: the `python -m is_prime_eval` path must install the CLI
        # signal handlers even when SIGINT is inherited as ignored. The real
        # main() is replaced by an offline probe so nothing evaluates; the
        # probe sends SIGINT/SIGTERM to itself and reports whether the
        # installed handlers converted them into KeyboardInterrupt.
        venv_bin = Path(sys.prefix) / "bin"
        for launcher, label in (
            (["-m", PACKAGE], "python -m is_prime_eval"),
            (["runpy_script", str(venv_bin / "is-prime-eval")], "installed is-prime-eval"),
        ):
            with self.subTest(launcher=label):
                result = self._run_signal_probe(launcher)
                self.assertEqual(result.returncode, 0, msg=result.stderr.decode(errors="replace"))
                self.assertEqual(
                    result.stdout.decode().strip(),
                    "handled:SIGINT,handled:SIGTERM",
                    msg=f"{label} did not install signal handlers\n"
                    f"stdout:\n{result.stdout.decode(errors='replace')}\n"
                    f"stderr:\n{result.stderr.decode(errors='replace')}",
                )

    @staticmethod
    def _run_signal_probe(launcher: list[str]) -> subprocess.CompletedProcess[bytes]:
        # The child first marks SIGINT as ignored (like a background shell),
        # patches cli.main with an offline probe, then runs the real entry
        # path via runpy so the actual bootstrap/entrypoint code executes.
        code = (
            "import os\n"
            "import signal\n"
            "import runpy\n"
            "signal.signal(signal.SIGINT, signal.SIG_IGN)\n"
            "from is_prime_eval import cli\n"
            "def probe(argv=None):\n"
            "    marks = []\n"
            "    for sig in (signal.SIGINT, signal.SIGTERM):\n"
            "        try:\n"
            "            os.kill(os.getpid(), sig)\n"
            "            marks.append('miss:' + signal.Signals(sig).name)\n"
            "        except KeyboardInterrupt:\n"
            "            marks.append('handled:' + signal.Signals(sig).name)\n"
            "    print(','.join(marks))\n"
            "    return 0\n"
            "cli.main = probe\n"
        )
        if launcher[0] == "runpy_script":
            code += f"runpy.run_path({launcher[1]!r}, run_name='__main__')\n"
        else:
            code += f"runpy.run_module({PACKAGE!r}, run_name='__main__')\n"
        with tempfile.TemporaryDirectory(prefix="is-prime-eval-sig-") as outside:
            env = dict(os.environ)
            env.pop("OR_KEY", None)
            env.pop("OPENROUTER_API_KEY", None)
            return subprocess.run(
                [sys.executable, "-c", code],
                cwd=outside,
                env=env,
                capture_output=True,
                timeout=60,
            )

    def test_workingdir_defaults_resolve_under_cwd(self):
        # Defaults (results dir, .env) must resolve from the process cwd, not
        # from the installed package location (src/site-packages). Spawn a
        # fresh interpreter from an outside temp dir that contains a .env
        # fixture, and verify both defaults pick it up. Only a boolean is
        # printed — the fixture key itself never leaves the test.
        code = (
            "import os\n"
            "from is_prime_eval.cli import build_parser\n"
            "from is_prime_eval.settings import load_dotenv, get_openrouter_key\n"
            "loaded = load_dotenv()\n"
            "results = os.path.abspath(build_parser().parse_args([]).results_dir)\n"
            "env_ok = loaded and get_openrouter_key() == 'fixture-secret'\n"
            "print(results)\n"
            "print('env:', env_ok)\n"
        )
        with tempfile.TemporaryDirectory(prefix="is-prime-eval-cwd-default-") as outside:
            Path(outside, ".env").write_text(
                "OR_KEY='fixture-secret'\n", encoding="utf-8"
            )
            env = dict(os.environ)
            env.pop("OR_KEY", None)
            env.pop("OPENROUTER_API_KEY", None)
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=outside,
                env=env,
                capture_output=True,
                timeout=60,
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr.decode(errors="replace"))
        lines = result.stdout.decode().splitlines()
        self.assertEqual(lines[0], os.path.join(outside, "results"))
        self.assertEqual(lines[1], "env: True")


class PublishedLayoutTests(unittest.TestCase):
    def test_package_anchors_exist(self):
        package_dir = PROJECT_ROOT / "src" / "is_prime_eval"
        for expected in (
            package_dir / "__init__.py",
            package_dir / "cli.py",
            package_dir / "__main__.py",
            package_dir / "report.py",
            package_dir / "plot_results.py",
            package_dir / "enrich_generations.py",
            PROJECT_ROOT / "scripts" / "prime_stats.py",
            PROJECT_ROOT / "docs" / "prime-stats.md",
            PROJECT_ROOT / "results" / "README.md",
        ):
            with self.subTest(path=expected):
                self.assertTrue(expected.is_file(), msg=f"missing {expected}")

    def test_no_root_python_shims_and_old_script_modules_are_gone(self):
        # The package owns all Python code; the root must contain no .py
        # shims, and the old script-style modules must be gone.
        self.assertEqual(
            list(PROJECT_ROOT.glob("*.py")),
            [],
            msg=f"unexpected root .py shims: {[p.name for p in PROJECT_ROOT.glob('*.py')]}",
        )
        for absent in (
            PROJECT_ROOT / "scripts" / "report.py",
            PROJECT_ROOT / "scripts" / "plot_results.py",
            PROJECT_ROOT / "scripts" / "enrich_generations.py",
        ):
            with self.subTest(path=absent):
                self.assertFalse(absent.exists(), msg=f"stale file present: {absent}")


class PrimeStatsModuleTests(unittest.TestCase):
    def test_prime_stats_module_imports_without_optional_dep_and_avoids_pollution(self):
        # primecountpy is optional for the standalone utility; stub it and
        # assert importing scripts.prime_stats does not load the real module
        # or leak unrelated entries into sys.modules.
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
        self.assertTrue(
            added <= {"scripts.prime_stats", "scripts"},
            msg=f"unexpected sys.modules additions: {added}",
        )
        sys.modules.pop("scripts.prime_stats", None)


if __name__ == "__main__":
    unittest.main()
