#!/usr/bin/env bash
set -euo pipefail

cd "${GRACE_REPO_ROOT:-/opt/astro-project}"

git config --global --add safe.directory "${GRACE_REPO_ROOT:-/opt/astro-project}" >/dev/null 2>&1 || true
git config --global user.name "${GRACE_GIT_USER_NAME:-GRACE Worker}" >/dev/null
git config --global user.email "${GRACE_GIT_USER_EMAIL:-grace-worker@local.invalid}" >/dev/null

if [[ "${1:-}" == "worker" ]]; then
  shift || true
  exec prefect worker start \
    --type process \
    --pool "${PREFECT_WORK_POOL:-astro-process}" \
    --work-queue "${PREFECT_LIVE_QUEUE:-grace-live}" \
    --work-queue "${PREFECT_MONITORING_QUEUE:-grace-monitoring}" \
    --limit "${PREFECT_WORKER_LIMIT:-1}" \
    --install-policy never \
    "$@"
fi

exec "$@"
