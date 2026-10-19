import unittest
from decimal import Decimal

from costs import (
    estimate_uncached_cost_usd,
    extract_provider_cost_usd,
    extract_usage,
)


class CostAccountingTests(unittest.TestCase):
    def test_uncached_estimate_prices_all_prompt_tokens_even_if_cached(self):
        usage = {
            "prompt_tokens": 1_000_000,
            "completion_tokens": 100,
            "cached_prompt_tokens": 900_000,
            "reasoning_tokens": 20,
        }
        estimate = estimate_uncached_cost_usd(usage, "0.1", "0.5")
        self.assertEqual(estimate, Decimal("0.10005"))

    def test_missing_tokens_or_rates_produce_unknown_not_zero(self):
        self.assertIsNone(
            estimate_uncached_cost_usd(
                {"prompt_tokens": 10, "completion_tokens": None}, "0.1", "0.5"
            )
        )
        self.assertIsNone(
            estimate_uncached_cost_usd(
                {"prompt_tokens": 10, "completion_tokens": 1}, None, "0.5"
            )
        )

    def test_explicit_free_provider_cost_is_zero_not_missing(self):
        self.assertEqual(
            extract_provider_cost_usd({"usage": {"cost": 0}}), Decimal("0")
        )
        self.assertIsNone(extract_provider_cost_usd({"usage": {}}))

    def test_usage_includes_cache_and_reasoning_details_without_recounting(self):
        response = {
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 12,
                "prompt_tokens_details": {"cached_tokens": 8},
                "completion_tokens_details": {"reasoning_tokens": 9},
            }
        }
        usage = extract_usage(response)
        self.assertEqual(usage["prompt_tokens"], 20)
        self.assertEqual(usage["completion_tokens"], 12)
        self.assertEqual(usage["cached_prompt_tokens"], 8)
        self.assertEqual(usage["reasoning_tokens"], 9)
        self.assertEqual(
            estimate_uncached_cost_usd(usage, "1", "2"), Decimal("0.000044")
        )

    def test_generation_metadata_fills_missing_usage_and_cost(self):
        generation = {
            "data": {
                "tokens_prompt": 15,
                "tokens_completion": 7,
                "native_tokens_prompt": 16,
                "native_tokens_completion": 9,
                "native_tokens_cached": 3,
                "native_tokens_reasoning": 4,
                "total_cost": "0.0000123",
            }
        }
        usage = extract_usage({}, generation)
        self.assertEqual(usage["prompt_tokens"], 15)
        self.assertEqual(usage["completion_tokens"], 7)
        self.assertEqual(usage["native_prompt_tokens"], 16)
        self.assertEqual(usage["native_completion_tokens"], 9)
        self.assertEqual(usage["estimate_prompt_tokens"], 16)
        self.assertEqual(usage["estimate_completion_tokens"], 9)
        self.assertEqual(usage["estimate_token_source"], "generation.native_tokens")
        self.assertEqual(usage["cached_prompt_tokens"], 3)
        self.assertEqual(usage["reasoning_tokens"], 4)
        # Native completion count is the total; reasoning_tokens is a subset,
        # so the reasoning count must not be added to the estimate.
        self.assertEqual(
            estimate_uncached_cost_usd(usage, "1", "2"), Decimal("0.000034")
        )
        self.assertEqual(
            extract_provider_cost_usd({}, generation), Decimal("0.0000123")
        )


if __name__ == "__main__":
    unittest.main()
