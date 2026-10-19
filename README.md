# is-prime-eval

A small prompt-only evaluation of whether language models can classify integers as prime or composite. No tools are supplied to the model. The first provider is OpenRouter.

## Test set

`depth` means the number of decimal digits. The default run tests depths 4 through 10 inclusive, with **10 primes and 10 non-primes at each depth**: 20 questions per depth and **140 questions per model**, before retries. The cases are generated from a recorded seed, labeled with an exact deterministic primality check, and saved with a content hash so models can be compared on the same questions.

Each model receives one prompt per case: “Is N prime? Reply with only PRIME or COMPOSITE.” Correct and incorrect percentages use all scheduled questions. Wrong labels, invalid answers, and retry-exhausted requests with no response are counted as not correct, with their reasons shown separately. An interrupted run with pending cases is provisional and is not ranked.

## Setup

The repository runs on Python 3.13+ and uses only the standard library for the evaluator. Existing `prime_stats.py` also needs `primecountpy`:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Create `.env` (it is ignored by Git) and set the OpenRouter key:

```env
OR_KEY=your-openrouter-key
```

The key is loaded from `.env` or the `OR_KEY` environment variable and is never written to run files. `OPENROUTER_API_KEY` is accepted as a fallback.

## Preflight and runs

A dry run resolves the model and current rates, prints the exact case count and seed, and sends **no chat-completion requests**:

```sh
.venv/bin/python run.py \
  --model gpt-6-luna \
  --model-alias gpt-6-luna-low \
  --reasoning-effort low \
  --dry-run
```

Small smoke run (one prime and one non-prime at depth 4):

```sh
.venv/bin/python run.py \
  --model gpt-6-luna \
  --model-alias gpt-6-luna-low \
  --reasoning-effort low \
  --depths 4 --samples-per-class 1 --seed 2026 --max-attempts 2
```

Default benchmark run (140 cases per model):

```sh
.venv/bin/python run.py \
  --model gpt-6-luna \
  --model-alias gpt-6-luna-low \
  --reasoning-effort low
```

Reasoning effort can be set to `low` or `medium`. Defaults are depths `4-10`, 10 examples of each class per depth, seed `2026`, three total API attempts per case, and a 512-token completion limit. A retry is only for transient/API errors; an invalid or truncated model answer is recorded as such and is not retried for a better answer.

Progress is written to **stderr**, separately for each model: completed/scheduled cases, elapsed time, estimated time remaining, observed completion tokens per second, and correct/incorrect counts. A periodic heartbeat refreshes elapsed/ETA while a slow request is in flight. Requests are non-streaming, so token speed is observed completion tokens divided by elapsed wall time—not live generation speed. Completion-token totals include reasoning tokens when OpenRouter reports them. Per-model elapsed/ETA includes request time and retry delays; a separate batch line reports total elapsed time. On Ctrl-C in a parallel batch, queued runs are recorded as pending and no new case/retry requests are started; an already in-flight request is allowed to finish and be logged before workers stop.

Run multiple models concurrently with repeatable `--model-qualifier` options. Qualifiers accept `MODEL-low`, `MODEL:medium`, or `ALIAS=MODEL:low`; all models use the same seed and frozen cases. `--parallelism` bounds the number of model runs in flight; requests within each model remain sequential:

```sh
.venv/bin/python run.py \
  --model-qualifier gpt-6-luna-low \
  --model-qualifier gpt-6-luna:medium \
  --parallelism 2
```

To deliberately run the same model/effort twice, give the runs distinct aliases, for example `--model-qualifier low-a=gpt-6-luna:low --model-qualifier low-b=gpt-6-luna:low`. Each run gets its own ledger and leaderboard row; the report includes a short run ID so repeats are distinguishable.

To resume a run, use its JSONL event ledger. The saved manifest fixes the model, reasoning setting, prompt/parser versions, dataset and pricing rates; conflicting overrides are rejected. An OS advisory lock prevents two processes from owning the same ledger at once and releases automatically if a process exits:

```sh
.venv/bin/python run.py --resume results/gpt-6-luna-low_....jsonl
```

## Leaderboard and run artifacts

Print a leaderboard for all run ledgers in `results/`, or for specific runs:

```sh
.venv/bin/python report.py
.venv/bin/python report.py results/gpt-6-luna-low_....jsonl --output results/leaderboard.md
```

The report shows trials, Correct/Incorrect counts and percentages, results per digit (including prime and non-prime questions correctly identified), tokens, and two separately labeled costs per run:

- **Provider-reported cost:** the dollar value OpenRouter reports for each request.
- **Estimated cost without cache discounts:** reported input/output token counts priced at the model's regular uncached rates, as if every input token were uncached.

Missing or partial cost coverage is labeled, never represented as `$0`. Both totals include retries. Run artifacts are ignored by Git; the JSONL event ledger is the authority for run completion and attempt status, while the manifest is the frozen configuration/pricing snapshot.

OpenRouter generation metadata may become available a few seconds after inference. Fetch it later without repeating model calls to add the exact provider route, native token counts and generation cost details:

```sh
.venv/bin/python enrich_generations.py results/gpt-6-luna-low_....jsonl
```

## Offline tests

No API key or network is required for unit tests:

```sh
.venv/bin/python -m unittest discover -s tests -v
```
