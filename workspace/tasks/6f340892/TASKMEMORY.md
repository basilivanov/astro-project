# GRACE Coverage Analysis Task Memory

**Task:** Analyze GRACE coverage and create roadmap to 95%
**Date:** 2026-03-27

## What Was Done

1. Analyzed current mandatory test profiles:
   - Backend: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
   - Frontend: `frontend:quick`, `frontend:targeted`, `smoke`, `full-regression`

2. Audited all 10 active VMs in `verification-matrix.md` - all have test coverage

3. Identified coverage gaps by Use Case:
   - **UC-BOT-DELIVERY**: 0% VM coverage (needs 2 new VMs)
   - **UC-REFERRAL-REWARD**: ~60% (tests exist but policy defect open)
   - **UC-REPORT-ASYNC**: Partial (workflow test file missing)
   - **UC-ADMIN-OPERATIONS**: ~70% (RBAC added, diagnostics missing)
   - **UC-AUTH-PROFILE**: ~80% (has quick tests, needs targeted)

4. Created task roadmap with 10 GRACE-XXX tasks:
   - GRACE-001: VM-BOT-NOTIFY
   - GRACE-002: VM-BOT-VOICE
   - GRACE-003: VM-REFERRAL-SIGNUP
   - GRACE-004: VM-REFERRAL-PARTNER
   - GRACE-005: UC-REPORT-ASYNC workflow test
   - GRACE-006: VM-ADMIN-DIAGNOSTICS
   - GRACE-007: Admin RBAC extended
   - GRACE-008: UC-AUTH-PROFILE E2E
   - GRACE-009: UC-AUTH-PROFILE backend
   - GRACE-010: Admin operations E2E

5. Estimated current coverage: ~70-75%

6. Generated execution order in 3 phases with dependencies

7. Created success criteria for reaching 95%:
   - All 16 VMs (10 current + 6 new) green
   - CI enforces coverage checks
   - No open defects blocking coverage

## Output Delivered

- `/opt/astro-project/output_to_user/grace_coverage_analysis_2026-03-27.md`
  - Complete analysis with current profiles, VM status, gaps, and roadmap
  - Task table with IDs, descriptions, tests, expected VMs, and dependencies
  - Execution phases and risk mitigation

## Key Findings

1. **Critical Gap**: UC-BOT-DELIVERY has ZERO VM coverage - 2 new VMs needed
2. **High Impact Gap**: UC-REPORT-ASYNC missing `test_report_workflow.py` (file referenced but doesn't exist)
3. **Known Defect**: DEFECT-REFERRAL-POLICY-DRIFT affects UC-REFERRAL-REWARD coverage
4. **Partial Coverage**: Admin ops has RBAC tests but no diagnostics VM

## Recommendations

1. Start with GRACE-005 (workflow test) - unblocks multiple verification paths
2. Execute Phase 1 tasks in parallel where possible
3. Add CI gate for GRACE coverage before merging PRs
4. Update `docs/GRACE_ARTIFACTS.md` with VM count and coverage metrics
