# Day/Week contract audit v2 — precise diagnosis

## Scope

Reviewed:
- `AGENTS.md`
- `GRACE.md`
- `frontend/lib/day-brief.ts`
- `frontend/lib/week-brief.ts`
- `frontend/lib/detail-layer.ts`
- `backend/app/services/day_brief.py`
- `backend/app/services/day_brief_types.py`
- `backend/app/services/week_brief_service.py`
- `backend/app/services/week_brief_types.py`
- supporting repo docs around current week/day contracts

Note: requested file `telegram_files/2026-04-01/day_week_review_and_fix_tz_v2.md` is not present in repo at the given path, so this audit is based on code + nearby docs only.

## 1) Day score disclosures: where the global fallback is now, and how to limit it safely

### Current behavior

There are **two fallback layers**, and both are broader than a clean contract should allow.

#### A. Backend global fill of score disclosures

In `backend/app/services/day_brief.py`:
- `_build_score_items(...)` creates `details` for every score from `semantic.score_details[key]` or from generic `advice_map[key]`.
- Later, in the final assembly/repair pass, every score item is overwritten/normalized again so that:
  - `why_title` always exists,
  - `why_text` falls back to score `advice` or a generic sentence,
  - `supporting_factors` are injected from `domain_factor_map` for **every domain**, regardless of whether the score detail actually has local evidence.

This is the real **global disclosure fallback**: score detail payload becomes domain-level explainability by default, not item-level explainability.

Affected path:
- `backend/app/services/day_brief.py` around score assembly and repair (`_build_score_items`, then final score-item repair block).

#### B. Frontend generic fill of detail text/factors

In `frontend/lib/day-brief.ts`:
- `normalizeDetails(...)` returns fallback `why_text` whenever `details` exists but `why_text` is missing.
- `normalizeSupportingFactors(...)` gives generic labels/explanations (`"Фактор дня"`, `"Фактор поддерживает вывод дня."`) for malformed entries.

This means malformed or thin score disclosures become presentable but semantically vague, which can mask contract drift.

#### C. Detail-layer fallback body

In `frontend/lib/detail-layer.ts`:
- `normalizeTodayDetailItems(...)` falls back from `score.details.why_text` to `score.advice`.

That fallback is acceptable as a render fallback, but only if the upstream contract clearly distinguishes:
- canonical disclosure body,
- UI fallback body.

Right now that distinction is implicit.

### Safe narrowing recommendation

#### Keep allowed fallback only at the item shell level

Safe rule:
- score item may exist without disclosure,
- but if `details` exists, it should be **locally true to that score**, not domain-global filler.

#### Recommended backend restriction

For `scores[*].details`:
- keep `why_title` optional;
- keep `why_text` required **only when `details` is emitted**;
- set `supporting_factors` only from score-specific evidence, not from unconditional `domain_factor_map`.

Practical minimal rule:
- if no score-local factor ids / score-local text source exist, emit either:
  - `details: null`, or
  - `details: { why_text: advice, supporting_factors: [] }`
- **do not auto-inject domain factor lists into every score disclosure**.

#### Recommended frontend restriction

In `frontend/lib/day-brief.ts`:
- preserve shell safety,
- but stop manufacturing generic supporting-factor records.

Specifically:
- malformed factor rows should be dropped, not converted to `"Фактор дня"` placeholders;
- fallback `why_text` may remain as last-resort rendering safety, but should not imply evidence.

#### Net contract principle

- `advice` = user-facing action line
- `details.why_text` = actual disclosure sentence
- `details.supporting_factors` = concrete evidence list, not domain-global filler

## 2) What weekly day cards exactly lack to become a day-like detail system

### Current weekly day card shape

`backend/app/services/week_brief_types.py` → `WeekDayCard` contains only:
- `date`
- `weekday`
- `mode`
- `score`
- `headline`
- `best_for`
- `avoid`
- `peak_window_label`

`frontend/lib/week-brief.ts` mirrors the same shallow structure.

### What day-like detail system requires

To match the day surface explainability model, weekly day cards are missing:

1. **Stable day-card id**
- Needed for detail routing / modal identity / analytics / relation keys.
- Today items already derive stable ids from score/window ids.

2. **Disclosure body**
- Equivalent of `why_text`.
- Current `headline` is not enough: it is card copy, not explainability copy.

3. **Supporting factors array**
- Equivalent of `supporting_factors`.
- Without this, weekly day cards cannot participate in `detail-layer.ts` as first-class detail items.

4. **Optional disclosure title**
- Equivalent of `why_title` or a lighter weekly variant.
- Not strictly mandatory, but useful for parity and UI consistency.

5. **Optional structured windows**
- `peak_window_label` is only a label string.
- To be truly day-like, weekly cards need either:
  - a `peak_window` mini object, or
  - `windows[]` with minimal structure.
- This is optional for v1 of the week-card detail system, but required for full parity.

6. **Related factor identity**
- Either `factor_ids[]` or enough stable identifiers to bind day card disclosures to `major_factors` / domain factors.
- Today has this implicitly through score/window/risk relation keys; week day cards currently do not.

### Minimal DTO addition to unlock day-like details

The smallest useful weekly card extension is:

- `id: string`
- `details?: {`
  - `why_text: string`
  - `supporting_factors: SupportingFactor[]`
  - `why_title?: string | null`
  - `factor_ids?: string[]`
`}`

With just that, `detail-layer.ts` can treat weekly day cards almost exactly like today scores/windows.

## 3) Minimal backend/frontend contract changes vs what can stay frontend-only

