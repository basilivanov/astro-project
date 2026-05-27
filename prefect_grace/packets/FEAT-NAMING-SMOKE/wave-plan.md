# Wave Plan: FEAT-NAMING-SMOKE

## Objective
Naming Smoke

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer technical gate, architect wave gate.

## Packet Registry
- `FEAT-NAMING-SMOKE-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-NAMING-SMOKE-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-NAMING-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET` — role `coder` — Live Implementation Packet
- `FEAT-NAMING-SMOKE-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-NAMING-SMOKE-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-NAMING-SMOKE-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-NAMING-SMOKE-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-NAMING-SMOKE-W00-PLANNER-SLICING` depends on FEAT-NAMING-SMOKE-W00-ARCHITECT-FORMALIZATION
- `FEAT-NAMING-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET` depends on FEAT-NAMING-SMOKE-W00-PLANNER-SLICING
- `FEAT-NAMING-SMOKE-W01-VERIFIER-EVIDENCE` depends on FEAT-NAMING-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET
- `FEAT-NAMING-SMOKE-W01-REVIEWER-VERDICT` depends on FEAT-NAMING-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET, FEAT-NAMING-SMOKE-W01-VERIFIER-EVIDENCE
- `FEAT-NAMING-SMOKE-W01-ARCHITECT-WAVE-GATE` depends on FEAT-NAMING-SMOKE-W01-REVIEWER-VERDICT

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, reviewer, and architect wave gate completed in order.
