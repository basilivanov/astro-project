#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose \
  -f docker-compose.yml \
  -f docker-compose.grace-worker.yml \
  --profile grace-worker \
  run --rm --no-deps grace_worker \
  bash -lc '
    set -euo pipefail
    python3 - <<PY
import prefect
print(f"prefect={prefect.__version__}")
PY
    curl -fsS "${PREFECT_API_URL%/api}/api/health"
    echo
    prefect work-pool inspect "${PREFECT_WORK_POOL:-astro-process}" >/tmp/grace-worker-work-pool.txt
    prefect work-queue ls --pool "${PREFECT_WORK_POOL:-astro-process}" >/tmp/grace-worker-work-queues.txt
    grep -F "${PREFECT_LIVE_QUEUE:-grace-live}" /tmp/grace-worker-work-queues.txt >/dev/null
    grep -F "${PREFECT_MONITORING_QUEUE:-grace-monitoring}" /tmp/grace-worker-work-queues.txt >/dev/null
    python3 -m prefect_grace.cli --help >/tmp/grace-worker-cli-help.txt
    git -C /opt/astro-project status --short >/tmp/grace-worker-git-status.txt
    test -S /var/run/docker.sock
    docker version --format "docker-client={{.Client.Version}}" >/tmp/grace-worker-docker.txt
    printf "grace worker smoke: ok\n"
  '
