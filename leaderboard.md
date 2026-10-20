# Prime-eval leaderboard

**No uncapped evaluation runs are currently leaderboard-eligible.** The previous 14-run comparison used an explicit 512-token completion cap and has been moved to recoverable Trash because truncation affected the scores. Its cleanup/provenance record is in [`ARTIFACT_CLEANUP_RECEIPT.md`](ARTIFACT_CLEANUP_RECEIPT.md).

No prior dataset or valid result is retained in the active repository results tree. The user can launch `bash scripts/run_14_pair_sweep.sh --live` from `/home/user/src/is-prime-eval` to generate fresh deterministic cases and write the 14-pair uncapped baseline to `results/uncapped-14-pair-sweep-clean` with a 600-second request timeout. This placeholder is not an empirical leaderboard. After validating the fresh results, regenerate it with:

```sh
.venv/bin/python report.py --results-dir results/uncapped-14-pair-sweep-clean --output leaderboard.md
```
