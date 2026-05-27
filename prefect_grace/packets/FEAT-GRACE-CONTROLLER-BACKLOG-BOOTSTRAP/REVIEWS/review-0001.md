# Review 0001 — FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP

status: rework_required
reviewer: codex
reviewed_at: 2026-05-27

## Verdict

Rework required.

The implementation delivers the main shape of the packet: a dedicated
`bootstrap-backlog` command, dry-run/apply separation, candidate output, warning
compaction, and temp-registry tests. The packet is not ready for acceptance yet
because bootstrap can still infer terminal registry state from non-terminal
evidence and can downgrade existing accepted registry records.

## Blockers

### 1. Evidence manifest recursion can mark a packet accepted from command-level `status: passed`

`prefect_grace/platform/controller_backlog_bootstrap.py:274-297` recursively
walks every nested dict/list in an evidence manifest. Combined with
`_normalize_artifact_status()` at `prefect_grace/platform/controller_backlog_bootstrap.py:232-242`,
any nested object with `"status": "passed"` becomes registry `accepted`.

That is too broad for bootstrap. Existing manifests commonly use command or
artifact-local status fields such as:

```json
{"commands": [{"status": "passed"}]}
```

Those fields prove command success, not packet acceptance. Bootstrap acceptance
must come only from bounded terminal evidence: explicit registry/domain verdict,
accepted review, packet summary current status, or a manifest field that is
defined as packet-level terminal state.

Required fix:

- stop recursively accepting generic nested `status` fields;
- restrict JSON evidence inference to top-level or schema-owned terminal fields;
- do not map local-gate `passed` to registry `accepted` unless the field is a
  packet-level domain/status field;
- add a regression test where `{"commands": [{"status": "passed"}]}` does not
  infer `accepted`.

### 2. Apply mode can downgrade existing accepted registry entries to `ready`

`build_backlog_bootstrap_plan()` falls back to `ready` when no terminal artifact
is found (`prefect_grace/platform/controller_backlog_bootstrap.py:480-489`), and
then `_planned_action()` returns `update` whenever current registry status differs
from the inferred status (`prefect_grace/platform/controller_backlog_bootstrap.py:402-416`).

That means an existing registry record like:

```yaml
registry_status: accepted
source_hash: <same hash>
```

can be downgraded to `ready` simply because the packet directory has no current
accepted review/summary/evidence artifact. Bootstrap should seed missing state;
it should not weaken an already terminal registry record when the source hash has
not changed.

Required fix:

- preserve existing `accepted` / `blocked` registry state when `source_hash` is
  unchanged and artifact inference is weaker or missing;
- only change terminal registry records when the source hash changed, evidence
  explicitly conflicts, or an explicit force/rerun flag is introduced;
- add a regression test: existing accepted registry + same source hash + no
  artifact evidence => `planned_action=noop`, status remains `accepted`.

### 3. Bootstrap ignores existing attempt evidence formats used by prior packets

The bootstrap artifact path only asks `latest_evidence_manifest()` for
`EVIDENCE/attempt-*/evidence_manifest.json`
(`prefect_grace/platform/controller_backlog_bootstrap.py:337-346`;
`prefect_grace/platform/packet_artifact_layout.py:99-109`).

Older accepted/reworked packets in this repo also use:

- `EVIDENCE/attempt-0002/evidence_manifest.md`;
- `EVIDENCE/attempt-0002/SUMMARY.md`;
- `EVIDENCE/attempt-0002/REWORK_SUMMARY.md`;
- `EVIDENCE/attempt-0002/REWORK_REPORT.md`.

Because those formats are ignored, the bootstrap plan can under-infer historical
state and leave packets as `ready` even when bounded attempt evidence exists.
This contradicts the packet goal of bootstrapping from the existing pipeline
history.

Required fix:

- extend evidence discovery to include markdown manifests and attempt summaries;
- parse only explicit terminal fields or sections from those files;
- keep rework summaries as blocker/rework evidence, not accepted evidence;
- add fixtures that mirror at least one real `attempt-0002` layout.

## Non-Blocking Notes

- The `bootstrap-backlog` CLI shape is reasonable, but `--dry-run` and `--apply`
  should ideally be mutually exclusive. Current behavior lets `--apply` win if
  both are provided.
- The compact skip warning work in `sync-packets` is the right direction.
- The repo-wide GRACE lint blocker in
  `prefect_grace/platform/prefect_e2e_real_dry_run_smoke.py` is pre-existing and
  not a blocker for this packet, as long as targeted lint for changed modules is
  clean.

## Verification Reviewed

- Reviewed implementation paths in:
  - `prefect_grace/platform/controller_backlog_bootstrap.py`
  - `prefect_grace/platform/backlog_controller.py`
  - `prefect_grace/platform/packet_artifact_layout.py`
  - `prefect_grace/cli.py`
  - `tests/test_prefect_grace_controller_backlog_bootstrap.py`
- Sampled real historical packet artifact layouts under `prefect_grace/packets/**/EVIDENCE/attempt-0002`.
- Ran a direct classifier check showing `{"commands": [{"status": "passed"}]}` currently maps to `accepted`.
- Sampled `bootstrap-backlog --dry-run --json` output for current project candidates.

## Required Rework

1. Restrict JSON artifact status inference to packet-level terminal fields.
2. Preserve existing terminal registry status when source hash is unchanged and
   bootstrap evidence is missing or weaker.
3. Support the existing markdown attempt evidence formats used in old packets.
4. Add tests for the three cases above.
5. Regenerate attempt evidence with targeted tests, strict packet validation,
   bootstrap dry-run output, and targeted GRACE lint for changed modules.

## Acceptance Criteria For Next Review

- Command-level or artifact-local `"status": "passed"` never infers registry
  `accepted`.
- Existing accepted/blocked registry entries are not downgraded on same source
  hash without explicit terminal conflicting evidence.
- Existing `attempt-0002` markdown evidence layouts are either parsed correctly
  or explicitly reported as unsupported with a blocker/warning.
- `bootstrap-backlog --dry-run --json` remains read-only.
- `bootstrap-backlog --apply --json` writes only the configured runtime registry.
- Source packet files and product backend/frontend files remain untouched.
