# Execution Packet: FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS-W01-GIT-NIGHTLY-GATES

## Objective

Make the remaining git, nightly, and live safety gates consume canonical YAML
review artifact status through `read_review_artifact_status()` /
`read_review_status()` instead of local markdown regex checks.

The canonical YAML sidecar must win over conflicting markdown text. Review
acceptance must fail closed when a YAML sidecar has a packet id mismatch.
Legacy markdown parsing may remain only inside the shared review helper.

## Slice

- slice_id: `SLICE-GRACE-REVIEW-YAML-GATE-CONSUMERS`
- slice_slug: `grace-review-yaml-gate-consumers`
- feature_id: `FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS`
- packet_id: `FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS-W01-GIT-NIGHTLY-GATES`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REVIEW-ARTIFACT-YAML-CONTRACT-W01-STRUCTURED-REVIEW-ARTIFACTS, FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE, FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK-W01-PREFLIGHT-RECHECK, FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/review_artifact_contract.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/nightly_preflight_risk_report.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_recheck.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_git_mutation_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_preflight_risk_report.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_batch_recheck.py`
- `/opt/astro-project/tests/test_prefect_grace_single_live_packet_pilot.py`

## Impacted Modules

- `M-GRACE-REVIEW-ARTIFACT-CONTRACT`
- `M-GRACE-GIT-MUTATION-GATE`
- `M-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT`
- `M-GRACE-NIGHTLY-BATCH-RECHECK`
- `M-GRACE-SINGLE-LIVE-PACKET-PILOT`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/nightly_preflight_risk_report.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_recheck.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_git_mutation_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_preflight_risk_report.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_batch_recheck.py`
- `/opt/astro-project/tests/test_prefect_grace_single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS/**`

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

- Git, nightly, and live gates continue to fail closed when review evidence is
  absent, invalid, or not accepted.
- Existing public result shapes remain stable: git gate review output keeps
  `present`, `accepted`, and `path`; nightly `_check_review()` keeps
  `(has_review, accepted)`.
- YAML sidecars take precedence over misleading markdown.
- YAML packet id mismatch blocks acceptance.
- Legacy markdown review parsing remains centralized inside
  `review_artifact_contract.py`.
- No runtime registry apply, no commits, no pushes, no live agents, no Docker,
  no backend/frontend services, and no Playwright runs are part of this packet.

## Recommended Role Assignment

- coder: `Codex high`
- verifier: `Codex high`
- reviewer: `Codex high`
- rework policy: light resume is acceptable for tests, evidence formatting, or
  lint-only issues; fresh session for any fail-open review acceptance bug.

## Required Changes

1. Update `git_mutation_gate.py` so latest review status is read through the
   canonical review helper with expected packet id from the parsed packet.
2. Update `nightly_preflight_risk_report.py` so `_check_review()` uses the
   canonical review helper, preserves its tuple return, and fails closed for
   acceptance when packet parsing fails.
3. Let `nightly_batch_recheck.py` inherit the updated `_check_review()`
   behavior without broader refactor.
4. Keep `single_live_packet_pilot.py` behavior compatible with git gate review
   output.
5. Add regression tests proving YAML sidecar precedence, YAML packet id
   mismatch blocking, and unquoted YAML timestamp acceptance.

## Verification

- `python3 -m pytest -q tests/test_prefect_grace_git_mutation_gate.py tests/test_prefect_grace_nightly_preflight_risk_report.py tests/test_prefect_grace_nightly_batch_recheck.py tests/test_prefect_grace_single_live_packet_pilot.py`
- `python3 -m compileall -q prefect_grace/platform/git_mutation_gate.py prefect_grace/platform/nightly_preflight_risk_report.py prefect_grace/platform/nightly_batch_recheck.py prefect_grace/platform/single_live_packet_pilot.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/git_mutation_gate.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/nightly_preflight_risk_report.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/nightly_batch_recheck.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/single_live_packet_pilot.py`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-REVIEW-YAML-GATE-CONSUMERS/EVIDENCE/attempt-0001 --json`
- `git diff --check`

## Expected Evidence

- `EVIDENCE/attempt-0001/evidence_manifest.json`
- `EVIDENCE/attempt-0001/bounded_summary.json`

## Escalation Triggers

- Any safety gate still treats markdown `accepted` as authoritative when a YAML
  sidecar says `rework_required` or has a mismatched packet id.
- Any updated gate accepts review after packet parsing fails.
- Any required verification command fails.
- Required changes need writes outside the allowed scope.
