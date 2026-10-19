from dataclasses import FrozenInstanceError
import unittest

from model_specs import (
    ModelSpec,
    parse_model_qualifier,
    parse_model_qualifiers,
)


class ParseModelQualifierTests(unittest.TestCase):
    def test_short_hyphen_effort_suffix(self):
        self.assertEqual(
            parse_model_qualifier("gpt-6-luna-low"),
            ModelSpec(
                requested_model="gpt-6-luna",
                display_model="gpt-6-luna-low",
                reasoning_effort="low",
            ),
        )

    def test_provider_qualified_colon_suffix(self):
        self.assertEqual(
            parse_model_qualifier("openai/gpt-6-luna:medium"),
            ModelSpec(
                requested_model="openai/gpt-6-luna",
                display_model="gpt-6-luna-medium",
                reasoning_effort="medium",
            ),
        )

    def test_alias_overrides_derived_display_name(self):
        self.assertEqual(
            parse_model_qualifier("baseline=openai/gpt-6-luna:medium"),
            ModelSpec(
                requested_model="openai/gpt-6-luna",
                display_model="baseline",
                reasoning_effort="medium",
            ),
        )

    def test_alias_without_explicit_effort_uses_default(self):
        self.assertEqual(
            parse_model_qualifier("reference=model-x", default_effort="HIGH"),
            ModelSpec("model-x", "reference", "high"),
        )

    def test_default_effort_and_no_effort(self):
        self.assertEqual(
            parse_model_qualifier("vendor/model-x"),
            ModelSpec("vendor/model-x", "model-x-low", "low"),
        )
        self.assertEqual(
            parse_model_qualifier("vendor/model-x", default_effort=None),
            ModelSpec("vendor/model-x", "model-x", None),
        )

    def test_explicit_effort_overrides_default_effort(self):
        self.assertEqual(
            parse_model_qualifier("model-x:high", default_effort="low"),
            ModelSpec("model-x", "model-x-high", "high"),
        )

    def test_model_spec_is_frozen(self):
        spec = parse_model_qualifier("model-x-low")
        with self.assertRaises(FrozenInstanceError):
            spec.display_model = "changed"

    def test_rejects_empty_or_malformed_qualifiers(self):
        invalid = (
            "",
            "   ",
            "=model-x",
            "alias=",
            "alias==model-x",
            "bad alias=model-x",
            "model with spaces",
            "model-x:",
            "model-x:fast",
            "model-x:low:medium",
            "model-x-low:medium",
            "model-x-low-high",
        )
        for text in invalid:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_model_qualifier(text)

    def test_rejects_invalid_default_effort(self):
        for effort in ("", "none", "fast", 3):
            with self.subTest(effort=effort):
                with self.assertRaises((TypeError, ValueError)):
                    parse_model_qualifier("model-x", default_effort=effort)


class ParseModelQualifiersTests(unittest.TestCase):
    def test_preserves_order_and_allows_replicates_with_distinct_aliases(self):
        specs = parse_model_qualifiers(
            ["baseline=model-x-low", "replicate=model-x:low", "other=model-y-medium"]
        )
        self.assertEqual(
            [spec.display_model for spec in specs],
            ["baseline", "replicate", "other"],
        )
        self.assertEqual(specs[0].requested_model, specs[1].requested_model)
        self.assertEqual(specs[0].reasoning_effort, specs[1].reasoning_effort)

    def test_rejects_duplicate_implicit_display_names(self):
        with self.assertRaisesRegex(ValueError, "duplicate model display name"):
            parse_model_qualifiers(["model-x-low", "model-x:low"])

    def test_rejects_duplicate_aliases(self):
        with self.assertRaisesRegex(ValueError, "duplicate model display name"):
            parse_model_qualifiers(["baseline=model-x-low", "baseline=model-y-medium"])

    def test_duplicate_detection_is_case_insensitive(self):
        with self.assertRaisesRegex(ValueError, "duplicate model display name"):
            parse_model_qualifiers(["Baseline=model-x-low", "baseline=model-y-low"])

    def test_alias_must_be_unique_against_an_implicit_display_name(self):
        with self.assertRaisesRegex(ValueError, "duplicate model display name"):
            parse_model_qualifiers(["model-x-low", "model-x-low=model-y"])

    def test_allows_empty_sequence_but_not_string_as_sequence(self):
        self.assertEqual(parse_model_qualifiers([]), [])
        with self.assertRaises(TypeError):
            parse_model_qualifiers("model-x-low")

    def test_rejects_non_iterable_and_invalid_entries(self):
        with self.assertRaises(TypeError):
            parse_model_qualifiers(3)
        with self.assertRaises(TypeError):
            parse_model_qualifiers(["model-x-low", None])


if __name__ == "__main__":
    unittest.main()
