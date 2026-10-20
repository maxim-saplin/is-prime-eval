#!/usr/bin/env bash
set -euo pipefail

# Safe by default: no completion requests unless --live is passed explicitly.
mode="${1:---dry-run}"
case "$mode" in
  --dry-run) mode_args=(--dry-run) ;;
  --live) mode_args=() ;;
  *) echo "Usage: $0 [--dry-run|--live]" >&2; exit 2 ;;
esac

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python="$project_root/.venv/bin/python"
results_dir="${EVAL_RESULTS_DIR:-$project_root/results/uncapped-14-pair-sweep-clean}"
old_partial_dir="/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep"
lock_file="$project_root/.run-locks/openrouter-live.lock"

if [[ ! -x "$python" ]]; then
  echo "Missing virtualenv Python: $python" >&2
  exit 2
fi
if ! command -v realpath >/dev/null || ! command -v flock >/dev/null; then
  echo "This script requires realpath and flock for safe launch isolation." >&2
  exit 2
fi

# Hold one stable lock across the entire live batch, independent of the output
# directory. This prevents two copies of this script from exceeding the shared
# account gate by running separate batches simultaneously.
if [[ "$mode" == "--live" ]]; then
  mkdir -p "$(dirname "$lock_file")"
  exec 9>"$lock_file"
  if ! flock -n 9; then
    echo "Another live batch holds the account launch lock: $lock_file" >&2
    exit 2
  fi
fi

canonical_results_dir="$(realpath -m -- "$results_dir")"
canonical_project_results="$(realpath -m -- "$project_root/results")"
canonical_old_partial_dir="$(realpath -m -- "$old_partial_dir")"
case "$canonical_results_dir" in
  "$canonical_old_partial_dir"|"$canonical_old_partial_dir"/*)
    echo "Refusing to use the immutable partial-run archive: $canonical_old_partial_dir" >&2
    exit 2
    ;;
esac
case "$canonical_results_dir" in
  "$canonical_project_results"/*) ;;
  *) echo "Results must be stored under the repository's results/ directory: $canonical_project_results" >&2; exit 2 ;;
esac
results_dir="$canonical_results_dir"

if [[ "$mode" == "--live" && -d "$results_dir" ]] && \
   find "$results_dir" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
  echo "Refusing to reuse a non-empty results directory: $results_dir" >&2
  exit 2
fi

printf 'Mode: %s\nResults directory: %s\nTimeout: 600s urllib socket inactivity\n' "$mode" "$results_dir"
command=(
  "$python" "$project_root/run.py"
  --model-id openai/gpt-6-luna --reasoning-effort low
  --model-id openai/gpt-6-luna --reasoning-effort medium
  --model-id openai/gpt-6-luna --reasoning-effort high
  --model-id openai/gpt-6-luna --reasoning-effort xhigh
  --model-id deepseek/deepseek-v4.1-flash-1017 --reasoning-effort low
  --model-id deepseek/deepseek-v4.1-flash-1017 --reasoning-effort medium
  --model-id deepseek/deepseek-v4.1-flash-1017 --reasoning-effort high
  --model-id anthropic/claude-haiku-5.5 --reasoning-effort low
  --model-id anthropic/claude-haiku-5.5 --reasoning-effort medium
  --model-id anthropic/claude-haiku-5.5 --reasoning-effort high
  --model-id anthropic/claude-haiku-5.5 --reasoning-effort xhigh
  --model-id openai/gpt-6.1-sol --reasoning-effort low
  --model-id openai/gpt-6.1-sol --reasoning-effort medium
  --model-id openai/gpt-4-turbo --reasoning-effort omit
  --parallelism 3
  --max-retries 5
  --retry-delay 1
  --timeout 600
  --requests-per-minute 15
  --results-dir "$results_dir"
  "${mode_args[@]}"
)
if [[ "$mode" == "--live" ]]; then
  "${command[@]}"  # Parent shell retains fd 9/lock until the run exits.
else
  exec "${command[@]}"
fi
