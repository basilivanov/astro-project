#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CONTAINER=${1:-astro-project-backend-1}
shift || true
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "[run_backend_tests] container ${CONTAINER} not running" >&2
  exit 1
fi
if [ $# -eq 0 ]; then
  docker exec -i "${CONTAINER}" python3 scripts/pipeline.py
else
  docker exec -i "${CONTAINER}" "$@"
fi
