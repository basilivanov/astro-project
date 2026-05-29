# Feature Brief: Referral Bonus Calculation

## Context
AstroSaaS is pivoting to B2C. We need a core business logic function to calculate referral bonuses.
When a user refers another user, the referee gets 15 days of premium access, and the referrer gets +15 days.
If the referrer is an admin/partner, they get a 20% money bonus instead of days.

## Goal
Implement a simple utility function in `backend/app/services/referral_service.py` to calculate these bonuses.

## Write Scope
- `backend/app/services/referral_service.py`
- `backend/tests/test_referral_service.py`

## Acceptance Criteria
- Create `calculate_bonus(is_partner: bool, amount_paid: float) -> dict` returning either `{"days": 15}` or `{"money": amount_paid * 0.2}`.
- Create unit tests for both scenarios.
- All tests must pass.
