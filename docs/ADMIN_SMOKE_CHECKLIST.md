# Admin Smoke Checklist

Дата обновления: 2026-03-27

Цель: быстрый QA smoke-чек для `admin surface` перед handoff / smoke-прогоном. Чеклист привязан к фактическим frontend admin routes и backend API.

## Acceptance commands

- Backend quick: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- Frontend admin smoke: `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts`

Ожидание для acceptance: обе команды завершаются с `exit code 0`.

## Coverage map

| Surface | Frontend route | Frontend file | Backend API |
| --- | --- | --- | --- |
| Dashboard | `/admin/dashboard` | `frontend/app/admin/dashboard/page.tsx` | `GET /api/admin/stats`, `GET /api/admin/reports`, `GET /api/admin/feedback` |
| Health | `/admin/health` | `frontend/app/admin/health/page.tsx` | `GET /health`, `GET /api/health`, `POST /api/diagnostics/run` |
| Reports list | `/admin/reports` | `frontend/app/admin/reports/page.tsx` | `GET /api/admin/reports` |
| Report detail | `/admin/reports/[id]` | `frontend/app/admin/reports/[id]/page.tsx` | `GET /api/admin/reports`, `GET /api/admin/reports/{report_id}`, `GET /api/admin/reports/{report_id}/sections/{section_id}`, `POST /api/admin/reports/{report_id}/sections/{section_id}/regenerate/async` |
| Users list | `/admin/users` | `frontend/app/admin/users/page.tsx` | `GET /api/admin/users`, `POST /api/admin/users/{user_id}/subscription/add-days` |
| User detail | `/admin/users/[id]` | `frontend/app/admin/users/[id]/page.tsx` | `GET /api/admin/users/{user_id}`, `POST /api/admin/users/{user_id}/subscription/add-days`, `POST /api/admin/users/{user_id}/balance/add`, `POST /api/admin/users/{user_id}/grant` |
| Clients list | `/admin/clients` | `frontend/app/admin/clients/page.tsx` | `GET /api/admin/clients`, `POST /api/admin/clients` |
| Client detail | `/admin/clients/[id]` | `frontend/app/admin/clients/[id]/page.tsx` | `GET /api/admin/clients/{client_id}`, `PUT /api/admin/clients/{client_id}`, `POST /api/workflows/report/async` |
| Audit | `/admin/audit` | `frontend/app/admin/audit/page.tsx` | `GET /api/admin/audit` |
| Broadcast | `/admin/broadcast` | `frontend/app/admin/broadcast/page.tsx` | `POST /api/admin/broadcast` |
| Tickets | `/admin/tickets` | `frontend/app/admin/tickets/page.tsx` | `GET /api/admin/tickets` |

## Dashboard

- Route: `/admin/dashboard` → `frontend/app/admin/dashboard/page.tsx`
- API contract:
  - `GET /api/admin/stats` from `backend/app/main.py`
  - `GET /api/admin/reports` from `backend/app/main.py`
  - `GET /api/admin/feedback` from `backend/app/main.py`
- Обязательные проверки:
  - Страница открывается без white screen / runtime crash.
  - Блоки counters рендерят значения для `clients`, `reports_total`, `reports_in_progress`, `reports_completed`, `reports_failed`.
  - График / daily activity не падает на пустом массиве `reports_daily`.
  - Recent reports показывает записи или корректный empty/fallback state.
  - Recent feedback показывает записи или корректный empty/fallback state.
  - Переключение query params `days` / `show_test` не приводит к 500 и сохраняет загрузку данных.

## Health

- Route: `/admin/health` → `frontend/app/admin/health/page.tsx`
- API contract:
  - `GET /health` и `GET /api/health` from `backend/app/main.py`
  - `POST /api/diagnostics/run` from `backend/app/main.py`
- Обязательные проверки:
  - Health endpoint возвращает статус без ошибки и UI показывает результат проверки.
  - Кнопка / действие diagnostics запускает `POST /api/diagnostics/run` без фронтового крэша.
  - При недоступности diagnostics UI показывает controlled error state, а не blank page.

## Reports

- Routes:
  - `/admin/reports` → `frontend/app/admin/reports/page.tsx`
  - `/admin/reports/[id]` → `frontend/app/admin/reports/[id]/page.tsx`
