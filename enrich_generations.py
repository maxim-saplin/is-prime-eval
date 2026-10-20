"""Fetch delayed OpenRouter generation metadata without repeating inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from costs import decimal_text, estimate_uncached_cost_usd, extract_provider_cost_usd, extract_usage
from events import append_event, ledger_lock, load_events
from openrouter import OpenRouterClient, OpenRouterError
from runner import _manifest_path, _validate_manifest
from settings import get_openrouter_key, load_dotenv


def _enrich_ledger_unlocked(ledger_path: str | Path, client: OpenRouterClient) -> dict[str, int]:
    ledger = Path(ledger_path).resolve()
    manifest_path = _manifest_path(ledger)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"run manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _validate_manifest(manifest)
    events, discarded = load_events(ledger, repair_torn_tail=True)
    if discarded:
        append_event(
            ledger,
            {
                "event_type": "ledger_recovered",
                "run_id": manifest.get("run_id"),
                "discarded_torn_tail_bytes": discarded,
                "torn_copy": f"{ledger.name}.torn",
            },
        )
        events, _ = load_events(ledger)

    already_enriched = {
        str(event.get("attempt_id"))
        for event in events
        if event.get("event_type") == "attempt_cost_update"
        and isinstance(event.get("generation_metadata"), Mapping)
        and event.get("attempt_id")
    }
    rates = manifest.get("pricing", {})
    input_rate = rates.get("prompt_rate_usd_per_million")
    output_rate = rates.get("completion_rate_usd_per_million")
    attempts: dict[str, Mapping[str, Any]] = {}
    for event in events:
        if event.get("event_type") not in {"attempt_response", "attempt_failed"}:
            continue
        attempt_id = event.get("attempt_id")
        if attempt_id:
            attempts[str(attempt_id)] = event

    enriched = failed = skipped = 0
    for attempt_id, event in attempts.items():
        if attempt_id in already_enriched:
            skipped += 1
            continue
        request_id = event.get("request_id")
        if not request_id:
            skipped += 1
            continue
        try:
            generation = client.generation_details(str(request_id))
        except OpenRouterError as exc:
            append_event(
                ledger,
                {
                    "event_type": "cost_lookup_failed",
                    "run_id": manifest.get("run_id"),
                    "case_id": event.get("case_id"),
                    "attempt_id": attempt_id,
                    "error_type": type(exc).__name__,
                    "status_code": exc.status_code,
                    "provider_reported_usd": event.get("provider_reported_usd"),
                    "normalized_uncached_usd": event.get("normalized_uncached_usd"),
                    "lookup_phase": "post-run enrichment",
                },
            )
            failed += 1
            continue

        raw_usage = event.get("raw_usage")
        usage = extract_usage({"usage": raw_usage} if isinstance(raw_usage, Mapping) else {}, generation)
        provider_cost = extract_provider_cost_usd(
            {"usage": raw_usage} if isinstance(raw_usage, Mapping) else {}, generation
        )
        normalized_cost = estimate_uncached_cost_usd(usage, input_rate, output_rate)
        data = generation.get("data") if isinstance(generation.get("data"), Mapping) else {}
        append_event(
            ledger,
            {
                "event_type": "attempt_cost_update",
                "run_id": manifest.get("run_id"),
                "case_id": event.get("case_id"),
                "trial_id": event.get("trial_id"),
                "attempt_id": attempt_id,
                "provider_reported_usd": decimal_text(provider_cost),
                "normalized_uncached_usd": decimal_text(normalized_cost),
                "usage": usage,
                "provider_route": data.get("provider_name"),
                "returned_model": data.get("model"),
                "generation_metadata": generation,
                "spend_status": "reported" if provider_cost is not None else "provider_cost_missing",
                "lookup_phase": "post-run enrichment",
            },
        )
        enriched += 1
    return {"enriched": enriched, "failed": failed, "skipped": skipped}


def enrich_ledger(ledger_path: str | Path, client: OpenRouterClient) -> dict[str, int]:
    """Fetch delayed metadata while exclusively owning the ledger."""
    ledger = Path(ledger_path).resolve()
    with ledger_lock(ledger):
        return _enrich_ledger_unlocked(ledger, client)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch delayed OpenRouter generation details without repeating model inference."
    )
    parser.add_argument("ledger", help="JSONL event ledger to enrich")
    parser.add_argument(
        "--timeout",
        type=float,
        required=True,
        help="Explicit urllib socket inactivity timeout for metadata lookup, in seconds",
    )
    args = parser.parse_args(argv)
    load_dotenv()
    api_key = get_openrouter_key()
    if not api_key:
        parser.error("OpenRouter key missing; set OR_KEY in .env or the environment")
    try:
        result = enrich_ledger(
            args.ledger,
            OpenRouterClient(api_key, timeout=args.timeout),
        )
    except (OSError, ValueError, OpenRouterError) as exc:
        parser.error(str(exc))
    print(
        f"Generation metadata: enriched {result['enriched']}, "
        f"failed {result['failed']}, skipped {result['skipped']} request(s)."
    )
    return 0 if result["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
