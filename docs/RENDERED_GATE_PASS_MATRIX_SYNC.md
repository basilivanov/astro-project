# Rendered Gate Pass Matrix Sync

## Purpose

This note is the minimal knowledge/docs-layer sync for the new rendered gate / pass matrix. It does **not** introduce a new runtime gate or duplicate packet-local verification matrices. It only records how the rendered pass matrix should be reflected in the durable GRACE graph/docs layer.

## Diagnosis

- The repo does not currently have a live `docs/GRACE/graph/` directory.
- The effective graph layer is `knowledge-graph.xml`.
- The effective global docs entrypoint for verification profiles/surfaces is `docs/REGRESSION_MAP.md`.
- Packet-local verification matrices already exist under `docs/*packet/verification-matrix*.md`; duplicating their full contents into the global graph/docs layer would create bloat and drift.

## Minimal sync rule

Reflect the rendered gate/pass matrix in the durable layer as a **routing/index artifact**, not as a second full matrix.

Keep only three things globally visible:

1. that rendered gate evidence belongs to the **observability evidence surface**;
2. which durable flows/modules are covered by the rendered gate view;
3. where the detailed packet-local or replay evidence continues to live.

## Proposed graph/doc representation

- Add one compact artifact node for the rendered gate sync note.
- Link that artifact to the durable verification surface and affected rendered flows.
- Keep packet-local matrices as the source of detailed scenario rows.
- Keep `docs/REGRESSION_MAP.md` as the place that explains the rendered pass matrix is an index/overlay over profiles `1-8`, not a replacement for the canonical regression profiles.

## Scope now

This sync is intentionally limited to:

- `FLOW-TODAY-PREMIUM`
- `FLOW-WEEK-BRIEF`
- `FLOW-READ-SURFACE`
- `M-FRONTEND-TODAY`
- `M-FRONTEND-WEEK`
- `M-FRONTEND-READ`
- observability evidence routing in `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md`

## Explicit non-goals

- no new gate execution logic;
- no new profile taxonomy beyond the existing allowed profiles;
- no duplication of packet-local verification matrices;
- no migration of all gate rows into `knowledge-graph.xml`.

## Planning note

If the rendered gate expands later, keep the global layer compact by adding only:

- one artifact reference;
- a few `documents` / `indexes` / `covers_rendered_gate` style edges;
- a pointer back to packet-local matrices and replay evidence.
