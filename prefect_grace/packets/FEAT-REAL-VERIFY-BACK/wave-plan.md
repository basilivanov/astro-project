# Wave Plan: FEAT-REAL-VERIFY-BACK

## Objective
Real Verify Back

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer technical gate, architect wave gate.

## Packet Registry
- `FEAT-REAL-VERIFY-BACK-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-REAL-VERIFY-BACK-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-REAL-VERIFY-BACK-W01-TEST-IMPLEMENTATION-PACKET` — role `coder` — Test Implementation Packet
- `FEAT-REAL-VERIFY-BACK-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-REAL-VERIFY-BACK-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-REAL-VERIFY-BACK-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-REAL-VERIFY-BACK-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-REAL-VERIFY-BACK-W00-PLANNER-SLICING` depends on FEAT-REAL-VERIFY-BACK-W00-ARCHITECT-FORMALIZATION
- `FEAT-REAL-VERIFY-BACK-W01-TEST-IMPLEMENTATION-PACKET` depends on FEAT-REAL-VERIFY-BACK-W00-PLANNER-SLICING
- `FEAT-REAL-VERIFY-BACK-W01-VERIFIER-EVIDENCE` depends on FEAT-REAL-VERIFY-BACK-W01-TEST-IMPLEMENTATION-PACKET
- `FEAT-REAL-VERIFY-BACK-W01-REVIEWER-VERDICT` depends on FEAT-REAL-VERIFY-BACK-W01-TEST-IMPLEMENTATION-PACKET, FEAT-REAL-VERIFY-BACK-W01-VERIFIER-EVIDENCE
- `FEAT-REAL-VERIFY-BACK-W01-ARCHITECT-WAVE-GATE` depends on FEAT-REAL-VERIFY-BACK-W01-REVIEWER-VERDICT

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, reviewer, and architect wave gate completed in order.
