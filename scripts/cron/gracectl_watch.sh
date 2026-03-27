#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VENV_PATH="${VENV_PATH:-$REPO_ROOT/venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_DIR="${LOG_DIR:-$REPO_ROOT/logs/gracectl/cron}"
SLICE_ID="${1:-FEED-PERSONALIZED-DAILY}"
VERIFY_FLAGS="${VERIFY_FLAGS:-"--frontend --backend"}"
WATCH_FLAGS="${WATCH_FLAGS:-"--flow feed"}"
RUN_DEMO="${RUN_DEMO:-0}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S)"
LOG_FILE="$LOG_DIR/${SLICE_ID}_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"

if [[ -d "$VENV_PATH" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_PATH/bin/activate"
fi

exec > >(tee -a "$LOG_FILE") 2>&1

printf '==>[gracectl-watch] %s slice=%s\n' "$TIMESTAMP" "$SLICE_ID"

read -r -a VERIFY_ARGS <<< "$VERIFY_FLAGS"
read -r -a WATCH_ARGS <<< "$WATCH_FLAGS"

$PYTHON_BIN -m gracectl.cli env check --config gracectl.yaml
$PYTHON_BIN -m gracectl.cli slice verify "$SLICE_ID" "${VERIFY_ARGS[@]}"
$PYTHON_BIN -m gracectl.cli watch run "$SLICE_ID" "${WATCH_ARGS[@]}"

if [[ "$RUN_DEMO" == "1" ]]; then
  $PYTHON_BIN -m gracectl.cli demo run "$SLICE_ID"
fi

echo "Logs stored in $LOG_FILE"
