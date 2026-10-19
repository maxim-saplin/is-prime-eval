# is-prime-eval plan

## Goal

Build a small, reproducible, no-tools evaluation runner that asks a model whether an integer is prime. The default depth range is **4–10 digits inclusive**. The first provider is OpenRouter; the initial design should be simple and provider-specific rather than a general multi-provider framework.

The first version should make results and costs auditable from saved request data. It is an exploratory benchmark, not a claim of publication-grade statistical power.

## Benchmark contract

- **Depth:** `d` means an integer with exactly `d` decimal digits, in `[10^(d-1), 10^d - 1]`. Default CLI depths: `4-10`.
- **Task:** one prompt per integer, one-turn classification, no tools. Use a fixed prompt such as: `Is N prime? Reply with only PRIME or COMPOSITE.` Save a prompt/version identifier and all relevant run settings.
- **Balanced cases:** at each depth, sample equal numbers of primes and composites. Uniform random integers are a poor default: the existing `prime-stats.md` reports about 11.79% primes at 4 digits and 4.49% at 10 digits, so an always-COMPOSITE answer would appear 88.21%–95.51% accurate. The primary score must not reward this class imbalance.
- **Sampling:** use seeded rejection sampling of uniformly drawn integers within each digit band, conditioned on the desired label; deduplicate cases. Do not use `nextprime(random_value)`, which biases the prime sample. Freeze/save the generated case manifest (case IDs, values, labels, depth, seed and generator version) and reuse it across models. Keep deliberately hard composites (e.g. semiprimes, squares, pseudoprimes) as a separate future dataset/distribution, not mixed into the initial score.
- **Initial size (proposed):** 10 primes and 10 composites per depth (140 cases total), configurable with a CLI option. Treat this as a quick baseline; increase the sample count for stronger comparisons.
- **Ground truth:** use a tested exact deterministic primality oracle for the supported range (up to 10 digits). `primecountpy` in the existing project calculates aggregate prime counts; it does not by itself label individual cases. Keep `prime_stats.py` as an independent sanity check, not as the per-case labeler.
- **Parsing:** version a deterministic parser for the PRIME/COMPOSITE contract. Accept only an unambiguous label (case/whitespace and optional terminal punctuation may be normalized); refusals, ambiguous answers and malformed/truncated answers are invalid. Preserve the raw response, report format/invalid rate, and count invalid model responses as incorrect rather than dropping them from accuracy.

## Scoring and reporting

Use all **scheduled test items** as the percentage denominator. For a complete 140-item run, Correct and Incorrect add up to 140. If interrupted, show **Not attempted** as a separate count so Correct + Incorrect + Not attempted still account for all 140 items.

- **Correct:** a correct PRIME or COMPOSITE answer.
- **Incorrect:** no correct result for that scheduled item. Show its mutually exclusive reasons as sub-counts: **wrong label**, **invalid response** (refusal, malformed or unparseable), or **no response** after retries (API/network failure). Items never sent are **Not attempted**, not a failed request. This keeps failures visible without hiding them or counting an item twice.
- Show Correct, Incorrect, and (for an interrupted run) Not attempted as `X/140 (Y%)`; all percentages use 140 scheduled items. Use the same rule for every digit depth, with that depth's scheduled-item count as the denominator.
- At each depth, also show **Primes correctly identified: X/Y** and **Non-primes correctly identified: X/Y**. This makes it obvious if a model only handles one kind of question.

Sort complete runs by **Correct %**. Equal numbers of prime and composite cases at each depth make that simple percentage fair and prevent an always-COMPOSITE response from looking strong. A 50% guess-every-time reference may be shown for context. Track scheduled cases, cases with at least one request attempt, cases with a response, terminal no-response cases, and cases never attempted separately. A failed request and a case never sent are different. A run is operationally complete when every scheduled case has a persisted terminal outcome: a received response (including invalid) or a retry-exhausted no-response. Include completed no-response cases in Incorrect and show the reason; rank these completed runs so API failures are not silently selected out. Cases still pending or never attempted after interruption make a run incomplete/provisional and unranked.

## Leaderboard presentation

Put a short benchmark summary above the tables: dataset/prompt version, digits 4–10, cases per digit, seed or dataset ID, no-tools setting, and run date. Keep the main results in familiar terms:

1. **Model results**, sorted by Correct %: model (requested ID and route if stable), scheduled trials, **Correct # (%)**, **Incorrect # (%)**, and the wrong-label / invalid-response / no-response counts that make up Incorrect.
2. **Results by digit depth:** one row per model and depth, with trials, Correct # (%), Incorrect # (%), **Primes correctly identified: X/Y**, and **Non-primes correctly identified: X/Y**. A full run has 20 cases per depth by default.
3. **Cost per run:** prompt/completion token totals, **Provider-reported cost (USD)**, and **Estimated cost without cache discounts (USD)**. Show how many request costs were reported; if a dollar value is unknown or partial, label it rather than showing `$0`.

