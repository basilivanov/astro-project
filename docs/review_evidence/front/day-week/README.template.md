# Day/Week Visual Evidence Template

## Folder
- Path: `docs/review_evidence/front/day-week/<YYYY-MM-DD>-<shortsha>/`
- Commit SHA: `<shortsha>`
- Build SHA / runtime bundle: `<sha-or-note>`
- Viewport: `<e.g. 430x932 Telegram mobile>`

## Verdict Scope
- Review mode: `code+visual` or `code-only`
- If screenshots are missing or partial: `visual verdict incomplete — screenshot evidence missing`

## Lane Map
- `today-canonical-top.png` — `signed`
- `today-canonical-domain-energy-expanded.png` — `signed`
- `today-canonical-domain-money-expanded.png` — `signed`
- `today-canonical-domain-love-expanded.png` — `signed`
- `today-canonical-domain-focus-expanded.png` — `signed`
- `today-canonical-windows.png` — `signed`
- `today-canonical-risks.png` — `signed`
- `today-compatibility-degraded.png` — `mock-helper` or `compatibility`
- `week-canonical-overview-top.png` — `signed`
- `week-canonical-domains.png` — `signed`
- `week-canonical-domain-work-expanded.png` — `signed`
- `week-canonical-domain-focus-expanded.png` — `signed`
- `week-canonical-rhythm-strip.png` — `signed`
- `week-canonical-day-drawer.png` — `signed`
- `week-canonical-actions-risks.png` — `signed`
- `week-canonical-explainability.png` — `signed`
- `week-canonical-deep-sections.png` — `signed` or `not-applicable`
- `week-compatibility-overview.png` — `mock-helper` or `compatibility`
- `week-compatibility-day-drawer.png` — `mock-helper` or `compatibility`
- `week-empty.png` — `signed` or `mock-helper`
- `week-in-progress.png` — `signed` or `mock-helper`

## Required Notes
- For every screenshot: source lane and whether it is canonical, compatibility, empty, or in-progress.
- If signed Telegram capture was unavailable, say why explicitly.
- If device screenshot differs from current HEAD behavior, mark it as deploy/cache parity issue until build SHA is confirmed.

## Recommended Extra Files
- `today-canonical-bottom.png`
- `week-canonical-bottom.png`
- `week-canonical-cta-area.png`
- `week-canonical-scroll-seam.png`
- `today-window-merge-edge-case.png`
- `week-monday-sunday-order-proof.png`
