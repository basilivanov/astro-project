# Execution Packet: FEAT-GRACE-RUNTIME-REGISTRY-SOURCE-INTEGRITY-AUDIT-W01-ACCEPTED-SOURCE-EVIDENCE-AUDIT

## Objective

Add a read-only runtime/source integrity audit for accepted GRACE runtime
registry packets so operators can see accepted packets that should not be used
for live or nightly execution without investigation.

## Slice

- packet_id: `FEAT-GRACE-RUNTIME-REGISTRY-SOURCE-INTEGRITY-AUDIT-W01-ACCEPTED-SOURCE-EVIDENCE-AUDIT`
- feature_id: `FEAT-GRACE-RUNTIME-REGISTRY-SOURCE-INTEGRITY-AUDIT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-RUNTIME-SAFETY`

## Source Of Truth

- `prefect_grace/platform/registry_source_integrity_audit.py`
- `prefect_grace/cli_commands/prefect_smokes.py`
- `prefect_grace/cli_commands/parser.py`
- `prefect_grace/platform/evidence_manifest.py`
- `prefect_grace/platform/artifact_validator.py`
- `prefect_grace/platform/packet_artifact_layout.py`
- `prefect_grace/platform/state_store.py`

## Impacted Modules

- `M-GRACE-RUNTIME-REGISTRY`
- `M-GRACE-SOURCE-INTEGRITY`
- `M-GRACE-EVIDENCE`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- prefect_grace/platform/registry_source_integrity_audit.py
- prefect_grace/cli_commands/prefect_smokes.py
- prefect_grace/cli_commands/parser.py
- tests/test_prefect_grace_registry_source_integrity_audit.py
- tests/test_prefect_grace_cli_registry_source_integrity_audit.py
- tests/test_prefect_grace_cli_contracts.py
- prefect_grace/packets/FEAT-GRACE-RUNTIME-REGISTRY-SOURCE-INTEGRITY-AUDIT/**

## Frozen Scope

- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST/**
- prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM/**
- /var/lib/grace-orchestrator/**
- prefect_grace/flows/**
- prefect_grace/tasks/**

## Must Preserve

- The audit is read-only.
- No registry writes are performed.
- No source edits are performed outside this packet.
- No Prefect flows, deployments, workers, or live agents are started.
- JSON output remains bounded and keeps `result == data`.
- Source paths are rooted under the configured project repository root.
- Git tracking checks fail closed when git is unavailable or errors.

## Required Behavior

- Audit accepted runtime registry records by default.
- Inspect packet id, registry status, registry source path, source existence,
  git tracking, source hash freshness, latest evidence manifest validity, and
  latest review status.
- Emit bounded issue counts and a bounded issue list.
- Treat source missing, source untracked, source hash mismatch, invalid evidence
  manifest, source parse failure, and git tracking check failure as blocking.
- Treat missing evidence manifests as blocking when `EVIDENCE/` exists without a
  latest manifest, and as warning when no `EVIDENCE/` directory exists.

## Verification

- `python3 -m pytest -q tests/test_prefect_grace_registry_source_integrity_audit.py tests/test_prefect_grace_cli_registry_source_integrity_audit.py tests/test_prefect_grace_cli_contracts.py`
- `python3 -m compileall -q prefect_grace/platform/registry_source_integrity_audit.py prefect_grace/cli_commands/prefect_smokes.py prefect_grace/cli_commands/parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/registry_source_integrity_audit.py`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-RUNTIME-REGISTRY-SOURCE-INTEGRITY-AUDIT/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-RUNTIME-REGISTRY-SOURCE-INTEGRITY-AUDIT/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-RUNTIME-REGISTRY-SOURCE-INTEGRITY-AUDIT/EXECUTION_PACKET.md --json`
- `python3 -m prefect_grace.cli registry-source-integrity-audit --project prefect_grace/project.yaml --json --max-items 20`
- `git diff --check`

## Expected Evidence

- Targeted pytest output.
- Compileall output.
- Targeted GRACE lint output.
- Strict packet validation output.
- Evidence manifest validation output.
- Real read-only CLI audit summary showing expected accepted packet integrity
  findings.
- Git diff whitespace check output.

## Escalation Triggers

- The audit writes registry/runtime/source state.
- The audit starts Prefect, Docker, Playwright, or a live agent.
- The audit silently trusts untracked accepted source packets.
- The audit accepts an evidence manifest with missing, `UNKNOWN`, or mismatched
  `packet_id`.
