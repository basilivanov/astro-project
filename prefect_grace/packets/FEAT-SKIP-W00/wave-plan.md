# Wave Plan: FEAT-SKIP-W00

## Objective
Skip W00 feature

## Waves
1. W01 — Wave 1: Single slice

## Packet Registry
- `FEAT-SKIP-W00-W01-MAIN-SLICE` — role `coder` — Main Slice
- `FEAT-SKIP-W00-W01-VERIFY-SLICE` — role `verifier` — Verify Slice
- `FEAT-SKIP-W00-W01-REVIEW-SLICE` — role `reviewer` — Review Slice
- `FEAT-SKIP-W00-W01-ARCHITECT-GATE` — role `architect` — Architect Gate

## Dependency Rules
- `FEAT-SKIP-W00-W01-MAIN-SLICE` depends on FEAT-SKIP-W00-W00-PLANNER-SLICING
- `FEAT-SKIP-W00-W01-VERIFY-SLICE` depends on FEAT-SKIP-W00-W01-MAIN-SLICE
- `FEAT-SKIP-W00-W01-REVIEW-SLICE` depends on FEAT-SKIP-W00-W01-MAIN-SLICE, FEAT-SKIP-W00-W01-VERIFY-SLICE
- `FEAT-SKIP-W00-W01-ARCHITECT-GATE` depends on FEAT-SKIP-W00-W01-REVIEW-SLICE

## Exit Conditions
- accepted
