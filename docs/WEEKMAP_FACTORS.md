# WeekBrief / WeekMap inputs and factor sources

## Short answer

For the current Wave 3/4 implementation, `WeekMap`/week top layer does **not** need to separately fetch profections or solar data on the frontend.

The correct model is:

- `WeekMap` legacy endpoint is assembled from deterministic `week_data` plus a semantic layer.
- `WeekBrief` already adds the **slow background drivers** on the backend when they are present in the report context/seed: profection, solar return, solar arcs, and long transits.
- The frontend should read `week_brief` first and only use legacy `week_map` as a compatibility fallback.

So the practical answer is: **`week_data` alone is enough for legacy `WeekMap`, but not enough to explain the full WeekBrief factor stack**. The richer slow-moving drivers are already folded into `WeekBrief.major_factors` on the backend; they do not need a separate frontend fetch.

## Why this matters

There are two different weekly layers in the repo:

- legacy `WeekMap` payload for older UI compatibility;
- canonical `WeekBrief` payload for the current week top layer.

This distinction is important because the user question mixes both concerns:

- if the question is about the old `WeekMap` endpoint shape, it is mostly driven by current `week_data` decomposition;
- if the question is about what the **current week surface should rely on**, then the answer is `WeekBrief`, and `WeekBrief` already includes slow background factors when they exist in backend context.

## Backend sources already in use

### 1. Legacy `WeekMap`

The legacy weekly endpoint lives in `backend/app/main.py:4128` and calls `build_week_map(...)` from `backend/app/services/week_map.py:289`.

`build_week_map()` is built from these backend ingredients:

- `engine.calculate_forecast_week_data(...)` → raw week/day decomposition in `backend/app/services/week_map.py:289`;
- normalized days via `_normalize_week_day_payload(...)` in `backend/app/services/week_map.py:290`;
- week summary via `_normalize_week_summary(...)` in `backend/app/services/week_map.py:291`;
- semantic overlay via `build_week_forecast_semantic_layer(...)` in `backend/app/services/week_map.py:292`;
- factor list via `_build_factor_inputs(...)` in `backend/app/services/week_map.py:295`;
- weighted factor aggregation via `apply_weighted_factors(...)` before emitting `major_factors`.

Important limitation: the legacy factor builder in `week_map.py` uses mostly:

- semantic theme/tension;
- best/worst day selection from weekly day cards;
- rare boosters from day events.

It does **not** independently assemble the full slow-driver stack like profection + solar return + solar arcs from report context.

### 2. Canonical `WeekBrief`

The canonical weekly payload is built in `backend/app/services/week_brief_service.py:1021` by `build_week_brief_payload(...)` and attached to report responses in `backend/app/main.py:3686`.

`WeekBrief` is built from a seed/context bundle, not only from raw `week_data`:

- `_build_seed(...)` in `backend/app/services/week_brief_service.py:1005`;
- `_build_week_brief_seed_bundle(...)` from workflow/report context;
- normalized weekly summary if missing;
- day cards via `_build_day_cards(...)`;
- factor seeds via `_build_factor_seeds(...)`;
- factor weighting via `_weighted_factor_payloads(...)`;
- deep markdown sections via `_build_deep_sections(...)`;
- final schema validation via `validate_week_brief_payload(...)`.

This is the place where the richer factor model actually lives.

## Week data decomposition

The fast/near-term weekly decomposition comes from `week_data` and is used in both layers.

The decomposition includes:

- daily records from `week_data["days"]`;
- normalized per-day traffic light / tension / moon / events via `_normalize_week_day_payload(...)` in `backend/app/services/week_map.py:124` and mirrored helpers in `backend/app/services/week_brief_service.py`;
- week summary/traffic light via `_normalize_week_summary(...)` in `backend/app/services/week_map.py:167`;
- top/bottom day extraction for practical best-use/risk framing.

In other words, `week_data` is the **fast tactical layer**:

- day decomposition;
- visible weekly triggers;
- tension color/status;
- event-derived headlines.

This layer is enough to render a usable week map, but it is not the complete explanation model for the current WeekBrief UX.

## Slow background drivers

The slow background drivers are assembled in `_build_factor_seeds(...)` in `backend/app/services/week_brief_service.py:453`.

This function explicitly consumes more than `week_data`:

- `year_forecast_data`;
- `month_forecast_data`;
- `semantic_layer`;
- normalized week summary/days.

### Drivers currently folded into `WeekBrief.major_factors`

When present in the seed/context, the backend already adds:

