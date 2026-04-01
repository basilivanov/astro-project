# Post-Test Observability Review Proposal (2026-04-01)

## Purpose

Этот memo фиксирует минимальный обязательный post-test observability gate для `Today/Week` и смежных flow, чтобы после зелёных тестов агент видел не только PASS, но и evidence по degradation/fallback/log/trace signals.

## Problem

Сейчас в проекте уже есть:
- correlation / trace propagation;
- structured JSONL logs;
- replay/watch tools;
- quality/week/day telemetry;
- targeted runbooks.

Но эти сигналы не сведены в обязательный единый post-test review шаг.
Поэтому сценарий может пройти тесты и при этом остаться product-degraded:
- anonymous fallback вместо Telegram-auth path;
- `profile_light` вместо полной персонализации;
- valid fallback payload вместо intended rich payload;
- low `factor_count` / minimal explainability;
- validator fallback / schema repair без явного fail;
- week/day content assembled as degraded but still shape-valid.

## Minimal mandatory gate

После любого `backend:quick`, `frontend:quick`, `smoke` или targeted scenario по `Today/Week/Read/Admin/Catalog` агент MUST выполнить единый post-test review шаг:

1. открыть/собрать structured evidence;
2. просмотреть fallback/degradation counters;
3. просмотреть replay/latest trace по затронутым flow;
4. явно зафиксировать verdict: `clean`, `degraded-but-expected`, `unexpected-degradation` или `no-evidence-blocker`.

## Recommended command profile

Канонический новый профиль:

```bash
python3 tools/post_test_review.py \
  --profile today-week \
  --since 90m \
  --report-format md
```

Minimal implementation shipped in wave 1:

```bash
python3 tools/post_test_review.py --profile today-week --since 90m --report-format md
```

Минимально полезный scope профиля `today-week`:
- `logs/feed.jsonl`
- `logs/report.jsonl`
- `logs/admin.jsonl` при смежных admin/create/read проверках
- latest `trace_id` / `report_id` для week/report flows
- fallback/degradation summary по `Today/Week`

## Mandatory review output

Команда/отчёт должны возвращать компактный digest:

### 1. Test context
- какие команды только что запускались;
- окно анализа (`since` / latest files);
- какие лог-файлы просмотрены.

### 2. Flow verdicts
- `FLOW-DAILY-FEED`
- `FLOW-DAY-BRIEF`
- `FLOW-WEEK-BRIEF`
- `FLOW-REPORT-WORKFLOW` (если релевантен)
- `FLOW-ADMIN-OPS` / `FLOW-FORECAST-CATALOG` при релевантности

Для каждого flow:
- `status = clean | degraded-but-expected | unexpected-degradation | no-evidence-blocker`
- `last_success_at`
- `fallback_count`
- `top_reason_codes`
- `sample_trace_id`
- `sample_correlation_id`

### 3. Product degradation counters
- `today.auth_fallback_anonymous`
- `today.personalization_profile_light`
- `today.fallback_mode`
- `today.validator_fallback`
- `today.low_factor_count`
- `week.fallback_mode`
- `week.validation_failed`
- `week.invalid_json`
- `week.minimal_explainability`
- `week.low_factor_count`
- `report.chunk_parse_degraded`
- `report.missing_required_sections`

### 4. Example evidence
- latest feed replay summary;
- latest week/report trace summary;
- 1–3 exact event snippets with `trace_id` / `reason_code`.

### 5. Final verdict
- `PASS_CLEAN` / `PASS_WITH_EXPECTED_DEGRADATION` / `FAIL_OBSERVABILITY_GATE` / `FAIL_NO_EVIDENCE`

## Wave 2 refinement

Bounded wave 2 tightens the gate without widening the profile surface:

- separates `unexpected-degradation` from `no-evidence-blocker` instead of folding both into generic fail;
- keeps `degraded-but-expected` only when logs carry explicit expected reason codes;
- includes sample `report_id` alongside `trace_id` / `correlation_id` in the digest;
- falls back to latest non-error evidence samples when the log window is clean, so reviewers still get a concrete trace anchor.
- `PASS_WITH_EXPECTED_DEGRADATION`
- `FAIL_OBSERVABILITY_GATE`

