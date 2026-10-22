#!/usr/bin/env bash
# Regenerate every published artifact from the saved ledgers - no live API calls.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
RESULTS="${EVAL_RESULTS_DIR:-results}"

# Detailed per-run/per-depth analysis (formerly leaderboard.md; now analysis.md).
"$PYTHON" -m is_prime_eval.report --results-dir "$RESULTS" --format analysis --output analysis.md

# Compact 7-15 leaderboard, and embed the same table in README between its markers.
"$PYTHON" -m is_prime_eval.report --results-dir "$RESULTS" --output leaderboard.md --readme README.md

# Depth graphs (4-15). Matplotlib is required; fail loudly if it is missing.
"$PYTHON" -c "import matplotlib" || {
    echo "error: install the package with plotting support first: python -m pip install -e '.[plots]'" >&2
    exit 1
}
"$PYTHON" -m is_prime_eval.plot_results --results-dir "$RESULTS"

echo "Regenerated analysis.md, leaderboard.md, README leaderboard section, and graphs."