Percentages use all scheduled items, including invalid/no-response items in Incorrect; the sub-counts distinguish wrong model answers from provider failures. Only operationally complete runs on the same saved items, prompt and settings belong in the ranked list; retry-exhausted no-response outcomes stay in the score as Incorrect. Show interrupted runs with pending/never-attempted cases separately as provisional. A per-model detail view can include the same plain-language breakdown, route/retry details, and links to JSONL results.

## OpenRouter and cost accounting (required from the first run)

Use a small OpenRouter adapter over its OpenAI-compatible chat-completions API, authenticated by `OPENROUTER_API_KEY`. Require a model ID on the CLI. Avoid adding LiteLLM or a provider registry at this stage so OpenRouter's usage, cost and routing metadata remain visible. Record requested model and returned model/provider route when available. Keep tests offline by injecting/mocking the adapter.

Store **two distinct dollar metrics per API attempt**; never merge them into a generic `cost` field:

1. **`provider_reported_usd`** — the dollar cost reported by OpenRouter for that request (from returned usage or its generation metadata/request ID when needed). This is provider-reported accounting, not a promise that it equals a settled invoice. If unavailable, store `null`, not zero, and report cost coverage/partial totals.
2. **`normalized_uncached_usd`** — a counterfactual list-rate estimate using reported token counts and the model's ordinary, non-cached input/output rates:

   `((prompt_tokens × uncached_input_usd_per_1M) + (completion_tokens × output_usd_per_1M)) / 1,000,000`

   This deliberately prices **all** prompt tokens at the normal uncached input rate (including tokens that happened to be cache hits), so it answers “what would this token usage cost without caching?” Record cache-hit token details when available, but do not subtract them from this estimate. Use provider-reported billable completion totals; preserve any reasoning-token breakdown without counting it twice. This estimate is not actual provider spend.

Resolve or explicitly configure model-specific rates before a run, snapshot the rate values, source, model ID and lookup time in run metadata, and use decimal-safe arithmetic. If token counts or a rate are missing, the normalized estimate is `null`, not zero. Preserve raw usage and mark unknown spend where a timeout/failure may have been billed. Both cost metrics must cover the same request attempts, including retries and any failed attempt with returned usage/cost; sum spend per attempt while scoring each case only once. Retries should have stable trial IDs and distinct attempt IDs/request IDs.

## Runner shape and saved data

Keep the implementation small and split only at useful test seams:

- `cases.py`: seeded balanced case generation and exact labels.
- `prompt.py` / `parse.py`: fixed prompt and deterministic label parser.
- `openrouter.py`: one API adapter, including usage, cost, route and error extraction.
- `runner.py` / `run.py`: CLI, sequential execution, bounded retry/backoff and resume.
- `report.py`: summaries derived from saved results, without re-querying models.
- `tests/`: offline tests with a fake OpenRouter response; no API key/network needed.

Write an append-only JSONL event ledger. Persist and flush an `attempt_started` event before dispatching each API request; append its response/error, usage and cost as a separate finish event, then persist the case's terminal result. Events include run/trial/case IDs, unique attempt ID, depth, integer, gold label, requested/returned model, prompt version, raw response when received, parsed label/correctness, timestamps/latency, provider usage, both cost fields, pricing provenance, request ID and error details. Never send the gold label or case metadata to the model. Store run configuration and pricing snapshot in an immutable manifest; do not store the API key. The append-only event ledger, not the manifest, is the authority for run/attempt status. Reports group attempts by case and sum costs once per attempt. Resume only against the same frozen dataset/configuration: skip cases with a persisted terminal result (including retry-exhausted no-response), preserve earlier failures, and assign a new attempt ID when retrying a pending case. A start event with no finish after a crash is an attempted request with unknown outcome/spend—not a never-attempted case. Preserve that uncertainty and record any retry as a new attempt; do not claim exactly-once remote billing. Recover/flag a torn trailing JSONL record before appending. Keep attempted, answered, terminal no-response and never-attempted counts distinct.

## Build sequence and acceptance checks

1. Implement and test the benchmark contract: depth ranges, seeded balanced/deduplicated cases, exact labels, prompt and parser behavior.
2. Add the OpenRouter adapter and both cost paths. Mock responses with/without usage, reported cost, cache details, model routing and failures; test the normalized-cost formula and missing-data behavior.
3. Add the runner CLI, attempt-level JSONL logging, retries, resume and default depths `4-10`.
4. Add the text summary, README usage/API-key guidance, and one opt-in live smoke test (small case count, one model).

MVP is ready when offline tests verify generation, parsing/scoring, retry/resume, JSONL replay, both cost calculations, torn-tail recovery, and an interrupted attempt with unknown spend; a run uses the same saved cases across models; and the report keeps the two dollar totals distinct with explicit missing-cost coverage. Tests must not call the real API or require a key.

## Inspiration and non-goals

Borrow the useful seams from `../llm_arithmetic`: exact case/answer separation, a fixed prompt, raw per-trial results, derived reports, retry/resume behavior and mocked provider tests. Do not port its arithmetic variants, permissive numeric parser, broad LiteLLM configuration, model-alias pricing CSV, context experiments or heatmaps. Defer other providers, tools/agentic runs, prompt sweeps, concurrency, hard-composite tracks and advanced visualization until this minimal OpenRouter baseline works.
