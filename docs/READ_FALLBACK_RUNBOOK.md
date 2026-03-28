# /read/[id] Fallback Runbook

## Scope

This runbook describes how `/read/[id]` should behave when the report payload is degraded but still potentially recoverable for the user. The canonical frontend entrypoint is `frontend/app/read/[id]/page.tsx:1`, and the backend API surface serving the page lives in `backend/app/main.py:1`.

Use this document when debugging read-surface regressions, clarifying expected UX for partial report payloads, or deciding whether the user should see inline fallback content, a retry CTA, or a support/history CTA.

## Sources of truth

- Frontend read surface: `frontend/app/read/[id]/page.tsx:1`
- Report block parsing and fallback card: `frontend/components/blocks/report-renderer.tsx:1`
- Backend report API / regenerate endpoints: `backend/app/main.py:1`

## Decision matrix

| Scenario | Expected `/read/[id]` behavior | Operator action |
| --- | --- | --- |
| Missing `chunks` or `chunks=[]`, report still `pending`/non-completed | Show pending state, do not render empty/failure copy | Wait, poll, or inspect generation job |
| Missing `chunks` or unusable `chunks`, report is `completed` | Show empty state (`report-empty-state`) because there is no readable content left | Inspect backend serialization / chunk persistence |
| Malformed section payload, but readable text can still be extracted | Render section with fallback card / safe text instead of crashing | Keep user on page; log and repair formatter upstream |
| Full read fetch failure / 4xx / 5xx / auth issue | Show `ErrorState` with retry via page reload path | Check API/auth/network first |
| Report status is terminal failure | Show dedicated failure surface with retry CTA and support/history CTA | User may regenerate; support can inspect history and logs |

## Scenario details

### 1. Missing chunks

`prepareRenderableSections()` on the frontend treats `report.chunks` as the canonical section source. When the backend returns no chunks, behavior splits by report status:

- If status is not `completed`, `frontend/app/read/[id]/page.tsx:1` sets `showPendingState` and renders the in-progress state.
- If status is `completed` and no usable sections remain, the page sets `showEmptyState` and renders `report-empty-state`.

Operationally, this means “missing chunks” is **not** automatically a failure page. It is interpreted as either:

- generation still in progress, or
- a completed report whose content envelope is empty/corrupted beyond safe recovery.

### 2. Malformed sections

Per `frontend/components/blocks/report-renderer.tsx:1`, the read surface attempts to salvage malformed content in this order:

1. `parseReportBlocks(content)` tries to normalize supported block JSON.
2. If blocks cannot be safely produced, `extractReportFallbackText(content)` tries to recover readable text.
3. If some content exists but cannot be structurally parsed, `frontend/app/read/[id]/page.tsx:1` falls back to `SECTION_FALLBACK_MESSAGE` so the user still understands the section degraded.

Expected UX:

- The page must keep the section visible.
- The page must not throw runtime errors because one chunk is malformed.
- The page should prefer recovered human-readable text over technical JSON/raw object output.
- Fallback is per-section, so one bad chunk must not blank the whole report.

### 3. Retry behavior

There are two retry layers and they mean different things:

#### Fetch retry

If loading `/api/reports/{id}` fails, `frontend/app/read/[id]/page.tsx:1` stores `error` and shows `ErrorState compact` with `onRetry={loadReport}`.

Use this when:

- the read request failed transiently,
- auth/init data was temporarily unavailable,
- backend returned transport-level or route-level failure.

#### Regenerate retry

If the report exists but is in a terminal failed state, the page renders the dedicated failure surface and the button `read-regenerate-button` triggers `POST /api/reports/{id}/regenerate` from `frontend/app/read/[id]/page.tsx:1`.

Use this when:

- the report assembly failed,
- retrying the same fetch will not fix missing generated output,
- product wants a user-facing self-heal path.

### 4. Support / history CTA

The support CTA is intentionally lightweight: on the failure surface the user gets `read-failure-history-link`, which routes to `/reports/history` and emits `catalog.read_support_click` telemetry in `frontend/app/read/[id]/page.tsx:1`.

Use history/support CTA instead of forcing endless retries when:

- regeneration already failed once,
- the user may want another report instead of blocking here,
- support needs the user to preserve context and navigate to an inspectable report list.

This CTA is part of the terminal failure path, not the per-section malformed-content fallback path.

## Backend expectations

The backend in `backend/app/main.py:1` should preserve a stable contract for read payloads:

- `report.status` communicates whether the UI should expect pending/completed/failed behavior.
- `chunks` should be present when readable report sections exist.
- malformed or legacy chunk content should still prefer a recoverable text payload over silent omission.
- regenerate endpoint behavior must remain idempotent enough for the read-page retry CTA.

When debugging, verify both:

- `GET /api/reports/{id}` shape and `report.status`, and
- `POST /api/reports/{id}/regenerate` behavior for failed reports.

## QA checklist

For `/read/[id]`, confirm at least the following before handoff:

- malformed content still renders readable fallback text;
- empty completed reports show `report-empty-state`;
- failed reports show retry + history CTA;
- transport/load failure shows `ErrorState` retry;
- no console/runtime crash occurs when a single chunk is malformed.

## Acceptance commands

- `cd frontend && npm exec tsc -- --noEmit`
- `./scripts/run_e2e.sh e2e/quality.spec.ts -g "read fallback"`
