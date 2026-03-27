#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/astro-project"
REVISION="${1:-nightly-$(date +%F)}"
EVIDENCE_DIR="$ROOT/test-results/evidence/$REVISION"

mkdir -p "$EVIDENCE_DIR"

python3 "$ROOT/automation/export_evidence.py" \
  --dest "$REVISION" \
  --hours 24 \
  --copy "$ROOT/test-results/grace-report.json" \
  --copy "$ROOT/logs/gracectl" \
  --copy "$ROOT/test-results/failures"
