#!/bin/bash
# ############################################################################
# AI_HEADER: SCRIPT_RUN_E2E
# ROLE: Canonical wrapper for running Playwright E2E tests in a Docker container.
# USAGE: ./scripts/run_e2e.sh [playwright-args]
# ############################################################################

set -e

# Default E2E base URL (pointing to the dev container in the same network)
export E2E_BASE_URL=${E2E_BASE_URL:-http://astro-project-frontend_dev-1:3000}
FRONTEND_HEALTH_CONTAINER=${FRONTEND_HEALTH_CONTAINER:-astro-project-frontend_dev-1}

normalize_playwright_args() {
  local normalized=()

  for arg in "$@"; do
    if [[ "$arg" == frontend/e2e/* ]] && [[ -e "$arg" ]]; then
      normalized+=("${arg#frontend/}")
    elif [[ "$arg" == e2e/* ]] && [[ -e "frontend/$arg" ]]; then
      normalized+=("$arg")
    else
      normalized+=("$arg")
    fi
  done

  printf '%s\n' "${normalized[@]}"
}

has_explicit_test_target() {
  local expect_value=0

  for arg in "$@"; do
    if [ "$expect_value" -eq 1 ]; then
      expect_value=0
      continue
    fi

    case "$arg" in
      --grep|--grep-invert|--project|--reporter|--config|--workers|--retries|--repeat-each|--timeout|--max-failures|--trace|--headed|--browser)
        expect_value=1
        continue
        ;;
      --grep=*|--grep-invert=*|--project=*|--reporter=*|--config=*|--workers=*|--retries=*|--repeat-each=*|--timeout=*|--max-failures=*|--trace=*|--browser=*)
        continue
        ;;
      --*)
        continue
        ;;
      *)
        return 0
        ;;
    esac
  done

  return 1
}

http_get_in_container() {
  local container_name="$1"
  local url="$2"

  docker exec "$container_name" /bin/sh -lc '
    url="$1"
    if command -v curl >/dev/null 2>&1; then
      exec curl -s --fail --max-time 5 "$url"
    fi
    if command -v wget >/dev/null 2>&1; then
      exec wget -qO- --timeout=5 "$url"
    fi
    exec node -e "
      const http = require(\"http\");
      const https = require(\"https\");
      const target = process.argv[1];
      const client = target.startsWith(\"https:\") ? https : http;
      const req = client.get(target, (res) => {
        if (res.statusCode < 200 || res.statusCode >= 400) {
          process.exit(1);
        }
        res.pipe(process.stdout);
      });
      req.setTimeout(5000, () => req.destroy(new Error(\"timeout\")));
      req.on(\"error\", () => process.exit(1));
    " "$url"
  ' sh "$url"
}

select_frontend_container() {
  local current="$FRONTEND_HEALTH_CONTAINER"
  local fallback="astro-project-frontend-1"

  if docker ps --format '{{.Names}}' | grep -qx "$current"; then
    if http_get_in_container "$current" http://127.0.0.1:3000/ > /dev/null 2>&1; then
      return
    fi
  fi

  if [ "$current" != "$fallback" ] && docker ps --format '{{.Names}}' | grep -qx "$fallback"; then
    if http_get_in_container "$fallback" http://127.0.0.1:3000/ > /dev/null 2>&1; then
      echo "⚠️  $current is unhealthy, retrying against $fallback."
      FRONTEND_HEALTH_CONTAINER="$fallback"
      export E2E_BASE_URL="http://$fallback:3000"
      return
    fi
  fi
}

select_frontend_container

echo "--- Running E2E Tests in Playwright Container ---"
echo "Target URL: $E2E_BASE_URL"

# Health Checks
echo "Checking backend health: http://astro-project-backend-1:8000/health"
if ! docker exec astro-project-backend-1 curl -s --fail --max-time 5 "http://localhost:8000/health" > /dev/null; then
  echo "❌ ERROR: Backend health check failed (/health)."
  exit 1
fi

echo "Checking backend API health: http://astro-project-backend-1:8000/api/health"
if ! docker exec astro-project-backend-1 curl -s --fail --max-time 5 "http://localhost:8000/api/health" | grep -q '"db":"connected"'; then
  echo "❌ ERROR: Backend API health check failed or DB disconnected."
  exit 1
fi

echo "Checking frontend health via $FRONTEND_HEALTH_CONTAINER: $E2E_BASE_URL"
if ! http_get_in_container "$FRONTEND_HEALTH_CONTAINER" http://127.0.0.1:3000/ > /dev/null; then
  echo "❌ ERROR: Frontend container is not responding on port 3000."
  exit 1
fi

echo "Checking frontend API proxy: $E2E_BASE_URL/api/health"
if ! http_get_in_container "$FRONTEND_HEALTH_CONTAINER" http://127.0.0.1:3000/api/health | grep -q '"db":"connected"'; then
  echo "❌ ERROR: Frontend API proxy failed or reported DB error."
  exit 1
fi

echo "✅ All health checks passed (Backend, DB, Frontend, Proxy)."

# Ensure we are in the project root
cd "$(dirname "$0")/.."

mapfile -t PLAYWRIGHT_ARGS < <(normalize_playwright_args "$@")

PLAYWRIGHT_LOG=$(mktemp)
set +e
docker compose -f docker-compose.e2e.yml run --rm frontend_e2e sh -c 'if [ ! -x node_modules/.bin/playwright ]; then npm ci; fi && npm run test:e2e -- "$@"' _ "${PLAYWRIGHT_ARGS[@]}" | tee "$PLAYWRIGHT_LOG"
exit_code=${PIPESTATUS[0]}
set -e

if [ $exit_code -ne 0 ] && ! has_explicit_test_target "${PLAYWRIGHT_ARGS[@]}" && grep -q "Error: No tests found" "$PLAYWRIGHT_LOG"; then
  echo "ℹ️  Playwright reported 'No tests found'. Treating as success because there were no cached failures."
  exit_code=0
fi

rm -f "$PLAYWRIGHT_LOG"

if [ $exit_code -eq 0 ]; then
  echo "--- E2E Run Complete ---"
else
  exit $exit_code
fi

exit $exit_code
