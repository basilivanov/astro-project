# Wave Plan: FEAT-DEMO

## Objective
Demo Feature

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer verdict.

## Packet Registry
- `FEAT-DEMO-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-DEMO-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-DEMO-W01-DEMO-REFACTOR-PACKET` — role `coder` — Demo Refactor Packet
- `FEAT-DEMO-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-DEMO-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict

## Dependency Rules
- `FEAT-DEMO-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-DEMO-W00-PLANNER-SLICING` depends on FEAT-DEMO-W00-ARCHITECT-FORMALIZATION
- `FEAT-DEMO-W01-DEMO-REFACTOR-PACKET` depends on FEAT-DEMO-W00-PLANNER-SLICING
- `FEAT-DEMO-W01-VERIFIER-EVIDENCE` depends on FEAT-DEMO-W01-DEMO-REFACTOR-PACKET
- `FEAT-DEMO-W01-REVIEWER-VERDICT` depends on FEAT-DEMO-W01-DEMO-REFACTOR-PACKET, FEAT-DEMO-W01-VERIFIER-EVIDENCE

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, and reviewer packets completed in order.
