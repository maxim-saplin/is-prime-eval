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

Every new run requires an explicit finite positive `--timeout`. It is urllib's socket inactivity timeout, not a strict total wall-clock deadline; a long-running response can exceed it while data keeps arriving. Choose it deliberately based on the model/provider. For the examples below, set `TIMEOUT_SECONDS` yourself before running the command. For the authorized 14-pair baseline, the chosen value is `600`:

```sh
TIMEOUT_SECONDS=600
```

A dry run resolves the explicit model ID and effort, checks current rates, prints the planned case count and seed, and sends **no chat-completion requests**:

```sh
.venv/bin/python run.py \
  --model-id openai/gpt-6-luna \
  --reasoning-effort low \
  --timeout "$TIMEOUT_SECONDS" \
  --dry-run
```

A live run keeps the two settings separate:

```sh
.venv/bin/python run.py \
  --model-id openai/gpt-6-luna \
  --reasoning-effort low \
  --timeout "$TIMEOUT_SECONDS"
```

Model ID and reasoning effort are separate explicit fields; every model requires one `--reasoning-effort`. For a model that should receive no reasoning control, use the explicit `omit` sentinel:

```sh
.venv/bin/python run.py \
  --model-id openai/gpt-4-turbo --reasoning-effort omit \
  --timeout "$TIMEOUT_SECONDS"
```

`omit` is not sent to the provider: it omits reasoning controls and uses the provider's default behavior (which does not necessarily disable default reasoning). The provider level `none` is a distinct literal effort and is sent unchanged. Supported values depend on the model/provider; unsupported settings are not silently substituted. Omission is saved as JSON `null` and preserved on resume; no effort is inferred or silently selected.

Other defaults are depths `4-10`, 10 examples of each class per depth, seed `2026`, and **five retries after the initial attempt** (six total attempts per case). Transient/API retries use an exponential backoff with a 1-second base and bounded ±20% jitter; invalid or truncated answers are recorded and are not retried for a better answer. Set `--max-retries N` to change retries after the initial request. By default, requests send neither `max_completion_tokens` nor `max_tokens`; use `--max-completion-tokens N` only as an explicit opt-in cap. There is no adapter fallback between these parameter names. Provider/model-side output limits may still truncate responses; dry runs report the output-only cost bound as unbounded when no explicit cap is set.

## Parallel model runs

Repeat both `--model-id` and `--reasoning-effort` for every run. The first effort pairs with the first model ID, the second with the second, and so on. Use the explicit `omit` sentinel for models that should receive no reasoning controls. This uses CLI arguments only—no external model-list file or model-name suffix parsing:

```sh
.venv/bin/python run.py \
  --model-id openai/gpt-6-luna --reasoning-effort low \
  --model-id openai/gpt-6-luna --reasoning-effort high \
  --parallelism 2 \
  --timeout "$TIMEOUT_SECONDS"
```

For mixed reasoning/non-reasoning batches, use `--reasoning-effort omit` for entries that should send no reasoning controls:

```sh
uv run run.py \
  --model-id openai/gpt-4-turbo --reasoning-effort omit \
  --model-id openai/gpt-6-luna --reasoning-effort high \
  --timeout "$TIMEOUT_SECONDS"
```

`omit` is a CLI sentinel, not sent to the provider. The provider effort `none` remains a literal value, distinct from omission. A partial or extra effort list, non-qualified model ID, or duplicate Model ID/Effort pair is rejected before inference. Each model receives the same frozen cases. `--parallelism` bounds the number of model runs in flight; requests within each model remain sequential. To repeat the same Model ID/Effort as a separate measurement, run it again in a separate command; each run has its own ID and leaderboard row.

The CLI applies a **shared account-request gate** across all workers and retries: default 15 completion dispatches per minute (4-second minimum spacing). HTTP 429 responses apply a coordinated cooldown to every worker for at least 60 seconds and for longer if `Retry-After` (delta-seconds or HTTP-date) requests it. Cancellation interrupts rate-gate waits and retry backoff before another attempt is recorded. The gate coordinates one evaluator process only; do not run another inference job with the same API key concurrently.

## Benchmark and request-policy audit

- The default test set is balanced by construction (10 prime + 10 non-prime per digit depth); it is not a natural-prevalence sample. `--seed` controls case generation only; it is not sent as a model sampling seed.
- No temperature or `top_p` is sent. OpenRouter provider routing is not pinned, and the requested reasoning effort is not independently verified as honored by the eventual route. `reasoning-effort omit` sends no reasoning control and uses provider default behavior; it does not mean reasoning is disabled.
- The parser accepts only the bare `PRIME`/`COMPOSITE` labels. Explanations, refusals, and truncated outputs are invalid; they are recorded, not retried. A completed score is accuracy within this exact prompt/output budget, not an estimate of unrestricted primality competence.
- Without an explicit token cap, provider/model-side limits can still truncate outputs and there is no finite output-only cost bound. Actual spend is read from per-attempt usage when available; timeouts/errors can leave spend unknown. Retries may incur additional cost.
- The CLI timeout is an urllib socket inactivity timeout, not a strict total wall-clock deadline. A request that continues delivering data may exceed the configured number of seconds; cancellation stops new dispatches but allows in-flight requests to finish or time out.

