import io
import json
from decimal import Decimal
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import runner as runner_module
from cases import is_prime
from openrouter import ModelInfo, OpenRouterError
from progress import ProgressReporter
from scripts.report import render_leaderboard, summarize_run
from runner import RunConfig, _new_ledger_path, resume_run, run_new


class FakeClient:
    def __init__(self, *, content_mode="correct", fail_first=False, finish_reason="stop"):
        self.calls = []
        self.content_mode = content_mode
        self.fail_first = fail_first
        self.finish_reason = finish_reason

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        self.last_model_id = model_id
        self.calls.append(
            {
                "model_id": model_id,
                "prompt": prompt,
                "reasoning_effort": reasoning_effort,
                "max_completion_tokens": max_completion_tokens,
            }
        )
        if self.fail_first and len(self.calls) == 1:
            raise OpenRouterError(
                "temporary upstream failure",
                status_code=503,
                retryable=True,
                may_have_been_billed=True,
            )
        number = int(prompt.split()[1])
        answer = "PRIME" if is_prime(number) else "COMPOSITE"
        if self.content_mode == "invalid":
            answer = f"The answer is {answer}."
        if self.content_mode == "always_prime":
            answer = "PRIME"
        return {
            "id": f"gen-{len(self.calls)}",
            "model": model_id,
            "choices": [
                {
                    "finish_reason": self.finish_reason,
                    "native_finish_reason": self.finish_reason,
                    "message": {"role": "assistant", "content": answer},
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 1,
                "completion_tokens_details": {"reasoning_tokens": 0},
                "cost": "0.00001",
            },
        }

    def generation_details(self, generation_id):
        return {
            "data": {
                "id": generation_id,
                "total_cost": "0.00001",
                "usage": "0.00001",
                "tokens_prompt": 10,
                "tokens_completion": 1,
                "native_tokens_prompt": 11,
                "native_tokens_completion": 2,
                "native_tokens_cached": 0,
                "native_tokens_reasoning": 1,
                "provider_name": "OpenAI",
                "model": getattr(self, "last_model_id", "openai/gpt-6-luna"),
            }
        }


class RetryBurstClient(FakeClient):
    def __init__(self, failures):
        super().__init__()
        self.failures_remaining = failures

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        if self.failures_remaining:
            self.failures_remaining -= 1
            self.calls.append({"model_id": model_id, "prompt": prompt})
            raise OpenRouterError(
                "temporary upstream failure",
                status_code=503,
                retryable=True,
                may_have_been_billed=True,
            )
        return super().complete(
            model_id,
            prompt,
            reasoning_effort=reasoning_effort,
            max_completion_tokens=max_completion_tokens,
        )


class NoChoicesClient(FakeClient):
    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        self.calls.append({"model_id": model_id, "prompt": prompt})
        self.last_model_id = model_id
        return {
            "id": f"gen-no-choices-{len(self.calls)}",
            "model": model_id,
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "cost": "0.00001"},
        }


class ErrorClient(FakeClient):
    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        self.calls.append({"prompt": prompt})
        payload = {
            "id": f"gen-error-{len(self.calls)}",
            "usage": {"prompt_tokens": 5, "completion_tokens": 0, "cost": "0.00003"},
            "error": {"code": 400, "message": "bad request"},
        }
        raise OpenRouterError(
            "OpenRouter returned HTTP 400",
            status_code=400,
            retryable=False,
            may_have_been_billed=False,
            response_payload=payload,
        )


