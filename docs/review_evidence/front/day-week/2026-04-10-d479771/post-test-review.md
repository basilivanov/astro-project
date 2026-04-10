# Post-test observability closeout

- Profile: `today-week`
- Command: `python3 tools/post_test_review.py --profile today-week --since 20m --report-format md`
- Verdict: `PASS_CLEAN`
- Capture mode: local live signed probe + canonical backend logs

## Today

- Verdict: `clean`
- Trace: `320349bd-97b8-4a4e-9eb4-ce14ac87fa7c`
- Correlation: `afbd68f6-978d-4ebd-a6bb-93f4a3618f93`
- Fallback: `false`
- Personalization: `personalized_v2`

Evidence samples:

- `feed.debug`
- `day_brief.response_returned`

## Week

- Verdict: `clean`
- Workflow trace: `7ff34c05-b011-4a00-bd85-b50bb62997ea`
- Read trace: `0b44c570-c358-4a91-9b70-f3de06c540b7`
- Report: `d554f856-92e9-458a-b6b9-1e439a0a35de`
- `week_brief`: `true`
- `week_map`: `false`

Evidence samples:

- `report.workflow.generation_complete`
- `week_brief_built`

## Notes

- Rendered Playwright evidence was present before canonical logs, but it was not treated as sufficient proof on its own.
- Canonical backend evidence was added through a live signed probe with real `X-Telegram-Auth`.
