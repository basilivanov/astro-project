# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-VERIFY-REPAIRED-ARTIFACT-CONSISTENCY

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-VERIFY-REPAIRED-ARTIFACT-CONSISTENCY`

## Summary
Check that the repaired architect artifacts are executable enough for a subsequent planner pass and do not force invalid canonical observability ownership.

## Wave
W01

## Role
verifier

## Reasoning
high

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-RUNTIME-INDICATOR-CLEAN/evidence/artifact-consistency.md

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-REPAIR-ARCHITECT-SLICE-BOUNDARIES
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W00-ARCHITECT-FORMALIZATION

## Acceptance Criteria
- Verifier records PASS/FAIL for artifact consistency.
- Verifier confirms impacted_modules and waves are populated in architect_manifest.
- Verifier confirms W01 goal, allowed_write_scope, frozen_scope, and acceptance_criteria are not placeholder-only.
- Verifier confirms frontend visual evidence requirements are present in the verification matrix.
- Verifier confirms no canonical flow commands exist unless observability_scope is `wave_final`.
- Verifier confirms implementation remains blocked if the consistency script fails.

## Verification Profile
- backend: Artifact consistency check only; no backend service behavior is verified.
- frontend: Artifact consistency check only; no Playwright execution is expected until a later implementation packet is generated.
- observability: Confirm the repaired artifact set does not invent a Today/Week canonical gate and keeps observability ownership aligned with the architect wave.
- execution:
  - backend_commands:
    - python3 - <<'PY'
import json
from pathlib import Path
import xml.etree.ElementTree as ET
base = Path('/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean')
manifest = json.loads((base / 'architect_manifest.json').read_text())
plan = ET.parse(base / 'development-plan.slice.expandable-dev-indicator-on-week-screen-clean.xml').getroot()
wave = plan.find(".//wave[@id='W01']")
assert wave is not None, 'missing W01 wave'
assert manifest.get('impacted_modules'), 'architect_manifest impacted_modules is empty'
assert manifest.get('waves'), 'architect_manifest waves is empty'
assert (wave.findtext('goal') or '').strip() not in ('', '-', 'None'), 'W01 goal is incomplete'
allowed = [(n.text or '').strip() for n in wave.findall('.//allowed_write_scope/file')]
assert any(v and v != '-' for v in allowed), 'allowed_write_scope is incomplete'
frozen = [(n.text or '').strip() for n in wave.findall('.//frozen_scope/file')]
assert frozen, 'frozen_scope missing'
criteria = [(n.text or '').strip() for n in wave.findall('.//acceptance_criteria/criterion')]
assert any(v and v != '-' for v in criteria), 'acceptance criteria incomplete'
obs = (wave.findtext('observability_scope') or '').strip()
assert obs in ('none', 'packet_local', 'wave_final'), f'invalid observability_scope: {obs!r}'
cmds = [(n.text or '').strip() for n in wave.findall('.//canonical_flow_commands/command')]
if obs != 'wave_final':
    assert not any(v and v != '-' for v in cmds), 'canonical flow commands must not be present outside wave_final'
if obs == 'wave_final':
    assert any(v and v != '-' for v in cmds), 'wave_final requires canonical flow commands'
vm = (base / 'verification-matrix.slice.expandable-dev-indicator-on-week-screen-clean.md').read_text().lower()
for needle in ('week', 'dev', 'prod', 'visual evidence'):
    assert needle in vm, f'missing verification matrix coverage: {needle}'
print('artifact-consistency PASS')
PY
  - frontend_commands:
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: False
  - requires_frontend_visual: False
  - artifact_globs:
    - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/architect_manifest.json
    - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/development-plan.slice.expandable-dev-indicator-on-week-screen-clean.xml
    - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/verification-matrix.slice.expandable-dev-indicator-on-week-screen-clean.md
    - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/knowledge-graph.slice.expandable-dev-indicator-on-week-screen-clean.xml
    - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/ARCHITECT_HANDOFF.md
    - /opt/astro-project/prefect_grace/packets/FEAT-WEEK-RUNTIME-INDICATOR-CLEAN/evidence/artifact-consistency.md

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_commands:
  - python3 - <<'PY'
import json
from pathlib import Path
import xml.etree.ElementTree as ET
base = Path('/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean')
manifest = json.loads((base / 'architect_manifest.json').read_text())
plan = ET.parse(base / 'development-plan.slice.expandable-dev-indicator-on-week-screen-clean.xml').getroot()
wave = plan.find(".//wave[@id='W01']")
assert wave is not None, 'missing W01 wave'
assert manifest.get('impacted_modules'), 'architect_manifest impacted_modules is empty'
assert manifest.get('waves'), 'architect_manifest waves is empty'
assert (wave.findtext('goal') or '').strip() not in ('', '-', 'None'), 'W01 goal is incomplete'
allowed = [(n.text or '').strip() for n in wave.findall('.//allowed_write_scope/file')]
assert any(v and v != '-' for v in allowed), 'allowed_write_scope is incomplete'
frozen = [(n.text or '').strip() for n in wave.findall('.//frozen_scope/file')]
assert frozen, 'frozen_scope missing'
criteria = [(n.text or '').strip() for n in wave.findall('.//acceptance_criteria/criterion')]
assert any(v and v != '-' for v in criteria), 'acceptance criteria incomplete'
obs = (wave.findtext('observability_scope') or '').strip()
assert obs in ('none', 'packet_local', 'wave_final'), f'invalid observability_scope: {obs!r}'
cmds = [(n.text or '').strip() for n in wave.findall('.//canonical_flow_commands/command')]
if obs != 'wave_final':
    assert not any(v and v != '-' for v in cmds), 'canonical flow commands must not be present outside wave_final'
if obs == 'wave_final':
    assert any(v and v != '-' for v in cmds), 'wave_final requires canonical flow commands'
vm = (base / 'verification-matrix.slice.expandable-dev-indicator-on-week-screen-clean.md').read_text().lower()
for needle in ('week', 'dev', 'prod', 'visual evidence'):
    assert needle in vm, f'missing verification matrix coverage: {needle}'
print('artifact-consistency PASS')
PY
- observability_scope: none
- touches_frontend: False
- requires_frontend_visual: False
- artifact_globs:
  - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/architect_manifest.json
  - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/development-plan.slice.expandable-dev-indicator-on-week-screen-clean.xml
  - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/verification-matrix.slice.expandable-dev-indicator-on-week-screen-clean.md
  - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/knowledge-graph.slice.expandable-dev-indicator-on-week-screen-clean.xml
  - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/ARCHITECT_HANDOFF.md
  - /opt/astro-project/prefect_grace/packets/FEAT-WEEK-RUNTIME-INDICATOR-CLEAN/evidence/artifact-consistency.md
- include_day_live_canary: False

## Reviewer Gate
- Reject if the verifier records PASS without running the artifact consistency command.
- Reject if any frontend implementation scope is inferred from the feature brief rather than repaired architect artifacts.
- Reject if the verifier allows `today-week` observability without architect-authorized wave_final ownership and canonical emitter commands.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-REPAIR-ARCHITECT-SLICE-BOUNDARIES

## Notes
- This verifier is packet-local artifact verification only.
- It intentionally does not run backend quick, Playwright, or Today/Week canonical observability because no implementation packet exists yet.
