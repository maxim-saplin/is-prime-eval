"""Plan one immutable supplemental dataset and one child ledger per parent."""

from __future__ import annotations

from collections import Counter
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
from typing import Any, Mapping, Sequence

from cases import CASE_GENERATOR_VERSION, Case, generate_supplemental_cases
from events import ledger_lock, load_events
from model_specs import ModelSpec
from multi_run import ModelRunSpec
from openrouter import ModelInfo
from report import summarize_run
from runner import (
    PreparedDataset,
    RunConfig,
    _atomic_write_json,
    _case_record,
    _config_from_manifest,
    _load_dataset,
    _manifest_path,
    _model_info_from_dict,
    _sha256,
    _validate_manifest,
    prepare_case_dataset_from_cases,
)


@dataclass(frozen=True)
class ExtensionParent:
    ledger_path: Path
    manifest_path: Path
    manifest: Mapping[str, Any]
    config: RunConfig
    model_info: ModelInfo
    cases: tuple[Case, ...]
    summary: Mapping[str, Any]
    ledger_sha256: str
    manifest_sha256: str


@dataclass(frozen=True)
class ExtensionPlan:
    batch_id: str
    manifest: Mapping[str, Any]
    parents: tuple[ExtensionParent, ...]
    prepared_dataset: PreparedDataset
    specs: tuple[ModelRunSpec, ...]
    target_depths: tuple[int, ...]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parent_id(parent: ExtensionParent) -> str:
    return str(parent.summary["run_id"])


def _parent_ref(parent: ExtensionParent) -> dict[str, Any]:
    return {
        "run_id": _parent_id(parent),
        "ledger_file": parent.ledger_path.name,
        "manifest_file": parent.manifest_path.name,
        "ledger_sha256": parent.ledger_sha256,
        "manifest_sha256": parent.manifest_sha256,
        "config_sha256": parent.manifest["config_sha256"],
        "dataset_sha256": parent.manifest["dataset"]["sha256"],
    }


def select_parent_ledgers(
    *,
    results_dir: str | Path,
    model_specs: Sequence[ModelSpec] | None = None,
    parent_ledgers: Sequence[str | Path] | None = None,
) -> list[Path]:
    """Select parents only from explicit ledger paths or exact model/effort pairs."""
    root = Path(results_dir).resolve()
    explicit = [Path(path).resolve() for path in (parent_ledgers or [])]
    if explicit and model_specs:
        raise ValueError("use either --parent-ledger or Model ID/Effort selectors")
    if explicit:
        if len(set(explicit)) != len(explicit):
            raise ValueError("parent ledger paths must be unique")
        return explicit
    if not model_specs:
        raise ValueError("extension requires explicit parent ledgers or Model ID/Effort selectors")
    if not root.is_dir():
        raise NotADirectoryError(root)

    manifests = []
    for ledger in sorted(root.glob("*.jsonl")):
        manifest_path = _manifest_path(ledger)
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("extension") is None:
            manifests.append((ledger.resolve(), manifest))

    selected = []
    for spec in model_specs:
        matches = []
        for ledger, manifest in manifests:
            model, config = manifest.get("model", {}), manifest.get("config", {})
            model_id = model.get("model_id") or config.get("model_id")
            effort = model.get("reasoning_effort", config.get("reasoning_effort"))
            if (model_id, effort) == (spec.model_id, spec.reasoning_effort):
                matches.append(ledger)
        if len(matches) != 1:
            reason = "no" if not matches else "multiple"
            raise ValueError(f"{reason} base ledgers found for {spec.model_id}/{spec.reasoning_effort!r}")
        selected.append(matches[0])
    if len(set(selected)) != len(selected):
        raise ValueError("extension selectors must resolve to distinct parent ledgers")
    return selected


