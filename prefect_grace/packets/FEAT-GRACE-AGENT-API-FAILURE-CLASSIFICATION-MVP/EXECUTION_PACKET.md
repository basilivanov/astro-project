# Execution Packet: GRACE Agent API Failure Classification MVP

## Objective

Implement deterministic classification for agent/API provider failures so the
orchestrator can distinguish quality rework from infrastructure/provider
blockers. This packet must not add retry/backoff behavior and must not call live
agent APIs.

The immediate goal is to make failures such as rate limits, quota exhaustion,
auth errors, and network timeouts visible as typed runtime outcomes. The
synthetic edge matrix may add an `api_failure` dimension only after this
classifier exists.

## Slice

- slice_id: `SLICE-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP`
- slice_slug: `grace-agent-api-failure-classification-mvp`
- feature_id: `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP`
- packet_id: `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP-W01-SYNTHETIC-EDGE-MATRIX`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_edge_matrix.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_runner.py`

## Impacted Modules

- `M-GRACE-AGENT-API-FAILURE-CLASSIFICATION`
- `M-GRACE-CODEX-LAUNCHER`
- `M-GRACE-SYNTHETIC-EDGE-MATRIX`

## Recommended Role Assignment

- coder: `Sonnet high` or `Codex high`; pure classifier plus focused launcher integration.
- verifier: `Codex medium`; must run fake stderr/stdout classification tests and matrix smoke.
- reviewer: `Opus` or `Codex xhigh`; reviewer must ensure no retry policy is smuggled in.
- rework policy: fresh session if launcher behavior changes unexpectedly; light resume only for classifier pattern fixes.

## Required Design Decisions

### 1. Classification Only

This packet must classify failures but must not decide full retry/backoff policy.
The classifier returns typed metadata; later packets may consume it for executor
rotation, delay, or operator notification.

Minimum categories:

- `none`;
- `rate_limit`;
- `quota_exceeded`;
- `auth_failed`;
- `network_timeout`;
- `provider_unavailable`;
- `unknown_api_error`.

Minimum classifier output:

```json
{
  "category": "rate_limit",
  "retryable": true,
  "quality_rework": false,
  "operator_action_required": false,
  "reason": "HTTP 429 rate limit",
  "matched_pattern": "429"
}
```

### 2. Fake Samples Only

Tests must use fake stderr/stdout/run metadata samples. Do not call Codex,
Claude, agy, OpenRouter, OpenAI, cliproxy, or any live provider.

### 3. Launcher Mapping

`codex_launcher.py` may map classifier results to termination metadata, but it
must not immediately retry based on classification in this packet.

Expected mapping:

- `rate_limit` -> infrastructure blocker, retryable later;
- `network_timeout` -> infrastructure blocker, retryable later;
- `provider_unavailable` -> infrastructure blocker, retryable later;
- `quota_exceeded` -> environment/config blocker, operator action;
- `auth_failed` -> environment/config blocker, operator action;
- `unknown_api_error` -> environment blocker unless caller has stronger signal.

### 4. Synthetic Matrix Follow-Up

After classifier integration, synthetic matrix may add:

```text
api_failure: none, rate_limit, quota_exceeded, auth_failed, network_timeout, provider_unavailable, unknown_api_error
```

Invariants must ensure API failures do not become quality rework and do not
immediately reuse a stale session.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/agent_failure_classifier.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_edge_matrix.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_runner.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_invariants.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_agent_failure_classifier.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing Codex launcher success paths keep passing.
- Existing synthetic matrix smoke remains green.
- No live agents or provider APIs are called by tests.
- No retry/backoff policy is added in this packet.
- API/provider failures are not counted as coder quality rework.

## Required Implementation Shape

Add a pure classifier module:

```python
class AgentFailureClassification:
    category: str
    retryable: bool
    quality_rework: bool
    operator_action_required: bool
    reason: str
    matched_pattern: str


def classify_agent_failure(*, stdout_text: str = "", stderr_text: str = "", exit_code: int | None = None) -> AgentFailureClassification:
    ...
```

Integrate only enough launcher metadata so downstream code can see the category.
Do not start any retry loop.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_agent_failure_classifier.py \
  tests/test_prefect_grace_codex_launcher.py \
  tests/test_prefect_grace_synthetic_edge_matrix.py
```

Run static checks:

```bash
python3 -m compileall prefect_grace/platform prefect_grace/tasks/codex_launcher.py
python3 scripts/grace_lint.py prefect_grace/platform prefect_grace/tasks/codex_launcher.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP/EXECUTION_PACKET.md \
  --strict --json
```

## Expected Evidence

Write evidence under:

```text
EVIDENCE/attempt-0001/evidence_manifest.json
```

Evidence must include:

- classification table for fake stderr/stdout samples;
- test outputs;
- matrix smoke output after adding `api_failure` only if implemented;
- confirmation that no live APIs were called;
- confirmation that no retry/backoff policy was added.

## Escalation Triggers

Stop and ask controller if:

- classifier requires live API calls;
- retry/backoff policy appears necessary;
- provider-specific secrets or tokens are needed for tests;
- flow/pipeline code must change.

## Reviewer Gate

Reviewer must reject this packet if:

- rate limit/quota/auth failures are treated as quality rework;
- live provider APIs are called;
- retry/backoff policy is added;
- existing launcher success behavior changes;
- API failure classification is hidden only in logs and not returned as typed metadata.
