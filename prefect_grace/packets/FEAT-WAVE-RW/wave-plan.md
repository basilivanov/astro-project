# Wave Plan: FEAT-WAVE-RW

## Objective
Wave Rework

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer technical gate, architect wave gate.

## Packet Registry
- `FEAT-WAVE-RW-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-WAVE-RW-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-WAVE-RW-W01-WAVE-PACKET` — role `coder` — Wave Packet
- `FEAT-WAVE-RW-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-WAVE-RW-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-WAVE-RW-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-WAVE-RW-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-WAVE-RW-W00-PLANNER-SLICING` depends on FEAT-WAVE-RW-W00-ARCHITECT-FORMALIZATION
- `FEAT-WAVE-RW-W01-WAVE-PACKET` depends on FEAT-WAVE-RW-W00-PLANNER-SLICING
- `FEAT-WAVE-RW-W01-VERIFIER-EVIDENCE` depends on FEAT-WAVE-RW-W01-WAVE-PACKET
- `FEAT-WAVE-RW-W01-REVIEWER-VERDICT` depends on FEAT-WAVE-RW-W01-WAVE-PACKET, FEAT-WAVE-RW-W01-VERIFIER-EVIDENCE
- `FEAT-WAVE-RW-W01-ARCHITECT-WAVE-GATE` depends on FEAT-WAVE-RW-W01-REVIEWER-VERDICT

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, reviewer, and architect wave gate completed in order.
