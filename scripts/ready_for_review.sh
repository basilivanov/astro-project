#!/usr/bin/env bash
set -euo pipefail

# Appends a dedicated READY_FOR_REVIEW marker line (with timestamp) to Task.md.
# Before appending, removes any existing marker lines to avoid duplicates.
#
# Usage:
#   ./scripts/ready_for_review.sh [task_file]

TASK_FILE="${1:-Task.md}"

ts_iso() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

[ -f "$TASK_FILE" ] || { echo "Task file not found: $TASK_FILE" >&2; exit 1; }

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

# Remove old markers (marker lines only; do NOT delete mentions in prose).
rg -v '^(READY_FOR_REVIEW|KICK_CODER)($|[[:space:]])' "$TASK_FILE" > "$tmp" || true
cat "$tmp" > "$TASK_FILE"

printf "\nREADY_FOR_REVIEW %s\n" "$(ts_iso)" >> "$TASK_FILE"
echo "READY_FOR_REVIEW set in $TASK_FILE"
