import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class BatchScriptTests(unittest.TestCase):
    def test_13_pair_script_is_explicit_safe_and_points_outside_git(self):
        script_path = PROJECT_ROOT / "scripts" / "run_13_pair_sweep.sh"
        text = script_path.read_text(encoding="utf-8")
        self.assertTrue(script_path.stat().st_mode & 0o111)
        self.assertIn('mode="${1:---dry-run}"', text)
        self.assertIn("--parallelism 3", text)
        self.assertIn("--max-retries 5", text)
        self.assertIn("--retry-delay 1", text)
        self.assertIn("--requests-per-minute 15", text)
        self.assertIn("flock -n 9", text)
        self.assertIn("realpath -m", text)
        self.assertIn("/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean", text)
        self.assertIn("old_partial_dir=\"/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep\"", text)

        pairs = re.findall(
            r"--model-id\s+(\S+)\s+--reasoning-effort\s+(\S+)", text
        )
        self.assertEqual(
            pairs,
            [
                ("openai/gpt-6-luna", "low"),
                ("openai/gpt-6-luna", "medium"),
                ("openai/gpt-6-luna", "high"),
                ("openai/gpt-6-luna", "xhigh"),
                ("deepseek/deepseek-v4.1-flash-1017", "low"),
                ("deepseek/deepseek-v4.1-flash-1017", "medium"),
                ("deepseek/deepseek-v4.1-flash-1017", "high"),
                ("anthropic/claude-haiku-5.5", "low"),
                ("anthropic/claude-haiku-5.5", "medium"),
                ("anthropic/claude-haiku-5.5", "high"),
                ("anthropic/claude-haiku-5.5", "xhigh"),
                ("openai/gpt-6.1-sol", "low"),
                ("openai/gpt-6.1-sol", "medium"),
            ],
        )

    def test_dry_run_rejects_path_traversal_into_immutable_archive(self):
        script = PROJECT_ROOT / "scripts" / "run_13_pair_sweep.sh"
        env = os.environ.copy()
        env["EVAL_RESULTS_DIR"] = (
            "/data/eval-runs/is-prim-eval/2026-10-20/../2026-10-19/13-pair-sweep"
        )
        completed = subprocess.run(
            [str(script), "--dry-run"],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("immutable partial-run archive", completed.stderr)

    def test_dry_run_rejects_symlink_into_immutable_archive(self):
        script = PROJECT_ROOT / "scripts" / "run_13_pair_sweep.sh"
        old_archive = Path("/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep")
        with tempfile.TemporaryDirectory() as temp_dir:
            alias = Path(temp_dir) / "archive-alias"
            alias.symlink_to(old_archive, target_is_directory=True)
            env = os.environ.copy()
            env["EVAL_RESULTS_DIR"] = str(alias)
            completed = subprocess.run(
                [str(script), "--dry-run"],
                cwd=PROJECT_ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("immutable partial-run archive", completed.stderr)

    def test_live_script_lock_rejects_overlapping_batches_with_different_dirs(self):
        if not shutil.which("flock"):
            self.skipTest("flock is required for the live launch-lock test")
        original = (PROJECT_ROOT / "scripts" / "run_13_pair_sweep.sh").read_text()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            (project / "scripts").mkdir(parents=True)
            (project / ".venv" / "bin").mkdir(parents=True)
            lock = root / "global-live.lock"
            script = original.replace(
                'lock_file="/data/eval-runs/is-prim-eval/.13-pair-sweep-live.lock"',
                f'lock_file="{lock}"',
            )
            script_path = project / "scripts" / "run_13_pair_sweep.sh"
            script_path.write_text(script, encoding="utf-8")
            script_path.chmod(0o755)
            fake_python = project / ".venv" / "bin" / "python"
            fake_python.write_text("#!/bin/sh\nsleep 0.5\n", encoding="utf-8")
            fake_python.chmod(0o755)

            base_env = os.environ.copy()
            base_env["EVAL_RESULTS_DIR"] = str(root / "first-results")
            first = subprocess.Popen(
                [str(script_path), "--live"],
                cwd=project,
                env=base_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.monotonic() + 2
            first_holds_lock = False
            while time.monotonic() < deadline:
                probe = subprocess.run(
                    ["flock", "-n", str(lock), "true"],
                    capture_output=True,
                    check=False,
                )
                if probe.returncode != 0:
                    first_holds_lock = True
                    break
                time.sleep(0.01)
            self.assertTrue(first_holds_lock, "first live launcher never acquired its lock")

            second_env = base_env.copy()
            second_env["EVAL_RESULTS_DIR"] = str(root / "different-results")
            second = subprocess.run(
                [str(script_path), "--live"],
                cwd=project,
                env=second_env,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            stdout, stderr = first.communicate(timeout=5)
            self.assertEqual(first.returncode, 0, stderr)
            self.assertEqual(second.returncode, 2, second.stdout)
            self.assertIn("holds the account launch lock", second.stderr)


if __name__ == "__main__":
    unittest.main()
