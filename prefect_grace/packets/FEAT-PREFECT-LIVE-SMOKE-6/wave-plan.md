# Wave Plan: FEAT-PREFECT-LIVE-SMOKE-6

## Objective
Prefect Live Smoke 6

## Waves
1. W00 — architect formalization and planner slicing.
2. W01 — coder implementation, verifier evidence, reviewer technical gate, architect wave gate.

## Packet Registry
- `FEAT-PREFECT-LIVE-SMOKE-6-W00-ARCHITECT-FORMALIZATION` — role `architect` — Architect Formalization
- `FEAT-PREFECT-LIVE-SMOKE-6-W00-PLANNER-SLICING` — role `planner` — Planner Slicing
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-LIVE-SMOKE-PACKET-6` — role `coder` — Live Smoke Packet 6
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-PREFECT-LIVE-SMOKE-6-W00-ARCHITECT-FORMALIZATION` depends on nothing
- `FEAT-PREFECT-LIVE-SMOKE-6-W00-PLANNER-SLICING` depends on FEAT-PREFECT-LIVE-SMOKE-6-W00-ARCHITECT-FORMALIZATION
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-LIVE-SMOKE-PACKET-6` depends on FEAT-PREFECT-LIVE-SMOKE-6-W00-PLANNER-SLICING
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-VERIFIER-EVIDENCE` depends on FEAT-PREFECT-LIVE-SMOKE-6-W01-LIVE-SMOKE-PACKET-6
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-REVIEWER-VERDICT` depends on FEAT-PREFECT-LIVE-SMOKE-6-W01-LIVE-SMOKE-PACKET-6, FEAT-PREFECT-LIVE-SMOKE-6-W01-VERIFIER-EVIDENCE
- `FEAT-PREFECT-LIVE-SMOKE-6-W01-ARCHITECT-WAVE-GATE` depends on FEAT-PREFECT-LIVE-SMOKE-6-W01-REVIEWER-VERDICT

## Exit Conditions
- Architect packet produced feature-local artifact deltas.
- Planner packet defined bounded execution packets.
- Coder, verifier, reviewer, and architect wave gate completed in order.
