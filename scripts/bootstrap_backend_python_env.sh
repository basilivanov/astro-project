#!/usr/bin/env sh
set -eu

REQ_FILE="${BACKEND_REQUIREMENTS_FILE:-/app/backend/requirements.txt}"
STAMP_FILE="${BACKEND_PYTHON_ENV_STAMP:-/tmp/backend_requirements.sha256}"
PYTHON_USER_BASE="${PYTHONUSERBASE:-/tmp/python-user-base}"

export PYTHONUSERBASE="$PYTHON_USER_BASE"
export PATH="$PYTHON_USER_BASE/bin:$PATH"

if [ ! -f "$REQ_FILE" ]; then
  echo "[bootstrap_backend_python_env] skip: missing $REQ_FILE"
  exec "$@"
fi

REQ_HASH="$(sha256sum "$REQ_FILE" | awk '{print $1}')"
NEEDS_INSTALL=0

if ! python3 -m pytest --version >/dev/null 2>&1; then
  NEEDS_INSTALL=1
fi

if [ ! -f "$STAMP_FILE" ] || [ "$(cat "$STAMP_FILE" 2>/dev/null || true)" != "$REQ_HASH" ]; then
  NEEDS_INSTALL=1
fi

if [ "$NEEDS_INSTALL" = "1" ]; then
  echo "[bootstrap_backend_python_env] syncing Python deps from $REQ_FILE"
  mkdir -p "$PYTHON_USER_BASE" "$(dirname "$STAMP_FILE")"
  python3 -m pip install --disable-pip-version-check --user -r "$REQ_FILE"
  printf '%s' "$REQ_HASH" > "$STAMP_FILE"
fi

exec "$@"
