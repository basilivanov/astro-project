#!/bin/bash
# ############################################################################
# AI_HEADER: SCRIPT_RUN_SMOKE
# ROLE: Canonical smoke loop wrapper for backend quick pipeline + targeted E2E.
# USAGE: ./scripts/run_smoke.sh
# ############################################################################

set -u

BACKEND_CMD=(docker exec astro-project-backend-1 python3 scripts/pipeline.py)
E2E_CMD=(./scripts/run_e2e.sh \
  e2e/admin.smoke.spec.ts \
  e2e/core-ux.spec.ts \
  e2e/report-create.spec.ts \
  e2e/quality.spec.ts)
CANARY_CMD=(./scripts/run_e2e.sh e2e/telegram-live-canary.spec.ts)

run_step() {
  local label="$1"
  shift

  echo "=== $label ==="
  echo "+ $*"
  "$@"
  local exit_code=$?

  if [ "$exit_code" -eq 0 ]; then
    echo "✅ $label passed"
  else
    echo "❌ $label failed with exit code $exit_code"
  fi

  echo
  return "$exit_code"
}

backend_exit=0
e2e_exit=0
canary_exit=0

run_step "Backend pipeline" "${BACKEND_CMD[@]}" || backend_exit=$?
run_step "Smoke E2E" "${E2E_CMD[@]}" || e2e_exit=$?
if [ "${RUN_DAY_LIVE_CANARY:-0}" = "1" ]; then
  run_step "Day live Telegram canary" "${CANARY_CMD[@]}" || canary_exit=$?
fi

echo "=== Smoke summary ==="
echo "backend_exit=$backend_exit"
echo "e2e_exit=$e2e_exit"
echo "canary_exit=$canary_exit"

if [ "$backend_exit" -eq 0 ] && [ "$e2e_exit" -eq 0 ] && [ "$canary_exit" -eq 0 ]; then
  echo "✅ Smoke loop passed"
  exit 0
fi

echo "❌ Smoke loop failed"
if [ "$backend_exit" -ne 0 ]; then
  exit "$backend_exit"
fi
if [ "$e2e_exit" -ne 0 ]; then
  exit "$e2e_exit"
fi
exit "$canary_exit"
