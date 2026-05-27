# Week backend/AI audit — 2026-04-02

## Scope

- Inputs reviewed: `/home/astro/.ductor/workspace/AGENTS.md`, `/opt/astro-project/AGENTS.md`, `/opt/astro-project/GRACE.md`.
- Requested backend/AI deltas reviewed against code reality:
  - minimum `3–4` sentence cluster summaries;
  - richer factor explanations;
  - strict calendar window `Monday–Sunday`;
  - heavier predictive methods for weekly forecast.

## Concise diagnosis

### 1) Already partially covered

- `WeekBrief` already has a deterministic assembly layer in `backend/app/services/week_brief_service.py` with explicit top-layer factors, domain explainability, action/risk enrichment, and fallback path.
- Factor explanations are already richer than a bare score: records carry both `explanation_human` and `explanation_astro`, and the DTO exposes `supporting_factors`, `why_text`, domains, actions, risks, and deep sections.
- The week prompt context already receives a partial slow-background pack via `_build_week_brief_seed_bundle(...)` in `backend/app/services/report_workflow.py`: `profection`, `solar_return`, `solar_arcs`, `long_transits`, `retrogrades`, `lunations`.
- Weekly prompts/validation already have a hard structural contract: `week_strategy` must include `главная тема`, `статус недели`, `подневная стратегия`, `резюме по срезам` in `backend/app/llm/orchestrator.py`.

### 2) Prompt-only gaps

- Prompt text for `week_strategy` is still shallow relative to the new ask. `backend/app/reporting/section_templates.py` asks only for status/theme/day strategy/traffic lights and does not explicitly demand `3–4` sentences per cluster summary.
- The validator in `backend/app/llm/orchestrator.py` enforces block presence, but not density/length/depth. So richer cluster summaries can be improved first with prompt contract tightening, but quality is not guaranteed without stronger validation.
- If the product ask is only “say more using the same facts”, then first-pass change is prompt-only plus maybe validator-only.

### 3) Backend / data / astrology-engine gaps

- Strict `Monday–Sunday` is not reliably enforced today. `stellium_engine.py:1259` simply loops `7` days from the provided `start_date`; if creation happens on Thursday, the produced week is Thursday–Wednesday, not canonical Monday–Sunday.
- “Heavier predictive methods” are only partially true. The week pipeline imports slow-background signals from month/year data into the seed, but the actual engine method `stellium_engine.py:1259` computes week traffic almost entirely from same-day transit hits, ingress checks, Moon phase/sign, and void-of-course. It does not itself score or rank weekly output from profections / solar arcs / solar return / progressions.
- Richer factor explanations are partially covered in DTO assembly, but not fully grounded in the engine. Many explanations are semantic wrappers over current week/day facts rather than explicit method-attributed reasoning like “weekly tone is dominated by profection lord + solar arc hit + long transit stack”.
- There is no evidence in the reviewed code that secondary progressions are present in the week engine/runtime path. If “more heavy methods” explicitly includes progressions, that is a backend/engine extension, not prompt work.

## Requested-change classification

### A. Minimum 3–4 sentences in cluster summaries

- **Partially covered:** deep sections and deterministic summaries already exist.
- **Prompt-only minimum:** yes, for instructing the LLM to output denser summaries.
- **Backend follow-up recommended:** yes, if this must be enforced consistently. Add validation for minimum sentence count / minimum semantic density on relevant weekly clusters or deterministic fallback expansions.

### B. Richer factor explanations

- **Partially covered:** yes, strongly.
- **Prompt-only minimum:** possible for week deep-read prose.
- **Backend/data change needed for full closure:** yes, if the goal is materially better explainability rather than longer copy. Need stronger factor provenance and/or attribution from slow methods into factor seeds and summaries.

### C. Strict calendar slice Monday–Sunday

- **Partially covered:** no reliable evidence.
- **Prompt-only:** no.
- **Backend/engine change:** required. Normalize the forecast window anchor before week generation and keep UI/API wording aligned to the normalized window.

### D. Heavier predictive methods for week

- **Partially covered:** yes, but only as borrowed background context from month/year layers.
- **Prompt-only:** no, not for the real requirement.
- **Backend/engine change:** required if the goal is that weekly judgement is genuinely computed from heavier methods rather than merely decorated with them.