class InterruptOnceClient(FakeClient):
    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        self.calls.append({"prompt": prompt})
        if len(self.calls) == 1:
            raise KeyboardInterrupt()
        number = int(prompt.split()[1])
        answer = "PRIME" if is_prime(number) else "COMPOSITE"
        return {
            "id": f"gen-after-interrupt-{len(self.calls)}",
            "model": model_id,
            "choices": [{"finish_reason": "stop", "message": {"content": answer}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 1,
                "cost": "0.00001",
            },
        }


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.results_dir = Path(self.temp_dir.name) / "results"
        self.model_info = ModelInfo(
            requested_id="openai/gpt-6-luna",
            model_id="openai/gpt-6-luna",
            name="OpenAI: GPT-6 Luna",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="fixture catalog",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        self.config = RunConfig(
            model_id="openai/gpt-6-luna",
            reasoning_effort="low",
            depths=(4,),
            samples_per_class=1,
            seed=77,
            max_attempts=2,
            retry_delay_seconds=0,
            timeout_seconds=2,
            max_completion_tokens=32,
            min_request_interval_seconds=0.0,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_user_model_id_and_effort_are_kept_separate_and_markdown_escaped(self):
        unusual_info = ModelInfo(
            requested_id="provider/model|variant",
            model_id="provider/model|variant",
            name="Fixture model",
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="fixture",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        unusual_config = RunConfig(
            model_id="provider/model|variant",
            reasoning_effort="custom|effort",
            depths=(4,),
            samples_per_class=1,
            seed=77,
            max_attempts=1,
            retry_delay_seconds=0,
            timeout_seconds=2,
            max_completion_tokens=32,
            min_request_interval_seconds=0.0,
        )
        client = FakeClient()
        result = run_new(
            client=client,
            config=unusual_config,
            model_info=unusual_info,
            results_dir=self.results_dir,
        )
        self.assertTrue(result["complete"])
        self.assertEqual(client.calls[0]["reasoning_effort"], "custom|effort")
        summary = summarize_run(result["ledger_path"])
        leaderboard = render_leaderboard([summary])
        self.assertIn("provider/model\\|variant", leaderboard)
        self.assertIn("custom\\|effort", leaderboard)

    def test_success_persists_manifest_results_and_clear_leaderboard(self):
        client = FakeClient()
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        self.assertTrue(result["complete"])
        self.assertEqual(result["scheduled_cases"], 2)
        self.assertEqual(result["summary"]["correct"], 2)
        self.assertEqual(len(client.calls), 2)
        manifest_text = Path(result["manifest_path"]).read_text(encoding="utf-8")
        self.assertNotIn("OR_KEY", manifest_text)
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["counts"]["correct"], 2)
        self.assertEqual(summary["counts"]["incorrect"], 0)
        self.assertEqual(summary["provider_cost_known_attempts"], 2)
        self.assertEqual(summary["normalized_cost_known_attempts"], 2)
        # Generation-native counts (11 prompt, 2 completion) replace API counts
        # (10, 1); the reasoning sub-count is not charged a second time.
        self.assertEqual(summary["normalized_cost_total"], Decimal("0.0000042"))
        self.assertEqual(summary["provider_cost_total"], Decimal("0.00002"))
        self.assertIn("OpenAI", summary["provider_routes"])
        leaderboard = render_leaderboard([summary])
        self.assertIn("openai/gpt-6-luna", leaderboard)
        self.assertIn("| low |", leaderboard)
        self.assertIn("Correct", leaderboard)
        self.assertIn("Primes correctly identified", leaderboard)
        self.assertIn("Provider-reported cost", leaderboard)
        self.assertIn("Estimated cost without cache discounts", leaderboard)

    def test_running_costs_match_report_after_retry_and_completed_resume(self):
        client = FakeClient(fail_first=True)
        with ProgressReporter(stream=io.StringIO()) as reporter:
            result = run_new(
                client=client, config=self.config, model_info=self.model_info,
                results_dir=self.results_dir, on_progress=reporter,
            )
            state = reporter._models[(self.config.model_id, self.config.reasoning_effort)]
            self.assertEqual(len(state.cost_attempts), 3)
            summary = summarize_run(result["ledger_path"])
            self.assertEqual(
                sum(Decimal(row["provider_reported_usd"]) for row in state.cost_attempts.values() if row["provider_reported_usd"] is not None),
                summary["provider_cost_total"],
            )
            self.assertEqual(sum(row["provider_reported_usd"] is not None for row in state.cost_attempts.values()), 2)
            before = len(client.calls)
            with ProgressReporter(stream=io.StringIO()) as resumed:
                resume_run(client=client, ledger_path=result["ledger_path"], on_progress=resumed)
                restored = resumed._models[(self.config.model_id, self.config.reasoning_effort)]
                self.assertEqual(restored.cost_attempts, state.cost_attempts)
            self.assertEqual(len(client.calls), before)

    def test_progress_receives_final_metadata_cost_without_double_counting(self):
        class EnrichedClient(FakeClient):
            def complete(self, *args, **kwargs):
                response = super().complete(*args, **kwargs)
                response["usage"].pop("cost")
                return response

            def generation_details(self, generation_id):
                return {"data": {
                    "total_cost": "0.00003", "native_tokens_prompt": 12,
                    "native_tokens_completion": 3,
                }}

        with ProgressReporter(stream=io.StringIO()) as reporter:
            result = run_new(
                client=EnrichedClient(), config=self.config, model_info=self.model_info,
                results_dir=self.results_dir, on_progress=reporter,
            )
            costs = reporter._models[(self.config.model_id, self.config.reasoning_effort)].cost_attempts
            self.assertEqual(len(costs), 2)
            self.assertEqual(sum(Decimal(row["provider_reported_usd"]) for row in costs.values()), Decimal("0.00006"))
            self.assertEqual(sum(Decimal(row["normalized_uncached_usd"]) for row in costs.values()), Decimal("0.0000054"))
            self.assertEqual(summarize_run(result["ledger_path"])["provider_cost_total"], Decimal("0.00006"))

    def test_completed_run_resume_does_not_repeat_requests_and_checks_config(self):
        client = FakeClient()
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        resumed = resume_run(client=client, ledger_path=result["ledger_path"])
        self.assertTrue(resumed["complete"])
        self.assertTrue(resumed["already_finished"])
        self.assertEqual(len(client.calls), 2)
        self.assertTrue(all(call["max_completion_tokens"] == 32 for call in client.calls))
        with self.assertRaisesRegex(ValueError, "reasoning_effort mismatch"):
            resume_run(
                client=client,
                ledger_path=result["ledger_path"],
                overrides={"reasoning_effort": "medium"},
            )
        with self.assertRaisesRegex(ValueError, "reasoning_effort mismatch"):
            resume_run(
                client=client, ledger_path=result["ledger_path"],
                overrides={"reasoning_effort": None},
            )

    def test_resume_rejects_manifest_with_missing_cap_policy(self):
        result = run_new(
            client=FakeClient(),
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        manifest_path = Path(result["manifest_path"])
        manifest = json.loads(manifest_path.read_text())
        del manifest["config"]["max_completion_tokens"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not record its completion-token-cap policy"):
            resume_run(client=FakeClient(), ledger_path=result["ledger_path"])

    def test_default_retry_budget_is_five_retries_six_total_attempts(self):
        from runner import DEFAULT_MAX_ATTEMPTS, DEFAULT_MAX_RETRIES

        self.assertEqual(DEFAULT_MAX_RETRIES, 5)
        self.assertEqual(DEFAULT_MAX_ATTEMPTS, 6)

    def test_backoff_doubles_with_bounded_jitter(self):
        client = RetryBurstClient(failures=5)
        config = RunConfig(
            **{
                **self.config.__dict__,
                "max_attempts": 6,
                "retry_delay_seconds": 1.0,
            }
        )
        with (
            patch("runner.random.uniform", side_effect=lambda _low, high: high),
            patch("runner.time.sleep") as sleep,
        ):
            result = run_new(
                client=client,
                config=config,
                model_info=self.model_info,
                results_dir=self.results_dir,
            )
        self.assertTrue(result["complete"])
        self.assertEqual(len(client.calls), 7)
        delays = [call.args[0] for call in sleep.call_args_list]
        self.assertEqual(len(delays), 5)
        for actual, expected in zip(delays, (1.2, 2.4, 4.8, 9.6, 19.2)):
            self.assertAlmostEqual(actual, expected)

    def test_rate_gate_cancellation_does_not_start_or_consume_an_attempt(self):
        class CancellingGate:
            def acquire(self, cancel_event, *, on_admitted=None):
                cancel_event.set()
                return False

        cancel_event = threading.Event()
        client = FakeClient()
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
            cancel_event=cancel_event,
            request_gate=CancellingGate(),
        )
        events, _ = runner_module.load_events(result["ledger_path"])
        self.assertFalse(result["complete"])
        self.assertEqual(client.calls, [])
        self.assertFalse(any(event.get("event_type") == "attempt_started" for event in events))
        self.assertEqual(summarize_run(result["ledger_path"])["attempt_count"], 0)

    def test_429_retry_after_is_persisted_and_applies_shared_cooldown(self):
        class RateLimitClient(FakeClient):
            def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
                self.calls.append({"model_id": model_id, "prompt": prompt})
                raise OpenRouterError(
                    "OpenRouter returned HTTP 429",
                    status_code=429,
                    retryable=True,
                    may_have_been_billed=True,
                    retry_after_seconds=7.5,
                )

        class RecordingGate:
            def __init__(self):
                self.acquisitions = 0
                self.cooldowns = []

            def acquire(self, _cancel_event, *, on_admitted=None):
                self.acquisitions += 1
                return on_admitted is None or on_admitted()

            def cool_down(self, retry_after_seconds):
                self.cooldowns.append(retry_after_seconds)
                return max(60.0, retry_after_seconds or 0.0)

        client = RateLimitClient()
        gate = RecordingGate()
        config = RunConfig(**{**self.config.__dict__, "max_attempts": 1})
        result = run_new(
            client=client,
            config=config,
            model_info=self.model_info,
            results_dir=self.results_dir,
            request_gate=gate,
        )
        events, _ = runner_module.load_events(result["ledger_path"])
        failures = [event for event in events if event.get("event_type") == "attempt_failed"]
        self.assertEqual(gate.acquisitions, 2)
        self.assertEqual(gate.cooldowns, [7.5, 7.5])
        self.assertTrue(all(event["retry_after_seconds"] == 7.5 for event in failures))
        self.assertTrue(all(event["shared_cooldown_seconds"] == 60.0 for event in failures))
        self.assertEqual(len(failures), 2)

    def test_retry_transient_error_but_cost_unknown_is_not_zero(self):
        client = FakeClient(fail_first=True)
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        self.assertTrue(result["complete"])
        self.assertEqual(len(client.calls), 3)
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["counts"]["correct"], 2)
        self.assertEqual(summary["attempt_count"], 3)
        self.assertEqual(summary["provider_cost_known_attempts"], 2)
        self.assertTrue(summary["provider_cost_cell"].startswith("Partial"))
        self.assertTrue(summary["normalized_cost_cell"].startswith("Partial"))

    def test_invalid_answer_is_terminal_and_not_retried(self):
        client = FakeClient(content_mode="invalid")
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        self.assertTrue(result["complete"])
        self.assertEqual(len(client.calls), 2)
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["counts"]["correct"], 0)
        self.assertEqual(summary["counts"]["invalid"], 2)
        self.assertEqual(summary["counts"]["incorrect"], 2)

    def test_truncated_finish_reason_is_invalid_and_not_retried(self):
        client = FakeClient(finish_reason="length")
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        self.assertTrue(result["complete"])
        self.assertEqual(len(client.calls), 2)
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["counts"]["invalid"], 2)
        self.assertEqual(summary["counts"]["truncated"], 2)
        self.assertEqual(summary["counts"]["other_invalid"], 0)
        self.assertEqual(summary["by_depth"][4]["truncated"], 2)

    def test_http_200_without_choices_is_invalid_and_not_retried(self):
        client = NoChoicesClient()
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        self.assertTrue(result["complete"])
        self.assertEqual(len(client.calls), 2)
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["counts"]["invalid"], 2)
        self.assertEqual(summary["provider_cost_known_attempts"], 2)

    def test_cost_update_replaces_attempt_cost_instead_of_double_counting(self):
        from events import append_event

        client = FakeClient()
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        events = [json.loads(line) for line in Path(result["ledger_path"]).read_text().splitlines()]
        first_attempt = next(event for event in events if event["event_type"] == "attempt_response")
        append_event(
            result["ledger_path"],
            {
                "event_type": "attempt_cost_update",
                "run_id": result["run_id"],
                "case_id": first_attempt["case_id"],
                "attempt_id": first_attempt["attempt_id"],
                "provider_reported_usd": "0.00002",
                "normalized_uncached_usd": "0.0000042",
            },
        )
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["provider_cost_total"], Decimal("0.00003"))
        self.assertEqual(summary["normalized_cost_total"], Decimal("0.0000063"))

    def test_terminal_http_failures_are_completed_but_count_incorrect_and_cost(self):
        client = ErrorClient()
        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        self.assertTrue(result["complete"])
        self.assertEqual(len(client.calls), 2)
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["counts"]["no_response"], 2)
        self.assertEqual(summary["counts"]["incorrect"], 2)
        self.assertEqual(summary["provider_cost_known_attempts"], 2)
        self.assertEqual(summary["provider_cost_total"], Decimal("0.00006"))

    def test_arbitrary_effort_cannot_escape_results_dir_or_collide_after_slugging(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "results"
            efforts = ("custom/../../outside", "custom/level", "custom-level", None, "none", "omitted")
            paths = [_new_ledger_path(root, "openai/gpt-6-luna", effort) for effort in efforts]
            self.assertTrue(all(path.parent == root.resolve() for path in paths))
            self.assertEqual(len({path.name for path in paths}), len(paths))
            self.assertTrue(all("/" not in path.name and "\\" not in path.name for path in paths))

    def test_cancel_after_attempt_start_prevents_http_dispatch_and_marks_case_unattempted(self):
        client = FakeClient()
        cancellation = threading.Event()

        def stop_after_durable_start(event):
            if event.get("event") == "attempt_started":
                cancellation.set()

        result = run_new(
            client=client,
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
            on_progress=stop_after_durable_start,
            cancel_event=cancellation,
        )
        self.assertFalse(result["complete"])
        self.assertEqual(client.calls, [])
        summary = summarize_run(result["ledger_path"])
        self.assertEqual(summary["attempt_count"], 0)
        self.assertEqual(summary["counts"]["attempted_cases"], 0)
        self.assertEqual(summary["counts"]["not_attempted"], 2)
        events = [json.loads(line) for line in Path(result["ledger_path"]).read_text().splitlines()]
        self.assertTrue(any(event["event_type"] == "attempt_cancelled_before_dispatch" for event in events))

    def test_omitted_effort_survives_interruption_resume_and_rejects_tampering(self):
        from dataclasses import replace

        config = replace(self.config, reasoning_effort=None)
        model = replace(self.model_info, supported_parameters=("temperature",))
        with self.assertRaises(KeyboardInterrupt):
            run_new(
                client=InterruptOnceClient(), config=config, model_info=model,
                results_dir=self.results_dir,
            )
        ledger = next(self.results_dir.glob("*.jsonl"))
        client = FakeClient()
        result = resume_run(client=client, ledger_path=ledger)
        self.assertTrue(result["complete"])
        self.assertTrue(all(call["reasoning_effort"] is None for call in client.calls))
        with self.assertRaisesRegex(ValueError, "reasoning_effort mismatch"):
            resume_run(client=client, ledger_path=ledger, overrides={"reasoning_effort": "high"})
        manifest_path = Path(result["manifest_path"])
        manifest = json.loads(manifest_path.read_text())
        manifest["model"]["reasoning_effort"] = "high"
        manifest["config"]["reasoning_effort"] = "high"
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "configuration hash mismatch"):
            resume_run(client=client, ledger_path=ledger)

    def test_interrupt_then_resume_preserves_unknown_spend_and_attempt_identity(self):
        client = InterruptOnceClient()
        with self.assertRaises(KeyboardInterrupt):
            run_new(
                client=client,
                config=self.config,
                model_info=self.model_info,
                results_dir=self.results_dir,
            )
        ledger = next(self.results_dir.glob("*.jsonl"))
        before = summarize_run(ledger)
        self.assertFalse(before["complete"])
        self.assertEqual(before["counts"]["pending"], 1)
        self.assertEqual(before["counts"]["not_attempted"], 1)
        provisional = render_leaderboard([before])
        self.assertIn("Incomplete runs (provisional, not ranked)", provisional)
        self.assertIn("Provider-reported cost (USD)", provisional)
        self.assertIn("Unknown (0/1 requests priced)", provisional)

        resumed_client = FakeClient()
        result = resume_run(client=resumed_client, ledger_path=ledger)
        self.assertTrue(result["complete"])
        after = summarize_run(ledger)
        self.assertEqual(after["counts"]["correct"], 2)
        self.assertEqual(after["attempt_count"], 3)
        self.assertEqual(after["provider_cost_known_attempts"], 2)
        self.assertEqual(after["normalized_cost_known_attempts"], 2)
        events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
        starts = [event for event in events if event["event_type"] == "attempt_started"]
        interrupted = [event for event in events if event["event_type"] == "attempt_interrupted"]
        self.assertEqual(len(interrupted), 1)
        self.assertEqual(len({event["attempt_id"] for event in starts}), len(starts))

    def test_crash_after_response_before_persist_is_unknown_then_resumed_as_new_attempt(self):
        client = FakeClient()
        original_append = runner_module.append_event
        interrupted_response_write = {"done": False}

        def fail_response_persist(path, event):
            if event.get("event_type") == "attempt_response" and not interrupted_response_write["done"]:
                interrupted_response_write["done"] = True
                raise KeyboardInterrupt()
            return original_append(path, event)

        with patch.object(runner_module, "append_event", side_effect=fail_response_persist):
            with self.assertRaises(KeyboardInterrupt):
                run_new(
                    client=client,
                    config=self.config,
                    model_info=self.model_info,
                    results_dir=self.results_dir,
                )
        self.assertEqual(len(client.calls), 1)  # remote response existed but was not durably logged
        ledger = next(self.results_dir.glob("*.jsonl"))
        with ledger.open("ab") as stream:
            stream.write(b'{"event_type":"torn')
        resumed_client = FakeClient()
        result = resume_run(client=resumed_client, ledger_path=ledger)
        self.assertTrue(result["complete"])
        self.assertTrue(Path(f"{ledger}.torn").exists())
        summary = summarize_run(ledger)
        self.assertEqual(summary["counts"]["correct"], 2)
        self.assertEqual(summary["attempt_count"], 3)
        self.assertEqual(summary["provider_cost_known_attempts"], 2)
        events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(event["event_type"] == "attempt_interrupted" for event in events))

    def test_same_seed_reuses_frozen_dataset_across_models(self):
        first = run_new(
            client=FakeClient(),
            config=self.config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        other_info = ModelInfo(
            requested_id="provider/other-model",
            model_id="provider/other-model",
            name="Other",
            prompt_rate_usd_per_million=Decimal("1"),
            completion_rate_usd_per_million=Decimal("2"),
            pricing_source="fixture catalog",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        other_config = RunConfig(
            **{
                **self.config.__dict__,
                "model_id": "provider/other-model",
                "reasoning_effort": "medium",
            }
        )
        second = run_new(
            client=FakeClient(),
            config=other_config,
            model_info=other_info,
            results_dir=self.results_dir,
        )
        replicate_config = RunConfig(**self.config.__dict__)
        replicate = run_new(
            client=FakeClient(),
            config=replicate_config,
            model_info=self.model_info,
            results_dir=self.results_dir,
        )
        first_manifest = json.loads(Path(first["manifest_path"]).read_text())
        second_manifest = json.loads(Path(second["manifest_path"]).read_text())
        replicate_manifest = json.loads(Path(replicate["manifest_path"]).read_text())
        self.assertEqual(first_manifest["dataset"]["dataset_id"], second_manifest["dataset"]["dataset_id"])
        self.assertEqual(first_manifest["dataset"]["sha256"], second_manifest["dataset"]["sha256"])
        self.assertEqual(first_manifest["dataset"]["dataset_id"], replicate_manifest["dataset"]["dataset_id"])
        summaries = [
            summarize_run(first["ledger_path"]),
            summarize_run(second["ledger_path"]),
            summarize_run(replicate["ledger_path"]),
        ]
        leaderboard = render_leaderboard(summaries)
        self.assertEqual(leaderboard.count("## Completed runs"), 1)
        self.assertNotIn("## Dataset `", leaderboard)
        self.assertIn("openai/gpt-6-luna", leaderboard)
        self.assertIn("provider/other-model", leaderboard)
        self.assertIn("| low |", leaderboard)
        self.assertIn("| medium |", leaderboard)
        self.assertIn("| Effort | Run (parent+child) |", leaderboard)
        self.assertIn(first["run_id"][:8], leaderboard)
        self.assertIn(second["run_id"][:8], leaderboard)
        self.assertIn(replicate["run_id"][:8], leaderboard)
        self.assertEqual(leaderboard.count("openai/gpt-6-luna"), 6)


if __name__ == "__main__":
    unittest.main()
