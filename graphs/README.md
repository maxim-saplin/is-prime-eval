# Depth graphs

- [Completion tokens vs depth](tokens-vs-depth.png) · [SVG](tokens-vs-depth.svg)
- [Accuracy vs depth](accuracy-vs-depth.png) · [SVG](accuracy-vs-depth.svg)

Both graphs have exactly two lines and gray pointwise 95% confidence bands:

1. **Best overall run:** select the highest overall scheduled-case accuracy once,
   then use that same model/effort at every depth. The current winner is
   `google/gemini-4-argon`, effort `high` (336/360, 93.3%). It is not a different
   winner at each depth.
2. **Average run:** the equal-weight mean of the 17 saved complete, uncapped
   4–15 runs. Different effort settings count as separate runs. Completed
   parent/extension pairs count once, not as two independent runs.

## Metrics and intervals

- **Tokens:** mean final-response completion tokens per recorded response,
  including provider-counted reasoning, counted once. Prefer native/billable
  token totals when available. Invalid and truncated returned responses are
  included. Failed/retry-failure attempt tokens are excluded: this is not a
  graph of total billed work. Missing final-response usage is excluded, not
  treated as zero. The winner has 29/30 usable responses at depths 9, 11, 13 and
  14; all 30 are available at the other depths. Per-run/per-depth coverage is
  recorded in `plot-data.json` in the same order as its `runs` list.
- **Accuracy:** correct / all scheduled questions, including invalid and
  terminal no-response outcomes as incorrect. The winner's bands are the same
  approximate 95% Wilson intervals used in the analysis.
- **Bootstrap bands:** token means and average accuracy use 2,000 percentile
  bootstrap replicates, stratified by depth and prime/non-prime class. Runs
  sharing the same question stratum reuse the same sampled question indices;
  genuinely separate fresh question sets are resampled independently. Each
  replicate first computes per-run means, then averages those equally. This
  preserves shared-question dependence rather than pretending the 14 extended
  runs used independent question sets. Pairing is exact for identical cohorts;
  incidental partial overlap between otherwise distinct random cohorts is not
  paired.
- These are **pointwise**, approximate intervals with the saved run roster
  fixed. They are not simultaneous whole-curve coverage, between-model spread,
  a model-population confidence interval, or inference-session rerun variance.
  The winner's intervals are conditional on post-hoc winner selection and do
  not adjust for that selection. Different runs used different frozen question
  sets; the curves are descriptive comparisons, not proof of superiority.

`plot-data.json` contains plotted values, interval endpoints, coverage, run IDs,
CI settings, Matplotlib version and source artifact SHA-256 hashes. It is generated from JSONL
ledgers/manifests through `is_prime_eval.report`, never by parsing or hand-editing
Markdown files.

## Regenerate, without model/API calls

From the repository root:

```sh
.venv/bin/python -m pip install -e '.[plots]'
.venv/bin/is-prime-plot
```

Optional: `--results-dir`, `--output-dir`, `--bootstrap-samples`,
`--bootstrap-seed`. The default plotting bootstrap seed is `1729` only to make
these figures reproducible; it never changes evaluation inputs or the CLI's
random-by-default question generation. PNG and SVG versions are saved. The
plotting dependency is optional and does not affect the evaluator.