- API contract:
  - `GET /api/admin/reports`
  - `GET /api/admin/reports/{report_id}`
  - `GET /api/admin/reports/{report_id}/sections/{section_id}`
  - `POST /api/admin/reports/{report_id}/sections/{section_id}/regenerate/async`
- Обязательные проверки:
  - Reports list грузится без 500, фильтр по статусу не ломает список.
  - У каждой строки отображаются `report_type`, `status`, `client_name`, timestamps / badges.
  - Переход в detail по report id открывает детали без endless loader.
  - Detail рендерит chunks/sections и корректно обрабатывает пустой `include_content` / fallback state.
  - Async regenerate section стартует без frontend crash и показывает ожидаемый pending/success feedback.
  - Ошибка по невалидному report id отображается как controlled error state.

## Users

- Routes:
  - `/admin/users` → `frontend/app/admin/users/page.tsx`
  - `/admin/users/[id]` → `frontend/app/admin/users/[id]/page.tsx`
- API contract:
  - `GET /api/admin/users`
  - `GET /api/admin/users/{user_id}`
  - `POST /api/admin/users/{user_id}/subscription/add-days`
  - `POST /api/admin/users/{user_id}/balance/add`
  - `POST /api/admin/users/{user_id}/grant`
- Обязательные проверки:
  - Users list открывается и поиск `q` не вызывает runtime error.
  - Список показывает user rows с основными полями и рабочей навигацией в detail.
  - Быстрое действие add subscription days из list отрабатывает без поломки UI.
  - User detail грузится по прямой ссылке.
  - Формы add-days / balance / grant отправляются и возвращают success/error message без зависания страницы.
  - Некорректный user id даёт controlled error state.

## Clients

- Routes:
  - `/admin/clients` → `frontend/app/admin/clients/page.tsx`
  - `/admin/clients/[id]` → `frontend/app/admin/clients/[id]/page.tsx`
- API contract:
  - `GET /api/admin/clients`
  - `POST /api/admin/clients`
  - `GET /api/admin/clients/{client_id}`
  - `PUT /api/admin/clients/{client_id}`
  - `POST /api/workflows/report/async`
- Обязательные проверки:
  - Clients list открывается и search / pagination / query params не ломают страницу.
  - Create client форма отправляется и после success список остаётся консистентным.
  - Client detail открывается по id и показывает профиль клиента.
  - Edit/save клиента через `PUT /api/admin/clients/{client_id}` завершается без фронтового крэша.
  - Trigger report workflow через `POST /api/workflows/report/async` стартует и даёт оператору понятный feedback.

## Audit

- Route: `/admin/audit` → `frontend/app/admin/audit/page.tsx`
- API contract:
  - `GET /api/admin/audit`
- Обязательные проверки:
  - Audit log грузится без 500.
  - Таблица / список событий показывает хотя бы основные поля (actor, action, target, time) либо корректный empty state.
  - Пустой результат и длинный результат не ломают layout.

## Broadcast

- Route: `/admin/broadcast` → `frontend/app/admin/broadcast/page.tsx`
- API contract:
  - `POST /api/admin/broadcast`
- Обязательные проверки:
  - Форма открывается и обязательное поле текста валидируется на клиенте.
  - Submit с валидным payload стартует broadcast и показывает success feedback.
  - Опциональный `image_url` не ломает submit path.
  - Ошибка API отображается без потери введённого текста.

## Tickets

- Route: `/admin/tickets` → `frontend/app/admin/tickets/page.tsx`
- API contract:
  - `GET /api/admin/tickets`
- Обязательные проверки:
  - Tickets page грузится server-side без 500.
  - Список тикетов показывает `topic`, `status`, `message`, `created_at`, user reference.
  - При отсутствии тикетов виден корректный empty state.
  - Telegram reply link отображается только когда есть `username`.

## Smoke execution order

- 1. Запустить backend quick acceptance: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- 2. Запустить admin Playwright smoke: `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts`
- 3. Если любой шаг падает, зафиксировать failing surface, добавить/обновить тест воспроизведения и чинить до PASS в рамках admin smoke профиля.

## Handoff evidence

- Сослаться на этот документ в task handoff и в `docs/TASK.md`.
- Зафиксировать статус acceptance команд: `PASS` / `FAIL` / `BLOCKED` с краткой причиной.