- **Profection / time-lord style annual focus**
  - source: `year_forecast_data["profection"]`;
  - code path: factor id `profection` in `backend/app/services/week_brief_service.py:489`.
- **Solar return background**
  - source: `year_forecast_data["solar_return"]`;
  - code path: factor id `solar_return` in `backend/app/services/week_brief_service.py:506`.
- **Solar arcs / directions**
  - source: `year_forecast_data["solar_arcs"]`;
  - code path: `direction_1`, `direction_2` in `backend/app/services/week_brief_service.py:523`.
- **Long transits**
  - source: `month_forecast_data["major_transits"]`;
  - code path: `long_transit_1`, `long_transit_2` in `backend/app/services/week_brief_service.py:541`.
- **Rare boosters / background ingresses**
  - source: `month_forecast_data["ingresses"]`;
  - code path: `booster_1` in `backend/app/services/week_brief_service.py:559`.

Additionally, the same factor stack also includes:

- period theme anchor from `semantic_layer`;
- best day / strongest window from weekly decomposition;
- worst day / friction point from weekly decomposition.

So the current backend model is already a merge of:

- **fast weekly triggers** (`week_data.days`, summary, events), and
- **slow background drivers** (`year_forecast_data`, `month_forecast_data`).

## Where factors are aggregated

There are two aggregation points.

### Legacy `WeekMap`

- raw factor candidates are assembled in `_build_factor_inputs(...)` in `backend/app/services/week_map.py:203`;
- weighted output is produced through `apply_weighted_factors(...)` and emitted as `major_factors` in `backend/app/services/week_map.py:315`.

This is a lightweight compatibility aggregator.

### Canonical `WeekBrief`

- typed factor seeds are assembled in `_build_factor_seeds(...)` in `backend/app/services/week_brief_service.py:453`;
- they are transformed by `_weighted_factor_payloads(...)` into `major_factors`;
- final payload includes `major_factors` in `backend/app/services/week_brief_service.py:1148`;
- schema validation runs in `validate_week_brief_payload(...)` immediately after assembly in `backend/app/services/week_brief_service.py:1154`.

This is the authoritative factor stack for the week top layer.

## Envelope / polling model

The repo explicitly supports an optional polling wrapper for weekly data.

- `WeekBriefEnvelope` is documented as optional transport in `docs/DAY_WEEK_TASK_PACKET.md:44`;
- it is built by `build_week_brief_envelope(...)` in `backend/app/services/week_brief_service.py:1194`;
- report responses attach both `week_brief` and `week_brief_envelope` in `backend/app/main.py:3714`;
- the envelope carries:
  - `status`,
  - `data`,
  - `message`,
  - `retry_after_seconds`.

Meaning:

- use `week_brief_envelope.data` when polling-compatible semantics are needed;
- use plain `week_brief` when the report is already ready;
- do not invent separate frontend polling for slow drivers, because they are part of the same backend-assembled brief.

## How the frontend reads this

The week page reads the report payload in `frontend/app/week/page.tsx:179`.

The mapping order is explicit:

- first try `payload?.week_brief_envelope?.data`;
- then fall back to `payload?.week_brief`;
- then fall back to legacy `payload?.week_map`.

This happens through `mapWeekReportToWeekBrief(...)` in `frontend/lib/week-brief.ts:187`.

### Frontend precedence rules

`mapWeekReportToWeekBrief(...)` uses:

- `brief.day_cards` first, else legacy `week_map.day_cards`;
- `brief.domains` first, else legacy `week_map.domains`;
- `brief.best_uses` / `brief.risks` first, else legacy `actions` / `risks`;
- `brief.major_factors` first, else legacy `week_map.major_factors`;
- `brief.deep_sections` first, else report `chunks` converted into markdown sections.

That means the current frontend is already designed around this rule:

- **`WeekBrief` is the source of truth**;
- `WeekMap` is compatibility fallback only.

This is also consistent with `docs/DAY_WEEK_TASK_PACKET.md:9` and `docs/GRACE_ARTIFACTS.md:245`.

## Answer to the original product question

### Do we need to additionally pull profection / solar for WeekMap?

**No, not as a separate frontend fetch and not for the current canonical week surface.**

More precise answer:

- for the **legacy `WeekMap` payload**, the current implementation mostly relies on `week_data` decomposition plus semantic aggregation, so adding extra frontend fetches for profection/solar would be the wrong integration point;
- for the **current Week week top layer**, the richer slow-moving factors are already assembled on the backend inside `WeekBrief.major_factors` from `year_forecast_data` and `month_forecast_data`.

