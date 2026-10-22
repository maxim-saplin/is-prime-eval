# Running and reproducing is-prime-eval

## Setup

Python **3.11+** on Linux or macOS: ledger locking uses POSIX `fcntl`. The installed evaluator and reporting have no runtime dependencies. Plot generation additionally needs Matplotlib (`plots` extra); the optional repository-only prime-density utility needs `primecountpy` (`stats` extra).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[plots]'
```

No API key or network is needed to read results, regenerate reports/plots, or run the tests:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/is-prime-report --results-dir results --output leaderboard.md --readme README.md
.venv/bin/is-prime-report --results-dir results --format analysis --output analysis.md
.venv/bin/is-prime-plot
# or reproduce everything (analysis.md, leaderboard.md, README table, graphs):
# bash scripts/publish_build.sh
```

The compact report ranks **depths 7–15**, while the detailed analysis and plots retain **depths 4–15**. See [plot definitions](../graphs/README.md). Regenerating artifacts never repeats inference.

The `-e` install is editable: changes under `src/is_prime_eval/` are available immediately. Omit `-e` for a regular installation. All four commands are installed into the environment's `bin/` directory; activating `.venv` lets you omit that prefix. Module invocation is also supported: `python -m is_prime_eval`, `python -m is_prime_eval.report`, `python -m is_prime_eval.plot_results`, and `python -m is_prime_eval.enrich_generations`.

Commands use their **current working directory** for the default `.env`, `results/`, and `graphs/`, never the source or installed package directory. Run the examples from the repository root, or pass explicit paths such as `--results-dir /path/to/results` (and `--output-dir` for plots). The wheel contains code only; published results, graphs, and development utilities remain in the repository.

## Live evaluation

Live runs incur API charges. Copy `.env.sample` to `.env` and set `OR_KEY`, or export it in your environment. `OPENROUTER_API_KEY` is also accepted. The key is never written to run files.

```sh
cp .env.sample .env
# Edit .env: OR_KEY=your-openrouter-key
.venv/bin/is-prime-eval --model-id inception/mercury-3 --dry-run
.venv/bin/is-prime-eval --model-id inception/mercury-3
```

A dry run retrieves the model catalog and checks pricing/settings, but sends **no completion requests**; it is not an offline command.

### Defaults and request policy

- Depth is decimal digit count. Fresh runs use depths **4–15**, **15 primes + 15 composites per depth**: 360 scheduled questions.
- A system-random case seed is recorded; use `--seed N` for reproducible questions. This is not a model sampling seed.
- No tools, temperature, or `top_p` are supplied. Provider routing is not pinned.
- No completion-token cap is sent by default. `--max-completion-tokens N` is an explicit opt-in; provider-side output limits can still truncate responses. There is no finite output-only cost bound when uncapped.
- Absent `--reasoning-effort`, no reasoning control is sent. `--reasoning-effort omit` explicitly selects the same provider-default policy; it **does not mean reasoning is disabled**. `none` is a distinct literal provider effort. Requested effort is not independently verified as honored by the route.
- The **600-second timeout** is socket inactivity, not a strict total request deadline. A response can exceed it while data keeps arriving.
- Five retries after the first request (six attempts maximum), exponential backoff with a one-second base and bounded ±20% jitter. Invalid/truncated answers are recorded, **not retried for a better answer**.
- A shared 15-request/minute gate covers workers and retries within one process. HTTP 429 applies at least a 60-second shared cooldown, longer if `Retry-After` requires it. Do not run another inference client with the same key concurrently.

Override model and reasoning separately:

```sh
.venv/bin/is-prime-eval \
  --model-id openai/gpt-6-luna --reasoning-effort low \
  --timeout 600 --seed 42
```

### Multiple models

Repeat `--model-id`. If supplying any efforts, supply exactly one per model, in order; use `omit` for provider defaults. Duplicate model/effort pairs in one command are rejected. Every model receives the same frozen questions. `--parallelism` controls concurrent model runs; each model processes its questions sequentially.

```sh
.venv/bin/is-prime-eval \
  --model-id openai/gpt-4-turbo --reasoning-effort omit \
  --model-id openai/gpt-6-luna --reasoning-effort high \
  --parallelism 2 --timeout 600
```

Progress on stderr includes completed/scheduled cases, correct/incorrect counts, elapsed time, ETA, observed completion tokens per wall-clock second, and running costs. This is not live generation speed. Retry backoff and rate-gate waits affect wall time. Missing usage and unknown costs are marked partial, not treated as free.

