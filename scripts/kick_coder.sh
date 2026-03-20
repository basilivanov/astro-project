#!/usr/bin/env bash
set -euo pipefail

# Resets review markers and (re)triggers the watcher to kick the coder.
#
# It works by:
# - removing existing READY_FOR_REVIEW / KICK_CODER marker lines
# - appending a fresh KICK_CODER line with timestamp (so watcher sees transition 0->1)
#
# Usage:
#   ./scripts/kick_coder.sh [task_file]

TASK_FILE="${1:-Task.md}"

ts_iso() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

[ -f "$TASK_FILE" ] || { echo "Task file not found: $TASK_FILE" >&2; exit 1; }

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

# Remove old markers (marker lines only; do NOT delete mentions in prose).
# NOTE: Use a regex that matches "marker" lines like:
#   READY_FOR_REVIEW 2026-02-09T...
#   KICK_CODER 2026-02-09T...
rg -v '^(READY_FOR_REVIEW|KICK_CODER)($|[[:space:]])' "$TASK_FILE" > "$tmp" || true

cat "$tmp" > "$TASK_FILE"
printf "\nKICK_CODER %s\n" "$(ts_iso)" >> "$TASK_FILE"

echo "KICK_CODER set in $TASK_FILE"