def _parent_settings(parent: ExtensionParent) -> tuple[Any, ...]:
    config, manifest = parent.config, parent.manifest
    return (
        config.depths,
        config.samples_per_class,
        config.samples_per_class_by_depth,
        config.seed,
        config.seed_source,
        config.max_attempts,
        config.retry_delay_seconds,
        config.timeout_seconds,
        config.max_completion_tokens,
        config.min_request_interval_seconds,
        manifest.get("prompt"),
        manifest.get("parser_version"),
        manifest["dataset"]["sha256"],
    )


def load_extension_parents(paths: Sequence[str | Path]) -> tuple[ExtensionParent, ...]:
    if not paths:
        raise ValueError("at least one parent ledger is required")
    parents = []
    for raw_path in paths:
        ledger = Path(raw_path).resolve()
        manifest_path = _manifest_path(ledger)
        if not ledger.is_file() or not manifest_path.is_file():
            raise FileNotFoundError(f"parent ledger/manifest missing: {ledger}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _validate_manifest(manifest)
        if manifest.get("extension") is not None:
            raise ValueError("select a base run, not an extension child, as the parent")
        if manifest.get("ledger_file") != ledger.name:
            raise ValueError(f"parent manifest points to a different ledger: {manifest_path}")
        load_events(ledger, repair_torn_tail=False)
        summary = summarize_run(ledger)
        config = _config_from_manifest(manifest)
        if not summary["complete"]:
            raise ValueError(f"parent run is incomplete: {ledger}")
        if config.max_completion_tokens is not None:
            raise ValueError(f"parent run has an explicit token cap: {ledger}")
        cases = tuple(_load_dataset(manifest_path, manifest["dataset"]))
        if len(cases) != summary["scheduled"]:
            raise ValueError(f"parent case count mismatch: {ledger}")
        parents.append(
            ExtensionParent(
                ledger_path=ledger,
                manifest_path=manifest_path,
                manifest=manifest,
                config=config,
                model_info=_model_info_from_dict(manifest["model"]),
                cases=cases,
                summary=summary,
                ledger_sha256=_file_sha256(ledger),
                manifest_sha256=_file_sha256(manifest_path),
            )
        )
    parents.sort(key=lambda p: (p.config.model_id, p.config.reasoning_effort or "", _parent_id(p)))
    identities = {(p.config.model_id, p.config.reasoning_effort) for p in parents}
    if len(identities) != len(parents):
        raise ValueError("parent Model ID/Effort identities must be unique")
    first = parents[0]
    if any(_parent_settings(p) != _parent_settings(first) or p.cases != first.cases for p in parents[1:]):
        raise ValueError("selected parents must share the same complete frozen dataset and settings")
    return tuple(parents)


@contextmanager
def locked_parents(parents: Sequence[ExtensionParent]):
    with ExitStack() as stack:
        for parent in sorted(parents, key=lambda p: str(p.ledger_path)):
            stack.enter_context(ledger_lock(parent.ledger_path))
        yield


def _batch_id(
    parents: Sequence[ExtensionParent], target: int, top_up: int, new_depth: int, seed: int | None
) -> str:
    return _sha256(
        {
            "parents": [_parent_ref(parent) for parent in parents],
            "target_depth": target,
            "top_up_per_class": top_up,
            "new_depths_per_class": new_depth,
            "requested_seed": seed,
        }
    )[:20]


def _load_prepared(root: Path, info: Mapping[str, Any]) -> PreparedDataset:
    anchor = root / "extension-plan-anchor.json"
    dataset_info = {key: info[key] for key in ("file", "dataset_id", "sha256", "case_count")}
    cases = tuple(_load_dataset(anchor, dataset_info))
    path = (root / str(info["file"])).resolve()
    return PreparedDataset(cases, path, json.loads(path.read_text(encoding="utf-8")))


def _dataset_info(root: Path, prepared: PreparedDataset) -> dict[str, Any]:
    payload = prepared.payload
    return {
        "file": str(prepared.path.relative_to(root)),
        "dataset_id": payload["dataset_id"],
        "sha256": payload["sha256"],
        "case_count": len(prepared.cases),
    }


def _target_dataset_hash(
    parent: ExtensionParent,
    prepared: PreparedDataset,
    *,
    target_depth: int,
    seed: int,
    seed_source: str,
    top_up_per_class: int,
    new_depths_per_class: int,
) -> tuple[str, str]:
    target_depths = list(range(min(parent.config.depths), target_depth + 1))
    old_depths = set(parent.config.depths)
    target_counts = {
        str(depth): (
            parent.config.samples_per_class + top_up_per_class
            if depth in old_depths
            else new_depths_per_class
        )
        for depth in target_depths
    }
    digest = _sha256(
        {
            "composition": "parent-plus-supplements-v1",
            "generator_version": CASE_GENERATOR_VERSION,
            "parent_dataset_sha256": parent.manifest["dataset"]["sha256"],
            "extension_seed": seed,
            "seed_source": seed_source,
            "top_up_per_class": top_up_per_class,
            "new_depths_per_class": new_depths_per_class,
            "depths": target_depths,
            "samples_per_class_by_depth": target_counts,
            "cases": [_case_record(case) for case in (*parent.cases, *prepared.cases)],
        }
    )
    return f"prime-extension-v1-{digest[:16]}", digest


def _child_metadata(parent: ExtensionParent, batch: Mapping[str, Any]) -> dict[str, Any]:
    parent_ref = _parent_ref(parent)
    return {
        "kind": "depth_extension",
        "extension_batch_id": batch["extension_batch_id"],
        "parent_run_id": parent_ref["run_id"],
        "parent_ledger_file": parent_ref["ledger_file"],
        "parent_ledger_sha256": parent_ref["ledger_sha256"],
        "parent_manifest_sha256": parent_ref["manifest_sha256"],
        "parent_config_sha256": parent_ref["config_sha256"],
        "parent_dataset_sha256": parent_ref["dataset_sha256"],
        "sampling_seed": batch["sampling_seed"],
        "seed_source": batch["seed_source"],
        "target_depth": batch["target_depth"],
        "target_depths": batch["target_depths"],
        "added_samples_per_class_by_depth": batch["added_samples_per_class_by_depth"],
        "target_dataset_id": batch["target_dataset_id"],
        "target_dataset_sha256": batch["target_dataset_sha256"],
        "target_samples_per_class": batch["target_samples_per_class"],
        "target_samples_by_depth": batch["target_samples_by_depth"],
        "supplement_dataset_id": batch["extension_dataset"]["dataset_id"],
        "supplement_dataset_sha256": batch["extension_dataset"]["sha256"],
    }


def _existing_child(root: Path, parent_id: str, batch_id: str) -> tuple[Path, dict[str, Any]] | None:
    matches = []
    for manifest_path in root.glob("*.manifest.json"):
        child = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata = child.get("extension")
        if not isinstance(metadata, Mapping) or metadata.get("parent_run_id") != parent_id:
            continue
        if metadata.get("kind") != "depth_extension":
            continue
        if metadata.get("extension_batch_id") != batch_id:
            raise ValueError(f"parent {parent_id} already has a different extension child")
        ledger_name = child.get("ledger_file") or manifest_path.name.removesuffix(".manifest.json") + ".jsonl"
        matches.append((manifest_path.with_name(str(ledger_name)), child))
    if len(matches) > 1:
        raise ValueError(f"multiple extension children found for parent {parent_id}")
    return matches[0] if matches else None


def _same_parent_refs(saved: Any, expected: Sequence[Mapping[str, Any]]) -> bool:
    return (
        isinstance(saved, list)
        and len(saved) == len(expected)
        and all(
            isinstance(old, Mapping)
            and all(old.get(key) == value for key, value in ref.items())
            for old, ref in zip(saved, expected)
        )
    )


def _saved_plan(
    root: Path,
    refs: Sequence[Mapping[str, Any]],
    target: int,
    top_up: int,
    new_depth: int,
    requested_seed: int | None,
) -> tuple[Path, dict[str, Any]] | None:
    matches = []
    for path in sorted(root.glob("extension-batch-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not _same_parent_refs(data.get("parents"), refs):
            continue
        if data.get("schema_version") != 1:
            raise ValueError(f"saved extension plan has an incompatible schema: {path}")
        settings = (
            data.get("target_depth"),
            data.get("top_up_per_class"),
            data.get("new_depths_per_class"),
            data.get("requested_seed"),
        )
        if settings != (target, top_up, new_depth, requested_seed):
            raise ValueError(f"saved extension plan settings differ from this preflight: {path}")
        matches.append((path, data))
    if len(matches) > 1:
        raise ValueError("multiple saved extension plans match the selected parent hashes")
    return matches[0] if matches else None


def _validate_saved_plan(
    batch: Mapping[str, Any],
    parents: Sequence[ExtensionParent],
    prepared: PreparedDataset,
    *,
    target_depth: int,
    top_up_per_class: int,
    new_depths_per_class: int,
    requested_seed: int | None,
) -> None:
    if not batch.get("extension_batch_id") or not isinstance(batch.get("extension_dataset"), Mapping):
        raise ValueError("saved extension plan is missing required provenance/dataset fields")
    parent = parents[0]
    parent_depths = tuple(parent.config.depths)
    target_depths = list(range(min(parent_depths), target_depth + 1))
    old_depths = set(parent_depths)
    added_counts = {
        str(depth): (top_up_per_class if depth in old_depths else new_depths_per_class)
        for depth in target_depths
        if (top_up_per_class if depth in old_depths else new_depths_per_class) > 0
    }
    target_counts = {
        str(depth): (
            parent.config.samples_per_class + top_up_per_class
            if depth in old_depths
            else new_depths_per_class
        )
        for depth in target_depths
    }
    seed = batch.get("sampling_seed")
    source = "explicit" if requested_seed is not None else "system_random"
    if isinstance(seed, bool) or not isinstance(seed, int) or batch.get("seed_source") != source:
        raise ValueError("saved extension plan has an invalid resolved seed/source")
    if requested_seed is not None and seed != requested_seed:
        raise ValueError("saved extension plan resolved seed differs from the requested seed")
    if (
        batch.get("target_depths") != target_depths
        or batch.get("added_samples_per_class_by_depth") != added_counts
        or batch.get("target_samples_by_depth") != target_counts
        or batch.get("added_case_count") != len(prepared.cases)
        or batch.get("target_case_count") != len(parent.cases) + len(prepared.cases)
    ):
        raise ValueError("saved extension plan counts/depths do not match the requested supplement")
    payload = prepared.payload
    if (
        payload.get("seed") != seed
        or payload.get("generator_version") != CASE_GENERATOR_VERSION
        or payload.get("samples_per_class_by_depth") != added_counts
        or payload.get("depths") != [int(depth) for depth in added_counts]
    ):
        raise ValueError("saved supplement dataset schema/counts/seed do not match its plan")
    top_up, new_cases = generate_supplemental_cases(
        parent.cases,
        target_depth=target_depth,
        existing_depths_per_class=top_up_per_class,
        new_depths_per_class=new_depths_per_class,
        seed=seed,
    )
    expected_cases = tuple(top_up + new_cases)
    if prepared.cases != expected_cases:
        raise ValueError("saved supplement does not reproduce from its seed or repeats parent cases")
    counts = Counter((case.depth, case.label) for case in prepared.cases)
    expected_counts = {
        (int(depth), label): count
        for depth, count in added_counts.items()
        for label in ("PRIME", "COMPOSITE")
    }
    if counts != expected_counts:
        raise ValueError("saved supplement has incorrect per-depth/class counts or labels")

    records = [_case_record(case) for case in (*parent.cases, *prepared.cases)]
    legacy_digest = _sha256(
        {
            "composition": "parent-plus-supplements-v1",
            "generator_version": CASE_GENERATOR_VERSION,
            "parent_dataset_sha256": parent.manifest["dataset"]["sha256"],
            "extension_seed": seed,
            "seed_source": source,
            "top_up_per_class": top_up_per_class,
            "new_depths_per_class": new_depths_per_class,
            "depths": target_depths,
            "samples_per_class_by_depth": target_counts,
            "cases": records,
        }
    )
    if (
        batch.get("target_dataset_sha256") != legacy_digest
        or batch.get("target_dataset_id") != f"prime-extension-v1-{legacy_digest[:16]}"
    ):
        raise ValueError("saved cumulative dataset hash/ID does not match its parent and supplement")


def prepare_extension_plan(
    *,
    results_dir: str | Path,
    parents: Sequence[ExtensionParent],
    target_depth: int,
    top_up_per_class: int,
    new_depths_per_class: int,
    requested_seed: int | None,
) -> ExtensionPlan:
    if not parents:
        raise ValueError("at least one parent run is required")
    parents = tuple(sorted(parents, key=lambda p: (p.config.model_id, p.config.reasoning_effort or "", _parent_id(p))))
    if isinstance(target_depth, bool) or not isinstance(target_depth, int) or not 1 <= target_depth <= 15:
        raise ValueError("extension target depth must be between 1 and 15")
    if isinstance(top_up_per_class, bool) or not isinstance(top_up_per_class, int) or top_up_per_class < 0:
        raise ValueError("top-up count must be a non-negative integer")
    if isinstance(new_depths_per_class, bool) or not isinstance(new_depths_per_class, int) or new_depths_per_class <= 0:
        raise ValueError("new-depth sample count must be a positive integer")
    if requested_seed is not None and (isinstance(requested_seed, bool) or not isinstance(requested_seed, int)):
        raise TypeError("explicit extension seed must be an integer")
    parent_depths = tuple(parents[0].config.depths)
    if target_depth < max(parent_depths) or any(tuple(p.config.depths) != parent_depths for p in parents):
        raise ValueError("extension target must cover the same parent depth set")

    root = Path(results_dir).resolve()
    refs = [_parent_ref(parent) for parent in parents]
    saved_plan = _saved_plan(
        root, refs, target_depth, top_up_per_class, new_depths_per_class, requested_seed
    )
    computed_id = _batch_id(parents, target_depth, top_up_per_class, new_depths_per_class, requested_seed)
    batch_id = str(saved_plan[1]["extension_batch_id"]) if saved_plan else computed_id
    existing_children = {
        _parent_id(parent): _existing_child(root, _parent_id(parent), batch_id)
        for parent in parents
    }
    plan_path = saved_plan[0] if saved_plan else root / f"extension-batch-{batch_id}.json"
    if saved_plan:
        batch = saved_plan[1]
        prepared = _load_prepared(root, batch["extension_dataset"])
        _validate_saved_plan(
            batch,
            parents,
            prepared,
            target_depth=target_depth,
            top_up_per_class=top_up_per_class,
            new_depths_per_class=new_depths_per_class,
            requested_seed=requested_seed,
        )
    elif plan_path.is_file():
        raise ValueError(f"extension plan with mismatched parent/settings already exists: {plan_path}")
    else:
        seed = requested_seed if requested_seed is not None else secrets.randbits(64)
        seed_source = "explicit" if requested_seed is not None else "system_random"
        top_up, new_cases = generate_supplemental_cases(
            parents[0].cases,
            target_depth=target_depth,
            existing_depths_per_class=top_up_per_class,
            new_depths_per_class=new_depths_per_class,
            seed=seed,
        )
        added = top_up + new_cases
        if not added:
            raise ValueError("extension adds no cases")
        target_depths = list(range(min(parent_depths), target_depth + 1))
        old_depths = set(parent_depths)
        added_counts = {
            depth: (top_up_per_class if depth in old_depths else new_depths_per_class)
            for depth in target_depths
            if (top_up_per_class if depth in old_depths else new_depths_per_class) > 0
        }
        child_config = replace(
            parents[0].config,
            depths=tuple(added_counts),
            samples_per_class=max(added_counts.values()),
            samples_per_class_by_depth=added_counts,
            seed=seed,
            seed_source=seed_source,
        )
        prepared = prepare_case_dataset_from_cases(
            results_dir=root, config=child_config, cases=added
        )
        target_samples = {
            str(depth): parents[0].config.samples_per_class + top_up_per_class
            if depth in old_depths
            else new_depths_per_class
            for depth in target_depths
        }
        target_id, target_sha = _target_dataset_hash(
            parents[0],
            prepared,
            target_depth=target_depth,
            seed=seed,
            seed_source=seed_source,
            top_up_per_class=top_up_per_class,
            new_depths_per_class=new_depths_per_class,
        )
        sample_values = set(target_samples.values())
        batch = {
            "schema_version": 1,
            "extension_batch_id": batch_id,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "parents": refs,
            "requested_seed": requested_seed,
            "sampling_seed": seed,
            "seed_source": seed_source,
            "target_depth": target_depth,
            "target_depths": target_depths,
            "top_up_per_class": top_up_per_class,
            "new_depths_per_class": new_depths_per_class,
            "added_samples_per_class_by_depth": {str(k): v for k, v in added_counts.items()},
            "target_samples_by_depth": target_samples,
            "target_samples_per_class": next(iter(sample_values)) if len(sample_values) == 1 else None,
            "target_dataset_id": target_id,
            "target_dataset_sha256": target_sha,
            "added_case_count": len(added),
            "target_case_count": len(parents[0].cases) + len(added),
            "extension_dataset": _dataset_info(root, prepared),
        }
        _atomic_write_json(plan_path, batch)

    specs = []
    for parent in parents:
        metadata = _child_metadata(parent, batch)
        existing = existing_children[_parent_id(parent)]
        if existing is None:
            config = replace(
                parent.config,
                depths=tuple(int(depth) for depth in batch["added_samples_per_class_by_depth"]),
                samples_per_class=max(int(count) for count in batch["added_samples_per_class_by_depth"].values()),
                samples_per_class_by_depth={
                    int(depth): int(count)
                    for depth, count in batch["added_samples_per_class_by_depth"].items()
                },
                seed=int(batch["sampling_seed"]),
                seed_source=str(batch["seed_source"]),
            )
            specs.append(ModelRunSpec(config=config, model_info=parent.model_info, extension_metadata=metadata))
            continue
        ledger, manifest = existing
        if not ledger.is_file():
            raise FileNotFoundError(f"extension child ledger missing: {ledger}")
        _validate_manifest(manifest)
        if manifest.get("extension") != metadata:
            raise ValueError(f"extension child provenance mismatch: {ledger}")
        config = _config_from_manifest(manifest)
        expected_counts = {int(depth): int(count) for depth, count in batch["added_samples_per_class_by_depth"].items()}
        if (
            config.model_id != parent.config.model_id
            or config.reasoning_effort != parent.config.reasoning_effort
            or config.depths != tuple(expected_counts)
            or config.samples_per_class != max(expected_counts.values())
            or config.samples_per_class_by_depth != expected_counts
            or config.seed != int(batch["sampling_seed"])
            or config.seed_source != batch["seed_source"]
        ):
            raise ValueError(f"extension child configuration mismatch: {ledger}")
        specs.append(
            ModelRunSpec(
                config=config,
                model_info=parent.model_info,
                extension_metadata=metadata,
                resume_ledger_path=ledger,
            )
        )

    return ExtensionPlan(batch_id, batch, tuple(parents), prepared, tuple(specs), tuple(batch["target_depths"]))
