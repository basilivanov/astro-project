# Canonical Astrology Fixture Pack — Phase 1

> Legacy fixture rationale. Prefer `docs/FIXTURES.md` for the durable fixture home and `docs/regression_fixtures/canonical_astrology_fixture_manifest.v1.json` for the canonical manifest.

## Status

Phase 1 defines the canonical synthetic fixture contract only. This packet does **not** change product logic. It establishes a small fixture manifest that future backend pytest, benchmark harnesses, and frontend Playwright/report-read seeding can adopt without inventing overlapping personas.

Manifest source of truth:

- `docs/regression_fixtures/canonical_astrology_fixture_manifest.v1.json`

## Why this pack exists

The repo already has several fixture-adjacent regression surfaces:

- benchmark manifests for natal reruns;
- chart serialization and report-context tests;
- a high-latitude verification script;
- cosmogram / unknown-birth-time coverage;
- frontend read/report reliability work that will need stable seeded personas.

Those surfaces currently use a mix of inline payloads, ad-hoc names, or slice-specific cases. Phase 1 creates a **single practical pack of three synthetic personas** that can become the shared fixture vocabulary across backend and frontend regression work.

## Design goals

- Keep the pack **small and canonical**: one normal control, one house-system edge, one unknown-time case.
- Make the personas **synthetic and repo-safe**.
- Preserve compatibility with existing coverage patterns instead of forcing new product behavior.
- Define fixtures by **purpose and invariant class**, not just by input payload.
- Make later adoption straightforward for:
  - `pytest` parametrization,
  - benchmark/replay manifests,
  - Playwright seeded report/read flows,
  - evidence packets and controller docs.

## Fixture roster

### 1. `CF-BE-001-baseline-exact-time`

**Persona:** `Ava Meridian`

**Purpose**

Use this as the default exact-time natal control. It is the stable “nothing tricky should break here” persona for chart generation, serialization, report context, and read/report rendering.

**Canonical inputs**

- exact birth time known
- local birth datetime: `1992-08-14T06:32:00`
- location: `London, UK`
- coordinates: `51.5074`, `-0.1278`
- timezone: `Europe/London`
- default house system: `placidus`
- default report type: `natal_master`

**Invariant classes guarded**

- datetime normalization
- timezone round-trip integrity
- baseline Placidus chart shape
- report-context contract
- serialization contract
- read/report surface regression

**Practical adoption**

- first backend fixture to wire into report-context and serialization tests;
- first frontend seeded persona for happy-path natal report create/read smoke;
- preferred baseline control for future benchmark reruns when edge behavior is not under test.

### 2. `CF-WS-002-whole-sign-edge`

**Persona:** `Mira North`

**Purpose**

Use this as the canonical house-system edge fixture. It protects the repo’s known high-latitude risk area where Whole Sign-safe behavior, fallback, or explicit warning/disclosure matters more than ordinary exact-time chart generation.

**Canonical inputs**

- exact birth time known
- local birth datetime: `1980-10-30T19:50:00`
- location: `Monchegorsk, RU`
- coordinates: `67.9387`, `32.9241`
- timezone: `Europe/Moscow`
- requested/default house system: `placidus`
- expected safe-mode comparison target: `whole_sign`
- default report type: `natal_master`

**Invariant classes guarded**

- high-latitude safety
- Whole Sign fallback or selection behavior
- house-system disclosure/warning integrity
- timezone display on edge geography flows
- input-frame/read-surface regression for special-case charts

**Practical adoption**

- align future replacements for `tests/verify_high_lat.py` around one canonical synthetic persona;
- seed frontend read/report cases that must prove “edge chart still renders with honest disclosure”;
- keep controller packets explicit when a slice touches house calculation, input frame, or read-layer display rules.

### 3. `CF-BTU-003-birth-time-unknown`

**Persona:** `Noon Vale`

**Purpose**

Use this as the canonical unknown-birth-time persona. It guards cosmogram-style flows where the application must preserve `birth_time_known=false`, apply a deterministic midday fallback for calculations, and avoid accidentally presenting uncertain data as exact.

**Canonical inputs**

- birth time unknown
- local birth datetime input: `1990-01-01T05:00:00`
- canonical local fallback expectation: `12:00:00`
- location: `Moscow, RU`
- coordinates: `55.75`, `37.61`
- timezone: `Europe/Moscow`
- default house system: `placidus`
- default report type: `natal_master`

**Invariant classes guarded**

- `birth_time_known` flag propagation
- deterministic midday fallback normalization
- cosmogram chart-shape expectations
- reduced-certainty copy/contract integrity
- unknown-time read/report regression

**Practical adoption**

- align future unknown-time backend tests with `tests/test_cosmogram.py` semantics;
- seed frontend report/read fixtures that must show “time unknown” semantics explicitly;
- prevent regressions where downstream layers silently treat fallback time as user-known exact time.

## Fixture policy for this repo

### Synthetic-only

All three personas are synthetic. They are intended for deterministic QA, not realism benchmarking against real customer charts.

### Canonical over exhaustive

This pack is intentionally minimal. If later waves need more personas, they should extend the manifest with a clear new invariant class rather than clone near-duplicates.

### Shared IDs across backend and frontend

The fixture `id` values are designed to be reused across:

- backend pytest parametrization;
- benchmark/replay manifests;
- frontend seeded state;
- evidence packet headings;
- future docs and controller packets.

### No hidden product assumptions

Phase 1 documents what the fixtures are meant to guard. It does **not** mandate any new runtime adapter, DB seed path, or endpoint shape yet.

## Recommended adoption sequence

### Backend Phase 2

- add a tiny fixture loader/helper that reads the JSON manifest or a derived Python mapping;
- migrate inline natal/cosmogram/high-latitude regression payloads to fixture ids where useful;
- keep current test intent, only replacing duplicated inputs.

### Frontend Phase 2

- define a stable seeded report/read strategy keyed by fixture id;
- use the baseline persona for happy-path read UX,
- use the Whole Sign edge persona for special-case disclosure rendering,
- use the unknown-time persona for confidence/label handling.

### Benchmark / evidence Phase 2+

- reference these fixture ids inside future benchmark manifests and controller packets;
- record which invariant classes each packet is proving so fixture choice stays explicit.

## Non-goals in Phase 1

- no house calculation logic changes;
- no report prompt or text generation changes;
- no new DB seeds or API endpoints;
- no Playwright or pytest rewiring yet, beyond future tiny scaffolding work if explicitly requested.

## Initial mapping to existing context

This pack is intentionally aligned with existing repo signals:

- `tests/test_chart_serialization_normalization.py`
- `tests/test_cosmogram.py`
- `tests/verify_high_lat.py`
- `docs/GRACE_TEST_PLAYBOOK.md`
- `docs/ASTRO_QUALITY_BENCHMARK_HARNESS.md`
- `docs/benchmark_manifests/`

That alignment keeps future migration practical: adopt the fixture ids first, then consolidate payloads gradually.
