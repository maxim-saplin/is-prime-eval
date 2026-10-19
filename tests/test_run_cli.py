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
from run import _select_specs, build_parser, main, parse_depths
from runner import RunConfig, run_new


class FakeCatalogClient(OpenRouterClient):
    completion_calls = 0

    def __init__(self, *args, **kwargs):
        self.requested = []

    def resolve_model(self, requested_id):
        self.requested.append(requested_id)
        return ModelInfo(
            requested_id=requested_id,
            model_id="openai/gpt-6-luna",
            name="GPT-6 Luna",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="test catalog",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )

    def complete(self, *args, **kwargs):
        type(self).completion_calls += 1
        raise AssertionError("dry-run must not make a completion request")


class ReplayClient(OpenRouterClient):
    def __init__(self, *args, interrupt_first=False, fail_if_called=False, **kwargs):
        self.calls = 0
        self.interrupt_first = interrupt_first
        self.fail_if_called = fail_if_called

    def complete(self, model_id, prompt, *, reasoning_effort=None, max_completion_tokens=512):
        if self.fail_if_called:
            raise AssertionError("completed-run resume must not dispatch inference")
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
    def test_repeatable_model_qualifiers_select_effort_and_alias(self):
        args = build_parser().parse_args(
            [
                "--model-qualifier",
                "gpt-6-luna-low",
                "--model-qualifier",
                "openai/gpt-6-luna:medium",
                "--parallelism",
                "2",
            ]
        )
        specs = _select_specs(args)
        self.assertEqual(
            [(s.requested_model, s.display_model, s.reasoning_effort) for s in specs],
            [
                ("gpt-6-luna", "gpt-6-luna-low", "low"),
                ("openai/gpt-6-luna", "gpt-6-luna-medium", "medium"),
            ],
        )
        self.assertEqual(args.parallelism, 2)

    def test_explicit_alias_and_global_effort_for_qualifiers(self):
        args = build_parser().parse_args(
            ["--model-qualifier", "baseline=openai/gpt-6-luna", "--reasoning-effort", "medium"]
        )
        specs = _select_specs(args)
        self.assertEqual(specs[0].display_model, "baseline")
        self.assertEqual(specs[0].reasoning_effort, "medium")

    def test_single_model_cli_remains_compatible(self):
        args = build_parser().parse_args(
            ["--model", "gpt-6-luna", "--model-alias", "luna-low", "--reasoning-effort", "low"]
        )
        specs = _select_specs(args)
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].requested_model, "gpt-6-luna")
        self.assertEqual(specs[0].display_model, "luna-low")

    def test_model_from_environment_can_be_overridden_with_alias(self):
        args = build_parser().parse_args(["--model-alias", "baseline-low"])
        with patch.dict("os.environ", {"MODEL": "gpt-6-luna", "REASONING_EFFORT": "low"}):
            specs = _select_specs(args)
        self.assertEqual(specs[0].requested_model, "gpt-6-luna")
        self.assertEqual(specs[0].display_model, "baseline-low")

    def test_multi_model_dry_run_resolves_all_without_inference(self):
        FakeCatalogClient.completion_calls = 0
        output = io.StringIO()
        with (
            patch("run.OpenRouterClient", FakeCatalogClient),
            patch("run.load_dotenv"),
            patch("run.get_openrouter_key", return_value="test-key"),
            redirect_stdout(output),
        ):
            result = main(
                [
                    "--model-qualifier", "gpt-6-luna-low",
                    "--model-qualifier", "gpt-6-luna:medium",
                    "--dry-run",
                ]
            )
        text = output.getvalue()
        self.assertEqual(result, 0)
        self.assertEqual(text.count("Total cases / inference requests: 140"), 2)
        self.assertIn("Display name: gpt-6-luna-low", text)
        self.assertIn("Display name: gpt-6-luna-medium", text)
        self.assertEqual(FakeCatalogClient.completion_calls, 0)

    def test_completed_run_cli_resume_is_a_no_op_with_summary(self):
        model_info = ModelInfo(
            requested_id="gpt-6-luna",
            model_id="openai/gpt-6-luna",
            name="GPT-6 Luna",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="test",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        config = RunConfig(
            requested_model="gpt-6-luna",
            display_model="gpt-6-luna-low",
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
                client=ReplayClient(),
                config=config,
                model_info=model_info,
                results_dir=Path(temp_dir) / "results",
            )
            ledger = Path(original["ledger_path"])
            before = ledger.read_bytes()
            output = io.StringIO()
            errors = io.StringIO()
            with (
                patch("run.OpenRouterClient", lambda *args, **kwargs: ReplayClient(fail_if_called=True)),
                patch("run.load_dotenv"),
                patch("run.get_openrouter_key", return_value="test-key"),
                redirect_stdout(output),
                redirect_stderr(errors),
            ):
                code = main(["--resume", str(ledger)])
            self.assertEqual(code, 0)
            self.assertIn("Correct: 2/2", output.getvalue())
            self.assertEqual(ledger.read_bytes(), before)

    def test_cli_resume_repairs_torn_tail_before_reading_progress(self):
        model_info = ModelInfo(
            requested_id="gpt-6-luna",
            model_id="openai/gpt-6-luna",
            name="GPT-6 Luna",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="test",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        config = RunConfig(
            requested_model="gpt-6-luna",
            display_model="gpt-6-luna-low",
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
                    client=ReplayClient(interrupt_first=True),
                    config=config,
                    model_info=model_info,
                    results_dir=Path(temp_dir) / "results",
                )
            ledger = Path(caught.exception.ledger_path)
            torn = b'{"event_type":"partial'
            with ledger.open("ab") as stream:
                stream.write(torn)
            output = io.StringIO()
            errors = io.StringIO()
            with (
                patch("run.OpenRouterClient", ReplayClient),
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