## Counters and thresholds

Минимальный начальный набор:

### Today
- `today_requests_total`
- `today_fallback_total`
- `today_auth_fallback_anonymous_total`
- `today_profile_light_total`
- `today_anonymous_total`
- `today_validator_fallback_total`
- `today_low_factor_count_total`

Threshold hints:
- any unexpected `auth_fallback_anonymous` in authenticated test run => warn/fail;
- any `profile_light` in persona tests expecting full profile => warn/fail;
- `factor_count < 3` for authenticated rich-profile run => warn;
- `fallback_mode=true` in nominal happy-path smoke => fail unless test explicitly expects fallback.

### Week
- `week_requests_total`
- `week_fallback_total`
- `week_validation_failed_total`
- `week_invalid_json_total`
- `week_prompt_repair_total`
- `week_repair_success_total`
- `week_low_factor_count_total`
- `week_minimal_explainability_total`
- `week_anonymous_total`

Threshold hints:
- any `week_fallback_total > 0` in nominal smoke => fail;
- any `primary_reason_code` in {`missing_required_sections`, `llm_invalid_json`, `validation_failed`} => fail in happy path;
- `factor_count <= 1` or `explanation_depth=minimal` in standard personalized run => warn/fail.

### Ratios for digests/alerts
- `today_fallback_ratio = today_fallback_total / today_requests_total`
- `week_fallback_ratio = week_fallback_total / week_requests_total`
- `profile_light_ratio`
- `anonymous_auth_fallback_ratio`
- `validator_fallback_ratio`
- `low_factor_count_ratio`

## Structured events to normalize

Нужны строгие summary-friendly fields:
- `flow_id`
- `surface`
- `event`
- `result`
- `fallback_mode`
- `reason`
- `primary_reason_code`
- `reason_codes[]`
- `personalization_level`
- `auth_mode`
- `generation_mode`
- `confidence_bucket`
- `factor_count`
- `explanation_depth`
- `birth_time_used`
- `validator_result`
- `expected_profile`
- `actual_profile`

Особенно важно, чтобы `Today` и `Week` consistently писали:
- `primary_reason_code`
- `reason_codes`
- `expected_personalization_level` when test/profile implies expectation
- `actual_personalization_level`

## Why current contour missed degradation

1. **Telemetry is present but fragmented** — replay/watch/trace tools существуют отдельно по feed/admin/report.
2. **Green tests dominate the decision** — тесты в основном проверяют correctness/shape/UX, а не post-run degradation digest.
3. **Fallbacks are often valid outputs** — контракт остаётся валидным, поэтому pipeline green не означает product quality green.
4. **No single mandatory command after tests** — агенту не навязан обязательный log/trace review шаг.
5. **Weak policy for expected vs unexpected degradation** — есть fallback telemetry, но мало явных gate rules: когда warn, когда fail.
6. **Today/Week summary metrics are not surfaced as digest** — сигналы есть в JSONL, но не сведены в ratios/weekly digest.

## Agent policy changes

Нужно добавить в agent-facing docs правило:

> После каждого существенного тестового прогона агент обязан смотреть не только PASS/FAIL тестов, но и post-test observability evidence по затронутому flow. Green tests без log/trace review не считаются полным verification evidence.

Минимальный checklist:
- tests green;
- latest replay/trace reviewed;
- fallback/degradation counters reviewed;
- verdict recorded.

## Recommended implementation order

1. Add `post-test observability gate` section to `AGENTS.md` and `docs/TESTING_GUIDE.md`.
2. Create `tools/post_test_review.py` that composes existing replay/watch/trace helpers.
3. Start with profiles: `today-week`, `feed-admin`, `catalog-read`.
4. Add normalized counters/reason codes where missing.
5. Add daily/weekly digest output for Today/Week fallback ratios.
6. Later wire the digest into CI/nightly summary and optional alerts.
