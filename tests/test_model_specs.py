from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import tempfile
import unittest

from model_specs import ModelSpec, load_model_specs


class LoadModelSpecsTests(unittest.TestCase):
    def _load_document(self, document):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "models.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            return load_model_specs(path)

    def test_loads_explicit_specs_in_order(self):
        specs = self._load_document(
            [
                {"model_id": "openai/gpt-6-luna", "reasoning_effort": "low"},
                {"model_id": "openai/gpt-6-luna", "reasoning_effort": "medium"},
                {"model_id": "anthropic/claude-sonnet", "reasoning_effort": "low"},
            ]
        )
        self.assertEqual(
            specs,
            [
                ModelSpec("openai/gpt-6-luna", "low"),
                ModelSpec("openai/gpt-6-luna", "medium"),
                ModelSpec("anthropic/claude-sonnet", "low"),
            ],
        )

    def test_rejects_duplicate_model_and_effort_identity(self):
        duplicate = {"model_id": "openai/gpt-6-luna", "reasoning_effort": "low"}
        with self.assertRaisesRegex(ValueError, "duplicate model run identity"):
            self._load_document([duplicate, duplicate])

    def test_same_model_with_distinct_efforts_is_valid(self):
        self.assertEqual(
            self._load_document(
                [
                    {"model_id": "openai/gpt-6-luna", "reasoning_effort": "low"},
                    {"model_id": "openai/gpt-6-luna", "reasoning_effort": "medium"},
                ]
            ),
            [
                ModelSpec("openai/gpt-6-luna", "low"),
                ModelSpec("openai/gpt-6-luna", "medium"),
            ],
        )

    def test_model_spec_is_frozen(self):
        spec = ModelSpec("openai/gpt-6-luna", "low")
        with self.assertRaises(FrozenInstanceError):
            spec.model_id = "other/model"

    def test_requires_a_nonempty_json_array(self):
        for document in ({"model_id": "openai/model", "reasoning_effort": "low"}, "[]", None, 3):
            with self.subTest(document=document):
                with self.assertRaisesRegex(ValueError, "JSON array"):
                    self._load_document(document)
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            self._load_document([])

    def test_requires_exact_object_keys(self):
        invalid = (
            {"model_id": "openai/model"},
            {"reasoning_effort": "low"},
            {
                "model_id": "openai/model",
                "reasoning_effort": "low",
                "alias": "baseline",
            },
        )
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, "invalid fields"):
                    self._load_document([row])

    def test_requires_fully_qualified_nonempty_model_id(self):
        for model_id in ("", "model", "/model", "openai/", "openai//model", " openai/model", "openai/model ", "openai/model name"):
            with self.subTest(model_id=model_id):
                with self.assertRaisesRegex(ValueError, "fully qualified|whitespace|non-empty"):
                    self._load_document(
                        [{"model_id": model_id, "reasoning_effort": "low"}]
                    )

    def test_requires_explicit_low_or_medium_effort(self):
        for effort in (None, "", "LOW", "high", 1):
            with self.subTest(effort=effort):
                with self.assertRaisesRegex(ValueError, "exactly 'low' or 'medium'"):
                    self._load_document(
                        [{"model_id": "openai/model", "reasoning_effort": effort}]
                    )

    def test_rejects_non_object_array_elements(self):
        with self.assertRaisesRegex(ValueError, r"model_specs\[0\] must be an object"):
            self._load_document(["openai/model:low"])

    def test_reports_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "models.json"
            path.write_text('[{"model_id":', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid model specs JSON"):
                load_model_specs(path)


if __name__ == "__main__":
    unittest.main()
