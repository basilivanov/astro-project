# Execution Packet: FEAT-GRACE-ORCHESTRATOR-BRIEF-INTAKE-W01-DYNAMIC-PLANNING

## Objective

Build the Brief Intake orchestrator which automatically parses a feature brief markdown file and generates a fully compliant, strict execution packet and sidecar YAML file, teaching the GRACE Architect role to automate dynamic planning.

## Slice

- slice_id: `SLICE-GRACE-ORCHESTRATOR-BRIEF-INTAKE`
- slice_slug: `grace-orchestrator-brief-intake`
- feature_id: `FEAT-GRACE-ORCHESTRATOR-BRIEF-INTAKE`
- packet_id: `FEAT-GRACE-ORCHESTRATOR-BRIEF-INTAKE-W01-DYNAMIC-PLANNING`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: []
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-BRIEF-INTAKE`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/brief_intake.py`
- `/opt/astro-project/prefect_grace/cli_commands/brief_intake.py`

## Impacted Modules

- `M-GRACE-BRIEF-INTAKE`
- `M-GRACE-ORCHESTRATOR`

## Allowed Write Scope

- `prefect_grace/platform/brief_intake.py`
- `prefect_grace/cli_commands/brief_intake.py`
- `prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-BRIEF-INTAKE/**`
- `tests/test_prefect_grace_brief_intake.py`

## Frozen Scope

- `backend/**`
- `frontend/**`
- `.worktrees/**`

## Must Preserve

- The Brief Intake system must parse markdown headers and lists without throwing syntax errors.
- Generated packets must pass the strict packet validation checks (`validate-packet --strict`).
- The sidecar YAML must correspond exactly to the generated markdown fields.
- Auto-generation must be dry-run by default unless explicitly applied.

## Verification

Run targeted tests to verify implementation:

```bash
pytest -q tests/test_prefect_grace_brief_intake.py
```

Run compile checks:

```bash
python3 -m compileall -q prefect_grace/platform/brief_intake.py prefect_grace/cli_commands/brief_intake.py
```

Run strict packet validation check on itself:

```bash
python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-BRIEF-INTAKE/EXECUTION_PACKET.md --strict --json
```

## Expected Evidence

- `EVIDENCE/attempt-0001/evidence_manifest.json`
- `EVIDENCE/attempt-0001/SUMMARY.md`
- `EVIDENCE/attempt-0001/strict_validate_packet.json`
- `EVIDENCE/attempt-0001/test_brief_intake.json`

## Escalation Triggers

- Parser cannot map standard brief sections.
- Generated packet fails strict validation.
- Writes occur outside allowed scope.
