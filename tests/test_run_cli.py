from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cases import is_prime
from openrouter import ModelInfo, OpenRouterClient
from run import build_parser, main, parse_depths
from runner import RunConfig, run_new


class FakeCatalogClient(OpenRouterClient):
    completion_calls = 0
    resolved_ids = []

    def __init__(self, *args, interrupt_first=False, fail_if_called=False, **kwargs):
        self.calls = 0
        self.interrupt_first = interrupt_first
        self.fail_if_called = fail_if_called

    def resolve_model(self, model_id):
        type(self).resolved_ids.append(model_id)
        return ModelInfo(
            requested_id=model_id,
            model_id=model_id,
            name="Catalog model name",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="test catalog",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens=512):
        if self.fail_if_called:
            raise AssertionError("completed-run resume must not dispatch inference")
        type(self).completion_calls += 1
        self.calls += 1
        if self.interrupt_first and self.calls == 1:
            raise KeyboardInterrupt()
        number = int(prompt.split()[1])
        answer = "PRIME" if is_prime(number) else "COMPOSITE"
        return {
            "id": f"gen-replay-{self.calls}",
            "model": model_id,
            "provider": "OpenAI",
            "choices": [{"finish_reason": "stop", "message": {"content": answer}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "cost": "0.00001"},
        }


class RunCliTests(unittest.TestCase):
    def test_single_run_requires_explicit_separate_model_id_and_effort(self):
        args = build_parser().parse_args(
            ["--model-id", "openai/gpt-6-luna", "--reasoning-effort", "high"]
        )
        self.assertEqual(args.model_id, ["openai/gpt-6-luna"])
        self.assertEqual(args.reasoning_effort, ["high"])

    def test_old_alias_and_qualifier_syntax_is_rejected(self):
        for argv in (
            ["--model-qualifier", "gpt-6-luna-low"],
            ["--model", "openai/gpt-6-luna"],
            ["--model-id", "openai/gpt-6-luna", "--model-alias", "luna-low"],
        ):
            with self.subTest(argv=argv), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    build_parser().parse_args(argv)
            self.assertEqual(caught.exception.code, 2)

    def test_missing_effort_fails_before_catalog_or_inference(self):
        FakeCatalogClient.resolved_ids = []
        with (
            patch("run.OpenRouterClient", FakeCatalogClient),
            patch("run.load_dotenv"),
            patch("run.get_openrouter_key", return_value="test-key"),
            redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(SystemExit) as caught:
                main(["--model-id", "openai/gpt-6-luna"])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(FakeCatalogClient.resolved_ids, [])

    def test_parallel_cli_pairs_repeated_model_ids_and_efforts_by_order(self):
        FakeCatalogClient.completion_calls = 0
        FakeCatalogClient.resolved_ids = []
        output = io.StringIO()
        with (
            patch("run.OpenRouterClient", FakeCatalogClient),
            patch("run.load_dotenv"),
            patch("run.get_openrouter_key", return_value="test-key"),
            redirect_stdout(output),
        ):
            result = main(
                [
                    "--model-id", "openai/gpt-6-luna", "--reasoning-effort", "low",
                    "--model-id", "openai/gpt-6-luna", "--reasoning-effort", "high",
                    "--parallelism", "2", "--dry-run",
                ]
            )
        text = output.getvalue()
        self.assertEqual(result, 0)
        self.assertEqual(FakeCatalogClient.resolved_ids, ["openai/gpt-6-luna", "openai/gpt-6-luna"])
        self.assertEqual(FakeCatalogClient.completion_calls, 0)
        self.assertEqual(text.count("Model ID: openai/gpt-6-luna"), 2)
        self.assertIn("Reasoning effort: low", text)
        self.assertIn("Reasoning effort: high", text)
        hashes = [line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("Dataset SHA-256:")]
        self.assertEqual(len(hashes), 2)
        self.assertEqual(hashes[0], hashes[1])

    def test_effort_list_must_pair_with_model_ids_and_duplicates_fail(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["--model-id", "openai/gpt-6-luna", "--model-id", "openai/gpt-6-luna", "--reasoning-effort", "low"])
        # Same identity repeated in one batch is rejected before catalog requests.
        FakeCatalogClient.resolved_ids = []
        with (
            patch("run.OpenRouterClient", FakeCatalogClient),
            patch("run.load_dotenv"),
            patch("run.get_openrouter_key", return_value="test-key"),
            redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(SystemExit):
                main(
                    [
                        "--model-id", "openai/gpt-6-luna", "--reasoning-effort", "low",
                        "--model-id", "openai/gpt-6-luna", "--reasoning-effort", "low",
                    ]
                )
        self.assertEqual(FakeCatalogClient.resolved_ids, [])

    def test_completed_run_cli_resume_is_a_no_op_with_summary(self):
        model_info = ModelInfo(
            requested_id="openai/gpt-6-luna",
            model_id="openai/gpt-6-luna",
            name="OpenAI: GPT-6 Luna",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="test",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        config = RunConfig(
            model_id="openai/gpt-6-luna",
            reasoning_effort="low",
            depths=(4,),
            samples_per_class=1,
            seed=2026,
            max_attempts=1,
            retry_delay_seconds=0,
            timeout_seconds=2,
            max_completion_tokens=64,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            original = run_new(
                client=FakeCatalogClient(),
                config=config,
                model_info=model_info,
                results_dir=Path(temp_dir) / "results",
            )
            ledger = Path(original["ledger_path"])
            before = ledger.read_bytes()
            output = io.StringIO()
            errors = io.StringIO()
            with (
                patch("run.OpenRouterClient", lambda *args, **kwargs: FakeCatalogClient(fail_if_called=True)),
                patch("run.load_dotenv"),
                patch("run.get_openrouter_key", return_value="test-key"),
                redirect_stdout(output),
                redirect_stderr(errors),
            ):
                code = main(["--resume", str(ledger)])
            self.assertEqual(code, 0)
            self.assertIn("Model ID: openai/gpt-6-luna", output.getvalue())
            self.assertIn("Reasoning effort: low", output.getvalue())
            self.assertIn("Correct: 2/2", output.getvalue())
            self.assertEqual(ledger.read_bytes(), before)

    def test_cli_resume_repairs_torn_tail_before_reading_progress(self):
        model_info = ModelInfo(
            requested_id="openai/gpt-6-luna",
            model_id="openai/gpt-6-luna",
            name="OpenAI: GPT-6 Luna",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="test",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        config = RunConfig(
            model_id="openai/gpt-6-luna",
            reasoning_effort="low",
            depths=(4,),
            samples_per_class=1,
            seed=2026,
            max_attempts=2,
            retry_delay_seconds=0,
            timeout_seconds=2,
            max_completion_tokens=64,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(KeyboardInterrupt) as caught:
                run_new(
                    client=FakeCatalogClient(interrupt_first=True),
                    config=config,
                    model_info=model_info,
                    results_dir=Path(temp_dir) / "results",
                )
            ledger = Path(caught.exception.ledger_path)
            with ledger.open("ab") as stream:
                stream.write(b'{"event_type":"partial')
            output = io.StringIO()
            errors = io.StringIO()
            with (
                patch("run.OpenRouterClient", FakeCatalogClient),
                patch("run.load_dotenv"),
                patch("run.get_openrouter_key", return_value="test-key"),
                redirect_stdout(output),
                redirect_stderr(errors),
            ):
                code = main(["--resume", str(ledger)])
            self.assertEqual(code, 0)
            self.assertIn("Run complete", output.getvalue())
            self.assertTrue(Path(f"{ledger}.torn").exists())
            events = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertTrue(any(event["event_type"] == "ledger_recovered" for event in events))
            self.assertEqual(sum(event["event_type"] == "attempt_started" for event in events), 3)

    def test_depth_range_parser_is_inclusive(self):
        self.assertEqual(parse_depths("4-10"), tuple(range(4, 11)))
        self.assertEqual(parse_depths("4,6,8"), (4, 6, 8))


if __name__ == "__main__":
    unittest.main()
