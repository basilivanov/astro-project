# Product Surface Brief — Today / Week / Store / Profile / Read

Короткий briefing для следующего агента по текущим consumer/admin surface’ам, DTO и незакрытым зависимостям. Документ опирается на актуальные реализации в `frontend/app/*`, DTO-адаптеры в `frontend/lib/*`, backend endpoints в `backend/app/main.py` и текущий task packet в `docs/DAY_WEEK_TASK_PACKET.md`.

## 1) Экраны и ключевые блоки

### Today (`/`)
- Основной consumer home surface: `frontend/app/page.tsx`.
- Рендерится через `ConsumerPageShell` + day-brief блоки из `frontend/components/today/daybrief-sections.tsx`.
- Ключевые блоки: hero/verdict, scores, windows, best uses/actions, risks, explainability, CTA panel, loading/empty/error states.
- Источник данных: `GET /api/feed/today` (`backend/app/main.py`) с вложенным `day_brief`; нормализация в `frontend/lib/day-brief.ts`.
- Today уже переведён на top-layer DTO consumption; legacy business logic убран из UI, остаётся только controlled fallback normalization.

### Week (`/week`)
- Недельная top-layer surface: `frontend/app/week/page.tsx`.
- Ключевые блоки: hero/theme, day cards map, domain cards, best uses, risks, major factors, explainability, CTA к full report/premium, embedded resume banner.
- Источник данных: backend week map/report payloads с `week_brief`; фронтовая нормализация в `frontend/lib/week-brief.ts`.
- Deep markdown sections по-прежнему живут как secondary/read layer; top layer экрана принадлежит `WeekBrief`, как зафиксировано в `docs/DAY_WEEK_TASK_PACKET.md`.

### Catalog / Store (`/reports`, `/reports/history`)
- Storefront/catalog listing: `frontend/app/reports/page.tsx`.
- История / resume bridge: `frontend/app/reports/history/page.tsx`.
- Ключевые блоки: product/catalog cards, checkout CTA, inline resume banner, filters/history actions, переходы в create/read.
- Общий resume UI: `frontend/components/catalog/catalog-checkout-resume.tsx` (`CatalogCheckoutResumeBanner`).
- Surface служит общей коммерческой точкой входа для premium/report flows и recovery незавершённого checkout.

### Profile / Admin (`/profile`, `/profile/edit`, `/admin/*`)
- Профиль пользователя: `frontend/app/profile/page.tsx`, редактирование — `frontend/app/profile/edit/page.tsx`.
- Источник данных: `GET /api/users/me`, update через тот же профильный backend модуль в `backend/app/main.py`.
- Ключевые блоки: birth data, subscription/referral status, edit actions, profile completeness.
- Admin surfaces: `frontend/app/admin/page.tsx` и дочерние страницы (`dashboard`, `health`, `reports`, `users`, `clients`, `audit`, `broadcast`, `tickets`).
- Admin — отдельный operational surface, не часть consumer Day/Week UX, но участвует в acceptance/smoke профилях.

### Read (`/read/[id]`)
- Экран чтения готового отчёта: `frontend/app/read/[id]/page.tsx`.
- Ключевые блоки: report sections/chunks, fallback text rendering для неразобранного формата, share/support/retry actions, embedded resume banner.
- Read сохраняет canonical telemetry surface=`read` и связывает completed report с resume/catalog flow.

## 2) DTO / факты и fallback режимы по экранам

### Today
- Канонический DTO: `DayBriefDto` в `frontend/lib/day-brief.ts`.
- Что используется экраном:
  - `summary`, `context`, `scores`, `windows`, `best_uses`, `risks`, `personalized_factors`, `explainability`, `premium`, `cta`.
  - `TodayViewModel.state` = `ready` | `fallback`; `source` = `dto` | `legacy_visual`.
- Backend contracts:
  - `GET /api/day/brief` возвращает `DayBriefDTO`.
  - `GET /api/feed/today` возвращает feed envelope с `day_brief`, telemetry fields и legacy-safe meta (`backend/app/main.py:4142`, `backend/app/main.py:3942` примерно в том же модуле).
