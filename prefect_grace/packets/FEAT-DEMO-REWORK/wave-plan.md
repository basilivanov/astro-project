# Wave Plan: FEAT-DEMO-REWORK

## Objective
Demo Rework

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer verdict.

## Packet Registry
- `FEAT-DEMO-REWORK-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-DEMO-REWORK-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-DEMO-REWORK-W01-REWORK-PACKET` — role `coder` — Rework Packet
- `FEAT-DEMO-REWORK-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-DEMO-REWORK-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict

## Dependency Rules
- `FEAT-DEMO-REWORK-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-DEMO-REWORK-W00-PLANNER-SLICING` depends on FEAT-DEMO-REWORK-W00-ARCHITECT-FORMALIZATION
- `FEAT-DEMO-REWORK-W01-REWORK-PACKET` depends on FEAT-DEMO-REWORK-W00-PLANNER-SLICING
- `FEAT-DEMO-REWORK-W01-VERIFIER-EVIDENCE` depends on FEAT-DEMO-REWORK-W01-REWORK-PACKET
- `FEAT-DEMO-REWORK-W01-REVIEWER-VERDICT` depends on FEAT-DEMO-REWORK-W01-REWORK-PACKET, FEAT-DEMO-REWORK-W01-VERIFIER-EVIDENCE

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, and reviewer packets completed in order.
