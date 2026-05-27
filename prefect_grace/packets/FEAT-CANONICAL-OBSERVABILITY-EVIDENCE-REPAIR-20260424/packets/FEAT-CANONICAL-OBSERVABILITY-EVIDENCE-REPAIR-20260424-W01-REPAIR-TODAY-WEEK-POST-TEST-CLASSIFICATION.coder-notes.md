# Coder Notes — W01 Today/Week Post-Test Classification

## Scope
- Touched only `tools/post_test_review.py`, `tests/test_post_test_review.py`, and this packet-local note.
- No frontend, backend product behavior, auth, pricing, billing, report schema, or producer changes.

## Implementation
- Today classification now preserves `unexpected-degradation` when request-bound degraded evidence exists, instead of letting a missing clean-success trace/request proof rewrite it to `no-evidence-blocker`.
- Week classification now treats `chunk_parse_degraded=true` as concrete degraded evidence, emits stable `chunk_parse_degraded` when producer reason codes are absent, and includes that record in evidence samples.
- Overall Today/Week verdict precedence now surfaces `unexpected-degradation` before `no-evidence-blocker` so concrete degraded evidence is not hidden by another flow with missing logs.
- Restored packet-local read-only hub compatibility in `tools/post_test_review.py` because `tests/test_post_test_review.py` imports and exercises that public helper.

## Verification
- `python3 -m pytest tests/test_post_test_review.py` — PASS, 13 tests.
- `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md` — `FAIL_NO_EVIDENCE` with `records_checked: 0` for both Today and Week; verdict is expected for true missing runtime logs in the packet-local 30m window, not a degraded-evidence misclassification.

## Verdict
- Packet-local code/test verdict: clean.
- Runtime observability verdict: no-evidence-blocker due to absent recent canonical Today/Week logs.
