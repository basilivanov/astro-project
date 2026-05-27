# Feature Brief: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417

## Business Intent
Довести системные backend-хабы до strict GRACE addressability и development-grade observability: contracts, maps, function contracts, semantic blocks и плотные structured logs на значимых переходах без изменения бизнес-логики продукта.

## Desired Outcome
Backend GRACE contracts and observability hubs

## In Scope
- Packet-first execution for backend hub contract parity, observability density, and final canonical closeout.
- Close only residual strict-GRACE addressability gaps that still exist in the current backend hub files.
- Tighten structured observability on gateway, Day, scheduler, analytics, and trace/logging hub transitions using the existing `log_grace_event(...)`, `build_grace_log_payload(...)`, and correlation model.
- Align verifier and watcher tooling so packet-local and wave-final evidence can be read by `module`, `fn`, `block`, `event`, `correlation_id`, and `trace_id`.
- Target `backend/app/main.py`, `backend/app/logging_utils.py`, `backend/app/middleware/correlation.py`, `backend/app/services/day_brief.py`, `backend/app/services/day_brief_validators.py`, `backend/app/services/scheduler.py`, `backend/app/services/analytics.py`, selected `tools/log_watch/*.py`, `tools/post_test_review.py`, and targeted backend tests.

## Out of Scope
- DayBrief, WeekBrief, report-read, billing, auth, and referral business-semantic changes.
- Frontend or visual work.
- Deep decomposition of `backend/app/services/report_workflow.py`.
- Repo-wide logging redesign or a new logging transport.
- Unbounded cleanup outside the approved backend hub and tooling scope.

## Impacted Surfaces
- backend: central gateway, trace/logging, Day, scheduler, and analytics hubs.
- observability: packet-local read-only review in W01 and W02, canonical `today-week` closeout in W03.
- tooling: post-test verdict and selected log-watch helpers only where needed to surface stable hub landmarks.

## Impacted GRACE Artifacts
- Feature-local packet-first artifacts only by default.
- Root GRACE canon stays frozen unless execution uncovers a real governing-artifact mismatch.

## Acceptance Criteria
- Current backend hub work stays bounded to existing business semantics and the existing GRACE logging envelope.
- Residual hub contract, map, function-contract, and semantic-block gaps are closed or explicitly proven already satisfied by targeted tests.
- Gateway, Day, scheduler, analytics, and trace/logging evidence is attributable by `module`, `fn`, `block`, `event`, `correlation_id`, and `trace_id`.
- Packet-local observability in W01 and W02 is explicit and reviewer-readable; W03 owns the final canonical `today-week` verdict.
- The feature completes without planner involvement unless a real decomposition change appears.

## Visual Expectations
-

## Wave Proposal
1. W00 formalizes the packet-first backend-hub slice.
2. W01 closes residual backend hub contract and addressability gaps.
3. W02 aligns dense hub observability and verdict tooling.
4. W03 owns the final canonical `today-week` backend closeout.

## Open Decisions
- None. Current root canon already covers the governing invariants, defects, and evidence policy for this backend slice.
