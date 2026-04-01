# REGRESSION MAP

`docs/REGRESSION_MAP.md` is the master agent-first regression map for this repo.

It replaces broad global duplication with one durable entrypoint for:

- canonical verification profiles;
- when each profile is required;
- the durable regression surfaces agents should think in;
- where slice-specific matrices live.

## Canonical profiles

### `backend:quick`

Required after every meaningful backend change.

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
```

### `frontend:quick`

Required after every meaningful frontend change.

```bash
./scripts/run_e2e.sh --last-failed
```

### `frontend:targeted`

Use when a single route or user flow changed and a focused Playwright rerun is enough.

```bash
./scripts/run_e2e.sh e2e/<file>.spec.ts -g "<case>"
```

### `smoke`

Use before high-confidence handoff on P0-level or broad UX-affecting work.

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/core-ux.spec.ts e2e/report-create.spec.ts e2e/quality.spec.ts
```

### `full-regression`

Use before release, deploy, or large merge.

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
./scripts/run_e2e.sh
```

### `llm-matrix`

Use only for expensive benchmark/release validation work.

```bash
X_TELEGRAM_AUTH=... python3 tests/grace_report_matrix.py
```

## Agent selection rule

- Pick the smallest honest profile that covers the changed surface.
- Escalate to smoke/full only when scope, risk, or handoff requires it.
- If a failure is a crash/500/build break, add or update a reproducing test first.

## Durable regression surfaces

These are the stable cross-slice surfaces that global docs should describe.

### Backend contract surface

- pipeline and deterministic pytest checks
- report/context/serialization contracts
- billing/access/runtime contract guards

### Frontend flow surface

- Playwright create/read/history/admin flows
- read-surface fallback and rendering safety
- targeted route regressions for changed UX

### Fixture surface

- canonical personas and invariant classes in `docs/FIXTURES.md`
- manifest-backed ids for reuse across backend, frontend, and evidence docs

### Packet-local surface

- slice verification matrices remain in packet folders such as `docs/*packet/verification-matrix*.md`
- use packet-local matrices for active waves and bounded implementation slices

## Current global anchors

- `AGENTS.md` — protocol and minimum required profiles
- `docs/TESTING.md` — testing home
- `docs/FIXTURES.md` — fixture home
- `docs/GRACE_HOME.md` — GRACE home
- `verification-matrix.md` — legacy root matrix retained for snapshot-specific detail and historical continuity

## Legacy note

Older global docs still exist for continuity, tooling, or historical context. When guidance overlaps, prefer this file and the three wave-1 homes above.
