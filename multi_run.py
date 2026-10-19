"""Parallel orchestration for independent model runs on one frozen dataset."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import sys
import threading
from typing import Any, Callable, Sequence

from openrouter import ModelInfo, OpenRouterClient
from runner import RunConfig, prepare_case_dataset, run_new


@dataclass(frozen=True)
class ModelRunSpec:
    config: RunConfig
    model_info: ModelInfo


ClientFactory = Callable[[float], OpenRouterClient]


def run_many(
    specs: Sequence[ModelRunSpec],
    *,
    client_factory: ClientFactory,
    results_dir: str | Path,
    parallelism: int,
    on_progress: Any = None,
) -> list[dict[str, Any]]:
    """Run model specs concurrently, each with its own sequential request loop.

    The shared case manifest is generated and saved before any worker starts.
    On Ctrl-C, a shared cancellation flag prevents new cases/retries from being
    dispatched, queued futures are cancelled, and each queued model receives a
    paused ledger with its scheduled items marked never attempted. An already
    in-flight HTTP request is allowed to return and be durably logged.
    """
    if not specs:
        return []
    if parallelism <= 0:
        raise ValueError("parallelism must be positive")
    for spec in specs:
        spec.config.validate()
    first_config = specs[0].config
    shared_settings = (
        first_config.depths,
        first_config.samples_per_class,
        first_config.seed,
        first_config.max_attempts,
        first_config.retry_delay_seconds,
        first_config.timeout_seconds,
        first_config.max_completion_tokens,
    )
    if any(
        (
            spec.config.depths,
            spec.config.samples_per_class,
            spec.config.seed,
            spec.config.max_attempts,
            spec.config.retry_delay_seconds,
            spec.config.timeout_seconds,
            spec.config.max_completion_tokens,
        )
        != shared_settings
        for spec in specs[1:]
    ):
        raise ValueError("all models in one parallel batch must share dataset and request settings")
    identities = [(spec.config.model_id, spec.config.reasoning_effort) for spec in specs]
    if len(set(identities)) != len(identities):
        raise ValueError("parallel model_id/reasoning_effort identities must be unique")
    worker_count = min(parallelism, len(specs))

    prepared_dataset = prepare_case_dataset(results_dir=results_dir, config=first_config)
    if on_progress is not None:
        if hasattr(on_progress, "set_active_model_limit"):
            on_progress.set_active_model_limit(worker_count)
        if hasattr(on_progress, "set_batch_total"):
            on_progress.set_batch_total(len(specs))
    cancellation = threading.Event()
    results: list[dict[str, Any] | None] = [None] * len(specs)

    def execute(index: int, spec: ModelRunSpec) -> tuple[int, dict[str, Any]]:
        config = spec.config
        if on_progress is not None and hasattr(on_progress, "register_model"):
            total = len(config.depths) * config.samples_per_class * 2
            on_progress.register_model(config.model_id, config.reasoning_effort, total)
        client = client_factory(config.timeout_seconds)
        result = run_new(
            client=client,
            config=config,
            model_info=spec.model_info,
            results_dir=results_dir,
            on_progress=on_progress,
            prepared_dataset=prepared_dataset,
            cancel_event=cancellation,
        )
        return index, {"spec": spec, "result": result, "error": None}

    def store(index: int, row: dict[str, Any]) -> None:
        results[index] = row
        if on_progress is not None and hasattr(on_progress, "model_finished"):
            result = row.get("result")
            on_progress.model_finished(
                specs[index].config.model_id,
                specs[index].config.reasoning_effort,
                success=bool(result and result.get("complete")),
            )

    pool = ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="prime-model")
    futures: dict[Future[tuple[int, dict[str, Any]]], int] = {}
    futures_by_index: dict[int, Future[tuple[int, dict[str, Any]]]] = {}
    interrupted = False
    try:
        for index, spec in enumerate(specs):
            future = pool.submit(execute, index, spec)
            futures[future] = index
            futures_by_index[index] = future
        for future in as_completed(futures):
            index = futures[future]
            try:
                result_index, row = future.result()
                store(result_index, row)
            except Exception as exc:
                store(
                    index,
                    {
                        "spec": specs[index],
                        "result": None,
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
    except KeyboardInterrupt:
        interrupted = True
        cancellation.set()
        notice = "cancel requested"
        if on_progress is not None and hasattr(on_progress, "set_batch_status"):
            on_progress.set_batch_status(notice)
        else:
            print(notice, file=sys.stderr, flush=True)
        for future in futures:
            future.cancel()
    finally:
        pool.shutdown(wait=True, cancel_futures=interrupted)

    # Collect workers that finished during shutdown and materialize cancelled
    # queued specs as pending ledgers without dispatching inference.
    for index, spec in enumerate(specs):
        if results[index] is not None:
            continue
        future = futures_by_index.get(index)
        try:
            if future is None or future.cancelled():
                _, row = execute(index, spec)  # cancellation is already set
            else:
                result_index, row = future.result()
                index = result_index
            store(index, row)
        except Exception as exc:
            store(
                index,
                {
                    "spec": spec,
                    "result": None,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )

    if interrupted:
        for row in results:
            if row is not None:
                row["batch_interrupted"] = True
    return [row for row in results if row is not None]
