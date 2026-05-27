# Wave Plan: FEAT-DEMO-2

## Objective
Demo Feature 2

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer verdict.

## Packet Registry
- `FEAT-DEMO-2-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-DEMO-2-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-DEMO-2-W01-LIFECYCLE-PACKET` — role `coder` — Lifecycle Packet
- `FEAT-DEMO-2-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-DEMO-2-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict

## Dependency Rules
- `FEAT-DEMO-2-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-DEMO-2-W00-PLANNER-SLICING` depends on FEAT-DEMO-2-W00-ARCHITECT-FORMALIZATION
- `FEAT-DEMO-2-W01-LIFECYCLE-PACKET` depends on FEAT-DEMO-2-W00-PLANNER-SLICING
- `FEAT-DEMO-2-W01-VERIFIER-EVIDENCE` depends on FEAT-DEMO-2-W01-LIFECYCLE-PACKET
- `FEAT-DEMO-2-W01-REVIEWER-VERDICT` depends on FEAT-DEMO-2-W01-LIFECYCLE-PACKET, FEAT-DEMO-2-W01-VERIFIER-EVIDENCE

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, and reviewer packets completed in order.
