# Day/Week v2 closure review — 2026-04-02

## Scope reviewed

- `AGENTS.md`
- `GRACE.md`
- `development-plan.xml`
- `knowledge-graph.xml`
- `docs/day_week_contract_audit_v2_2026-04-02.md`
- `docs/today_screen_packet/*`
- `docs/week_ui_packet/*`
- `docs/frontend_test_hardening_packet/*`
- `docs/frontend_functional_reliability_packet/*`
- `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md`
- `docs/RENDERED_GATE_PASS_MATRIX_SYNC.md`
- relevant day/week frontend/backend adapters and detail-layer code

## Closure summary

### 1) What is already effectively closed

#### Product / contract
- Today top-layer cleanup is materially closed: packet + verification slice define a short-first Today surface with no duplicate hero semantics and no raw technical tags/birth-time leakage.
- Today detail layer is materially closed at the UI-system level: scores, windows, best uses, and risks are normalized into one detail-layer model via `frontend/lib/detail-layer.ts`.
- Week top-layer parity is materially closed for hero/state/CTA/domain/factor mapping: the Week packet and verification slice freeze `/week` as a `WeekBrief`-driven surface rather than a legacy mixed assembly.
- Week detail parity pilot is materially closed for domains/actions/risks/major factors: they already normalize into the shared detail layer and have explicit regression surface wording in `docs/REGRESSION_MAP.md`.
- Docs/graph sync is materially closed: global docs now route agents through canonical profiles, packet-local matrices, and the observability overlay without adding a second matrix taxonomy.

#### Test / verification
- Day/Week verification is materially structured and bounded: packet-local VM slices exist for Today and Week, with explicit targeted checks and evidence rules.
- QA hardening is materially closed at the policy/tooling layer for this slice: frontend functional reliability and frontend test hardening packets both exist and align to canonical runners rather than ad hoc test selection.
- Observability gate is no longer just proposed; it is materially implemented as a repo tool: `tools/post_test_review.py` plus tests (`tests/test_post_test_review.py`) and rendered-artifact coverage.
- Rendered gate/pass-matrix sync is materially closed as a compact overlay, consistent with the allowed profile model and without introducing profile drift beyond the canonical set.

#### Code reality
- Today adapter/detail code already suppresses many placeholder/raw-label problems and keeps fallback rendering bounded.
- Week adapter/detail code already supports shared detail rendering for domains/actions/risks/factors, which is enough for a parity pilot on explainability behavior.
- The repo history indicates the main integrated wave already landed in `da34a0b` (`Ship Day/Week detail layer and read continuity fixes`) on top of the earlier packet/hardening wave in `dcad781`.

### 2) Bounded remaining items after the current parity pilot

These look like genuine bounded leftovers rather than evidence of an open-ended Day/Week v2 rewrite.

#### A. Today score disclosure contract is not fully clean yet
- The audit still identifies backend-global score disclosure filling in `backend/app/services/day_brief.py`.
- The frontend side is cleaner, but backend can still inject domain-global supporting factors into every score disclosure.
- Closure implication: parity pilot is good enough for shared detail UX, but strict contract honesty for `scores[*].details.supporting_factors` is not yet fully closed.

#### B. Week day cards are not yet first-class detail items
- `WeekBrief.day_cards[]` still lacks the minimal explicit day-like disclosure object described in the audit (`id`, `details.why_text`, `details.supporting_factors`, optional `factor_ids`).
- Existing week detail parity is therefore partial: domains/actions/risks/factors are unified, but day-card tap/disclosure parity is not fully real at DTO level.
- Closure implication: this is the cleanest bounded residual for a follow-up wave if product wants “day card opens like Today item” parity.

#### C. Done evidence still depends on running the final targeted profile on the current snapshot
- The repo contains packet rules, verification slices, observability docs, and the `post_test_review` tool.
- This review did not execute the canonical Day/Week targeted profiles itself because the task is closure/reviewer synthesis rather than a change-validation wave.
- Closure implication: product closure can be stated now at the workstream level, but release-style closure for the current snapshot still requires the exact targeted test+observability evidence bundle on the final parity pilot SHA.

#### D. One source artifact referenced by the audit is absent
- `telegram_files/2026-04-01/day_week_review_and_fix_tz_v2.md` is explicitly missing from repo according to the audit doc.
- Closure implication: the repo is sufficient for closure review, but archival completeness of external review inputs is not perfect.

### 3) Recommended done criteria for Day/Week v2

Day/Week v2 should be considered done only when all three workstreams are simultaneously true.

#### Product done
- Today is a single-center, short-first, explainable surface with no duplicate semantic layer and no raw technical leakage.
- Week is a `WeekBrief`-driven surface with explicit state boundary, CTA correctness, compact fallback transparency, and bounded explainability.
- Shared detail behavior is real for Today and Week explainability surfaces; no fake frontend-invented evidence is used.
- If full parity is claimed for weekly day cards, `day_cards[]` must expose explicit detail DTO fields rather than relying on headline/best_for/avoid inference.

#### Test done
- Backend slice passes `backend:quick`.
- Frontend slice passes the minimal honest Day/Week targeted profile from packet-local matrices.
- Any reproduced crash/500/detail regression has a deterministic reproducer test and that test is green.
- Observability review is run after the targeted profiles using `tools/post_test_review.py --profile today-week ...` or an equivalent current command, with an explicit verdict of either `clean` or an intentionally accepted `degraded-but-expected`.
- No unexpected degradation or no-evidence blocker remains for `FLOW-DAY-BRIEF` / `FLOW-WEEK-BRIEF` on the claimed done snapshot.

#### Docs / graph done
- `docs/REGRESSION_MAP.md`, packet-local matrices, and `knowledge-graph.xml` all point to the same canonical Day/Week verification surface.
- Observability gate remains documented as first-class evidence, not optional follow-up.
- Any residual non-goal/deferred item is explicitly recorded as bounded post-v2 work, not left as silent parity debt.

## Reviewer verdict

### What can be called closed now
- Day/Week v2 is substantially closed as a product/test/docs workstream for the current parity pilot.
- The repo has enough code, packetization, verification routing, and observability machinery to treat the slice as converged rather than exploratory.

### What should remain open only as bounded residuals
- backend cleanup of Today score disclosure evidence injection;
- explicit Week day-card detail DTO parity if product wants full day-card disclosure parity, not just general Week detail-layer parity;
- final snapshot-specific targeted test + observability evidence bundle before any release-style “fully done” claim.

### Practical closure stance
- **Closed enough for parity-pilot closure:** yes.
- **Closed enough for strict “v2 fully done” claim:** yes, only if the project treats the two residual contract gaps above as post-v2 bounded follow-ups or confirms they are intentionally out of scope; otherwise they remain the last narrow blockers.
