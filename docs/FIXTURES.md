# FIXTURES

`docs/FIXTURES.md` is the durable home for canonical regression fixtures used by agents across backend, frontend, and evidence packets.

## Purpose

Use canonical fixture ids instead of re-explaining the same personas across tests and docs.

These fixtures exist to protect invariant classes, not to model real customer data.

## Canonical source

- Manifest: `docs/regression_fixtures/canonical_astrology_fixture_manifest.v1.json`
- Legacy rationale doc: `docs/CANONICAL_ASTROLOGY_FIXTURE_PACK_PHASE1.md`

## Fixture policy

- Synthetic-only
- Canonical over exhaustive
- Shared ids across backend, frontend, and docs
- Add new fixtures only when they protect a new invariant class

## Current canonical fixtures

### `CF-BE-001-baseline-exact-time`

- Persona: `Ava Meridian`
- Use for baseline exact-time natal happy-path verification
- Guards datetime normalization, timezone round-trip, chart serialization, and report/read surface stability

### `CF-WS-002-whole-sign-edge`

- Persona: `Mira North`
- Use for high-latitude and house-system edge verification
- Guards safe fallback/disclosure behavior and special-case chart rendering

### `CF-BTU-003-birth-time-unknown`

- Persona: `Noon Vale`
- Use for unknown birth-time flows
- Guards `birth_time_known=false`, deterministic midday fallback, and reduced-certainty presentation

## Adoption rule

When adding or updating a regression, prefer referencing one of the canonical fixture ids in tests, packet docs, and evidence notes instead of introducing duplicate inline personas.
