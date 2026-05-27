# Wave Plan: FEAT-DEMO-VISUAL

## Objective
Demo Visual

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer technical gate, architect wave gate.

## Packet Registry
- `FEAT-DEMO-VISUAL-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-DEMO-VISUAL-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-DEMO-VISUAL-W01-TEST-IMPLEMENTATION-PACKET` — role `coder` — Test Implementation Packet
- `FEAT-DEMO-VISUAL-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-DEMO-VISUAL-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-DEMO-VISUAL-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-DEMO-VISUAL-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-DEMO-VISUAL-W00-PLANNER-SLICING` depends on FEAT-DEMO-VISUAL-W00-ARCHITECT-FORMALIZATION
- `FEAT-DEMO-VISUAL-W01-TEST-IMPLEMENTATION-PACKET` depends on FEAT-DEMO-VISUAL-W00-PLANNER-SLICING
- `FEAT-DEMO-VISUAL-W01-VERIFIER-EVIDENCE` depends on FEAT-DEMO-VISUAL-W01-TEST-IMPLEMENTATION-PACKET
- `FEAT-DEMO-VISUAL-W01-REVIEWER-VERDICT` depends on FEAT-DEMO-VISUAL-W01-TEST-IMPLEMENTATION-PACKET, FEAT-DEMO-VISUAL-W01-VERIFIER-EVIDENCE
- `FEAT-DEMO-VISUAL-W01-ARCHITECT-WAVE-GATE` depends on FEAT-DEMO-VISUAL-W01-REVIEWER-VERDICT

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, reviewer, and architect wave gate completed in order.