SIGINT/SIGTERM stop new dispatches and cancel queued work/backoff; in-flight requests drain or time out and are logged. An advisory ledger lock prevents concurrent ownership and releases on process exit.

## Resume and depth extension

Resume using the saved ledger. Its manifest preserves model, reasoning, prompt/parser, dataset, pricing, timeout, and token-cap policy; conflicting overrides are rejected.

```sh
.venv/bin/is-prime-eval --resume results/<run-ledger>.jsonl
```

The published data includes 14 original 4–10 parent runs (140 questions each), their disjoint 220-question supplements, and three standalone 4–15 runs. Each completed parent+child pair is reported **once**, giving 17 completed 360-question results. Parent ledgers remain immutable. Frozen question sets are essential inputs, not disposable caches; see [results/README.md](../results/README.md).

To extend an explicitly selected parent, inspect a no-completion preflight first:

```sh
.venv/bin/is-prime-eval \
  --parent-ledger results/<parent-ledger>.jsonl \
  --extend-through 15 --top-up-existing-per-class 5 --new-depths-per-class 15 \
  --parallelism 3 --max-retries 5 --retry-delay 1 \
  --requests-per-minute 15 --timeout 600 --results-dir results --dry-run
```

Remove `--dry-run` only when ready to spend. Repeat `--parent-ledger` for multiple parents. Rerunning the same extension command resumes the saved child ledgers and reuses the frozen supplement; use `--seed N` only when intentionally selecting a reproducible extension seed. Incomplete runs remain provisional and are not ranked.

## Reports and accounting

The compact leaderboard uses 270 questions per published row: depths 7–15, 15 prime + 15 composite per depth. All scheduled questions are in the denominator; wrong labels, invalid/truncated answers, and exhausted requests count against accuracy. Independent runs are not averaged into a single model row. Rankings on different frozen question sets are descriptive, not paired comparisons.

Tokens, cost, and API time are scoped to the same selected depths. The table contains numbers only; the generated [leaderboard](../leaderboard.md) documents units and any missing coverage below it. Cost is provider-reported USD, displayed to three decimal places, not the uncached estimate available in the [detailed analysis](../analysis.md). Retries can incur additional costs; missing charges are never assumed to be zero. When transport failures return neither usage nor a generation ID, totals are known subtotals. Complete historical accounting requires reconciliation with provider logs; repeating inference cannot repair the original bill.

The detailed report preserves per-depth class breakdowns, request policy, route, invalid-answer reasons, item-level Wilson intervals, and both provider-reported and uncached estimated spend. These intervals are not model-difference or session-to-session confidence intervals.

Delayed generation metadata can be fetched without repeating inference (this **does** contact OpenRouter):

```sh
.venv/bin/is-prime-enrich results/<run-ledger>.jsonl --timeout 600
```

Reports scan immediate `*.jsonl` files in the selected results directory, not subdirectories. A specific ledger can be passed instead of `--results-dir`.

## Repository layout

| Path | Purpose |
|---|---|
| `pyproject.toml` | Package metadata, optional dependencies, installed CLI entry points |
| `src/is_prime_eval/` | Importable package: evaluation CLI, generation, API adapter, orchestration, accounting, reporting, plots, enrichment |
| `scripts/` | Repository-only publication build and optional prime-density utility |
| `results/` | Raw ledgers, run manifests, frozen datasets, extension provenance |
| `graphs/` | Published PNG/SVG plots and machine-readable plot data |
| `analysis.md` | Detailed full-depth results |
| `leaderboard.md` | Compact hard-depth leaderboard |
| `tests/` | Offline unit and CLI tests |

### Build distributions

```sh
.venv/bin/python -m pip install build
.venv/bin/python -m build
```

This produces a source distribution and an installable wheel in ignored `dist/`. CI builds both and checks the wheel's entry points and reporting from outside the checkout. Building/installing never sends model requests. `pyproject.toml` is the single source of dependency and command configuration; no `PYTHONPATH` or `sys.path` workaround is needed.

For the optional natural prime-density calculation (not needed to run this balanced benchmark):

```sh
.venv/bin/python -m pip install -e '.[stats]'
.venv/bin/python scripts/prime_stats.py
```

Its output is [prime-stats.md](prime-stats.md). Do not commit `.env`, local locks, virtual environments, or active-run snapshots. Review new result ledgers for completion and unknown costs before publishing.
