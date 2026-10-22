# Evaluation results

This directory holds the output of paid inference runs (OpenRouter). All files
are committed and are part of the published evaluation record.

## Artifacts

- **`<run>.jsonl`** — the raw event ledger for one run. This is the
  **authoritative** source of truth for outcomes, attempts, retries, usage,
  and costs. Each line is one JSON event; the file is append-only and may be
  recovered from a torn tail on load.
- **`<run>.manifest.json`** — run metadata: model ID, reasoning effort,
  pricing snapshot, config hash, and the frozen dataset reference
  (`dataset.dataset_id`, `dataset.sha256`, `dataset.file`). It does not
  duplicate the ledger; it binds the ledger to the exact model, prompt/parser
  versions, pricing, and case set used.
- **`datasets/prime-v1-*.json`** — frozen, content-hashed case sets
  (schema version, generator version, seed, depths, cases). They are
  **retained on purpose**:
  - Every file is referenced by at least one run manifest; none is orphaned.
    The extension batch record also references its frozen supplement.
  - `is_prime_eval.report` and plot regeneration re-read the case files through
    `is_prime_eval.runner._load_dataset`; deleting them breaks reproducibility of the
    published leaderboard and graphs.
  - They are deterministically regenerable from their recorded seed, but
    keeping the files guarantees byte-identical reuse across runs, disjoint
    cohort checks for extensions, and exact resume behavior.
  - Total size is ~172 KB — negligible.
- **`extension-batch-*.json`** — frozen plan record for an extension batch:
  parent run IDs, supplement dataset, sampling seed, and target dataset
  metadata.

## Transient artifacts

`*.jsonl.lock` files support advisory OS locks while a run is in progress.
They are never committed (see `.gitignore`). Lock ownership releases on
process exit, but the files may remain; their existence alone does not mean
a run is active. Remove stale files only after verifying no process owns them.