The checked-in 14-pair script defaults to a no-completion preflight and requires `--live` explicitly to send requests. It uses the user-selected 600-second urllib socket timeout, writes to repository-local `results/uncapped-14-pair-sweep-clean`, takes a stable exclusive host lock for the whole live batch, rejects aliases of the old partial archive and non-empty output directories, and sends no completion-token cap. The lock serializes this script's batches; keep all other processes/clients using the same API key idle. Results are gitignored during an active run to avoid accidental snapshots; after validation, intentionally force-add the selected ledgers/manifests/dataset/report to the private repository.

```sh
bash scripts/run_14_pair_sweep.sh --dry-run
bash scripts/run_14_pair_sweep.sh --live
```

Progress is written to **stderr**, with Model ID and Effort shown separately: completed/scheduled cases, elapsed time, estimated remaining time, observed completion tokens per second, and correct/incorrect counts. In a terminal, each active model gets an in-place progress bar rather than a scrolling line per case; the dashboard is bounded to the active worker count, while the header tracks finished runs and final output lists every model. Redirected output is throttled to periodic summaries. A heartbeat refreshes elapsed time/ETA during slow non-streaming requests and shared rate-gate waits. Token speed is observed completion tokens divided by wall-clock time—not live generation speed—and completion totals include reasoning tokens when OpenRouter reports them. Per-model elapsed/ETA includes request time and retry backoff; a separate line reports total batch elapsed time. The CLI explicitly handles SIGINT and SIGTERM even if SIGINT was inherited as ignored: queued runs and gate/backoff waits are cancelled, while already-dispatched requests drain and are logged before workers stop.

## Resume

To resume an interrupted run, pass its JSONL event ledger. The saved manifest supplies the exact Model ID, Effort, prompt/parser versions, dataset and pricing rates; conflicting overrides are rejected. An OS advisory lock prevents concurrent ownership of a ledger and releases automatically when a process exits:

```sh
.venv/bin/python run.py --resume results/<run-ledger>.jsonl
```

## Leaderboard and run artifacts

Print a leaderboard for the uncapped sweep's ledgers or a specific run (the report scan is not recursive):

```sh
.venv/bin/python report.py --results-dir results/uncapped-14-pair-sweep-clean --output leaderboard.md
.venv/bin/python report.py results/uncapped-14-pair-sweep-clean/<run-ledger>.jsonl --output leaderboard.md
```

The report has separate **Model ID** and **Reasoning effort** columns, a provider-route column, and a short run ID. Different efforts of the same model and repeated runs are distinct rows without encoding settings into model names. It shows Correct/Incorrect counts and percentages, results by digit (including prime and non-prime questions correctly identified), tokens, and two per-run costs:

- **Provider-reported cost:** the amount OpenRouter reports.
- **Estimated cost without cache discounts:** reported token counts priced at ordinary uncached rates, as if every prompt token were uncached.

Missing/partial cost coverage is labeled, never shown as `$0`. Both totals include retries. The JSONL event ledger is authoritative for attempt/run status, while the manifest stores the separate Model ID, Effort, timeout/token-cap policy, dataset and pricing configuration. Delayed OpenRouter generation metadata can be fetched without repeating inference:

```sh
.venv/bin/python enrich_generations.py results/<run-ledger>.jsonl --timeout "$TIMEOUT_SECONDS"
```

## Current result status

There are currently **no valid results and no retained prior datasets** in the active repository results tree. Earlier comparisons that explicitly used a 512-token completion cap, their datasets, and generated leaderboards have been moved to recoverable Trash because truncation dominated their scores; see `ARTIFACT_CLEANUP_RECEIPT.md` for hashes and recovery mappings. The previously deferred `/data/eval-runs/is-prim-eval/2026-10-19/results` directory was also safely moved to Trash after inspection found no open handles in that copied directory; LibreOffice was not closed or killed. The checked-in `leaderboard.md` is only a no-results placeholder.

The user personally launches the fresh uncapped baseline (this sends paid API requests):

```sh
cd /home/user/src/is-prime-eval
bash scripts/run_14_pair_sweep.sh --live
```

The script uses 14 Model ID/Effort pairs including GPT-4 Turbo with `omit`, timeout `600`, no explicit token cap, 3 parallel model runs, 5 retries with a 1-second base delay, and the shared 15-RPM gate. It generates a fresh deterministic dataset from the default seed (`2026`) at launch, shared by all 14 runs, under the new repo-local output directory `results/uncapped-14-pair-sweep-clean`. Deterministic regeneration may reproduce the former dataset's content hash; no old dataset file is reused. Keep other clients using the same API key idle. No preflight, catalog lookup, or live evaluation was performed as part of the offline cleanup.

## Offline tests

No API key or network is required for unit tests:

```sh
.venv/bin/python -m unittest discover -s tests -v
```
