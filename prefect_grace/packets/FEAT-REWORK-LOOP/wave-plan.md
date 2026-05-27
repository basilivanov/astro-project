# Wave Plan: FEAT-REWORK-LOOP

## Objective
Rework loop feature

## Waves
1. W01 — Wave 1: Single slice

## Packet Registry
- `FEAT-REWORK-LOOP-W01-MAIN-SLICE` — role `coder` — Main Slice
- `FEAT-REWORK-LOOP-W01-VERIFY-SLICE` — role `verifier` — Verify Slice
- `FEAT-REWORK-LOOP-W01-REVIEW-SLICE` — role `reviewer` — Review Slice
- `FEAT-REWORK-LOOP-W01-ARCHITECT-GATE` — role `architect` — Architect Gate

## Dependency Rules
- `FEAT-REWORK-LOOP-W01-MAIN-SLICE` depends on FEAT-REWORK-LOOP-W00-PLANNER-SLICING
- `FEAT-REWORK-LOOP-W01-VERIFY-SLICE` depends on FEAT-REWORK-LOOP-W01-MAIN-SLICE
- `FEAT-REWORK-LOOP-W01-REVIEW-SLICE` depends on FEAT-REWORK-LOOP-W01-MAIN-SLICE, FEAT-REWORK-LOOP-W01-VERIFY-SLICE
- `FEAT-REWORK-LOOP-W01-ARCHITECT-GATE` depends on FEAT-REWORK-LOOP-W01-REVIEW-SLICE

## Exit Conditions
- accepted