- Факты/расчёты под капотом по packet’у: summary, scores, windows, best uses, risks, personalized factors, premium, explainability считаются детерминированно; LLM только полирует текстовые поля (`docs/DAY_WEEK_TASK_PACKET.md`).
- Fallback:
  - strict normalization во фронте;
  - render-safe fallback DTO при schema/polish failure;
  - допускается legacy visual fallback, но без возврата скрытой бизнес-логики в UI.

### Week
- Канонический DTO: `WeekBrief` / `WeekBriefEnvelope` (packet + frontend adapter `frontend/lib/week-brief.ts`).
- Что используется экраном:
  - `summary`, `status`, `day_cards`, `domains`, `best_uses`, `risks`, `major_factors`, `deep_sections`, `report_ref`, `premium`, `explainability`, `cta`.
- Backend facts/transport:
  - `GET /api/week/map` даёт week top-layer payload (`backend/app/main.py:4128`).
  - Week UI также умеет жить рядом с report/read transport, если нужен envelope/polling-compatible режим.
- Факты/расчёты под капотом: week boundaries, daily signals, workflow/report state, slow background factors, domain aggregation, report linkage; детерминистический `WeekBrief`, затем bounded polish текста (`docs/DAY_WEEK_TASK_PACKET.md`).
- Fallback:
  - `WeekBriefEnvelope.status` для `in_progress` / `ready` / error-compatible состояний;
  - детерминистический fallback payload при schema/polish failure;
  - deep markdown sections остаются secondary UX, даже если top layer частично деградировал.

### Catalog / Store
- Явного одного DTO на всю storefront surface нет: экран собирается из catalog/report listing и billing/resume фактов.
- Ключевые факты:
  - список доступных report/product карточек,
  - checkout token / resume token,
  - billing session status,
  - report history entries,
  - optional resumed report id / return path.
- Resume banner использует унифицированный компонент `CatalogCheckoutResumeBanner` и общую resume telemetry namespace.
- Fallback:
  - inline resume banner может быть hidden/idle/ready/status-based;
  - catalog/history страницы держат empty/error states, не ломая shell и не теряя recovery path.

### Profile / Admin
- Profile использует `UserProfileOut` / update payload из `backend/app/main.py:3207` и `/api/users/me` (`backend/app/main.py:3242`).
- Ключевые факты профиля: имя, birth date/time/place completeness, subscription status, referral code, доступность consumer personalization.
- Fallback:
  - неполный профиль не должен ломать surface; вместо этого backend/frontend ведут к profile completion;
  - для day/week это напрямую влияет на `personalization_level`, explainability и часть gating/empty-state логики.
- Admin использует набор operational DTO для dashboard/reports/users/clients/health; fallback — стандартные loading/error/admin empty states.

### Read
- Read использует report payload/chunks, а не `DayBrief`/`WeekBrief` как основной формат.
- Ключевые факты: `report.id`, `report_type`, `status`, `client_name`, `access_source`, `chunks`, optional `chart_svg` (`frontend/app/read/[id]/page.tsx`).
- Fallback:
  - если секция не разбирается в rich blocks, экран показывает safe text fallback (`SECTION_FALLBACK_MESSAGE`);
  - retry/support/failure context сохраняются отдельными semantic blocks;
  - resume banner остаётся доступным для recovery flow.

## 3) Что уже реализовано по telemetry / acceptance

### Telemetry
- Today и Week уже имеют generation + UX telemetry contract, зафиксированный в `docs/DAY_WEEK_TASK_PACKET.md`.
- Day backend пишет trace/fallback/generation fields вокруг `day_brief` build paths в `backend/app/main.py:4023`, `backend/app/main.py:4088`, `backend/app/main.py:4190`.
- Catalog/resume telemetry централизована в:
  - `frontend/components/catalog/catalog-analytics.ts`
  - `frontend/components/catalog/catalog-checkout-resume.tsx`
  - backend log helpers в `backend/app/catalog_logging.py`.
