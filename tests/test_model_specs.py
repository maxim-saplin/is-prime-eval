from dataclasses import FrozenInstanceError
import unittest

from model_specs import ModelSpec, parse_model_specs


class ParseModelSpecsTests(unittest.TestCase):
    def test_pairs_separate_ids_and_efforts_in_order(self):
        self.assertEqual(
            parse_model_specs(
                ["openai/gpt-6-luna", "anthropic/claude-sonnet"],
                ["low", "medium"],
            ),
            [
                ModelSpec("openai/gpt-6-luna", "low"),
                ModelSpec("anthropic/claude-sonnet", "medium"),
            ],
        )

    def test_accepts_high_or_other_nonempty_provider_values_without_assuming_level_set(self):
        self.assertEqual(
            parse_model_specs(["openai/gpt-6-luna"], ["high"]),
            [ModelSpec("openai/gpt-6-luna", "high")],
        )
        self.assertEqual(
            parse_model_specs(["openai/gpt-6-luna"], ["xhigh"])[0].reasoning_effort,
            "xhigh",
        )

    def test_no_effort_is_inferred_or_defaulted(self):
        with self.assertRaisesRegex(ValueError, "one --reasoning-effort"):
            parse_model_specs(["openai/gpt-6-luna"], None)
        with self.assertRaisesRegex(ValueError, "explicit and non-empty"):
            parse_model_specs(["openai/gpt-6-luna"], [""])
        with self.assertRaisesRegex(ValueError, "explicit and non-empty"):
            parse_model_specs(["openai/gpt-6-luna"], [None])

    def test_requires_fully_qualified_ids(self):
        for model_id in ("", "gpt-6-luna", "/model", "provider/", "provider//model", " model/id"):
            with self.subTest(model_id=model_id):
                with self.assertRaises(ValueError):
                    parse_model_specs([model_id], ["low"])

    def test_rejects_repeated_identical_model_effort_pair(self):
        with self.assertRaisesRegex(ValueError, "duplicate model_id/reasoning_effort"):
            parse_model_specs(
                ["openai/gpt-6-luna", "openai/gpt-6-luna"], ["low", "low"]
            )

    def test_same_model_with_distinct_efforts_is_valid(self):
        self.assertEqual(
            parse_model_specs(
                ["openai/gpt-6-luna", "openai/gpt-6-luna"], ["low", "medium"]
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

    def test_rejects_duplicate_counts_whitespace_and_string_as_sequence(self):
        with self.assertRaisesRegex(ValueError, "one --reasoning-effort"):
            parse_model_specs(["openai/gpt-6-luna", "openai/gpt-6-luna"], ["low"])
        with self.assertRaisesRegex(ValueError, "whitespace"):
            parse_model_specs(["openai/gpt-6-luna"], ["low effort"])
        with self.assertRaises(TypeError):
            parse_model_specs("openai/gpt-6-luna", ["low"])


if __name__ == "__main__":
    unittest.main()
