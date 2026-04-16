# Wave Plan: FEAT-NOTIFY-CHECK

## Objective
Notify check

## Waves
1. W01 — Implementation and acceptance wave: Implement, verify, review, and architect-accept the first bounded feature slice.

## Packet Registry
- `FEAT-NOTIFY-CHECK-W01-LIVE-IMPLEMENTATION-PACKET` — role `coder` — Live Implementation Packet
- `FEAT-NOTIFY-CHECK-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-NOTIFY-CHECK-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-NOTIFY-CHECK-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-NOTIFY-CHECK-W01-LIVE-IMPLEMENTATION-PACKET` depends on FEAT-NOTIFY-CHECK-W00-PLANNER-SLICING
- `FEAT-NOTIFY-CHECK-W01-VERIFIER-EVIDENCE` depends on FEAT-NOTIFY-CHECK-W01-LIVE-IMPLEMENTATION-PACKET
- `FEAT-NOTIFY-CHECK-W01-REVIEWER-VERDICT` depends on FEAT-NOTIFY-CHECK-W01-LIVE-IMPLEMENTATION-PACKET, FEAT-NOTIFY-CHECK-W01-VERIFIER-EVIDENCE
- `FEAT-NOTIFY-CHECK-W01-ARCHITECT-WAVE-GATE` depends on FEAT-NOTIFY-CHECK-W01-REVIEWER-VERDICT

## Exit Conditions
- Coder packet is completed within scope.
- Verifier evidence is recorded.
- Reviewer technical gate is accepted or routed to rework.
- Architect wave gate accepts or blocks the wave.
