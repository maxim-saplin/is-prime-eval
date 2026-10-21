import unittest

from parse import parse_response
from prompt import make_prompt


class ResponseParserTests(unittest.TestCase):
    def test_accepts_bare_labels_with_optional_punctuation(self):
        examples = (
            ("PRIME", "PRIME"),
            (" composite ", "COMPOSITE"),
            ("Prime.", "PRIME"),
            ("COMPOSITE!\n", "COMPOSITE"),
            ("\tprime?  ", "PRIME"),
        )
        for raw, expected in examples:
            with self.subTest(raw=raw):
                self.assertEqual(parse_response(raw), expected)

    def test_rejects_ambiguous_or_malformed_output(self):
        invalid_responses = (
            None,
            "",
            "   ",
            "It is PRIME",
            "not prime",
            "PRIME or COMPOSITE",
            "COMPOSITE because it is divisible by 3",
            "**PRIME**",
            "PRIME!!",
            "The answer is COMPOSITE.",
            1,
        )
        for raw in invalid_responses:
            with self.subTest(raw=raw):
                self.assertIsNone(parse_response(raw))


class PromptTests(unittest.TestCase):
    def test_make_prompt_uses_fixed_label_contract(self):
        self.assertEqual(
            make_prompt(1_234_567),
            "Is 1234567 prime? Reply with only PRIME or COMPOSITE.",
        )
        self.assertEqual(
            make_prompt(10_000_000_000),
            "Is 10000000000 prime? Reply with only PRIME or COMPOSITE.",
        )

    def test_make_prompt_rejects_numbers_outside_supported_domain(self):
        for number in (0, -2, 10**15):
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    make_prompt(number)

    def test_make_prompt_rejects_non_integer_numbers(self):
        for number in (True, "123"):
            with self.subTest(number=number):
                with self.assertRaises(TypeError):
                    make_prompt(number)


if __name__ == "__main__":
    unittest.main()
