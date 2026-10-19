import io
import json
import unittest
from decimal import Decimal
from urllib.error import HTTPError

from openrouter import ModelInfo, OpenRouterClient, OpenRouterError


class FakeHTTPResponse:
    def __init__(self, body, status=200):
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class OpenRouterClientTests(unittest.TestCase):
    def test_resolves_short_model_and_converts_catalog_rates(self):
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeHTTPResponse(
                {
                    "data": [
                        {
                            "id": "openai/gpt-6-luna",
                            "name": "OpenAI: GPT-6 Luna",
                            "pricing": {"prompt": "0.0000001", "completion": "0.0000005"},
                            "supported_parameters": ["reasoning_effort"],
                        },
                        {
                            "id": "openai/gpt-6-luna:batch",
                            "name": "OpenAI: GPT-6 Luna Batch",
                            "pricing": {"prompt": "0.00000005", "completion": "0.00000025"},
                            "supported_parameters": ["reasoning_effort"],
                        },
                    ]
                }
            )

        client = OpenRouterClient("test-secret", opener=opener)
        model = client.resolve_model("gpt-6-luna")
        self.assertEqual(model.model_id, "openai/gpt-6-luna")
        self.assertEqual(model.requested_id, "gpt-6-luna")
        self.assertEqual(model.prompt_rate_usd_per_million, Decimal("0.1000000"))
        self.assertEqual(model.completion_rate_usd_per_million, Decimal("0.5000000"))
        self.assertIn("Bearer test-secret", calls[0][0].get_header("Authorization"))
        OpenRouterClient.validate_reasoning_effort(model, "low")

    def test_short_name_ambiguity_requires_full_catalog_id(self):
        def opener(request, timeout):
            return FakeHTTPResponse(
                {
                    "data": [
                        {"id": "a/model", "pricing": {"prompt": "0", "completion": "0"}},
                        {"id": "b/model", "pricing": {"prompt": "0", "completion": "0"}},
                    ]
                }
            )

        client = OpenRouterClient("test-secret", opener=opener)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            client.resolve_model("model")

    def test_completion_payload_uses_low_effort_and_never_prints_key(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["body"] = json.loads(request.data)
            return FakeHTTPResponse(
                {"id": "gen-1", "model": "openai/gpt-6-luna", "choices": [{"message": {"content": "PRIME"}}]}
            )

        client = OpenRouterClient("do-not-log-this", opener=opener)
        result = client.complete(
            "openai/gpt-6-luna",
            "Is 101 prime? Reply with only PRIME or COMPOSITE.",
            reasoning_effort="low",
            max_completion_tokens=128,
        )
        self.assertEqual(captured["body"]["reasoning_effort"], "low")
        self.assertEqual(captured["body"]["max_completion_tokens"], 128)
        self.assertEqual(captured["body"]["messages"][0]["role"], "user")
        self.assertEqual(result["choices"][0]["message"]["content"], "PRIME")
        self.assertNotIn("do-not-log-this", repr(result))

    def test_http_failure_is_sanitized_and_retryable(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 503, "unavailable", {}, None)

        client = OpenRouterClient("test-secret", opener=opener)
        with self.assertRaises(OpenRouterError) as caught:
            client.complete("openai/gpt-6-luna", "test")
        self.assertEqual(caught.exception.status_code, 503)
        self.assertTrue(caught.exception.retryable)
        self.assertTrue(caught.exception.may_have_been_billed)
        self.assertNotIn("test-secret", str(caught.exception))

    def test_generation_details_uses_encoded_identifier(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            return FakeHTTPResponse({"data": {"total_cost": "0.01"}})

        client = OpenRouterClient("test-secret", opener=opener)
        data = client.generation_details("gen /+ id")
        self.assertIn("id=gen+%2F%2B+id", captured["url"])
        self.assertEqual(data["data"]["total_cost"], "0.01")

    def test_http_error_preserves_structured_usage_without_key(self):
        payload = {"id": "gen-error", "usage": {"prompt_tokens": 4, "cost": 0.01}, "error": {"code": 503}}

        def opener(request, timeout):
            raise HTTPError(
                request.full_url,
                503,
                "unavailable",
                {"Content-Type": "application/json"},
                io.BytesIO(json.dumps(payload).encode()),
            )

        client = OpenRouterClient("test-secret", opener=opener)
        with self.assertRaises(OpenRouterError) as caught:
            client.complete("openai/gpt-6-luna", "test")
        self.assertEqual(caught.exception.response_payload, payload)
        self.assertNotIn("test-secret", repr(caught.exception.response_payload))

    def test_http_200_without_choices_is_returned_for_invalid_scoring(self):
        def opener(request, timeout):
            return FakeHTTPResponse({"id": "gen-empty", "usage": {"prompt_tokens": 4}})

        client = OpenRouterClient("test-secret", opener=opener)
        response = client.complete("openai/gpt-6-luna", "test")
        self.assertEqual(response["id"], "gen-empty")
        self.assertNotIn("choices", response)

    def test_http_200_structured_error_is_preserved_and_classified(self):
        payload = {
            "id": "gen-structured-error",
            "error": {"code": 429, "message": "provider busy"},
            "usage": {"prompt_tokens": 9, "cost": 0.0002},
        }

        def opener(request, timeout):
            return FakeHTTPResponse(payload)

        client = OpenRouterClient("test-secret", opener=opener)
        with self.assertRaises(OpenRouterError) as caught:
            client.complete("openai/gpt-6-luna", "test")
        self.assertTrue(caught.exception.retryable)
        self.assertEqual(caught.exception.response_payload, payload)
        self.assertNotIn("test-secret", repr(caught.exception.response_payload))


if __name__ == "__main__":
    unittest.main()
