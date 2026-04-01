# 🤖 AI Agent Roles & Protocols (LLM Driven Development)

**Philosophy:** The User acts as the **Architect**. The AI Agents act as **Developers, QA, and DevOps**.

## 👑 User (Architect)
*   Defines high-level goals and business logic.
*   Approves architectural decisions.
*   Reviews final results (UAT).
*   *Does NOT write boilerplate code or run manual regression tests.*

## 🤖 AI Agent (Developer & QA)
*   **Implement:** Writes code based on Architect's constraints.
*   **Verify (Self-Correction):** MUST run tests after every significant change.
*   **Debug:** Analyzes logs/errors and fixes them autonomously.
*   **Refactor:** Maintains code quality and GRACE structure.

## 🧪 Testing Protocol (Log-Driven & E2E)
1.  **Правило “до зелёного” = до зелёного в рамках профиля тестов задачи.**
    - Агент НЕ обязан гонять полный регресс после каждой мелкой правки.
    - Агент обязан итеративно чинить до PASS тех тестов, которые покрывают изменённый участок (минимально‑достаточный набор).
    - **Green tests сами по себе не закрывают verification gate:** после PASS агент обязан посмотреть post-test log/trace evidence по затронутому flow и только потом фиксировать итоговый verdict.
2.  **Backend Logic:** verify via `scripts/pipeline.py` (обязательный быстрый набор) + при необходимости точечные `tests/*.py`.
    - Канонично: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
3.  **Frontend/UI:** verify via `Playwright` E2E **только через Playwright‑контейнер** (в `frontend_dev` нет установленных браузеров):
    - Канонично: `./scripts/run_e2e.sh`
    - Быстро: `./scripts/run_e2e.sh --last-failed` или точечно по файлу/grep
4.  **Critical Rule:** Если билд падает или страница даёт 500/краш — Агент ОБЯЗАН:
    - добавить/обновить тест воспроизведения,
    - починить,
    - убедиться, что тест PASS.
5.  **Post-test observability gate (обязателен после каждого существенного прогона):**
    - После `backend:quick`, `frontend:quick`, `smoke` и любого targeted scenario агент ОБЯЗАН просмотреть `digest/replay/trace evidence`, а не считать PASS тестов достаточным доказательством.
    - Минимум нужно проверить: релевантные structured logs, latest replay/digest summary, latest `trace_id` / `report_id` / `request_id` по затронутому flow и сигналы degradation/fallback/error.
    - Для работ, затрагивающих `Today`, `Week`, `Admin`, `Catalog`, `Billing`, этот шаг обязателен всегда, даже если тесты зелёные и UI визуально выглядит корректно.
    - Агент ОБЯЗАН явно зафиксировать verdict: `clean`, `degraded-but-expected`, `unexpected-degradation` или `no-evidence-blocker`.
    - Если evidence отсутствует, fragmented или показывает unexpected degradation, задача НЕ считается завершённой до разбора логов/trace и фикса/эскалации причины.

## ✅ Test Profiles (быстро → полно)

- **backend:quick (обязательный на каждую существенную правку бэка):**
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- **frontend:quick (обязательный на каждую существенную правку фронта):**
  - `./scripts/run_e2e.sh --last-failed`
  - или точечно: `./scripts/run_e2e.sh e2e/<file>.spec.ts -g "<case>"`
- **smoke (перед тем как отмечать P0/перед отдачей знакомым):**
  - backend:quick
  - `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/core-ux.spec.ts e2e/report-create.spec.ts e2e/quality.spec.ts`
- **full-regression (перед релизом/деплоем/большим мерджем):**
  - backend:quick
  - `./scripts/run_e2e.sh`
- **llm-matrix (дорого/долго, только перед релизом или ночной прогон):**
  - `X_TELEGRAM_AUTH=... python3 tests/grace_report_matrix.py`

## 🛠 Tools
*   **Backend (quick):** `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
*   **Backend (matrix, optional):** `python3 tests/grace_report_matrix.py`
*   **Frontend (quick):** `./scripts/run_e2e.sh --last-failed`
*   **Frontend (full):** `./scripts/run_e2e.sh` (Playwright)
