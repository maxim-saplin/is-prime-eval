from pathlib import Path
import subprocess
import sys
import unittest


class RunSignalHandlerTests(unittest.TestCase):
    def test_cli_overrides_inherited_ignored_sigint_and_handles_sigterm(self):
        script = """
import os
import signal
signal.signal(signal.SIGINT, signal.SIG_IGN)
import is_prime_eval.cli as run
run._install_cli_signal_handlers()
for sig in (signal.SIGINT, signal.SIGTERM):
    try:
        os.kill(os.getpid(), sig)
    except KeyboardInterrupt:
        print(signal.Signals(sig).name)
"""
        project_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.splitlines(), ["SIGINT", "SIGTERM"])


if __name__ == "__main__":
    unittest.main()
