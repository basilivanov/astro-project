# gracectl CI and cron integration

This document describes how to run `gracectl` inside GitHub Actions (or any generic CI) and how to schedule watch/demo loops via cron on a self-hosted runner.

## GitHub Action workflow

File: `.github/workflows/gracectl.yml`

```yaml
name: gracectl slices

on:
  workflow_dispatch:
    inputs:
      slice-id:
        description: 'Slice identifier from docs/gracectl.md (e.g. FEED-PERSONALIZED-DAILY)'
        required: true
        default: FEED-PERSONALIZED-DAILY
      verify-flags:
        description: 'Extra flags for gracectl slice verify (e.g. --frontend --backend)'
        required: false
        default: '--frontend --backend'
  schedule:
    - cron: '15 5 * * *' # daily 05:15 UTC
  push:
    paths:
      - '.github/workflows/gracectl.yml'
      - 'gracectl/**'
      - 'docs/gracectl.md'
      - 'requirements.txt'

jobs:
  gracectl:
    name: Gracectl slice verify
    runs-on: ubuntu-latest
    timeout-minutes: 45
    env:
      PYTHONUNBUFFERED: '1'
      SLICE_ID: 'FORECAST-LADDER-CATALOG-FLIP'
      VERIFY_FLAGS: '--frontend --backend'
    steps:
      - uses: actions/checkout@v4

      - if: github.event_name == 'workflow_dispatch'
        run: |
          echo "SLICE_ID=${{ github.event.inputs['slice-id'] }}" >> "$GITHUB_ENV"
          echo "VERIFY_FLAGS=${{ github.event.inputs['verify-flags'] }}" >> "$GITHUB_ENV"

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - run: python -m gracectl.cli env check --config gracectl.yaml

      - run: python -m gracectl.cli slice verify ${SLICE_ID} ${VERIFY_FLAGS}

      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: gracectl-logs
          path: |
            logs/gracectl
            test-results
```

### Step overview
1. `actions/checkout` pulls the repo.
2. `actions/setup-python` installs Python 3.11 with pip cache.
3. Dependencies are installed from `requirements.txt`.
4. `gracectl env check` validates docker services, configs, docs, and slices.
5. `gracectl slice verify` runs the requested profile (defaults to backend+frontend).
6. Artifacts (logs, test-results) are uploaded on any outcome.
7. Optional `workflow_dispatch` inputs allow ad‑hoc slice overrides.

Swap `ubuntu-latest` with your self-hosted runner label or reuse the same blueprint in GitLab, Jenkins, or Argo by porting these steps.

## Cron watcher

File: `scripts/cron/gracectl_watch.sh`

```bash
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
```

### Usage notes
- Pass slice ID as first argument to override default (`FEED-PERSONALIZED-DAILY`).
- Override `VERIFY_FLAGS`/`WATCH_FLAGS`/`RUN_DEMO` via env vars.
- Optional virtualenv activation happens automatically when `venv/` exists.
- Output streams into timestamped files under `logs/gracectl/cron`.

### Crontab entry
Example entry (`crontab -e` on the host running docker-compose):

```
*/30 * * * * /opt/astro-project/scripts/cron/gracectl_watch.sh FORECAST-LADDER-CATALOG-FLIP \
  >> /opt/astro-project/logs/gracectl/cron/cron.log 2>&1
```

This runs every 30 minutes, verifying the slice, running watch hooks, and appending to `cron.log` (individual log files stay per run). Adjust cadence based on slice volatility.
