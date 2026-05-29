# Execution Packet: FEAT-UNKNOWN-W01-DYNAMIC-PLANNING

## Objective
Dynamic planning auto-generated slice objective.

## Slice
- slice_id: `SLICE-FEAT-UNKNOWN`
- slice_slug: `feat-unknown`
- feature_id: `FEAT-UNKNOWN`
- packet_id: `FEAT-UNKNOWN-W01-DYNAMIC-PLANNING`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: []
- feature_dir: `prefect_grace/packets/FEAT-UNKNOWN`

## Source Of Truth
- `prefect_grace/platform/brief_intake.py`

## Impacted Modules
- `M-GRACE-BRIEF-INTAKE`
- `M-GRACE-ORCHESTRATOR`

## Allowed Write Scope
- `prefect_grace/platform/brief_intake.py`
- `prefect_grace/cli_commands/brief_intake.py`
- `prefect_grace/packets/FEAT-UNKNOWN/**`
- `tests/test_prefect_grace_brief_intake.py`
- `backend/**`

## Frozen Scope
- `frontend/**`
- `.worktrees/**`

## Must Preserve
- Create `calculate_bonus(is_partner: bool, amount_paid: float) -> dict` returning either `{"days": 15}` or `{"money": amount_paid * 0.2}`.
- Create unit tests for both scenarios.
- All tests must pass.

## Verification
Run strict validation check:

```bash
python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-UNKNOWN/EXECUTION_PACKET.md --strict --json
```

## Expected Evidence
- EVIDENCE/attempt-0002/evidence_manifest.json
- EVIDENCE/attempt-0002/SUMMARY.md
- EVIDENCE/attempt-0002/strict_validate_packet.json

## Escalation Triggers
- Parser cannot map standard brief sections.
- Generated packet fails strict validation.
