import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from is_prime_eval.settings import get_openrouter_key, load_dotenv


class DotenvTests(unittest.TestCase):
    def test_loads_or_key_without_logging_or_overwriting_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / ".env"
            path.write_text("OR_KEY='file-secret'\nMODEL=gpt-6-luna\n", encoding="utf-8")
            with patch.dict(os.environ, {"OR_KEY": "shell-secret"}, clear=True):
                self.assertTrue(load_dotenv(path))
                self.assertEqual(get_openrouter_key(), "shell-secret")
                self.assertEqual(os.environ["MODEL"], "gpt-6-luna")

    def test_loads_quoted_values_and_ignores_invalid_lines(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / ".env"
            path.write_text("export OR_KEY=\"secret value\" # comment\nnot-an-assignment\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                load_dotenv(path)
                self.assertEqual(get_openrouter_key(), "secret value")

    def test_missing_file_is_a_noop(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                self.assertFalse(load_dotenv(Path(temp_dir) / "missing.env"))
                self.assertIsNone(get_openrouter_key())


if __name__ == "__main__":
    unittest.main()
