# Today Screen Execution Packet

## Objective
Deliver the Today screen refinement according to `telegram_files/2026-03-31/today_screen_review_changes.md` under strict GRACE, with the main agent acting only as architect/reviewer and workers executing inside bounded waves.

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `telegram_files/2026-03-31/today_screen_review_changes.md`
- `/opt/astro-project/docs/TODAY_BLOCKS.md`

## Execution policy
- Respect the slice requirements and write scope exactly.
- Implement `WAVE-TODAY-MUSTFIX-NOW` first; do not start second-layer depth until first-layer duplication/leakage is green.
- Run the required verification profile after each significant change until green.
- If backend or UI crashes, add/update a reproduction test and fix to pass.
- Report back with: files changed, tests run, failures encountered, and any deferred items.

## Worker deliverables
1. Code changes for the active wave only.
2. Updated/added tests for the affected slice.
3. Verification evidence.
4. A short reviewer note: risks, open questions, and whether the next wave is unblocked.