- Resume telemetry уже покрывает события `catalog.checkout_resume_ready/start/success/cancel/status`; week/history/read surface’ы прокидывают свой `surface`/`entryPoint` и correlation context (`docs/CORRELATION_ID_PLAN.md`).
- Read surface держит strict telemetry contract с `surface="read"` и `FLOW-FORECAST-CATALOG` в `frontend/app/read/[id]/page.tsx`.

### Acceptance / tests
- Каноничный backend quick profile: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
- Каноничный frontend quick profile: `./scripts/run_e2e.sh --last-failed` или точечный запуск нужного spec.
- Уже есть прямые e2e/regression тесты для Day/Week surface’ов:
  - `frontend/e2e/today-daybrief.spec.ts`
  - `frontend/e2e/week-home-refresh.regression.spec.ts`
  - дополнительно `frontend/e2e/week-live.spec.ts`, `frontend/e2e/week-page-fallback.spec.ts`, `frontend/e2e/week-fallback.regression.spec.ts`.
- Smoke profile из AGENTS.md/packet: backend quick + `e2e/admin.smoke.spec.ts`, `e2e/core-ux.spec.ts`, `e2e/report-create.spec.ts`, `e2e/quality.spec.ts`.

## 4) Что ещё в работе (Wave 4 / 5) и оставшиеся зависимости

### Wave 4 — frontend hardening
- По packet’у и `docs/TASK.md`, цель Wave 4: полностью зачистить hidden legacy logic на Today/Week, оставить только rollout adapters и tighten premium/empty/loading/error states вокруг strict DTO.
- Существенная часть уже сделана: `/week` top layer мигрирован на `WeekBrief`, Today/Week legacy UI assembly paths удалены, TypeScript debt после cutover закрыт (`docs/TASK.md`).
- Что ещё важно держать в фокусе:
  - не возвращать astro-calculation логику во фронт;
  - удерживать premium gating только как render/gating policy поверх DTO, а не как локальные вычисления;
  - стабилизировать edge cases envelope/fallback/resume пересечений.

### Wave 5 — quality loop
- Ещё открытый слой: lock prompt contracts, schema failure telemetry, repair outcome visibility, benchmark linkage (`docs/DAY_WEEK_TASK_PACKET.md`).
- Требуются/ожидаются:
  - стабильная запись `quality.schema_failure`, `quality.invalid_json`, `quality.fallback_activated`, `quality.prompt_repair`, `quality.repair_success`, `quality.benchmark_linked`;
  - связка trace/correlation/prompt version/model/fallback mode в diagnostics;
  - smoke profile перед P0 handoff.

### Оставшиеся зависимости
- Backend остаётся source of truth для DayBrief/WeekBrief расчётов; фронт не должен пересобирать score/window/domain logic.
- Profile completeness и entitlement/subscription data остаются зависимостью для personalization, premium gating и CTA выбора.
- Resume/banner flows зависят от billing session + checkout token plumbing и общей correlation chain между catalog/history/week/read.
- Deep week report content остаётся отдельным read/report transport слоем; top-layer `WeekBrief` не должен размываться назад в markdown-first UX.

## Быстрые ссылки
- Task packet: `docs/DAY_WEEK_TASK_PACKET.md`
- Текущий статус работ: `docs/TASK.md`
- Today surface: `frontend/app/page.tsx`
- Week surface: `frontend/app/week/page.tsx`
- Store surfaces: `frontend/app/reports/page.tsx`, `frontend/app/reports/history/page.tsx`
- Profile: `frontend/app/profile/page.tsx`
- Read: `frontend/app/read/[id]/page.tsx`
- Day adapter: `frontend/lib/day-brief.ts`
- Week adapter: `frontend/lib/week-brief.ts`
- Backend contracts: `backend/app/main.py`
- Resume telemetry/logging: `frontend/components/catalog/catalog-checkout-resume.tsx`, `backend/app/catalog_logging.py`, `docs/CORRELATION_ID_PLAN.md`
