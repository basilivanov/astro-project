# Execution Packet: FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY-W01-LAYOUT-HELPERS

## Objective

Make packet review discovery YAML-first while preserving legacy markdown
compatibility. Review artifacts named `REVIEWS/review-000N.yaml` and
`REVIEWS/review-000N.yml` must be discoverable even when no markdown anchor
exists.

## Slice

- slice_id: `SLICE-GRACE-REVIEW-YAML-FIRST-DISCOVERY`
- slice_slug: `grace-review-yaml-first-discovery`
- feature_id: `FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY`
- packet_id: `FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY-W01-LAYOUT-HELPERS`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT-W01-STRUCTURED-REVIEW-ARTIFACTS, FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS-W01-GIT-NIGHTLY-GATES`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/review_artifact_contract.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/merge_steward.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/nightly_preflight_risk_report.py`
- `/opt/astro-project/prefect_grace/platform/context_bundle.py`

## Impacted Modules

- `M-GRACE-PACKET-ARTIFACT-LAYOUT`
- `M-GRACE-REVIEW-DISCOVERY`
- `M-GRACE-MERGE-STEWARD`
- `M-GRACE-GIT-MUTATION-GATE`
- `M-GRACE-NIGHTLY-PREFLIGHT-RISK`
- `M-GRACE-CONTEXT-BUNDLE`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/merge_steward.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/nightly_preflight_risk_report.py`
- `/opt/astro-project/prefect_grace/platform/context_bundle.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_artifact_layout.py`
- `/opt/astro-project/tests/test_prefect_grace_merge_steward.py`
- `/opt/astro-project/tests/test_prefect_grace_git_mutation_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_preflight_risk_report.py`
- `/opt/astro-project/tests/test_prefect_grace_context_bundle.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/executor_history.yaml`
- `/opt/astro-project/prefect_grace/packet_registry.yaml`
- `/opt/astro-project/prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST/**`
- `/opt/astro-project/prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM/**`
- `/var/lib/grace-orchestrator/**`

## Must Preserve

- Existing markdown-only review discovery remains valid.
- YAML review sidecars remain canonical over markdown for the same review stem.
- YAML-only accepted reviews pass merge, git mutation, and nightly preflight review gates.
- YAML-only packet-id mismatches fail closed.
- Latest review ordering is based on the numeric `review-000N` stem, not string suffix ordering.
- No runtime registry apply, Prefect/live agents, Docker, backend, frontend, or Playwright commands are used.

## Recommended Role Assignment

- coder: `Codex high`
- verifier: `Codex high`
- reviewer: `Codex high`
- rework policy: light resume for test or lint-only blockers; fresh session for contract changes outside this packet.

## Required Design Decisions

### 1. YAML-First Layout Helper

Update `latest_review(layout)` so it scans `review-*.yaml`, `review-*.yml`,
and `review-*.md`, accepts only numeric stems, and returns the highest numeric
review. For the same numeric review, prefer `.yaml`, then `.yml`, then `.md`.

### 2. Shared Discovery In Consumers

Update direct review discovery in merge steward, git mutation gate, nightly
preflight risk report, and context bundle where in scope. Prefer
`resolve_packet_layout()` plus `latest_review()` for latest-review decisions.

### 3. Regression Tests

Cover yaml-only, yml-only, md-only, same-stem precedence, numeric ordering,
YAML-only accepted reviews, YAML-only mismatch blocking, and context bundle
inclusion of YAML review artifacts.

## Verification

```bash
python3 -m pytest -q tests/test_prefect_grace_packet_artifact_layout.py tests/test_prefect_grace_merge_steward.py tests/test_prefect_grace_git_mutation_gate.py tests/test_prefect_grace_nightly_preflight_risk_report.py tests/test_prefect_grace_context_bundle.py
python3 -m compileall -q prefect_grace/platform/packet_artifact_layout.py prefect_grace/platform/merge_steward.py prefect_grace/platform/git_mutation_gate.py prefect_grace/platform/nightly_preflight_risk_report.py prefect_grace/platform/context_bundle.py
python3 scripts/grace_lint.py prefect_grace/platform/packet_artifact_layout.py
python3 scripts/grace_lint.py prefect_grace/platform/merge_steward.py
python3 scripts/grace_lint.py prefect_grace/platform/git_mutation_gate.py
python3 scripts/grace_lint.py prefect_grace/platform/nightly_preflight_risk_report.py
python3 scripts/grace_lint.py prefect_grace/platform/context_bundle.py
python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY/EXECUTION_PACKET.md --strict --json
python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY/EVIDENCE/attempt-0002/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY/EVIDENCE/attempt-0002 --json
git diff --check
```

## Expected Evidence

- `EVIDENCE/attempt-0001/evidence_manifest.json`
- `EVIDENCE/attempt-0001/yaml_first_discovery_summary.md`
- `EVIDENCE/attempt-0002/evidence_manifest.json`
- `EVIDENCE/attempt-0002/dependency_rework_summary.md`

## Escalation Triggers

- A direct review discovery consumer still ignores YAML-only review artifacts.
- Markdown-only review fallback regresses.
- YAML packet-id mismatch is accepted.
- Required verification fails and cannot be fixed within the allowed write scope.
