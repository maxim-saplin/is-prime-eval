import json
from decimal import Decimal
import tempfile
import unittest
from pathlib import Path

from cases import is_prime
from enrich_generations import enrich_ledger
from openrouter import ModelInfo
from report import summarize_run
from runner import RunConfig, run_new


class DirectCompletionClient:
    def __init__(self):
        self.calls = 0

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        self.calls += 1
        number = int(prompt.split()[1])
        answer = "PRIME" if is_prime(number) else "COMPOSITE"
        return {
            "id": f"gen-smoke-{self.calls}",
            "model": model_id,
            "provider": "OpenAI",
            "choices": [{"finish_reason": "stop", "native_finish_reason": "completed", "message": {"content": answer}}],
            "usage": {
                "prompt_tokens": 21,
                "completion_tokens": 36,
                "completion_tokens_details": {"reasoning_tokens": 27},
                "cost": "0.0000201",
            },
        }


class GenerationMetadataClient:
    def __init__(self):
        self.calls = []

    def generation_details(self, generation_id):
        self.calls.append(generation_id)
        return {
            "data": {
                "id": generation_id,
                "model": "openai/gpt-6-luna-20260922",
                "provider_name": "OpenAI",
                "tokens_prompt": 13,
                "tokens_completion": 97,
                "native_tokens_prompt": 21,
                "native_tokens_completion": 36,
                "native_tokens_reasoning": 27,
                "native_tokens_cached": 0,
                "usage": 0.0000201,
                "total_cost": 0.0000201,
            }
        }


class GenerationEnrichmentTests(unittest.TestCase):
    def test_delayed_details_update_tokens_route_and_cost_once_without_inference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model = ModelInfo(
                requested_id="gpt-6-luna",
                model_id="openai/gpt-6-luna",
                name="OpenAI: GPT-6 Luna",
                prompt_rate_usd_per_million=Decimal("0.1"),
                completion_rate_usd_per_million=Decimal("0.5"),
                pricing_source="fixture",
                pricing_retrieved_at="2026-10-19T00:00:00Z",
                supported_parameters=("reasoning_effort",),
            )
            config = RunConfig(
                requested_model="gpt-6-luna",
                display_model="gpt-6-luna-low",
                reasoning_effort="low",
                depths=(4,),
                samples_per_class=1,
                seed=77,
                max_attempts=1,
                retry_delay_seconds=0,
                timeout_seconds=2,
                max_completion_tokens=512,
            )
            inference = DirectCompletionClient()
            result = run_new(
                client=inference,
                config=config,
                model_info=model,
                results_dir=Path(temp_dir) / "results",
            )
            self.assertEqual(inference.calls, 2)
            before = summarize_run(result["ledger_path"])
            self.assertEqual(before["provider_cost_total"], Decimal("0.0000402"))

            metadata = GenerationMetadataClient()
            first = enrich_ledger(result["ledger_path"], metadata)
            self.assertEqual(first, {"enriched": 2, "failed": 0, "skipped": 0})
            after = summarize_run(result["ledger_path"])
            self.assertEqual(after["normalized_cost_total"], Decimal("0.0000402"))
            self.assertEqual(after["provider_cost_total"], Decimal("0.0000402"))
            self.assertEqual(after["provider_routes"], ["OpenAI"])
            for attempt in after["attempts"].values():
                self.assertEqual(attempt["usage"]["estimate_token_source"], "generation.native_tokens")
                self.assertEqual(attempt["usage"]["native_completion_tokens"], 36)
                self.assertEqual(attempt["usage"]["reasoning_tokens"], 27)
                self.assertEqual(attempt["returned_model"], "openai/gpt-6-luna-20260922")

            second = enrich_ledger(result["ledger_path"], metadata)
            self.assertEqual(second, {"enriched": 0, "failed": 0, "skipped": 2})
            self.assertEqual(len(metadata.calls), 2)
            self.assertEqual(summarize_run(result["ledger_path"])["provider_cost_total"], Decimal("0.0000402"))


if __name__ == "__main__":
    unittest.main()
