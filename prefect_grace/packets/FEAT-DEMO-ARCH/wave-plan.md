# Wave Plan: FEAT-DEMO-ARCH

## Objective
Demo Architect

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer verdict.

## Packet Registry
- `FEAT-DEMO-ARCH-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-DEMO-ARCH-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-DEMO-ARCH-W01-ARCHITECT-PACKET` — role `coder` — Architect Packet
- `FEAT-DEMO-ARCH-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-DEMO-ARCH-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict

## Dependency Rules
- `FEAT-DEMO-ARCH-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-DEMO-ARCH-W00-PLANNER-SLICING` depends on FEAT-DEMO-ARCH-W00-ARCHITECT-FORMALIZATION
- `FEAT-DEMO-ARCH-W01-ARCHITECT-PACKET` depends on FEAT-DEMO-ARCH-W00-PLANNER-SLICING
- `FEAT-DEMO-ARCH-W01-VERIFIER-EVIDENCE` depends on FEAT-DEMO-ARCH-W01-ARCHITECT-PACKET
- `FEAT-DEMO-ARCH-W01-REVIEWER-VERDICT` depends on FEAT-DEMO-ARCH-W01-ARCHITECT-PACKET, FEAT-DEMO-ARCH-W01-VERIFIER-EVIDENCE

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, and reviewer packets completed in order.
