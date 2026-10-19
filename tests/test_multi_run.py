import io
import json
from decimal import Decimal
import tempfile
import threading
import time
import unittest
from pathlib import Path
from contextlib import redirect_stderr
from unittest.mock import patch

from cases import is_prime
import multi_run
from multi_run import ModelRunSpec, run_many
from openrouter import ModelInfo
from progress import ProgressReporter
from report import summarize_run
from runner import RunConfig


class ParallelMetrics:
    def __init__(self):
        self.lock = threading.Lock()
        self.barrier = threading.Barrier(2)
        self.active = 0
        self.max_active = 0
        self.calls = 0


class ParallelFakeClient:
    def __init__(self, metrics):
        self.metrics = metrics

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        with self.metrics.lock:
            self.metrics.active += 1
            self.metrics.max_active = max(self.metrics.max_active, self.metrics.active)
            self.metrics.calls += 1
        try:
            self.metrics.barrier.wait(timeout=3)
            number = int(prompt.split()[1])
            answer = "PRIME" if is_prime(number) else "COMPOSITE"
            return {
                "id": f"gen-{model_id.replace('/', '-')}-{self.metrics.calls}",
                "model": model_id,
                "provider": "OpenAI",
                "choices": [{"finish_reason": "stop", "message": {"content": answer}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 1,
                    "cost": "0.00001",
                },
            }
        finally:
            with self.metrics.lock:
                self.metrics.active -= 1

    def generation_details(self, generation_id):
        raise AssertionError("direct provider route and cost should avoid inline metadata lookup")


class InterruptMetrics:
    def __init__(self):
        self.started = threading.Event()
        self.lock = threading.Lock()
        self.calls = []


class InterruptFakeClient:
    def __init__(self, metrics):
        self.metrics = metrics

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        with self.metrics.lock:
            self.metrics.calls.append(model_id)
        self.metrics.started.set()
        time.sleep(0.1)  # simulate one request already in flight when Ctrl-C arrives
        number = int(prompt.split()[1])
        answer = "PRIME" if is_prime(number) else "COMPOSITE"
        return {
            "id": f"gen-cancel-{model_id}-{number}",
            "model": model_id,
            "provider": "OpenAI",
            "choices": [{"finish_reason": "stop", "message": {"content": answer}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "cost": "0.00001"},
        }

    def generation_details(self, generation_id):
        raise AssertionError("direct usage is sufficient")


class MultiRunTests(unittest.TestCase):
    def _spec(self, model_id, effort):
        model = ModelInfo(
            requested_id=model_id,
            model_id=model_id,
            name=model_id,
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="fixture",
            pricing_retrieved_at="2026-10-19T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )
        config = RunConfig(
            model_id=model_id,
            reasoning_effort=effort,
            depths=(4,),
            samples_per_class=1,
            seed=2026,
            max_attempts=1,
            retry_delay_seconds=0,
            timeout_seconds=2,
            max_completion_tokens=64,
        )
        return ModelRunSpec(config=config, model_info=model)

    def test_models_run_in_parallel_share_same_cases_and_report_progress_separately(self):
        metrics = ParallelMetrics()
        specs = [
            self._spec("provider/model-a", "low"),
            self._spec("provider/model-b", "low"),
        ]
        output = io.StringIO()
        reporter = ProgressReporter(stream=output)
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("multi_run.prepare_case_dataset", wraps=multi_run.prepare_case_dataset) as prepare:
                results = run_many(
                    specs,
                    client_factory=lambda _timeout: ParallelFakeClient(metrics),
                    results_dir=Path(temp_dir) / "results",
                    parallelism=2,
                    on_progress=reporter,
                )
            self.assertEqual(prepare.call_count, 1)
            self.assertEqual(len(results), 2)
            self.assertTrue(all(row["error"] is None for row in results))
            self.assertTrue(all(row["result"]["complete"] for row in results))
            self.assertGreaterEqual(metrics.max_active, 2)
            self.assertLessEqual(metrics.max_active, 2)
            self.assertEqual(metrics.calls, 4)
            self.assertEqual(len({row["result"]["ledger_path"] for row in results}), 2)
            manifests = [json.loads(Path(row["result"]["manifest_path"]).read_text()) for row in results]
            self.assertEqual(manifests[0]["dataset"]["dataset_id"], manifests[1]["dataset"]["dataset_id"])
            self.assertIn("model_id=provider/model-a | reasoning_effort=low", output.getvalue())
            self.assertIn("model_id=provider/model-b | reasoning_effort=low", output.getvalue())
            self.assertIn("ETA", output.getvalue())
            self.assertIn("tok/s", output.getvalue())
            self.assertIn("batch elapsed", output.getvalue())

    def test_ctrl_c_stops_queued_models_and_leaves_resumable_ledgers(self):
        metrics = InterruptMetrics()
        specs = [
            self._spec("provider/model-a", "low"),
            self._spec("provider/model-b", "low"),
        ]
        def interrupt_after_first_dispatch(futures):
            if not metrics.started.wait(timeout=3):
                raise AssertionError("worker did not dispatch the first request")
            time.sleep(0.01)
            raise KeyboardInterrupt()

        output = io.StringIO()
        errors = io.StringIO()
        reporter = ProgressReporter(stream=output, heartbeat_interval=0.02)
        with tempfile.TemporaryDirectory() as temp_dir:
            with redirect_stderr(errors):
                with patch("multi_run.as_completed", side_effect=interrupt_after_first_dispatch):
                    results = run_many(
                        specs,
                        client_factory=lambda _timeout: InterruptFakeClient(metrics),
                        results_dir=Path(temp_dir) / "results",
                        parallelism=1,
                        on_progress=reporter,
                    )
            self.assertEqual(len(results), 2)
            self.assertTrue(all(row.get("batch_interrupted") for row in results))
            self.assertEqual(metrics.calls, ["provider/model-a"])
            summaries = [summarize_run(row["result"]["ledger_path"]) for row in results]
            self.assertTrue(all(not summary["complete"] for summary in summaries))
            self.assertEqual(summaries[0]["counts"]["answered_cases"], 1)
            self.assertEqual(summaries[0]["counts"]["pending"] + summaries[0]["counts"]["not_attempted"], 1)
            self.assertEqual(summaries[1]["counts"]["attempted_cases"], 0)
            self.assertEqual(summaries[1]["counts"]["not_attempted"], 2)
            self.assertIn("Cancellation requested", errors.getvalue())
            reporter.close()


if __name__ == "__main__":
    unittest.main()