### Backend changes that are actually required

#### Required A — narrow day score disclosure fallback

Change backend day assembly so score disclosures stop receiving unconditional domain-global supporting factors.

Why backend-required:
- otherwise frontend cannot distinguish real score evidence from injected generic/domain evidence.
- this is source-of-truth contract behavior, not just rendering.

#### Required B — extend `WeekDayCard` DTO for details

If weekly day cards must become first-class detail items, backend needs to expose at least:
- `id`
- `details.why_text`
- `details.supporting_factors`

Why backend-required:
- current surface model simply lacks the fields.
- frontend cannot synthesize trustworthy supporting factors from headline/best_for/avoid alone.

#### Optional but recommended backend C — formalize a reusable supporting-factor model

Today and week both already carry similar factor entries, but without a single explicit cross-surface contract.
Backend should converge the nested detail factor object to one canonical DTO shape shared across day/week.

### Changes that can be done frontend-only

#### Frontend-only A — detail-layer unification logic

`frontend/lib/detail-layer.ts` can be updated without backend changes to:
- use a shared normalizer for day/week supporting factors;
- dedupe label/body/astro text more aggressively;
- treat week domains/actions/risks/factors through one cleaner contract path.

#### Frontend-only B — stricter placeholder suppression

`frontend/lib/day-brief.ts` and `frontend/lib/detail-layer.ts` can stop exposing generic placeholder factor rows (`"Фактор дня"`, generic explanations) purely on the frontend.

This improves UI honesty even before backend cleanup.

#### Frontend-only C — derive week day detail items once backend fields land

Once weekly card details are added to DTO, frontend changes are straightforward:
- extend `WeekBrief` TS type,
- map `day_cards[*].details`,
- include weekly day cards in `normalizeWeekDetailItems(...)`.

### What should NOT be frontend-only

Do **not** solve weekly day-card explainability by generating fake supporting factors from:
- `best_for`
- `avoid`
- `headline`
- `peak_window_label`

Those are UX hints, not explainability evidence.

## 4) Clean SupportingFactor/detail contract without duplicates or raw labels

### Current problem

Current frontend cleanup in `frontend/lib/detail-layer.ts` already tries to suppress:
- raw semantic keys,
- duplicate label/body pairs,
- duplicate astro/human text.

But the clean contract is still implicit, and `frontend/lib/day-brief.ts` can still manufacture placeholder rows.

### Recommended canonical contract

Use one shared nested contract for all day/week detail disclosures:

```ts
type SupportingFactor = {
  id?: string | null;
  label: string;
  explanation_human: string;
  explanation_astro?: string | null;
  value?: string | null;
  impact?: "high" | "medium" | "low" | null;
  source?: string | null;
};

type DetailDisclosure = {
  why_text: string;
  why_title?: string | null;
  supporting_factors: SupportingFactor[];
};
```

### Clean contract rules

#### SupportingFactor rules

- `label` must be human-readable display copy, never raw semantic keys.
- `explanation_human` is mandatory and is the primary sentence for UI.
- `explanation_astro` is optional secondary technical rationale.
- `value` is optional compact metric/orb/status string.
- `id/source/impact` are optional but strongly recommended for stable joins and analytics.

#### Rejection/drop rules

Drop factor row if:
- both `label` and `explanation_human` are empty;
- `label` is a raw key / snake_case semantic token;
- `label` duplicates `explanation_human` semantically;
- `explanation_astro` duplicates `explanation_human` semantically.

#### DetailDisclosure rules

- `why_text` is required if disclosure exists.
- `supporting_factors` may be empty.
- `why_title` is optional and should not carry business meaning.
- no duplicate factor rows after normalization.

### Practical contract split

To keep source-of-truth clean:
- backend should emit already-humanized factor labels,
- frontend should only validate, dedupe, and drop junk,
- frontend should not invent semantic content.

## Recommended execution order

1. **Backend contract cleanup for day score disclosures**
   - remove unconditional domain-global factor injection into every `scores[*].details`
   - preserve render-safe `advice` fallback, but separate it from evidence

2. **Backend extension of weekly day cards**
   - add `id`
   - add `details.why_text`
   - add `details.supporting_factors`
   - optionally add `details.why_title` / `factor_ids`

3. **Frontend TS contract updates**
   - update `frontend/lib/week-brief.ts`
   - update `frontend/lib/day-brief.ts` factor normalization to drop placeholders instead of inventing them

4. **Detail-layer unification**
   - add week day cards into `normalizeWeekDetailItems(...)`
   - reuse one strict supporting-factor sanitizer across day/week

5. **Targeted verification after implementation**
   - backend: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
   - targeted schema/tests for day/week contracts
   - post-test observability review for day/week traces with explicit verdict

## Minimal change set recommendation

### Minimal backend diff
- `backend/app/services/day_brief.py`
- `backend/app/services/day_brief_types.py`
- `backend/app/services/week_brief_service.py`
- `backend/app/services/week_brief_types.py`
- relevant day/week schema tests

### Minimal frontend diff
- `frontend/lib/day-brief.ts`
- `frontend/lib/week-brief.ts`
- `frontend/lib/detail-layer.ts`
- relevant adapter tests

## Bottom line

- **Day score disclosures are currently globally backfilled at the backend repair layer**; that is the main contract bug to narrow.
- **Weekly day cards are not missing presentation logic; they are missing disclosure fields in the DTO itself**.
- **SupportingFactor should become one explicit shared nested contract across day/week**, with frontend limited to sanitation/deduplication, not semantic invention.
