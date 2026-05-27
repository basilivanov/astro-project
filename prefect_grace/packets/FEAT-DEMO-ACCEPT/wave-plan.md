# Wave Plan: FEAT-DEMO-ACCEPT

## Objective
Demo Accept

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer verdict.

## Packet Registry
- `FEAT-DEMO-ACCEPT-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-DEMO-ACCEPT-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-DEMO-ACCEPT-W01-ACCEPT-PACKET` — role `coder` — Accept Packet
- `FEAT-DEMO-ACCEPT-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-DEMO-ACCEPT-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict

## Dependency Rules
- `FEAT-DEMO-ACCEPT-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-DEMO-ACCEPT-W00-PLANNER-SLICING` depends on FEAT-DEMO-ACCEPT-W00-ARCHITECT-FORMALIZATION
- `FEAT-DEMO-ACCEPT-W01-ACCEPT-PACKET` depends on FEAT-DEMO-ACCEPT-W00-PLANNER-SLICING
- `FEAT-DEMO-ACCEPT-W01-VERIFIER-EVIDENCE` depends on FEAT-DEMO-ACCEPT-W01-ACCEPT-PACKET
- `FEAT-DEMO-ACCEPT-W01-REVIEWER-VERDICT` depends on FEAT-DEMO-ACCEPT-W01-ACCEPT-PACKET, FEAT-DEMO-ACCEPT-W01-VERIFIER-EVIDENCE

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, and reviewer packets completed in order.
