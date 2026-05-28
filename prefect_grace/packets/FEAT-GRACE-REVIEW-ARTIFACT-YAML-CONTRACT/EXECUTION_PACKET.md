# Execution Packet: FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT-W01-STRUCTURED-REVIEW-ARTIFACTS

## Objective

Make YAML review artifacts the canonical contract for GRACE review status while
keeping markdown review parsing as a legacy fallback for existing reviews.

## Slice

- packet_id: `FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT-W01-STRUCTURED-REVIEW-ARTIFACTS`
- feature_id: `FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-RUNTIME-SAFETY`

## Source Of Truth

- `prefect_grace/platform/review_artifact_contract.py`
- `prefect_grace/platform/packet_artifacts.py`
- `prefect_grace/platform/controller_backlog_bootstrap.py`
- `prefect_grace/platform/registry_source_integrity_audit.py`
- `prefect_grace/platform/merge_steward.py`

## Impacted Modules

- `M-GRACE-REVIEW-CONTRACT`
- `M-GRACE-RUNTIME-REGISTRY`
- `M-GRACE-MERGE-STEWARD`
- `M-GRACE-PACKET-ARTIFACTS`

## Allowed Write Scope

- prefect_grace/platform/review_artifact_contract.py
- prefect_grace/platform/packet_artifacts.py
- prefect_grace/platform/controller_backlog_bootstrap.py
- prefect_grace/platform/registry_source_integrity_audit.py
- prefect_grace/platform/merge_steward.py
- tests/test_prefect_grace_review_artifact_contract.py
- tests/test_prefect_grace_packet_artifact_layout.py
- tests/test_prefect_grace_controller_backlog_bootstrap.py
- tests/test_prefect_grace_registry_source_integrity_audit.py
- tests/test_prefect_grace_merge_steward.py
- prefect_grace/packets/FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT/**

## Frozen Scope

- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST/**
- prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM/**
- /var/lib/grace-orchestrator/**

## Must Preserve

- Existing callers of `write_review()` still receive the markdown review path.
- Existing markdown review artifacts remain readable through legacy fallback.
- Canonical YAML sidecars fail closed when required review contract fields are
  missing, invalid, or packet identity mismatches.
- No runtime registry apply, Prefect/live agent, Docker, backend, frontend, or
  Playwright flows are started for this packet.

## Required Behavior

- Parse `REVIEWS/review-000N.yaml` and `.yml` as canonical review contracts.
- When a markdown review has a same-stem YAML sidecar, the YAML sidecar wins.
- Require canonical YAML to include `status` or `verdict`, `reviewer` or
  `generated_by`, and `reviewed_at` or `timestamp`.
- If canonical YAML includes `packet_id`, it must match the expected packet id.
- Accept terminal review statuses `accepted`, `blocked`, and `rework_required`.
- Treat invalid or missing YAML verdict/status as a fail-closed result.
- Keep markdown regex parsing only as legacy fallback when no YAML exists.

## Verification

- `python3 -m pytest -q tests/test_prefect_grace_review_artifact_contract.py tests/test_prefect_grace_packet_artifact_layout.py tests/test_prefect_grace_controller_backlog_bootstrap.py tests/test_prefect_grace_registry_source_integrity_audit.py tests/test_prefect_grace_merge_steward.py`
- `python3 -m compileall -q prefect_grace/platform/review_artifact_contract.py prefect_grace/platform/packet_artifacts.py prefect_grace/platform/controller_backlog_bootstrap.py prefect_grace/platform/registry_source_integrity_audit.py prefect_grace/platform/merge_steward.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/review_artifact_contract.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_artifacts.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/controller_backlog_bootstrap.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/registry_source_integrity_audit.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/merge_steward.py`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT/EXECUTION_PACKET.md --json`
- `git diff --check`

## Expected Evidence

- Targeted pytest output.
- Compileall output.
- Targeted GRACE lint output for each touched platform module.
- Strict packet validation output.
- Evidence manifest validation output.
- Git diff whitespace check output.
- Confirmation that frozen/runtime/backend/frontend/live-agent scopes were not
  touched.

## Escalation Triggers

- A YAML review sidecar is present but markdown status is still trusted.
- Missing or invalid canonical review verdict/status is treated as accepted.
- Review packet id mismatch is ignored.
- Runtime registry, live Prefect agents, Docker, backend, frontend, Playwright,
  or frozen packet/state files are mutated.
