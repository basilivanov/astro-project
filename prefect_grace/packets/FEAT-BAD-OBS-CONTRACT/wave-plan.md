# Wave Plan: FEAT-BAD-OBS-CONTRACT

## Objective
Bad observability contract

## Waves
1. W01 — Wave 1: Single slice

## Packet Registry
- `FEAT-BAD-OBS-CONTRACT-W01-MAIN` — role `coder` — Main
- `FEAT-BAD-OBS-CONTRACT-W01-VERIFY` — role `verifier` — Verify
- `FEAT-BAD-OBS-CONTRACT-W01-REVIEW` — role `reviewer` — Review

## Dependency Rules
- `FEAT-BAD-OBS-CONTRACT-W01-MAIN` depends on FEAT-BAD-OBS-CONTRACT-W00-PLANNER-SLICING
- `FEAT-BAD-OBS-CONTRACT-W01-VERIFY` depends on FEAT-BAD-OBS-CONTRACT-W01-MAIN
- `FEAT-BAD-OBS-CONTRACT-W01-REVIEW` depends on FEAT-BAD-OBS-CONTRACT-W01-MAIN, FEAT-BAD-OBS-CONTRACT-W01-VERIFY

## Exit Conditions
- All generated coder packets are implemented.
- Verifier evidence is recorded for the wave.
- Reviewer and architect gates are resolved.
