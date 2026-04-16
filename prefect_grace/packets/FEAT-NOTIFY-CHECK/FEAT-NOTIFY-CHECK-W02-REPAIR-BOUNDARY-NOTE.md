# FEAT-NOTIFY-CHECK W02 Repair Boundary Note

## Purpose

Bound the W02 repair loop after the original verifier run was blocked by sandbox startup failure and unresolved placeholder bindings.

## Environment Repair

- Packet execution for `FEAT-NOTIFY-CHECK` W01/W02 must run with `sandbox: danger-full-access`.
- Reviewer and architect reruns must use `resume_strategy: none` for this feature so they do not resume stale `feature_role` threads created under the broken workspace-write path.
- Reason: local `codex1 exec --sandbox workspace-write` fails in this environment with `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`, while `--dangerously-bypass-approvals-and-sandbox` succeeds in `/opt/astro-project`.

## Concrete Binding Verdict

- `M-FE-DAY-RUNTIME-INDICATOR` binds to `frontend/app/page.tsx`, `frontend/components/today/day-runtime-diagnostics-disclosure.tsx`, and `frontend/e2e/day-dev-indicator.spec.ts`.
- `e2e/<day-notify-check-spec>.spec.ts` can be concretized only as `frontend/e2e/day-dev-indicator.spec.ts` if the slice is downgraded to the existing Day runtime-indicator surface.
- `M-FE-NOTIFY-CHECK-INTAKE-DEFAULTS` has no concrete frontend file binding in the current repo.
- `M-FE-NOTIFY-CHECK-DISPATCH` has no concrete frontend file binding in the current repo.
- `existing-notify-check-endpoint` has no Day-owned frontend caller in the current repo; the only repo-level notify evidence found is backend notification plumbing and unrelated telemetry coverage in `frontend/e2e/bot-notify.spec.ts`.

## Implication

- The original W01/W02 feature contract is no longer blocked by environment alone.
- After environment repair, the remaining blocker is contract mismatch: the requested Day Notify-check intake/default/dispatch surface is not present in the repository as a Day-owned frontend flow.
- W02 cannot be honestly accepted without architect reslicing or a new implementation packet that first establishes a real product surface within allowed scope.

## Suggested Next Blocker Label

- `contract-mismatch-no-day-notify-surface`
