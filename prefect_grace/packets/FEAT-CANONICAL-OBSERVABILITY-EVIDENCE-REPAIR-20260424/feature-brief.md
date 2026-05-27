# Feature Brief: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424

## Business Intent
Repair the canonical post-test observability evidence path so Today, Week, Admin, and Catalog gates produce fresh, correctly classified GRACE evidence. The prior backend refactor stopped at W02 because repeated evidence refresh still failed with Today/Week degradation and stale Admin/Catalog evidence.

## Desired Outcome
Canonical observability evidence repair for Today Week Admin Catalog

## In Scope
- Fix misleading `FAIL_NO_EVIDENCE` classification when canonical logs contain concrete degraded evidence with trace/request/correlation identifiers.
- Ensure Today evidence reports `unexpected-degradation` for real auth/text-layer degradation instead of no-evidence.
- Ensure Week evidence clearly reports chunk parse fallback/degradation with stable reason codes or fixes the producer if fallback is unintended.
- Refresh or repair Admin and Catalog evidence freshness so reviewer can distinguish stale evidence from missing evidence.
- Preserve GRACE module contracts, maps, function contracts, and paired START/END blocks for touched modules.
- Do not hide real degradation by marking it clean; acceptance requires clean evidence or explicit expected-degradation reason codes approved by architect.

## Out of Scope
- Do not redesign product behavior, auth, pricing, report schemas, or frontend UI.
- Do not weaken observability gates to pass degraded behavior as clean.
- Do not perform broad backend refactors beyond the evidence producers/tooling needed for this repair.
- Do not touch frontend visual tests unless the architect proves rendered evidence production is the root cause.

## Impacted Surfaces
- tools/post_test_review.py
- tools/log_watch
- backend/app logging producers for Today, Week, Admin, and Catalog only where evidence production is broken
- backend tests covering observability evidence and GRACE logging contracts

## Impacted GRACE Artifacts
- docs/prefect_grace/BLUEPRINT.md only if the evidence contract changes
- verification-matrix.md only if the canonical observability gate semantics change
- knowledge-graph.xml only if module/evidence ownership changes materially

## Acceptance Criteria
- `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md` no longer returns `FAIL_NO_EVIDENCE` when canonical logs contain request-bound evidence.
- Today and Week verdicts are either clean or explicit expected-degradation with reason codes; unexpected-degradation must be repaired or blocked by architect.
- Admin and Catalog evidence is fresh within the configured review window or the tooling explains exactly which producer command is missing.
- Targeted tests cover Today classification, Week fallback classification, and stale-vs-missing evidence behavior.
- Verifier records concrete log paths, report paths, commands run, and before/after verdicts.
- Reviewer rejects fabricated evidence and rejects green-only evidence without canonical logs/traces.

## Visual Expectations
-

## Wave Proposal
1. W00 architect formalization must identify whether failures are runtime data absence, stale log windows, incorrect classification, or broken producers.
2. Architect must split producer fixes from reviewer/tooling classification fixes if both are needed.
3. Each execution wave must include concrete commands that generate or locate fresh evidence before running post_test_review.
4. Intermediate verifier packets must stay packet_local/read-only unless they intentionally generate fresh Today/Week canonical runtime evidence.
5. The final integrated verifier may run the Today/Week canonical gate, but if it does, its packet_candidates entry must set verification_profile.execution.observability_scope to wave_final and include the exact canonical_flow_commands.
6. If live data cannot be generated safely, architect must create a bounded dev evidence producer or explicitly block with a user-action requirement.

## Open Decisions
- Decide whether Today auth fallback and text-layer failures are expected development degradation or real product regressions.
- Decide whether Week chunk parse fallback is expected during backend refactor or must be repaired before acceptance.
- Decide the minimum fresh Admin/Catalog evidence commands required for reviewer acceptance.
