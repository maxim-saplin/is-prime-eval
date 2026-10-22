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

from cases import PRIME, COMPOSITE, is_prime
from extensions import load_extension_parents, prepare_extension_plan
from multi_run import run_many
from openrouter import ModelInfo
from report import load_summaries, render_leaderboard
from runner import RunConfig, run_new


class FakeClient:
    def __init__(self):
        self.calls = []
        self._lock = threading.Lock()
        self._next_id = 0

    def complete(self, model_id, prompt, *, reasoning_effort, max_completion_tokens):
        number = int(prompt.split()[1])
        with self._lock:
            self._next_id += 1
            generation_id = f"fake-{self._next_id}"
            self.calls.append((model_id, number))
        answer = "PRIME" if is_prime(number) else "COMPOSITE"
        return {
            "id": generation_id,
            "model": model_id,
            "provider": "OpenAI",
            "choices": [{"finish_reason": "stop", "message": {"content": answer}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "cost": "0.00001"},
        }

    def generation_details(self, generation_id):
        raise AssertionError("fixture response includes provider cost")


class CancelAfterOneClient(FakeClient):
    def __init__(self, cancel_event):
        super().__init__()
        self.cancel_event = cancel_event

    def complete(self, *args, **kwargs):
        response = super().complete(*args, **kwargs)
        self.cancel_event.set()
        return response


class ExtensionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "results"
        self.root.mkdir()
        self.parent_client = FakeClient()
        self.parent_ledgers = []
        self.parent_pairs = set()
        for model_id in ("provider/model-a", "provider/model-b"):
            model_info = self._model_info(model_id)
            config = RunConfig(
                model_id=model_id,
                reasoning_effort="low",
                depths=tuple(range(4, 11)),
                samples_per_class=1,
                seed=2026,
                max_attempts=1,
                retry_delay_seconds=0,
                timeout_seconds=2,
                max_completion_tokens=None,
                min_request_interval_seconds=0,
            )
            result = run_new(
                client=self.parent_client,
                config=config,
                model_info=model_info,
                results_dir=self.root,
            )
            self.assertTrue(result["complete"])
            self.parent_ledgers.append(Path(result["ledger_path"]))
        parents = load_extension_parents(self.parent_ledgers)
        self.parents = parents
        self.parent_pairs = {(case.depth, case.number) for case in parents[0].cases}
        self.parent_hashes = {
            path: (
                hashlib.sha256(path.read_bytes()).hexdigest(),
                hashlib.sha256(path.with_name(f"{path.stem}.manifest.json").read_bytes()).hexdigest(),
            )
            for path in self.parent_ledgers
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def _model_info(model_id):
        return ModelInfo(
            requested_id=model_id,
            model_id=model_id,
            name=model_id,
            prompt_rate_usd_per_million=Decimal("0.1"),
            completion_rate_usd_per_million=Decimal("0.5"),
            pricing_source="fixture",
            pricing_retrieved_at="2026-10-20T00:00:00Z",
            supported_parameters=("reasoning_effort",),
        )

    def _assert_parent_hashes_unchanged(self):
        for path, (ledger_hash, manifest_hash) in self.parent_hashes.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ledger_hash)
            manifest = path.with_name(f"{path.stem}.manifest.json")
            self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(), manifest_hash)

    def _plan(self, seed=None):
        return prepare_extension_plan(
            results_dir=self.root,
            parents=self.parents,
            target_depth=15,
            top_up_per_class=5,
            new_depths_per_class=15,
            requested_seed=seed,
        )

    def test_one_frozen_220_case_dataset_is_shared_and_disjoint(self):
        plan = self._plan(seed=314159)
        self.assertEqual(len(plan.specs), 2)
        self.assertEqual(plan.manifest["added_case_count"], 220)
        self.assertEqual(len(plan.prepared_dataset.cases), 220)
        self.assertEqual(plan.specs[0].config.scheduled_case_count, 220)
        self.assertEqual(
            plan.specs[0].extension_metadata["supplement_dataset_sha256"],
            plan.specs[1].extension_metadata["supplement_dataset_sha256"],
        )
        counts = Counter(
            (case.depth, case.label) for case in plan.prepared_dataset.cases
        )
        self.assertEqual(
            counts,
            {
                (depth, label): 5
                for depth in range(4, 11)
                for label in (PRIME, COMPOSITE)
            }
            | {
                (depth, label): 15
                for depth in range(11, 16)
                for label in (PRIME, COMPOSITE)
            },
        )
        added_pairs = {
            (case.depth, case.number) for case in plan.prepared_dataset.cases
        }
        self.assertFalse(self.parent_pairs & added_pairs)
        self.assertEqual(len(added_pairs), 220)
        self._assert_parent_hashes_unchanged()

    def test_reuses_valid_legacy_frozen_batch_without_regenerating_dataset(self):
        original = self._plan()
        current_plan_path = self.root / f"extension-batch-{original.batch_id}.json"
        batch = json.loads(current_plan_path.read_text(encoding="utf-8"))
        current_plan_path.unlink()
        batch["extension_batch_id"] = "legacy-frozen-batch"
        batch["parents"] = [
            {
                **parent_ref,
                "model_id": parent.config.model_id,
                "reasoning_effort": parent.config.reasoning_effort,
                "dataset_id": parent.manifest["dataset"]["dataset_id"],
                "depths": list(parent.config.depths),
                "samples_per_class": parent.config.samples_per_class,
                "seed": parent.config.seed,
                "seed_source": parent.config.seed_source,
            }
            for parent, parent_ref in zip(original.parents, batch["parents"])
        ]
        saved_path = self.root / "extension-batch-legacy.json"
        saved_path.write_text(json.dumps(batch), encoding="utf-8")
        dataset_files_before = sorted((self.root / "datasets").glob("*.json"))

        reused = self._plan()

        self.assertEqual(reused.batch_id, "legacy-frozen-batch")
        self.assertEqual(reused.manifest["sampling_seed"], original.manifest["sampling_seed"])
        self.assertEqual(
            reused.prepared_dataset.payload["sha256"],
            original.prepared_dataset.payload["sha256"],
        )
        self.assertEqual(sorted((self.root / "datasets").glob("*.json")), dataset_files_before)
        self._assert_parent_hashes_unchanged()

    def test_cli_dry_run_uses_explicit_parents_without_dispatch(self):
        import run

        class FakeCatalog:
            def __init__(self, _api_key, *, timeout):
                self.timeout = timeout

            def resolve_model(self, model_id):
                return ExtensionIntegrationTests._model_info(model_id)

            @staticmethod
            def validate_reasoning_effort(_model_info, _effort):
                return None

        output = io.StringIO()
        with (
            patch("run.OpenRouterClient", FakeCatalog),
            patch("run.run_many", side_effect=AssertionError("dry-run must not dispatch")),
            patch("run.load_dotenv"),
            patch("run.get_openrouter_key", return_value="offline-test-key"),
            redirect_stdout(output),
            redirect_stderr(io.StringIO()),
        ):
            status = run.main(
                [
                    "--parent-ledger", str(self.parent_ledgers[0]),
                    "--parent-ledger", str(self.parent_ledgers[1]),
                    "--extend-through", "15",
                    "--timeout", "2",
                    "--results-dir", str(self.root),
                    "--dry-run",
                ]
            )
            inherited_status = run.main(
                [
                    "--parent-ledger", str(self.parent_ledgers[0]),
                    "--parent-ledger", str(self.parent_ledgers[1]),
                    "--extend-through", "15",
                    "--results-dir", str(self.root),
                    "--dry-run",
                ]
            )
        self.assertEqual(status, 0)
        self.assertEqual(inherited_status, 0)
        self.assertEqual(output.getvalue().count("Timeout: 2.0s socket inactivity"), 2)
        self.assertIn("Added cases per model: 220", output.getvalue())
        self.assertIn("Supplement sampling seed:", output.getvalue())
        self._assert_parent_hashes_unchanged()

    def test_random_manifest_reuse_partial_resume_and_cumulative_cost_once(self):
        first_plan = self._plan()
        first_seed = first_plan.manifest["sampling_seed"]
        self.assertEqual(first_plan.manifest["seed_source"], "system_random")
        reused_plan = self._plan()
        self.assertEqual(reused_plan.batch_id, first_plan.batch_id)
        self.assertEqual(reused_plan.manifest["sampling_seed"], first_seed)
        self.assertEqual(
            reused_plan.prepared_dataset.payload["sha256"],
            first_plan.prepared_dataset.payload["sha256"],
        )

        first_spec = first_plan.specs[0]
        cancelled = threading.Event()
        partial_client = CancelAfterOneClient(cancelled)
        partial = run_new(
            client=partial_client,
            config=first_spec.config,
            model_info=first_spec.model_info,
            results_dir=self.root,
            prepared_dataset=first_plan.prepared_dataset,
            cancel_event=cancelled,
            extension_metadata=first_spec.extension_metadata,
        )
        self.assertFalse(partial["complete"])
        self.assertEqual(len(partial_client.calls), 1)
        provisional = load_summaries([self.parent_ledgers[0], Path(partial["ledger_path"])])
        self.assertEqual(len(provisional), 2)
        self.assertEqual(sum(not row["complete"] for row in provisional), 1)

        resumed_plan = self._plan()
        self.assertEqual(Path(resumed_plan.specs[0].resume_ledger_path), Path(partial["ledger_path"]))
        self.assertIsNone(resumed_plan.specs[1].resume_ledger_path)
        child_client = FakeClient()
        rows = run_many(
            resumed_plan.specs,
            client_factory=lambda _timeout: child_client,
            results_dir=self.root,
            parallelism=2,
            prepared_dataset=resumed_plan.prepared_dataset,
        )
        self.assertTrue(all(row["error"] is None for row in rows))
        self.assertTrue(all(row["result"]["complete"] for row in rows))
        self.assertEqual(len(child_client.calls), 439)
        self.assertNotIn(partial_client.calls[0], child_client.calls)
        child_pairs = {
            (case.depth, case.number) for case in resumed_plan.prepared_dataset.cases
        }
        self.assertFalse(self.parent_pairs & child_pairs)
        self.assertTrue(all((len(str(number)), number) not in self.parent_pairs for _, number in child_client.calls))

        reports = load_summaries(
            [self.parent_ledgers[0], self.parent_ledgers[1], *[Path(row["result"]["ledger_path"]) for row in rows]]
        )
        self.assertEqual(len(reports), 2)
        for summary in reports:
            self.assertTrue(summary["complete"])
            self.assertEqual(summary["scheduled"], 234)
            self.assertEqual(summary["counts"]["correct"], 234)
            self.assertEqual(summary["attempt_count"], 234)
            self.assertEqual(summary["provider_cost_total"], Decimal("0.00234"))
            self.assertEqual(len(summary["extension_child_run_ids"]), 1)
            self.assertIn(
                f"{summary['parent_run_id'][:8]}+{summary['extension_child_run_ids'][0][:8]}",
                render_leaderboard([summary]),
            )
        self._assert_parent_hashes_unchanged()


if __name__ == "__main__":
    unittest.main()
