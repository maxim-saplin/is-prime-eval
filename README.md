# is-prime-eval

A small prompt-only evaluation of whether language models can classify integers as prime or composite. No tools are supplied to the model. The first provider is OpenRouter.

## Test set

`depth` means the number of decimal digits. The default run tests depths 4 through 10 inclusive, with **10 primes and 10 non-primes at each depth**: 20 questions per depth and **140 questions per model**, before retries. Cases are generated from a recorded seed, labeled with an exact deterministic primality check, and saved with a content hash so models can be compared on exactly the same questions.

Each model receives one prompt per case: “Is N prime? Reply with only PRIME or COMPOSITE.” Correct and incorrect percentages use all scheduled questions. Wrong labels, invalid answers, and retry-exhausted requests with no response are counted as not correct, with their reasons shown separately. An interrupted run with pending cases is provisional and is not ranked.

## Setup

The evaluator uses only the Python standard library. Existing `prime_stats.py` also needs `primecountpy`:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Create `.env` (ignored by Git) and set the OpenRouter key:

```env
OR_KEY=your-openrouter-key
```

The key is loaded from `.env` or the `OR_KEY` environment variable and is never written to run files. `OPENROUTER_API_KEY` is accepted as a fallback.

## Preflight and single-model runs

A dry run resolves the explicit model ID and effort, checks current rates, prints the planned case count and seed, and sends **no chat-completion requests**:

```sh
.venv/bin/python run.py \
  --model-id openai/gpt-6-luna \
  --reasoning-effort low \
  --dry-run
```

A live run keeps the two settings separate:

```sh
.venv/bin/python run.py \
  --model-id openai/gpt-6-luna \
  --reasoning-effort low
```

Both fields are required; no model or effort is silently selected. The effort string is passed unchanged to OpenRouter/the model. Supported values depend on the selected model/provider; if a value is rejected, the request error is recorded rather than silently substituted.

Defaults for the test itself are depths `4-10`, 10 examples of each class per depth, seed `2026`, **five retries after the initial attempt** (six total attempts per case), and a 512-token completion limit. Transient/API retries use an exponential backoff with a 1-second base and bounded ±20% jitter; invalid or truncated answers are recorded and are not retried for a better answer. Set `--max-retries N` to change retries after the initial request.

## Parallel model runs

Repeat `--model-id` and `--reasoning-effort` for every run. The first effort pairs with the first model ID, the second with the second, and so on. This uses CLI arguments only—no external model-list file or model-name suffix parsing:

```sh
.venv/bin/python run.py \
  --model-id openai/gpt-6-luna --reasoning-effort low \
  --model-id openai/gpt-6-luna --reasoning-effort high \
  --parallelism 2
```

A missing effort, extra effort, non-qualified model ID, or duplicate Model ID/Effort pair is rejected before inference. Each model receives the same frozen cases. `--parallelism` bounds the number of model runs in flight; requests within each model remain sequential. To repeat the same Model ID/Effort as a separate measurement, run it again in a separate command; each run has its own ID and leaderboard row.

The CLI applies a **shared account-request gate** across all workers and retries: default 15 completion dispatches per minute (4-second minimum spacing). HTTP 429 responses apply a coordinated cooldown to every worker for at least 60 seconds and for longer if `Retry-After` (delta-seconds or HTTP-date) requests it. Cancellation interrupts rate-gate waits and retry backoff before another attempt is recorded. The gate coordinates one evaluator process only; do not run another inference job with the same API key concurrently.

The checked-in 13-pair script defaults to a no-completion preflight and requires `--live` explicitly to send requests. It takes a stable exclusive host lock for the whole live batch, canonicalizes the output path to reject aliases of the immutable old archive, and rejects reuse of a non-empty live-output directory. The lock serializes this script's batches; keep all other processes/clients using the same API key idle:

```sh
scripts/run_13_pair_sweep.sh --dry-run
scripts/run_13_pair_sweep.sh --live
```

Progress is written to **stderr**, with Model ID and Effort shown separately: completed/scheduled cases, elapsed time, estimated remaining time, observed completion tokens per second, and correct/incorrect counts. In a terminal, each active model gets an in-place progress bar rather than a scrolling line per case; the dashboard is bounded to the active worker count, while the header tracks finished runs and final output lists every model. Redirected output is throttled to periodic summaries. A heartbeat refreshes elapsed time/ETA during slow non-streaming requests and shared rate-gate waits. Token speed is observed completion tokens divided by wall-clock time—not live generation speed—and completion totals include reasoning tokens when OpenRouter reports them. Per-model elapsed/ETA includes request time and retry backoff; a separate line reports total batch elapsed time. The CLI explicitly handles SIGINT and SIGTERM even if SIGINT was inherited as ignored: queued runs and gate/backoff waits are cancelled, while already-dispatched requests drain and are logged before workers stop.

## Resume

To resume an interrupted run, pass its JSONL event ledger. The saved manifest supplies the exact Model ID, Effort, prompt/parser versions, dataset and pricing rates; conflicting overrides are rejected. An OS advisory lock prevents concurrent ownership of a ledger and releases automatically when a process exits:

```sh
.venv/bin/python run.py --resume results/<run-ledger>.jsonl
```

## Leaderboard and run artifacts

Print a leaderboard for all run ledgers in `results/`, or a specific run:

```sh
.venv/bin/python report.py --results-dir results --output leaderboard.md
.venv/bin/python report.py results/<run-ledger>.jsonl --output leaderboard.md
```

The report has separate **Model ID** and **Reasoning effort** columns, a provider-route column, and a short run ID. Different efforts of the same model and repeated runs are distinct rows without encoding settings into model names. It shows Correct/Incorrect counts and percentages, results by digit (including prime and non-prime questions correctly identified), tokens, and two per-run costs:

- **Provider-reported cost:** the amount OpenRouter reports.
- **Estimated cost without cache discounts:** reported token counts priced at ordinary uncached rates, as if every prompt token were uncached.

Missing/partial cost coverage is labeled, never shown as `$0`. Both totals include retries. Run artifacts are ignored by Git; the JSONL event ledger is authoritative for attempt/run status, while the manifest stores the separate Model ID, Effort, dataset and pricing configuration. Delayed OpenRouter generation metadata can be fetched without repeating inference:

```sh
.venv/bin/python enrich_generations.py results/<run-ledger>.jsonl
```

The local `results/` directory was cleaned after archiving the earlier smoke/full runs to `/data/eval-runs/is-prim-eval/2026-10-19/`.

## Offline tests

No API key or network is required for unit tests:

```sh
.venv/bin/python -m unittest discover -s tests -v
```
