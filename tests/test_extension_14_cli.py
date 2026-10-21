from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

from cases import is_prime
from extensions import load_extension_parents
from openrouter import ModelInfo
from report import load_summaries, render_leaderboard
from request_gate import AccountRequestGate
from runner import RunConfig, run_new


PAIRS = [
    ("openai/gpt-6-luna", "low"),
    ("openai/gpt-6-luna", "medium"),
    ("openai/gpt-6-luna", "high"),
    ("openai/gpt-6-luna", "xhigh"),
    ("deepseek/deepseek-v4.1-flash-1017", "low"),
    ("deepseek/deepseek-v4.1-flash-1017", "medium"),
    ("deepseek/deepseek-v4.1-flash-1017", "high"),
    ("anthropic/claude-haiku-5.5", "low"),
    ("anthropic/claude-haiku-5.5", "medium"),
    ("anthropic/claude-haiku-5.5", "high"),
    ("anthropic/claude-haiku-5.5", "xhigh"),
    ("openai/gpt-6.1-sol", "low"),
    ("openai/gpt-6.1-sol", "medium"),
    ("openai/gpt-4-turbo", None),
]


def model_info(model_id):
    return ModelInfo(
        requested_id=model_id,
        model_id=model_id,
        name=model_id,
        prompt_rate_usd_per_million=Decimal("0.1"),
        completion_rate_usd_per_million=Decimal("0.5"),
        pricing_source="local fake adapter",
        pricing_retrieved_at="2026-10-21T00:00:00Z",
        supported_parameters=("reasoning_effort",),
    )


class FakeAdapter:
    calls = []
    lock = threading.Lock()

    def __init__(self, _api_key, *, timeout):
        self.timeout = timeout

    def resolve_model(self, model_id):
        return model_info(model_id)

    @staticmethod
    def validate_reasoning_effort(_model_info, _effort):
        return None

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        number = int(prompt.split()[1])
        answer = "PRIME" if is_prime(number) else "COMPOSITE"
        with self.lock:
            self.calls.append((model_id, reasoning_effort, number))
        return {
            "id": f"fake-{uuid4().hex}",
            "model": model_id,
            "provider": "OpenAI",
            "choices": [{"finish_reason": "stop", "message": {"content": answer}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "cost": "0.00001"},
        }

    def generation_details(self, _generation_id):
        raise AssertionError("fake response includes usage and cost")


class Full14ExtensionCliTests(unittest.TestCase):
    def test_exact_14_pair_cli_runs_3080_fake_cases_then_resumes_without_dispatch(self):
        import run

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "results"
            root.mkdir()
            parent_paths = []
            parent_client = FakeAdapter("local", timeout=600)
            config_settings = dict(
                depths=tuple(range(4, 11)),
                samples_per_class=10,
                seed=2026,
                max_attempts=6,
                retry_delay_seconds=1,
                timeout_seconds=600,
                max_completion_tokens=None,
                min_request_interval_seconds=4,
            )
            for model_id, effort in PAIRS:
                result = run_new(
                    client=parent_client,
                    config=RunConfig(
                        model_id=model_id,
                        reasoning_effort=effort,
                        **config_settings,
                    ),
                    model_info=model_info(model_id),
                    results_dir=root,
                    request_gate=AccountRequestGate(0.001),
                )
                self.assertTrue(result["complete"])
                parent_paths.append(Path(result["ledger_path"]))
            parents = load_extension_parents(parent_paths)
            parent_pairs = {(case.depth, case.number) for case in parents[0].cases}
            parent_hashes = {
                path: (
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    hashlib.sha256(path.with_name(f"{path.stem}.manifest.json").read_bytes()).hexdigest(),
                )
                for path in parent_paths
            }
            FakeAdapter.calls = []

            args = []
            for model_id, effort in PAIRS:
                args.extend(("--model-id", model_id, "--reasoning-effort", effort or "omit"))
            args.extend(
                (
                    "--extend-through", "15",
                    "--top-up-existing-per-class", "5",
                    "--new-depths-per-class", "15",
                    "--parallelism", "3",
                    "--max-retries", "5",
                    "--retry-delay", "1",
                    "--timeout", "600",
                    "--requests-per-minute", "15",
                    "--results-dir", str(root),
                )
            )

            def invoke():
                with (
                    patch("run.OpenRouterClient", FakeAdapter),
                    patch("run.AccountRequestGate", lambda _interval: AccountRequestGate(0.001)),
                    patch("run.load_dotenv"),
                    patch("run.get_openrouter_key", return_value="offline-only"),
                    redirect_stdout(io.StringIO()),
                    redirect_stderr(io.StringIO()),
                ):
                    return run.main(args)

            self.assertEqual(invoke(), 0)
            self.assertEqual(len(FakeAdapter.calls), 14 * 220)
            self.assertEqual(
                Counter((model_id, effort) for model_id, effort, _number in FakeAdapter.calls),
                {pair: 220 for pair in PAIRS},
            )
            self.assertFalse(
                parent_pairs
                & {(len(str(number)), number) for _model, _effort, number in FakeAdapter.calls}
            )

            child_manifests = []
            for path in sorted(root.glob("*.manifest.json")):
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if manifest.get("extension"):
                    child_manifests.append((path, manifest))
            self.assertEqual(len(child_manifests), 14)
            metadata = [manifest["extension"] for _path, manifest in child_manifests]
            self.assertEqual(len({item["extension_batch_id"] for item in metadata}), 1)
            self.assertEqual(len({item["supplement_dataset_sha256"] for item in metadata}), 1)
            for _path, manifest in child_manifests:
                self.assertEqual(manifest["dataset"]["case_count"], 220)
                self.assertIsNone(manifest["config"]["max_completion_tokens"])
                self.assertEqual(manifest["config"]["timeout_seconds"], 600)
                self.assertEqual(manifest["config"]["max_attempts"], 6)
                self.assertEqual(manifest["config"]["min_request_interval_seconds"], 4)

            child_paths = [path.with_name(manifest["ledger_file"]) for path, manifest in child_manifests]
            reports = load_summaries([*parent_paths, *child_paths])
            self.assertEqual(len(reports), 14)
            for summary in reports:
                self.assertEqual(summary["scheduled"], 360)
                self.assertEqual(summary["counts"]["correct"], 360)
                for depth in range(4, 16):
                    cell = summary["by_depth"][depth]
                    self.assertEqual(cell["scheduled"], 30)
                    self.assertEqual(cell["primes_scheduled"], 15)
                    self.assertEqual(cell["nonprimes_scheduled"], 15)
            self.assertIn("Approx. 95% Wilson CI", render_leaderboard(reports))

            call_count = len(FakeAdapter.calls)
            self.assertEqual(invoke(), 0)
            self.assertEqual(len(FakeAdapter.calls), call_count)
            for path, (ledger_hash, manifest_hash) in parent_hashes.items():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ledger_hash)
                manifest_path = path.with_name(f"{path.stem}.manifest.json")
                self.assertEqual(hashlib.sha256(manifest_path.read_bytes()).hexdigest(), manifest_hash)


if __name__ == "__main__":
    unittest.main()
