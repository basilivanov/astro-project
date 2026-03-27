# GRACE Coverage Analysis: Path to 95%

**Date:** 2026-03-27
**Snapshot:** grace-2026-03-21
**Goal:** Identify gaps and create task roadmap to reach 95% GRACE coverage

---

## 1. Current Mandatory Test Profiles

### Backend Profiles
| Profile | Command | Purpose |
| --- | --- | --- |
| `backend:quick` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py` | Fast sanity check for all backend changes |

### Frontend Profiles
| Profile | Command | Purpose |
| --- | --- | --- |
| `frontend:quick` | `./scripts/run_e2e.sh --last-failed` | Re-run failed tests |
| `frontend:targeted` | `./scripts/run_e2e.sh e2e/<file>.spec.ts -g "<case>"` | Run specific test case |
| `smoke` | `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/core-ux.spec.ts e2e/report-create.spec.ts e2e/quality.spec.ts` | Critical smoke suite |
| `full-regression` | `./scripts/run_e2e.sh` | Complete E2E run |

---

## 2. Current VM Coverage Status

| VM ID | UC Coverage | Has Tests | Status |
| --- | --- | --- | --- |
| `VM-NATAL-CONTEXT` | UC-NATAL-FACTS-FIRST | ✅ | `test_natal_section_context.py`, `test_report_contract.py`, `test_report_context.py` |
| `VM-NATAL-STYLE-CONTRACT` | STYLE_CONTRACT.md | ✅ | `test_natal_section_context.py -k prompt_contract`, `grace_lint.py` |
| `VM-NATAL-SUMMARY-REPAIR` | executive_summary, final_synthesis | ✅ | `test_validation_relaxed.py`, `test_validation_template_fallback.py`, `test_natal_section_context.py` |
| `VM-FORECAST-CREATE-READ` | week/month/year/decade forecast | ✅ | Multiple E2E specs + forecast read tests |
| `VM-FORECAST-SEMANTICS` | forecast semantic layer | ✅ | `test_forecast_semantics.py`, `test_month_forecast_validation.py`, `test_report_context.py` |
| `VM-READ-QUALITY` | report rendering, fallback | ✅ | `test_report_contract.py`, E2E `quality.spec.ts`, `week-page-fallback.spec.ts` |
| `VM-REPORTS-UX-CONSISTENCY` | /reports, /reports/history | ✅ | Multiple bridge-storefront + catalog E2E specs |
| `VM-BILLING-ACCESS` | one-off phase-2 runtime | ✅ | 7 backend tests + billing E2E specs |
| `VM-FEED-ROBUSTNESS` | daily feed endpoint | ✅ | `test_daily_feed_robustness.py`, `test_personalized_daily_service.py`, `verify_daily_feed.py` |
| `VM-START-GATEWAY` | /start routing | ✅ | E2E `landing.spec.ts`, `core-ux.spec.ts` |

**Summary:** All 10 active VMs have backend/frontend test coverage.

---

## 3. Slices/Use Cases Without Confirmed Tests/VM

### Coverage Analysis by Use Case

| UC ID | Scenarios | VM Coverage | Missing Tests |
| --- | --- | --- | --- |
| **UC-AUTH-PROFILE** | SCN-AUTH-VALID-INITDATA, SCN-PROFILE-COMPLETE-BIRTHDATA | ✅ via backend:quick + E2E | Minimal targeted tests; needs dedicated auth unit tests |
| **UC-B2C-REPORT** | SCN-B2C-REPORT-CREATE, SCN-HORARY-QUOTA-OR-CREDITS | ✅ via VMs | Full coverage exists |
| **UC-REPORT-ASYNC** | SCN-ASYNC-REPORT-GENERATE, SCN-ASYNC-SECTION-REGENERATE | ⚠️ PARTIAL | Missing `test_report_workflow.py` (referenced but file is `test_report_workflow_regression.py`) |
| **UC-BILLING-ACCESS** | SCN-BILLING-SUBSCRIPTION-WEBHOOK, SCN-BILLING-CREDITS-WEBHOOK, SCN-BILLING-ONE-OFF-PHASE2 | ✅ via VM-BILLING-ACCESS | Full coverage exists |
| **UC-REFERRAL-REWARD** | SCN-REFERRAL-SIGNUP, SCN-REFERRAL-PARTNER-REWARD | ⚠️ PARTIAL | Tests exist but DEFECT-REFERRAL-POLICY-DRIFT open |
| **UC-FEED-DAILY** | SCN-FEED-TODAY | ✅ via VM-FEED-ROBUSTNESS | Full coverage exists |
| **UC-ADMIN-OPERATIONS** | SCN-ADMIN-REPORT-VIEW, SCN-ADMIN-DIAGNOSTICS | ✅ via ADMIN-ENTITLEMENTS-FLOW | Partial coverage; admin RBAC tests added recently |
| **UC-BOT-DELIVERY** | SCN-BOT-NOTIFY, SCN-BOT-VOICE-TRANSCRIBE | ❌ NONE | Missing dedicated VMs; only basic replay test exists |

### Critical Gaps Identified

1. **UC-BOT-DELIVERY (No VM Coverage)**
   - `SCN-BOT-NOTIFY`: Has replay helper but no dedicated VM
   - `SCN-BOT-VOICE-TRANSCRIBE`: Has `test_telegram_renderer.py` but no VM

2. **UC-REFERRAL-REWARD (Known Defect)**
   - `DEFECT-REFERRAL-POLICY-DRIFT`: 14 days vs 15 days policy drift
   - Tests exist but don't validate the defect condition

3. **UC-REPORT-ASYNC (Missing Workflow Test)**
   - Test bundle references `tests/test_report_workflow.py` but actual file is `test_report_workflow_regression.py`
   - No comprehensive workflow test file exists

4. **Admin Surface Coverage Gaps**
   - `frontend/e2e/admin.rbac.spec.ts` recently added
   - `admin.natal-master.spec.ts`, `admin.natal-master-ui.spec.ts` exist
   - Gap: No VM for admin diagnostic flow beyond `SCN-ADMIN-DIAGNOSTICS`

---

## 4. Current Coverage Estimation

| Layer | Total VMs | Covered | Coverage % |
| --- | --- | --- | --- |
| **Natal & Forecast Core** | 6 VMs | 6 VMs | 100% |
| **Read & UX** | 3 VMs | 3 VMs | 100% |
| **Billing & Access** | 1 VMs | 1 VMs | 100% |
| **Daily Feed** | 1 VMs | 1 VMs | 100% |
| **Admin & Ops** | Partial | Partial | ~70% |
| **Bot Delivery** | 0 VMs | 0 VMs | 0% |
| **Referral** | Has tests | Has defects | ~60% |

**Overall Estimated Coverage: ~70-75%**

---

## 5. Task Roadmap: Path to 95% GRACE Coverage

| ID | Description | Tests to Add/Expand | Expected VM Coverage | Dependencies |
| --- | --- | --- | --- | --- |
| **GRACE-001** | Create `VM-BOT-NOTIFY`: test bot notification failure handling, blocked chat behavior, non-fatal error contract | `test_bot_notification.py` + E2E spec | None |
| **GRACE-002** | Create `VM-BOT-VOICE`: test voice transcription helper, media handling, fallback behavior | `test_bot_voice_transcribe.py` | None |
| **GRACE-003** | Create `VM-REFERRAL-SIGNUP`: test 15-day policy, self-referral rejection, duplicate link handling | `test_referral_policy_15days.py` | GRACE-001 |
| **GRACE-004** | Create `VM-REFERRAL-PARTNER`: test partner reward 20% logic, payout validation, balance updates | `test_referral_partner_reward.py` | GRACE-003 |
| **GRACE-005** | Fix `UC-REPORT-ASYNC` coverage: create `tests/test_report_workflow.py` covering workflow lifecycle, chunk ordering, section regeneration | `tests/test_report_workflow.py` | None |
| **GRACE-006** | Create `VM-ADMIN-DIAGNOSTICS`: test diagnostics runner, log evidence capture, failed step identification | `test_admin_diagnostics.py` | None |
| **GRACE-007** | Extend Admin RBAC: add tests for role-based access, denied paths, telemetry capture on `/admin/users`, `/admin/*` | `test_admin_rbac_extended.py` | GRACE-006 |
| **GRACE-008** | Add E2E coverage for `UC-AUTH-PROFILE`: test `/start` routing, auth wait behavior, profile check | `e2e/start-gateway.spec.ts` | None |
| **GRACE-009** | Add targeted backend tests for auth: test `authenticate_telegram_user`, development bypass limits, profile persistence | `test_auth_targeted.py` | GRACE-008 |
| **GRACE-010** | Create E2E spec for admin report operations beyond entitlements: test admin detail view, section regenerate flow, export functionality | `e2e/admin.operations.spec.ts` | GRACE-007 |

---

## 6. Execution Order & Dependencies

```
Phase 1 (Immediate - High ROI, No Dependencies)
├── GRACE-005: Fix UC-REPORT-ASYNC workflow test
├── GRACE-001: VM-BOT-NOTIFY
└── GRACE-003: VM-REFERRAL-SIGNUP policy fix

Phase 2 (After Phase 1)
├── GRACE-002: VM-BOT-VOICE
├── GRACE-004: VM-REFERRAL-PARTNER
├── GRACE-008: UC-AUTH-PROFILE E2E
└── GRACE-009: UC-AUTH-PROFILE backend

Phase 3 (After Phase 2)
├── GRACE-006: VM-ADMIN-DIAGNOSTICS
├── GRACE-007: Admin RBAC extended
└── GRACE-010: Admin operations E2E
```

---

## 7. Automation Needs

To maintain 95% coverage long-term:

1. **CI Integration**
   - Add GRACE coverage check to CI pipeline
   - Fail PR if VM coverage drops below 90%
   - Auto-run targeted tests per changed slice

2. **Test Data Management**
   - Centralize test fixtures and seeds
   - Create replayable test datasets
   - Maintain test result history

3. **Coverage Tracking**
   - Add coverage badge to `docs/GRACE_ARTIFACTS.md`
   - Weekly coverage reports
   - Auto-update `verification-matrix.md`

---

## 8. Success Criteria for 95% Coverage

- [ ] All 10 current VMs have green backend + frontend tests
- [ ] New VM-BOT-NOTIFY and VM-BOT-VOICE are green
- [ ] New VM-REFERRAL-SIGNUP and VM-REFERRAL-PARTNER are green
- [ ] VM-ADMIN-DIAGNOSTICS exists and is green
- [ ] Auth gateway E2E tests are green
- [ ] Admin operations E2E suite passes
- [ ] All 16 VMs (10 current + 6 new) tracked in `verification-matrix.md`
- [ ] No open defects blocking VM coverage
- [ ] CI pipeline enforces coverage checks

---

## 9. Risk Mitigation

| Risk | Mitigation |
| --- | --- |
| Test flakiness due to external dependencies (Telegram, billing) | Use mocks where possible; add retry logic |
| Bot delivery changes affect other flows | Isolate bot tests with dedicated VMs |
| Referral policy changes impact existing users | Add migration tests and backward compatibility checks |

---

**Next Step:** Execute GRACE-005 first (create workflow test) as it unblocks multiple verification paths.
