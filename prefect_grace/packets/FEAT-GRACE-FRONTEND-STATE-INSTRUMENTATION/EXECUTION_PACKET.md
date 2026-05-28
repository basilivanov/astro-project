# Execution Packet: FEAT-GRACE-FRONTEND-STATE-INSTRUMENTATION-W01-HEADLESS-TESTING

## Objective

Implement frontend state instrumentation and headless testing infrastructure to enable
debugging and testing of browser state during packet execution.

Currently, when GRACE orchestrator runs packets that modify frontend code, there is no
way to verify browser state, test UI rendering, or debug frontend behavior in headless
mode. This packet establishes:

1. **Browser state exposure** for headless testing tools
2. **Playwright e2e infrastructure** with mock backend
3. **Correlation ID round-trip** (browser → backend → logs)
4. **Structured frontend logging** aligned with backend logging spine (GRACE Canon §8)
5. **Test instrumentation gates** for frontend verification

This enables packets to prove frontend changes work through automated headless tests,
not just "it compiles" checks.

## Slice

- slice_id: `SLICE-GRACE-FRONTEND-STATE-INSTRUMENTATION`
- slice_slug: `grace-frontend-state-instrumentation`
- feature_id: `FEAT-GRACE-FRONTEND-STATE-INSTRUMENTATION`
- packet_id: `FEAT-GRACE-FRONTEND-STATE-INSTRUMENTATION-W01-HEADLESS-TESTING`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-STRUCTURED-LOGGING-MVP-W01-LOG-ENVELOPE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FRONTEND-STATE-INSTRUMENTATION`

## Source Of Truth

Patterns from solarsage-astro project:
- `../solarsage-astro/grace/packets/W-1.5.md` - Playwright e2e with mock backend
- `../solarsage-astro/grace/packets/W-1.6.md` - Logging spine with correlation IDs
- `../solarsage-astro/grace/packets/W-1.7.md` - Frontend log shipping
- `../solarsage-astro/grace/packets/W-2.8.md` - Vitest test runner

GRACE Canon section 8: Structured logs и log-driven development

## Impacted Modules

- `M-GRACE-PLAYWRIGHT-E2E` (new)
- `M-GRACE-FRONTEND-LOGGER` (new)
- `M-GRACE-CORRELATION-MIDDLEWARE` (new)
- `M-GRACE-MOCK-BACKEND-SERVER` (new)
- `M-GRACE-E2E-PACKET-RUNNER` (update)
- `M-GRACE-EVIDENCE-MANIFEST` (update)

## Allowed Write Scope

- `/opt/astro-project/frontend/tests/e2e/**`
- `/opt/astro-project/frontend/tests/fixtures/**`
- `/opt/astro-project/frontend/lib/log/index.ts`
- `/opt/astro-project/frontend/lib/log/correlation.ts`
- `/opt/astro-project/frontend/lib/api/_client.ts`
- `/opt/astro-project/frontend/playwright.config.ts`
- `/opt/astro-project/frontend/package.json`
- `/opt/astro-project/backend/app/middleware/correlation.py`
- `/opt/astro-project/backend/app/api/_log.py`
- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/tests/test_prefect_grace_e2e_packet_runner.py`
- `/opt/astro-project/tests/e2e/test_frontend_correlation.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-FRONTEND-STATE-INSTRUMENTATION/**`

## Frozen Scope

- `/opt/astro-project/backend/app/models/**`
- `/opt/astro-project/backend/app/services/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Playwright tests run in headless mode by default (no GUI).
- Mock backend reuses existing JSON fixtures (no duplication).
- Correlation IDs are UUID v4, injected on every fetch as `X-Correlation-Id` header.
- Frontend logger uses ring buffer (max 200 envelopes, oldest dropped on overflow).
- Log envelope matches backend format (GRACE Canon §8.1).
- All timestamps are ISO-8601 UTC.
- Tests are bounded (max 5 minutes per spec, max 30 seconds per test).
- No external dependencies (no Sentry, no third-party log shipping).

## Required Design Decisions

### 1. Playwright E2E Infrastructure

**Three test projects** (following solarsage-astro W-1.5 pattern):

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    {
      name: 'fixtures-only',
      use: { baseURL: 'http://localhost:3000' },
      // Visual snapshot parity with mock data
    },
    {
      name: 'mock-backend',
      use: { baseURL: 'http://localhost:3000' },
      // Real fetch calls against in-process mock server
    },
    {
      name: 'error-states',
      use: { baseURL: 'http://localhost:3000' },
      // 401/422/500 error UI rendering
    },
  ],
});
```

**Mock backend server** (`tests/fixtures/server.ts`):
- Express/Fastify in-process server on random port
- Reuses existing JSON fixtures from `tests/fixtures/*.json`
- Supports correlation ID echo (returns `X-Correlation-Id` in response)
- Supports error injection (401, 422, 500 via query params)

### 2. Frontend Structured Logging

**Log envelope format** (aligned with backend GRACE Canon §8.1):

```typescript
interface LogEnvelope {
  module: string;           // "M-FRONTEND-API-CLIENT"
  fn: string;               // "fetchToday"
  block: string;            // "HTTP_REQUEST"
  event: string;            // "fetch_started"
  result: "ok" | "fail" | "retry" | "skip";
  correlation_id: string;   // UUID v4
  timestamp: string;        // ISO-8601 UTC
  level: "debug" | "info" | "warn" | "error";
  payload?: Record<string, any>;
}
```

**Ring buffer** (`lib/log/index.ts`):
- Max 200 envelopes in memory
- Oldest dropped on overflow with warning
- Flush on page unload (optional, best-effort)

### 3. Correlation ID Middleware

**Frontend** (`lib/log/correlation.ts`):
- Generate UUID v4 on every fetch
- Inject as `X-Correlation-Id` header
- Store in log envelope

**Backend** (`app/middleware/correlation.py`):
- Extract `X-Correlation-Id` from request headers
- Inject into structured logger context
- Echo in response headers
- Include in all backend log envelopes

### 4. Frontend Log Shipping (Optional, deferred to W02)

**Endpoint** (`/api/_log`):
- POST batch of log envelopes
- Rate limit: 200 envelopes/min per user
- Backpressure: 429 retry with exponential backoff
- Kill-switch: `GRACE_LOG_SHIPPING=on|off` env var

**Shipper** (`lib/log/shipper.ts`):
- Batch: 50 envelopes or 5s timeout (whichever first)
- Retry: 429 → 2s, 5xx → exponential backoff (2s→60s, max 5 retries)
- Hard cap: 1000 envelopes, oldest dropped with warning

**Note**: Log shipping is **optional** for W01. Focus is on correlation round-trip and e2e testing.

### 5. E2E Packet Runner Integration

**New module** (`e2e_packet_runner.py`):
- Wraps managed_packet_runner with Playwright test execution
- Starts Next.js dev server on random port
- Starts mock backend server on random port
- Runs Playwright tests with `--project=mock-backend`
- Collects test results and screenshots
- Shuts down servers on exit

**Evidence artifacts**:
- `playwright-report/` - HTML test report
- `test-results/` - Screenshots and traces
- `execution_trace.jsonl` - Backend logs with correlation IDs
- `frontend_logs.jsonl` - Frontend logs (if shipping enabled)

### 6. Verification Gates

**Gate 1: Playwright installed**
```bash
npx playwright --version
```

**Gate 2: Mock backend starts**
```bash
node tests/fixtures/server.js &
curl -s http://localhost:$PORT/health
```

**Gate 3: Correlation round-trip**
```bash
# Frontend sends X-Correlation-Id
# Backend echoes it in response
# Backend logs include correlation_id
```

**Gate 4: E2E tests pass**
```bash
npx playwright test --project=mock-backend
```

**Gate 5: Frontend logger envelope**
```bash
# Check log envelope matches GRACE Canon §8.1
# Check ring buffer overflow handling
```

## Implementation Requirements

1. **Install Playwright** (`frontend/package.json`):
   ```json
   {
     "devDependencies": {
       "@playwright/test": "^1.40.0"
     },
     "scripts": {
       "test:e2e": "playwright test",
       "test:e2e:ui": "playwright test --ui"
     }
   }
   ```

2. **Create Playwright config** (`frontend/playwright.config.ts`):
   - Three projects: fixtures-only, mock-backend, error-states
   - Headless by default
   - Screenshots on failure
   - Trace on first retry
   - Max 5 minutes per spec, 30 seconds per test

3. **Create mock backend server** (`frontend/tests/fixtures/server.ts`):
   - Express/Fastify on random port
   - Reuse JSON fixtures from `tests/fixtures/*.json`
   - Echo `X-Correlation-Id` header
   - Support error injection via query params

4. **Create frontend logger** (`frontend/lib/log/index.ts`):
   - `log(envelope: LogEnvelope)` function
   - Ring buffer (max 200 envelopes)
   - ISO-8601 timestamp generation
   - Overflow warning

5. **Create correlation middleware** (`frontend/lib/log/correlation.ts`):
   - `generateCorrelationId()` - UUID v4
   - `injectCorrelationId(headers: Headers)` - Add X-Correlation-Id
   - `extractCorrelationId(response: Response)` - Read from response

6. **Update API client** (`frontend/lib/api/_client.ts`):
   - Inject correlation ID on every fetch
   - Log fetch_started, fetch_completed, fetch_failed events
   - Include correlation_id in log envelopes

7. **Create backend correlation middleware** (`backend/app/middleware/correlation.py`):
   - Extract `X-Correlation-Id` from request
   - Inject into logger context
   - Echo in response headers

8. **Create log endpoint** (`backend/app/api/_log.py`):
   - POST `/api/_log` accepts batch of envelopes
   - Rate limit: 200 envelopes/min per user
   - Validate envelope schema
   - Write to stdout (structured JSON)

9. **Create e2e packet runner** (`prefect_grace/platform/e2e_packet_runner.py`):
   - Start Next.js dev server
   - Start mock backend server
   - Run Playwright tests
   - Collect results and artifacts
   - Shutdown servers

10. **Update evidence manifest** (`prefect_grace/platform/evidence_manifest.py`):
    - Add `playwright_report` evidence type
    - Add `frontend_logs` evidence type
    - Validate correlation ID presence in logs

11. **Create e2e tests**:
    - `tests/e2e/test_frontend_correlation.py` - Correlation round-trip
    - `frontend/tests/e2e/today.spec.ts` - Today page rendering
    - `frontend/tests/e2e/error-states.spec.ts` - 401/500 error UI

## Acceptance Criteria

- Playwright installed and `npx playwright --version` works.
- Mock backend server starts and responds to health check.
- Correlation ID round-trip: frontend → backend → logs.
- E2E tests pass in headless mode.
- Frontend logger envelope matches GRACE Canon §8.1.
- Ring buffer overflow handling works (200 envelope limit).
- Test artifacts collected: HTML report, screenshots, traces.
- Evidence manifest validates playwright_report and frontend_logs.
- No external dependencies (no Sentry, no third-party services).
- All tests bounded (max 5 min per spec, 30s per test).

## Verification

Run Playwright installation:

```bash
cd frontend
npm install
npx playwright install
npx playwright --version
```

Run mock backend server:

```bash
cd frontend
node tests/fixtures/server.js &
curl -s http://localhost:$PORT/health
kill %1
```

Run e2e tests:

```bash
cd frontend
npx playwright test --project=mock-backend
```

Run correlation round-trip test:

```bash
pytest tests/e2e/test_frontend_correlation.py -v
```

Run frontend logger tests:

```bash
cd frontend
npm test -- lib/log/index.test.ts
```

Run e2e packet runner:

```bash
python3 -m prefect_grace.cli e2e-packet-run \
  --packet-id FEAT-EXAMPLE-W01-TASK \
  --dry-run
```

Verify evidence artifacts:

```bash
ls -lh prefect_grace/state/artifacts/*/playwright-report/
ls -lh prefect_grace/state/artifacts/*/test-results/
ls -lh prefect_grace/state/artifacts/*/execution_trace.jsonl
```

## Expected Evidence

- Playwright installation output (`npx playwright --version`).
- Mock backend health check output.
- E2E test results (all pass).
- Correlation round-trip proof (frontend log + backend log with matching correlation_id).
- Frontend logger unit test output.
- E2E packet runner output with artifacts.
- Evidence manifest validation output.
- Confirmation zero backend models/services changed.
- Confirmation zero pipeline.py/run_e2e.sh changes.

## Escalation Triggers

- Playwright tests timeout (exceed 5 min per spec).
- Correlation IDs don't match between frontend and backend logs.
- Frontend logger envelope deviates from GRACE Canon §8.1.
- Ring buffer overflow breaks execution (should warn, not crash).
- Mock backend server fails to start or respond.
- E2E packet runner fails to collect artifacts.
- Evidence manifest rejects valid playwright reports.
- External dependencies introduced (Sentry, third-party log shipping).
