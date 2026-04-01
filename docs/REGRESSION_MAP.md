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
- Today score-disclosure quality contract and score-tap disclosure behavior
- Week day-card detail disclosure behavior and user-facing day-card semantics

### Fixture surface

- canonical personas and invariant classes in `docs/FIXTURES.md`
- manifest-backed ids for reuse across backend, frontend, and evidence docs

### Packet-local surface

- slice verification matrices remain in packet folders such as `docs/*packet/verification-matrix*.md`
- use packet-local matrices for active waves and bounded implementation slices
- active packet-local slices currently include Today screen, Week UI, natal daily backend, Today/Week detail-layer refactor, frontend functional reliability, and frontend test hardening
- the current Day/Week v2 wave also has a narrow audit artifact in `docs/day_week_contract_audit_v2_2026-04-02.md` covering the materialized day score-disclosure contract and weekly day-card detail system

### Observability evidence surface

- post-test observability is a first-class verification surface, not a note after green tests
- use `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md` as the durable memo for required digest/replay/trace review and verdict vocabulary
- for `Today`, `Week`, `Admin`, `Catalog`, and `Billing`, verification is incomplete without explicit evidence review
- rendered gate/pass-matrix views should stay as compact routing overlays on top of canonical profiles and packet-local matrices, not duplicated global matrices

### Auth and webapp entry surface

- Telegram signed-auth remains a durable entry lane through WebApp init data and bot-assisted identity/profile routing
- keep global docs aligned with `knowledge-graph.xml` whenever auth entry scopes expand beyond the existing webapp/bot lane

## Current global anchors

- `AGENTS.md` — protocol and minimum required profiles
- `docs/TESTING.md` — testing home
- `docs/FIXTURES.md` — fixture home
- `docs/GRACE_HOME.md` — GRACE home
- `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md` — observability gate memo
- `docs/RENDERED_GATE_PASS_MATRIX_SYNC.md` — minimal global sync for rendered gate/pass-matrix routing
- `verification-matrix.md` — legacy root matrix retained for snapshot-specific detail and historical continuity

## Legacy note

Older global docs still exist for continuity, tooling, or historical context. When guidance overlaps, prefer this file and the three wave-1 homes above.
