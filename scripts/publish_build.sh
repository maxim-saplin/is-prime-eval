#!/usr/bin/env bash
# Regenerate every published artifact from the saved ledgers - no live API calls.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
RESULTS="${EVAL_RESULTS_DIR:-results}"

# Detailed per-run/per-depth analysis (formerly leaderboard.md; now analysis.md).
"$PYTHON" scripts/report.py --results-dir "$RESULTS" --format analysis --output analysis.md

# Compact 7-15 leaderboard, and embed the same table in README between its markers.
"$PYTHON" scripts/report.py --results-dir "$RESULTS" --output leaderboard.md --readme README.md

# Depth graphs (4-15). Matplotlib is required; fail loudly if it is missing.
"$PYTHON" -c "import matplotlib" || {
    echo "error: matplotlib is required to regenerate graphs (pip install -r requirements-plots.txt)" >&2
    exit 1
}
"$PYTHON" scripts/plot_results.py --results-dir "$RESULTS"

echo "Regenerated analysis.md, leaderboard.md, README leaderboard section, and graphs."