### Is `week_data` enough?

- **Enough for legacy map rendering:** yes.
- **Enough for full explanatory factor model:** no.
- **Enough for the current product surface:** only because the backend already augments it with slow drivers in `WeekBrief`.

## Recommended wording for handoff

Recommended concise answer to the architect/user:

> Для текущего Week surface отдельно тянуть профекцию/соляр не нужно. Legacy `week_map` в основном собирается из `week_data` факторов, но канонический `WeekBrief` уже дополняет их slow background drivers из backend context: profection/time-lord annual focus, solar return, solar arcs и long transits. Поэтому фронт должен читать `week_brief`/`week_brief_envelope`, а `week_map` оставлять только как compatibility fallback.

## Practical implication

If later we want the **legacy `/api/week/map` endpoint itself** to expose the same richer explanation model, then the right change would be backend-side:

- enrich `build_week_map()` with the same seed/context-derived slow drivers,
- or deprecate direct `week_map` usage and continue converging everything onto `WeekBrief`.

For Wave 3/4, the second option is already what the codebase implements.

## Envelope transport vs deep report

### Transport contract

There are two separate backend contracts that must stay aligned but should not be conflated:

- `week_brief_envelope` is the lightweight transport contract for week top surfaces and resume/read polling;
- deep report content lives inside `WeekBrief.deep_sections` and the full `/read/{id}` flow.

`WeekBriefEnvelope` exists so clients can safely distinguish transport state from content state:

- `status=ready` means `data` is present and contains a validated `WeekBrief` payload;
- `status=in_progress` means `data=null`, `message` explains that assembly is still running, and `retry_after_seconds` tells resume/read layers when to poll again;
- `status=error` means `data=null`, `message` carries either `report.error_message` or the backend fallback error text, and the client should stop optimistic polling and render failure/retry UI.

### Legacy week map vs canonical brief

The compatibility rule is:

- canonical read path: consume `week_brief_envelope` first;
- canonical content payload: consume `week_brief` inside envelope `data` when `status=ready`;
- legacy fallback: only fall back to `week_map` when `week_brief` is unavailable or when an older surface still requires the legacy DTO.

So `week_map` is not a transport-state protocol. It is only a compatibility content payload.

### Resume/read layer expectations

Resume/read layers should interpret envelope states this way:

- `in_progress` → keep resume banner / loading state active and poll using `retry_after_seconds`;
- `ready` → switch from polling transport to rendering `summary`, `day_cards`, `major_factors`, and `deep_sections` from `data`;
- `error` → stop polling, preserve resume/failure UX, and show `message` as the backend-authored reason.

This split keeps frontend state management simple:

- transport state comes from envelope fields (`status`, `message`, `retry_after_seconds`);
- report semantics come from `WeekBrief` itself (`summary`, `major_factors`, `deep_sections`, `report_ref`);
- legacy `week_map` remains a fallback renderer, not the source of polling truth.

## Deep sections fallback and read surface

`WeekBrief` top layer and legacy report chunks must coexist without collapsing back into markdown-first week UX.

The contract is:

- backend keeps canonical deep content in `WeekBrief.deep_sections` when chunk parsing succeeds;
- backend fallback mode still preserves legacy report chunks as `deep_sections`, so `/read/{id}` and week resume surfaces do not lose long-form content even if the richer WeekBrief layer degrades;
- frontend read surface consumes `week_brief_envelope.data` / `week_brief` first, and only synthesizes `deepSections` from legacy report `chunks` when `week_brief.deep_sections` is empty or absent;
- legacy `week_map.deep_sections` is compatibility-only metadata and should not become the primary read payload when report chunks are available.

### Precedence and fallback rules

`frontend/lib/week-brief.ts` enforces this precedence for deep content:

1. use `week_brief.deep_sections` when present;
2. otherwise map backend `report_chunks` into `deepSections` for the read/resume layer;
3. do not treat legacy `week_map.deep_sections` string arrays as the canonical read surface.

This keeps responsibilities separated:

- `WeekBrief.summary`, `day_cards`, `domains`, and `major_factors` drive the top week screen;
- `deep_sections` carry secondary long-form reading content;
- legacy chunks remain the durable fallback transport for read surfaces while the product converges on WeekBrief.

### Verification hooks

Regression coverage for this coexistence lives in:

- `tests/test_week_brief_service.py` for backend preservation of deep sections and fallback from legacy report chunks;
- `tests/test_week_brief_frontend_mapping.py` for runtime verification of `frontend/lib/week-brief.ts` mapping precedence.

