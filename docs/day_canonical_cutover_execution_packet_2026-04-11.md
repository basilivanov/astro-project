# Day canonical cutover execution packet

Date: 2026-04-11
Branch baseline: `prod-release-20260327`
Packet family: `DAY-NEXT-PHASE`

## Goal
Lock the shared repository truth around Day to the canonical product surface:
- Telegram initData authenticated lane
- `/api/feed/today`
- `day_brief_canon_v1`
- hero + 4 domains + CTA
- honest `ready | no_data | error`
- no legacy user-facing reconstruction

## Product truth
Day is now a canonical-only product surface.

Allowed user-facing Day output:
- hero
- 4 domains
- CTA / premium block
- explicit `ready`, `no_data`, `error`, `domain_failed` semantics inside the four-domain shell

Forbidden as intended Day product truth:
- windows
- best uses
- risks
- factor-card explainability feeds
- legacy/fallback-safe synthetic Day surfaces
- compatibility Day as a first-class product mode

## Execution order
1. Packet A — shared artifact realignment
2. Packet B — backend DayBrief hard cut
3. Packet C — frontend canonical cutover
4. Packet D — evidence and observability closure

## Verification expectations
- Signed Telegram lane is the primary acceptance path for Day.
- Mock remains visual/debug helper only.
- Observability stays strict: contamination in the same evidence window cannot be re-labeled clean.