## Safe bounded waves

### Wave 0 — Audit/contract hardening only

- Freeze desired semantics in a compact packet/doc before code changes.
- Define what counts as a “cluster” for week output and which blocks need `3–4` sentence minimum.
- Define whether “heavier methods” means only existing `profection + solar return + solar arcs + long transits`, or also requires `secondary progressions` / time-lord refinement.

### Wave 1 — Prompt-only quality lift

- Write scope:
  - `backend/app/reporting/section_templates.py`
  - optionally `backend/app/llm/orchestrator.py`
- Change:
  - strengthen `week_strategy` prompt contract to require `3–4` sentence summaries for each target cluster/block;
  - require explicit factor explanation format: practical meaning + astrological mechanism + implication for action/risk;
  - optionally add light validation on sentence count / mandatory subfields.
- Why bounded:
  - no DTO/schema churn;
  - no engine math changes;
  - low blast radius.

### Wave 2 — Calendar correctness

- Write scope:
  - `stellium_engine.py`
  - `backend/app/services/report_workflow.py`
  - tests around week window normalization.
- Change:
  - normalize weekly anchor to local-calendar Monday start and Sunday end before `calculate_forecast_week_data(...)`;
  - preserve explicit `forecast_window.start/end` evidence in response/logs.
- Why bounded:
  - business-correctness fix with limited surface area;
  - independent from prose quality.

### Wave 3 — Backend explainability grounding

- Write scope:
  - `backend/app/services/week_brief_service.py`
  - `backend/app/services/report_workflow.py`
  - possibly `backend/app/services/forecast_semantics.py`
- Change:
  - propagate slow-background source attribution into factor seeds more explicitly;
  - distinguish factors driven by fast transits vs month/year background;
  - expand cluster summaries/factors using method-tagged evidence, not just generic semantic text.
- Why bounded:
  - improves explainability without rewriting the engine core.

### Wave 4 — Real weekly method upgrade

- Write scope:
  - `stellium_engine.py`
  - maybe adjacent engine helpers if extracted.
- Change:
  - revise `calculate_forecast_week_data(...)` so weekly status and ranking incorporate heavier methods in scoring, not only imported context;
  - candidate sources: profection emphasis, solar-return active houses/angles, solar arcs already available in year layer, long-transit dominance, optional secondary progressions if approved.
- Why bounded:
  - this is the only wave that changes forecast truth-path rather than presentation.

## Risks and blockers

- **Requirement ambiguity:** “cluster summaries” is not yet canonical in code. Need exact mapping: which week sections/DTO fields count as clusters.
- **Method ambiguity:** “heavier methods” may mean different astrology stacks. Without explicit controller decision, there is a risk of building the wrong truth path.
- **Prompt-only illusion risk:** adding prose depth without engine changes can create nicer copy but not materially stronger forecast logic.
- **Regression risk on week DTO/tests:** sentence-count or structure changes can break current deterministic/fallback expectations and validation assumptions.
- **Calendar/timezone risk:** Monday–Sunday must be defined in the user forecast locale, not server UTC; otherwise “strict week” will still drift near timezone boundaries.
- **Observability gap:** once week truth-path changes, evidence should log which methods actually influenced the result; today that provenance is only partial.

## Recommended controller stance

- Treat `Monday–Sunday` as a mandatory backend correctness fix, not a prompt tweak.
- Treat `3–4` sentence summaries as a prompt-first wave with optional validator hardening.
- Treat “richer factor explanations” as already partially closed, but not fully closed if the product expects stronger causal attribution.
- Treat “heavier weekly methods” as a truth-path change requiring explicit bounded design before coding.

## Reviewer verdict

- **Already partially covered:** richer factor explanations; slow-background context in week seed; deterministic WeekBrief explainability.
- **Prompt-only:** denser `3–4` sentence weekly cluster summaries, plus some style/depth improvement in factor prose.
- **Backend/data/engine required:** strict `Monday–Sunday`; real weekly use of heavier predictive methods; full method-grounded explainability.
- **Best safe sequence:** Wave 1 prompt hardening → Wave 2 calendar normalization → Wave 3 explainability grounding → Wave 4 engine-method upgrade.
