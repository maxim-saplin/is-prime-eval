"""Evaluation orchestration, immutable run manifests and resumable request ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from cases import CASE_GENERATOR_VERSION, Case, generate_cases
from costs import (
    decimal_text,
    estimate_uncached_cost_usd,
    extract_provider_cost_usd,
    extract_usage,
)
from events import append_event, ledger_lock, load_events
from openrouter import ModelInfo, OpenRouterClient, OpenRouterError
from parse import parse_response
from prompt import make_prompt

DEFAULT_DEPTHS = tuple(range(4, 11))
DEFAULT_SAMPLES_PER_CLASS = 10
DEFAULT_SEED = 2026
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 90.0
DEFAULT_MAX_COMPLETION_TOKENS = 512
RUN_SCHEMA_VERSION = 1
DATASET_SCHEMA_VERSION = 1
PROMPT_VERSION = "prime-label-v1"
PARSER_VERSION = "bare-prime-composite-v1"
PROMPT_TEMPLATE = "Is {number} prime? Reply with only PRIME or COMPOSITE."

ProgressCallback = Callable[[dict[str, Any]], None]


class EvaluationInterrupted(KeyboardInterrupt):
    """Ctrl-C stopped a run after its ledger was safely paused."""

    def __init__(self, ledger_path: str | Path):
        self.ledger_path = str(Path(ledger_path).resolve())
        self.manifest_path = str(_manifest_path(Path(self.ledger_path)))
        super().__init__(f"evaluation paused; resume with --resume {self.ledger_path}")


@dataclass(frozen=True)
class PreparedDataset:
    """Frozen case list/manifests shared by every model in one batch."""

    cases: tuple[Case, ...]
    path: Path
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class RunConfig:
    model_id: str
    reasoning_effort: str
    depths: tuple[int, ...] = DEFAULT_DEPTHS
    samples_per_class: int = DEFAULT_SAMPLES_PER_CLASS
    seed: int = DEFAULT_SEED
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS

    def validate(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ValueError("model_id must be an explicit non-empty OpenRouter model ID")
        if "/" not in self.model_id or self.model_id.startswith("/") or self.model_id.endswith("/"):
            raise ValueError("model_id must be fully qualified (provider/model)")
        if any(character.isspace() for character in self.model_id):
            raise ValueError("model_id must not contain whitespace")
        if not self.depths or any(depth < 1 or depth > 10 for depth in self.depths):
            raise ValueError("depths must be between 1 and 10")
        if len(set(self.depths)) != len(self.depths):
            raise ValueError("depths must not contain duplicates")
        if self.samples_per_class <= 0:
            raise ValueError("samples_per_class must be positive")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_completion_tokens <= 0:
            raise ValueError("max_completion_tokens must be positive")
        if (
            not isinstance(self.reasoning_effort, str)
            or not self.reasoning_effort
            or self.reasoning_effort != self.reasoning_effort.strip()
            or any(character.isspace() for character in self.reasoning_effort)
        ):
            raise ValueError("reasoning_effort must be explicitly specified as a non-empty value")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _case_record(case: Case) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "depth": case.depth,
        "number": case.number,
        "label": case.label,
    }


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    encoded = (json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n").encode("utf-8")
    fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        view = memoryview(encoded)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("failed to write run manifest")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temp_path, path)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _write_or_verify_dataset(
    results_dir: Path, cases: Sequence[Case], config: RunConfig
) -> tuple[Path, dict[str, Any]]:
    records = [_case_record(case) for case in cases]
    content_hash = _sha256(
        {
            "schema_version": DATASET_SCHEMA_VERSION,
            "generator_version": CASE_GENERATOR_VERSION,
            "seed": config.seed,
            "depths": list(config.depths),
            "samples_per_class": config.samples_per_class,
            "cases": records,
        }
    )
    dataset_id = f"prime-{CASE_GENERATOR_VERSION}-{content_hash[:16]}"
    dataset_dir = results_dir / "datasets"
    dataset_path = dataset_dir / f"{dataset_id}.json"
    dataset_payload = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "sha256": content_hash,
        "generator_version": CASE_GENERATOR_VERSION,
        "seed": config.seed,
        "depths": list(config.depths),
        "samples_per_class": config.samples_per_class,
        "cases": records,
    }
    if dataset_path.exists():
        existing = json.loads(dataset_path.read_text(encoding="utf-8"))
        if existing.get("sha256") != content_hash or existing.get("cases") != records:
            raise ValueError(f"existing dataset manifest does not match: {dataset_path}")
    else:
        _atomic_write_json(dataset_path, dataset_payload)
    return dataset_path, dataset_payload


def _manifest_path(ledger_path: Path) -> Path:
    return ledger_path.with_name(f"{ledger_path.stem}.manifest.json")


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug[:100] or "model"


def _model_info_to_dict(model_info: ModelInfo) -> dict[str, Any]:
    return {
        "model_id": model_info.model_id,
        "name": model_info.name,
        "prompt_rate_usd_per_million": decimal_text(
            model_info.prompt_rate_usd_per_million
        ),
        "completion_rate_usd_per_million": decimal_text(
            model_info.completion_rate_usd_per_million
        ),
        "pricing_source": model_info.pricing_source,
        "pricing_retrieved_at": model_info.pricing_retrieved_at,
        "supported_parameters": list(model_info.supported_parameters),
    }


def _model_info_from_dict(data: Mapping[str, Any]) -> ModelInfo:
    prompt_rate = data.get("prompt_rate_usd_per_million")
    completion_rate = data.get("completion_rate_usd_per_million")
    model_id = str(data.get("model_id") or data.get("requested_id") or "")
    return ModelInfo(
        requested_id=model_id,
        model_id=model_id,
        name=str(data.get("name", "")),
        prompt_rate_usd_per_million=(Decimal(prompt_rate) if prompt_rate is not None else None),
        completion_rate_usd_per_million=(
            Decimal(completion_rate) if completion_rate is not None else None
        ),
        pricing_source=str(data.get("pricing_source", "")),
        pricing_retrieved_at=str(data.get("pricing_retrieved_at", "")),
        supported_parameters=tuple(data.get("supported_parameters", [])),
    )


def _make_manifest(
    *,
    run_id: str,
    config: RunConfig,
    model_info: ModelInfo,
    dataset_path: Path,
    dataset_payload: Mapping[str, Any],
    ledger_path: Path,
) -> dict[str, Any]:
    if model_info.prompt_rate_usd_per_million is None or model_info.completion_rate_usd_per_million is None:
        raise ValueError(
            "OpenRouter did not provide both input and output rates; cannot start a run "
            "with the required estimated-cost accounting"
        )
    config.validate()
    if config.model_id != model_info.model_id:
        raise ValueError("model_id in run config does not match resolved OpenRouter model")
    OpenRouterClient.validate_reasoning_effort(model_info, config.reasoning_effort)
    try:
        dataset_ref = dataset_path.relative_to(ledger_path.parent)
    except ValueError:
        dataset_ref = Path(os.path.relpath(dataset_path, ledger_path.parent))
    manifest: dict[str, Any] = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": _utc_now(),
        "model": {
            **_model_info_to_dict(model_info),
            "reasoning_effort": config.reasoning_effort,
        },
        "config": {
            **asdict(config),
            "depths": list(config.depths),
        },
        "prompt": {"version": PROMPT_VERSION, "template": PROMPT_TEMPLATE},
        "parser_version": PARSER_VERSION,
        "dataset": {
            "dataset_id": dataset_payload["dataset_id"],
            "sha256": dataset_payload["sha256"],
            "file": str(dataset_ref),
            "case_count": len(dataset_payload["cases"]),
            "generator_version": CASE_GENERATOR_VERSION,
            "seed": config.seed,
            "depths": list(config.depths),
            "samples_per_class": config.samples_per_class,
        },
        "pricing": {
            "source": model_info.pricing_source,
            "retrieved_at": model_info.pricing_retrieved_at,
            "model_id": model_info.model_id,
            "prompt_rate_usd_per_million": decimal_text(
                model_info.prompt_rate_usd_per_million
            ),
            "completion_rate_usd_per_million": decimal_text(
                model_info.completion_rate_usd_per_million
            ),
        },
        "ledger_file": ledger_path.name,
    }
    fingerprint_payload = {
        "model_id": manifest["model"]["model_id"],
        "reasoning_effort": config.reasoning_effort,
        "config": manifest["config"],
        "prompt": manifest["prompt"],
        "parser_version": manifest["parser_version"],
        "dataset_sha256": manifest["dataset"]["sha256"],
        "pricing": manifest["pricing"],
    }
    manifest["config_sha256"] = _sha256(fingerprint_payload)
    return manifest


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError("unsupported run manifest schema version")
    model = manifest.get("model")
    config = manifest.get("config")
    prompt = manifest.get("prompt")
    dataset = manifest.get("dataset")
    pricing = manifest.get("pricing")
    if not all(isinstance(item, Mapping) for item in (model, config, prompt, dataset, pricing)):
        raise ValueError("run manifest is missing required configuration")
    model_id = model.get("model_id") or model.get("requested_id")
    effort = model.get("reasoning_effort") or config.get("reasoning_effort")
    if not isinstance(model_id, str) or "/" not in model_id:
        raise ValueError("saved run has no fully qualified model ID")
    if not isinstance(effort, str) or not effort or effort != effort.strip() or any(ch.isspace() for ch in effort):
        raise ValueError("saved run has no explicit non-empty reasoning effort")
    expected_payload = {
        "model_id": model_id,
        "reasoning_effort": effort,
        "config": config,
        "prompt": prompt,
        "parser_version": manifest.get("parser_version"),
        "dataset_sha256": dataset.get("sha256"),
        "pricing": pricing,
    }
    # Read old manifests from the first MVP release, where display_model was
    # part of the config hash. New manifests keep model ID and effort separate.
    if "display_model" in manifest:
        expected_payload["display_model"] = manifest.get("display_model")
    if manifest.get("config_sha256") != _sha256(expected_payload):
        raise ValueError("run manifest configuration hash mismatch; refusing resume")
    if prompt.get("version") != PROMPT_VERSION or manifest.get("parser_version") != PARSER_VERSION:
        raise ValueError("prompt/parser version mismatch; refusing resume")


def _load_dataset(manifest_path: Path, dataset_info: Mapping[str, Any]) -> list[Case]:
    dataset_path = (manifest_path.parent / str(dataset_info.get("file", ""))).resolve()
    if not dataset_path.is_file():
        raise FileNotFoundError(f"saved dataset manifest is missing: {dataset_path}")
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    if data.get("dataset_id") != dataset_info.get("dataset_id"):
        raise ValueError("dataset ID mismatch; refusing resume")
    if data.get("sha256") != dataset_info.get("sha256"):
        raise ValueError("dataset hash mismatch; refusing resume")
    cases = [
        Case(
            case_id=str(row["case_id"]),
            depth=int(row["depth"]),
            number=int(row["number"]),
            label=str(row["label"]),
        )
        for row in data.get("cases", [])
    ]
    if len(cases) != int(dataset_info.get("case_count", -1)):
        raise ValueError("saved dataset case count mismatch; refusing resume")
    if _sha256(
        {
            "schema_version": DATASET_SCHEMA_VERSION,
            "generator_version": data.get("generator_version"),
            "seed": data.get("seed"),
            "depths": data.get("depths"),
            "samples_per_class": data.get("samples_per_class"),
            "cases": [_case_record(case) for case in cases],
        }
    ) != dataset_info.get("sha256"):
        raise ValueError("saved dataset contents do not match their hash")
    return cases


def _config_from_manifest(manifest: Mapping[str, Any]) -> RunConfig:
    config = manifest["config"]
    model = manifest.get("model", {})
    model_id = str(config.get("model_id") or model.get("model_id") or config.get("requested_model") or "")
    effort = config.get("reasoning_effort") or model.get("reasoning_effort")
    return RunConfig(
        model_id=model_id,
        reasoning_effort=effort,
        depths=tuple(int(depth) for depth in config["depths"]),
        samples_per_class=int(config["samples_per_class"]),
        seed=int(config["seed"]),
        max_attempts=int(config["max_attempts"]),
        retry_delay_seconds=float(config["retry_delay_seconds"]),
        timeout_seconds=float(config["timeout_seconds"]),
        max_completion_tokens=int(config["max_completion_tokens"]),
    )


def _validate_resume_overrides(
    manifest: Mapping[str, Any], overrides: Mapping[str, Any] | None
) -> None:
    if not overrides:
        return
    config = manifest["config"]
    model = manifest["model"]
    saved_model_id = str(config.get("model_id") or model.get("model_id") or config.get("requested_model") or "")
    checks = {
        "model_id": (overrides.get("model_id"), saved_model_id),
        "reasoning_effort": (
            overrides.get("reasoning_effort"),
            config.get("reasoning_effort"),
        ),
        "depths": (
            tuple(overrides["depths"]) if overrides.get("depths") is not None else None,
            tuple(config.get("depths", [])),
        ),
        "samples_per_class": (
            overrides.get("samples_per_class"),
            config.get("samples_per_class"),
        ),
        "seed": (overrides.get("seed"), config.get("seed")),
        "max_attempts": (
            overrides.get("max_attempts"),
            config.get("max_attempts"),
        ),
        "max_completion_tokens": (
            overrides.get("max_completion_tokens"),
            config.get("max_completion_tokens"),
        ),
    }
    for name, (provided, recorded) in checks.items():
        if provided is not None and provided != recorded:
            raise ValueError(
                f"resume {name} mismatch: saved run has {recorded!r}, "
                f"requested {provided!r}"
            )
    if model.get("model_id") != manifest["pricing"].get("model_id"):
        raise ValueError("saved model and pricing snapshot do not match; refusing resume")


def _new_ledger_path(results_dir: Path, model_id: str, reasoning_effort: str) -> Path:
    root = results_dir.resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    model_slug = _safe_slug(model_id)
    effort_slug = _safe_slug(reasoning_effort)[:48] or "effort"
    effort_hash = hashlib.sha256(reasoning_effort.encode("utf-8")).hexdigest()[:10]
    path = root / f"{model_slug}__effort-{effort_slug}-{effort_hash}_{stamp}_{uuid4().hex[:8]}.jsonl"
    if path.parent != root:
        raise ValueError("generated run ledger path escaped the results directory")
    return path


def _extract_response_text(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
        return ""
    message = choices[0].get("message")
    if not isinstance(message, Mapping):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, Mapping) and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
        return "".join(text_parts)
    refusal = message.get("refusal")
    return refusal if isinstance(refusal, str) else ""


def _events_state(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    started: dict[str, Mapping[str, Any]] = {}
    completed_attempts: set[str] = set()
    attempts_by_case: dict[str, list[Mapping[str, Any]]] = {}
    terminal_cases: dict[str, Mapping[str, Any]] = {}
    finished = False
    for event in events:
        event_type = event.get("event_type")
        attempt_id = event.get("attempt_id")
        case_id = str(event.get("case_id", ""))
        if event_type == "attempt_started" and attempt_id:
            started[str(attempt_id)] = event
            attempts_by_case.setdefault(case_id, []).append(event)
        elif event_type in {
            "attempt_response",
            "attempt_failed",
            "attempt_interrupted",
            "attempt_cancelled_before_dispatch",
        } and attempt_id:
            completed_attempts.add(str(attempt_id))
            if event_type == "attempt_response":
                terminal_cases[case_id] = event
        elif event_type == "case_terminal":
            terminal_cases[case_id] = event
        elif event_type == "run_finished":
            finished = True
    cancelled_before_dispatch = {
        str(event.get("attempt_id"))
        for event in events
        if event.get("event_type") == "attempt_cancelled_before_dispatch"
        and event.get("attempt_id")
    }
    attempts_by_case = {
        case_id: [
            attempt for attempt in attempts
            if str(attempt.get("attempt_id")) not in cancelled_before_dispatch
        ]
        for case_id, attempts in attempts_by_case.items()
    }
    return {
        "started": started,
        "completed_attempts": completed_attempts,
        "attempts_by_case": attempts_by_case,
        "terminal_cases": terminal_cases,
        "finished": finished,
    }


def _append_orphan_attempts(
    ledger_path: Path, run_id: str, events: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    state = _events_state(events)
    for attempt_id, start_event in state["started"].items():
        if attempt_id in state["completed_attempts"]:
            continue
        event = append_event(
            ledger_path,
            {
                "event_type": "attempt_interrupted",
                "run_id": run_id,
                "case_id": start_event.get("case_id"),
                "trial_id": start_event.get("trial_id"),
                "attempt_id": attempt_id,
                "attempt_number": start_event.get("attempt_number"),
                "reason": "no finish event persisted before process interruption",
                "spend_status": "unknown",
                "provider_reported_usd": None,
                "normalized_uncached_usd": None,
                "may_have_been_billed": True,
            },
        )
        events.append(event)
    return events


def _write_run_created(
    ledger_path: Path,
    manifest: Mapping[str, Any],
) -> None:
    append_event(
        ledger_path,
        {
            "event_type": "run_created",
            "run_id": manifest["run_id"],
            "model_id": manifest["model"]["model_id"],
            "reasoning_effort": manifest["model"]["reasoning_effort"],
            "dataset_id": manifest["dataset"]["dataset_id"],
            "scheduled_cases": manifest["dataset"]["case_count"],
            "config_sha256": manifest["config_sha256"],
        },
    )


def _record_response(
    *,
    client: OpenRouterClient,
    ledger_path: Path,
    case: Case,
    config: RunConfig,
    model_info: ModelInfo,
    run_id: str,
    attempt_id: str,
    attempt_number: int,
    response: Mapping[str, Any],
    started_at: str,
    started_monotonic: float,
) -> dict[str, Any]:
    raw_response = _extract_response_text(response)
    choices = response.get("choices")
    first_choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], Mapping) else {}
    finish_reason = first_choice.get("finish_reason")
    native_finish_reason = first_choice.get("native_finish_reason")
    truncated = str(finish_reason).lower() in {
        "length", "max_tokens", "max_completion_tokens", "token_limit"
    }
    parsed_label = None if truncated else parse_response(raw_response)
    correct = parsed_label == case.label if parsed_label is not None else False
    message = first_choice.get("message") if isinstance(first_choice, Mapping) else None
    refusal = message.get("refusal") if isinstance(message, Mapping) else None
    invalid_reason = (
        "completion_truncated"
        if truncated
        else "refusal"
        if parsed_label is None and refusal
        else "unparseable_response"
        if parsed_label is None
        else None
    )
    outcome = (
        "invalid_response"
        if parsed_label is None
        else "correct"
        if correct
        else "wrong_label"
    )
    usage = extract_usage(response)
    provider_cost = extract_provider_cost_usd(response)
    normalized_cost = estimate_uncached_cost_usd(
        usage,
        model_info.prompt_rate_usd_per_million,
        model_info.completion_rate_usd_per_million,
    )
    response_id = response.get("id")
    choice_metadata = {
        key: value
        for key, value in first_choice.items()
        if key not in {"message", "delta"}
    } if isinstance(first_choice, Mapping) else {}
    message = first_choice.get("message") if isinstance(first_choice, Mapping) else None
    if isinstance(message, Mapping):
        # Keep response/choice metadata, but do not persist hidden reasoning or
        # duplicate the visible message body; raw_response stores only content.
        choice_metadata["message_metadata"] = {
            key: value
            for key, value in message.items()
            if key not in {"content", "reasoning", "thinking"}
        }
    response_metadata = {
        "id": response.get("id"),
        "created": response.get("created"),
        "object": response.get("object"),
        "model": response.get("model"),
        "provider": response.get("provider"),
        "choices": [choice_metadata],
    }
    response_event = append_event(
        ledger_path,
        {
            "event_type": "attempt_response",
            "run_id": run_id,
            "trial_id": case.case_id,
            "case_id": case.case_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "depth": case.depth,
            "number": case.number,
            "gold_label": case.label,
            "model_id": model_info.model_id,
            "reasoning_effort": config.reasoning_effort,
            "returned_model": response.get("model"),
            "provider_route": response.get("provider") or response.get("provider_name"),
            "response_metadata": response_metadata,
            "prompt_version": PROMPT_VERSION,
            "raw_response": raw_response,
            "parsed_label": parsed_label,
            "correct": correct,
            "outcome": outcome,
            "invalid_reason": invalid_reason,
            "finish_reason": finish_reason,
            "native_finish_reason": native_finish_reason,
            "usage": usage,
            "raw_usage": response.get("usage"),
            "provider_reported_usd": decimal_text(provider_cost),
            "normalized_uncached_usd": decimal_text(normalized_cost),
            "pricing_model_id": model_info.model_id,
            "prompt_rate_usd_per_million": decimal_text(
                model_info.prompt_rate_usd_per_million
            ),
            "completion_rate_usd_per_million": decimal_text(
                model_info.completion_rate_usd_per_million
            ),
            "request_id": response_id,
            "started_at": started_at,
            "latency_seconds": round(time.monotonic() - started_monotonic, 6),
            "reasoning_effort": config.reasoning_effort,
            "spend_status": "reported" if provider_cost is not None else "provider_cost_missing",
        },
    )

    # Persist the answer first. Look up generation details inline only when the
    # completion omitted cost/model/route; otherwise enrich after the run so an
    # eventually-consistent metadata endpoint does not slow every inference.
    if response_id and (
        provider_cost is None
        or not response.get("model")
        or not (response.get("provider") or response.get("provider_name"))
    ):
        try:
            generation = client.generation_details(str(response_id))
            updated_usage = extract_usage(response, generation)
            updated_provider_cost = extract_provider_cost_usd(response, generation)
            updated_normalized_cost = estimate_uncached_cost_usd(
                updated_usage,
                model_info.prompt_rate_usd_per_million,
                model_info.completion_rate_usd_per_million,
            )
            gen_data = generation.get("data") if isinstance(generation.get("data"), Mapping) else {}
            append_event(
                ledger_path,
                {
                    "event_type": "attempt_cost_update",
                    "run_id": run_id,
                    "case_id": case.case_id,
                    "trial_id": case.case_id,
                    "attempt_id": attempt_id,
                    "provider_reported_usd": decimal_text(updated_provider_cost),
                    "normalized_uncached_usd": decimal_text(updated_normalized_cost),
                    "usage": updated_usage,
                    "provider_route": gen_data.get("provider_name"),
                    "returned_model": gen_data.get("model") or response.get("model"),
                    "generation_metadata": generation,
                    "spend_status": (
                        "reported" if updated_provider_cost is not None else "provider_cost_missing"
                    ),
                },
            )
        except Exception as exc:  # Metadata lookup must never retry a paid completion.
            append_event(
                ledger_path,
                {
                    "event_type": "cost_lookup_failed",
                    "run_id": run_id,
                    "case_id": case.case_id,
                    "attempt_id": attempt_id,
                    "error_type": type(exc).__name__,
                    "provider_reported_usd": decimal_text(provider_cost),
                    "normalized_uncached_usd": decimal_text(normalized_cost),
                },
            )
    return response_event


def _execute_run(
    *,
    client: OpenRouterClient,
    ledger_path: Path,
    manifest: dict[str, Any],
    cases: Sequence[Case],
    config: RunConfig,
    model_info: ModelInfo,
    events: list[dict[str, Any]],
    on_progress: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    run_id = str(manifest["run_id"])
    events = _append_orphan_attempts(ledger_path, run_id, events)
    state = _events_state(events)
    terminal_cases = dict(state["terminal_cases"])
    progress_counts = _basic_counts(cases, terminal_cases)
    if on_progress:
        on_progress(
            {
                "event": "run_progress_init",
                "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                "total_cases": len(cases),
                "completed_cases": len(terminal_cases),
                "correct": progress_counts["correct"],
                "incorrect": progress_counts["incorrect"],
            }
        )
    if state["finished"]:
        return {
            "ledger_path": str(ledger_path),
            "manifest_path": str(_manifest_path(ledger_path)),
            "run_id": run_id,
            "complete": True,
            "already_finished": True,
            "scheduled_cases": len(cases),
            "terminal_cases": len(terminal_cases),
            "summary": progress_counts,
        }

    append_event(
        ledger_path,
        {
            "event_type": "run_resumed" if any(e.get("event_type") == "run_paused" for e in events) else "run_started",
            "run_id": run_id,
        },
    )
    state = _events_state(events)
    terminal_cases = dict(state["terminal_cases"])
    attempts_by_case = state["attempts_by_case"]
    config_dict = manifest["config"]
    max_attempts = int(config_dict["max_attempts"])
    retry_delay = float(config_dict["retry_delay_seconds"])

    try:
        for case in cases:
            if cancel_event is not None and cancel_event.is_set():
                break
            if case.case_id in terminal_cases:
                continue
            prior_attempts = list(attempts_by_case.get(case.case_id, []))
            next_attempt = len(prior_attempts) + 1
            previous_error: Mapping[str, Any] | None = None
            for event in reversed(events):
                if event.get("case_id") == case.case_id and event.get("event_type") in {
                    "attempt_failed",
                    "attempt_interrupted",
                }:
                    previous_error = event
                    break
            if previous_error and previous_error.get("event_type") == "attempt_failed" and not previous_error.get("retryable", False):
                append_event(
                    ledger_path,
                    {
                        "event_type": "case_terminal",
                        "run_id": run_id,
                        "case_id": case.case_id,
                        "trial_id": case.case_id,
                        "outcome": "no_response",
                        "reason": previous_error.get("error_type", "non-retryable provider error"),
                        "attempt_count": len(prior_attempts),
                    },
                )
                if on_progress:
                    on_progress({"event": "case_finished", "model_id": config.model_id, "reasoning_effort": config.reasoning_effort, "case_id": case.case_id, "outcome": "no_response", "completion_tokens": 0, "total_cases": len(cases)})
                continue
            if next_attempt > max_attempts:
                append_event(
                    ledger_path,
                    {
                        "event_type": "case_terminal",
                        "run_id": run_id,
                        "case_id": case.case_id,
                        "trial_id": case.case_id,
                        "outcome": "no_response",
                        "reason": "maximum attempts already reached",
                        "attempt_count": len(prior_attempts),
                    },
                )
                if on_progress:
                    on_progress({"event": "case_finished", "model_id": config.model_id, "reasoning_effort": config.reasoning_effort, "case_id": case.case_id, "outcome": "no_response", "completion_tokens": 0, "total_cases": len(cases)})
                continue

            while next_attempt <= max_attempts:
                if cancel_event is not None and cancel_event.is_set():
                    break
                attempt_id = uuid4().hex
                prompt_text = make_prompt(case.number)
                attempt_started_at = _utc_now()
                attempt_started_monotonic = time.monotonic()
                append_event(
                    ledger_path,
                    {
                        "event_type": "attempt_started",
                        "run_id": run_id,
                        "trial_id": case.case_id,
                        "case_id": case.case_id,
                        "attempt_id": attempt_id,
                        "attempt_number": next_attempt,
                        "depth": case.depth,
                        "number": case.number,
                        "gold_label": case.label,
                        "model_id": config.model_id,
                        "reasoning_effort": config.reasoning_effort,
                        "prompt_version": PROMPT_VERSION,
                        "prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
                    },
                )
                if on_progress:
                    on_progress(
                        {
                            "event": "attempt_started",
                            "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                            "case_id": case.case_id,
                            "attempt_number": next_attempt,
                            "max_attempts": max_attempts,
                            "total_cases": len(cases),
                        }
                    )
                if cancel_event is not None and cancel_event.is_set():
                    append_event(
                        ledger_path,
                        {
                            "event_type": "attempt_cancelled_before_dispatch",
                            "run_id": run_id,
                            "trial_id": case.case_id,
                            "case_id": case.case_id,
                            "attempt_id": attempt_id,
                            "attempt_number": next_attempt,
                            "may_have_been_billed": False,
                            "spend_status": "not_dispatched",
                            "reason": "cancel requested before HTTP dispatch",
                        },
                    )
                    if on_progress:
                        on_progress(
                            {
                                "event": "attempt_cancelled_before_dispatch",
                                "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                                "case_id": case.case_id,
                                "attempt_number": next_attempt,
                                "total_cases": len(cases),
                            }
                        )
                    break
                try:
                    response = client.complete(
                        model_info.model_id,
                        prompt_text,
                        reasoning_effort=config.reasoning_effort,
                        max_completion_tokens=config.max_completion_tokens,
                    )
                except OpenRouterError as exc:
                    error_payload = exc.response_payload or {}
                    error_usage = extract_usage(error_payload)
                    error_provider_cost = extract_provider_cost_usd(error_payload)
                    error_normalized_cost = estimate_uncached_cost_usd(
                        error_usage,
                        model_info.prompt_rate_usd_per_million,
                        model_info.completion_rate_usd_per_million,
                    )
                    append_event(
                        ledger_path,
                        {
                            "event_type": "attempt_failed",
                            "run_id": run_id,
                            "trial_id": case.case_id,
                            "case_id": case.case_id,
                            "attempt_id": attempt_id,
                            "attempt_number": next_attempt,
                            "status_code": exc.status_code,
                            "retryable": exc.retryable,
                            "may_have_been_billed": exc.may_have_been_billed,
                            "spend_status": (
                                "reported" if error_provider_cost is not None
                                else "unknown" if exc.may_have_been_billed
                                else "not_reported"
                            ),
                            "provider_reported_usd": decimal_text(error_provider_cost),
                            "normalized_uncached_usd": decimal_text(error_normalized_cost),
                            "usage": error_usage,
                            "raw_usage": error_payload.get("usage"),
                            "raw_error_response": error_payload or None,
                            "request_id": error_payload.get("id"),
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "latency_seconds": round(time.monotonic() - attempt_started_monotonic, 6),
                        },
                    )
                    if on_progress:
                        error_tokens = error_usage.get("completion_tokens")
                        on_progress(
                            {
                                "event": "attempt_failed",
                                "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                                "case_id": case.case_id,
                                "attempt_number": next_attempt,
                                "max_attempts": max_attempts,
                                "completion_tokens": error_tokens if isinstance(error_tokens, int) else 0,
                                "reason": str(exc),
                                "retryable": exc.retryable,
                            }
                        )
                    if exc.retryable and next_attempt < max_attempts:
                        delay = retry_delay * (2 ** (next_attempt - 1))
                        if cancel_event is not None:
                            if cancel_event.wait(delay):
                                break
                        elif delay:
                            time.sleep(delay)
                        if cancel_event is not None and cancel_event.is_set():
                            break
                        next_attempt += 1
                        continue
                    append_event(
                        ledger_path,
                        {
                            "event_type": "case_terminal",
                            "run_id": run_id,
                            "case_id": case.case_id,
                            "trial_id": case.case_id,
                            "outcome": "no_response",
                            "reason": str(exc),
                            "attempt_count": next_attempt,
                        },
                    )
                    if on_progress:
                        on_progress(
                            {
                                "event": "case_finished",
                                "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                                "case_id": case.case_id,
                                "outcome": "no_response",
                                "completion_tokens": 0,
                                "total_cases": len(cases),
                            }
                        )
                    break
                except Exception as exc:
                    # Unexpected client exceptions are recorded without exposing
                    # arbitrary exception text, then terminate this case.
                    append_event(
                        ledger_path,
                        {
                            "event_type": "attempt_failed",
                            "run_id": run_id,
                            "trial_id": case.case_id,
                            "case_id": case.case_id,
                            "attempt_id": attempt_id,
                            "attempt_number": next_attempt,
                            "status_code": None,
                            "retryable": False,
                            "may_have_been_billed": True,
                            "spend_status": "unknown",
                            "provider_reported_usd": None,
                            "normalized_uncached_usd": None,
                            "error_type": type(exc).__name__,
                            "error": "unexpected client error",
                            "latency_seconds": round(time.monotonic() - attempt_started_monotonic, 6),
                        },
                    )
                    append_event(
                        ledger_path,
                        {
                            "event_type": "case_terminal",
                            "run_id": run_id,
                            "case_id": case.case_id,
                            "trial_id": case.case_id,
                            "outcome": "no_response",
                            "reason": type(exc).__name__,
                            "attempt_count": next_attempt,
                        },
                    )
                    if on_progress:
                        on_progress(
                            {
                                "event": "case_finished",
                                "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                                "case_id": case.case_id,
                                "outcome": "no_response",
                                "completion_tokens": 0,
                                "total_cases": len(cases),
                            }
                        )
                    break

                if not isinstance(response, Mapping):
                    response = {}
                event = _record_response(
                    client=client,
                    ledger_path=ledger_path,
                    case=case,
                    config=config,
                    model_info=model_info,
                    run_id=run_id,
                    attempt_id=attempt_id,
                    attempt_number=next_attempt,
                    response=response,
                    started_at=attempt_started_at,
                    started_monotonic=attempt_started_monotonic,
                )
                events.append(event)
                terminal_cases[case.case_id] = event
                if on_progress:
                    on_progress(
                        {
                            "event": "case_finished",
                            "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                            "case_id": case.case_id,
                            "outcome": event["outcome"],
                            "completion_tokens": event.get("usage", {}).get("completion_tokens") or 0,
                            "completed_cases": len(terminal_cases),
                            "total_cases": len(cases),
                        }
                    )
                break
            else:
                append_event(
                    ledger_path,
                    {
                        "event_type": "case_terminal",
                        "run_id": run_id,
                        "case_id": case.case_id,
                        "trial_id": case.case_id,
                        "outcome": "no_response",
                        "reason": "maximum attempts exhausted",
                        "attempt_count": max_attempts,
                    },
                )
                if on_progress:
                    on_progress(
                        {
                            "event": "case_finished",
                            "model_id": config.model_id, "reasoning_effort": config.reasoning_effort,
                            "case_id": case.case_id,
                            "outcome": "no_response",
                            "completion_tokens": 0,
                            "total_cases": len(cases),
                        }
                    )
    except KeyboardInterrupt:
        append_event(
            ledger_path,
            {"event_type": "run_paused", "run_id": run_id, "reason": "keyboard interrupt"},
        )
        raise

    final_events, _ = load_events(ledger_path, repair_torn_tail=True)
    final_state = _events_state(final_events)
    terminal_cases = final_state["terminal_cases"]
    completed = len(terminal_cases) == len(cases)
    if completed:
        summary = _basic_counts(cases, terminal_cases)
        append_event(
            ledger_path,
            {
                "event_type": "run_finished",
                "run_id": run_id,
                "status": "completed",
                "scheduled_cases": len(cases),
                "terminal_cases": len(terminal_cases),
                "correct": summary["correct"],
                "incorrect": summary["incorrect"],
                "no_response": summary["no_response"],
            },
        )
    else:
        append_event(
            ledger_path,
            {
                "event_type": "run_paused",
                "run_id": run_id,
                "reason": (
                    "cancellation requested"
                    if cancel_event is not None and cancel_event.is_set()
                    else "pending cases remain"
                ),
                "scheduled_cases": len(cases),
                "terminal_cases": len(terminal_cases),
            },
        )
    return {
        "ledger_path": str(ledger_path),
        "manifest_path": str(_manifest_path(ledger_path)),
        "run_id": run_id,
        "complete": completed,
        "scheduled_cases": len(cases),
        "terminal_cases": len(terminal_cases),
        "summary": _basic_counts(cases, terminal_cases),
    }


def _basic_counts(cases: Sequence[Case], terminal_cases: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    counts = {"correct": 0, "incorrect": 0, "wrong_label": 0, "invalid": 0, "no_response": 0}
    for case in cases:
        result = terminal_cases.get(case.case_id)
        if result is None:
            continue
        outcome = result.get("outcome")
        if outcome == "correct" or (outcome is None and result.get("correct") is True):
            counts["correct"] += 1
        else:
            counts["incorrect"] += 1
            if outcome == "wrong_label":
                counts["wrong_label"] += 1
            elif outcome == "invalid_response":
                counts["invalid"] += 1
            elif outcome == "no_response":
                counts["no_response"] += 1
    return counts


def _run_new_unlocked(
    *,
    client: OpenRouterClient,
    config: RunConfig,
    model_info: ModelInfo,
    results_dir: str | Path = "results",
    ledger_path: str | Path | None = None,
    on_progress: ProgressCallback | None = None,
    prepared_dataset: PreparedDataset | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Create a frozen dataset/run manifest and execute a new evaluation."""
    config.validate()
    if config.model_id != model_info.model_id:
        raise ValueError("model_id in run config does not match resolved OpenRouter model")
    OpenRouterClient.validate_reasoning_effort(model_info, config.reasoning_effort)
    if model_info.prompt_rate_usd_per_million is None or model_info.completion_rate_usd_per_million is None:
        raise ValueError("model input/output rates are required for normalized cost estimates")

    root = Path(results_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if prepared_dataset is None:
        cases = generate_cases(config.depths, config.samples_per_class, config.seed)
        dataset_path, dataset_payload = _write_or_verify_dataset(root, cases, config)
    else:
        cases = list(prepared_dataset.cases)
        dataset_path = prepared_dataset.path.resolve()
        dataset_payload = dict(prepared_dataset.payload)
        if (
            int(dataset_payload.get("seed", -1)) != config.seed
            or tuple(dataset_payload.get("depths", ())) != config.depths
            or int(dataset_payload.get("samples_per_class", -1)) != config.samples_per_class
            or not dataset_path.is_file()
        ):
            raise ValueError("prepared dataset does not match run configuration")
    ledger = (
        Path(ledger_path).resolve()
        if ledger_path is not None
        else _new_ledger_path(root, config.model_id, config.reasoning_effort)
    )
    if ledger.exists() or _manifest_path(ledger).exists():
        raise FileExistsError(f"run output already exists: {ledger}")

    run_id = uuid4().hex
    manifest = _make_manifest(
        run_id=run_id,
        config=config,
        model_info=model_info,
        dataset_path=dataset_path,
        dataset_payload=dataset_payload,
        ledger_path=ledger,
    )
    _atomic_write_json(_manifest_path(ledger), manifest)
    _write_run_created(ledger, manifest)
    events, _ = load_events(ledger, repair_torn_tail=True)
    return _execute_run(
        client=client,
        ledger_path=ledger,
        manifest=manifest,
        cases=cases,
        config=config,
        model_info=model_info,
        events=events,
        on_progress=on_progress,
        cancel_event=cancel_event,
    )


def run_new(
    *,
    client: OpenRouterClient,
    config: RunConfig,
    model_info: ModelInfo,
    results_dir: str | Path = "results",
    ledger_path: str | Path | None = None,
    on_progress: ProgressCallback | None = None,
    prepared_dataset: PreparedDataset | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Start a run while exclusively owning its target ledger."""
    root = Path(results_dir).resolve()
    ledger = (
        Path(ledger_path).resolve()
        if ledger_path is not None
        else _new_ledger_path(root, config.model_id, config.reasoning_effort)
    )
    try:
        with ledger_lock(ledger):
            return _run_new_unlocked(
                client=client,
                config=config,
                model_info=model_info,
                results_dir=root,
                ledger_path=ledger,
                on_progress=on_progress,
                prepared_dataset=prepared_dataset,
                cancel_event=cancel_event,
            )
    except KeyboardInterrupt as exc:
        raise EvaluationInterrupted(ledger) from exc


def prepare_case_dataset(
    *, results_dir: str | Path, config: RunConfig
) -> PreparedDataset:
    """Generate and persist the one immutable case manifest before batch dispatch."""
    config.validate()
    root = Path(results_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    cases = generate_cases(config.depths, config.samples_per_class, config.seed)
    dataset_path, dataset_payload = _write_or_verify_dataset(root, cases, config)
    return PreparedDataset(tuple(cases), dataset_path, dataset_payload)


def _resume_run_unlocked(
    *,
    client: OpenRouterClient,
    ledger_path: str | Path,
    overrides: Mapping[str, Any] | None = None,
    on_progress: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Resume only pending cases from a matching frozen run/configuration."""
    ledger = Path(ledger_path).resolve()
    manifest_file = _manifest_path(ledger)
    if not manifest_file.is_file():
        raise FileNotFoundError(f"run manifest not found: {manifest_file}")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    _validate_manifest(manifest)
    _validate_resume_overrides(manifest, overrides)
    config = _config_from_manifest(manifest)
    model_info = _model_info_from_dict(manifest["model"])
    if model_info.model_id != manifest["pricing"].get("model_id"):
        raise ValueError("pricing snapshot does not match the saved model ID")
    if decimal_text(model_info.prompt_rate_usd_per_million) != manifest["pricing"].get("prompt_rate_usd_per_million"):
        raise ValueError("saved prompt rate does not match pricing snapshot")
    if decimal_text(model_info.completion_rate_usd_per_million) != manifest["pricing"].get("completion_rate_usd_per_million"):
        raise ValueError("saved completion rate does not match pricing snapshot")
    dataset = manifest.get("dataset")
    if not isinstance(dataset, Mapping):
        raise ValueError("run manifest has no dataset metadata")
    cases = _load_dataset(manifest_file, dataset)
    events, discarded = load_events(ledger, repair_torn_tail=True)
    if discarded:
        append_event(
            ledger,
            {
                "event_type": "ledger_recovered",
                "run_id": manifest["run_id"],
                "discarded_torn_tail_bytes": discarded,
                "torn_copy": f"{ledger.name}.torn",
            },
        )
        events, _ = load_events(ledger)
    return _execute_run(
        client=client,
        ledger_path=ledger,
        manifest=manifest,
        cases=cases,
        config=config,
        model_info=model_info,
        events=events,
        on_progress=on_progress,
        cancel_event=cancel_event,
    )


def resume_run(
    *,
    client: OpenRouterClient,
    ledger_path: str | Path,
    overrides: Mapping[str, Any] | None = None,
    on_progress: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Resume pending cases while exclusively owning the event ledger."""
    ledger = Path(ledger_path).resolve()
    try:
        with ledger_lock(ledger):
            return _resume_run_unlocked(
                client=client,
                ledger_path=ledger,
                overrides=overrides,
                on_progress=on_progress,
                cancel_event=cancel_event,
            )
    except KeyboardInterrupt as exc:
        raise EvaluationInterrupted(ledger) from exc


def create_dry_run_plan(
    *,
    config: RunConfig,
    model_info: ModelInfo,
) -> dict[str, Any]:
    """Build a no-inference plan for review; no run files are written."""
    config.validate()
    if config.model_id != model_info.model_id:
        raise ValueError("model_id in run config does not match resolved OpenRouter model")
    OpenRouterClient.validate_reasoning_effort(model_info, config.reasoning_effort)
    cases = generate_cases(config.depths, config.samples_per_class, config.seed)
    dataset_payload = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "generator_version": CASE_GENERATOR_VERSION,
        "seed": config.seed,
        "depths": list(config.depths),
        "samples_per_class": config.samples_per_class,
        "cases": [_case_record(case) for case in cases],
    }
    return {
        "model_id": config.model_id,
        "resolved_model_name": model_info.name,
        "reasoning_effort": config.reasoning_effort,
        "depths": list(config.depths),
        "samples_per_class": config.samples_per_class,
        "seed": config.seed,
        "case_count": len(cases),
        "cases_by_depth": {
            str(depth): sum(1 for case in cases if case.depth == depth)
            for depth in config.depths
        },
        "dataset_sha256": _sha256(dataset_payload),
        "prompt_rate_usd_per_million": decimal_text(
            model_info.prompt_rate_usd_per_million
        ),
        "completion_rate_usd_per_million": decimal_text(
            model_info.completion_rate_usd_per_million
        ),
        "max_output_cost_bound_usd": decimal_text(
            Decimal(config.max_completion_tokens * len(cases) * config.max_attempts)
            * model_info.completion_rate_usd_per_million
            / Decimal(1_000_000)
        ),
        "pricing_source": model_info.pricing_source,
        "pricing_retrieved_at": model_info.pricing_retrieved_at,
        "max_attempts": config.max_attempts,
        "max_completion_tokens": config.max_completion_tokens,
        "inference_requests": len(cases),
    }
