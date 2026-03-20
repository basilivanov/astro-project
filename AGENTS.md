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
2.  **Backend Logic:** verify via `scripts/pipeline.py` (обязательный быстрый набор) + при необходимости точечные `tests/*.py`.
    - Канонично: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
3.  **Frontend/UI:** verify via `Playwright` E2E **только через Playwright‑контейнер** (в `frontend_dev` нет установленных браузеров):
    - Канонично: `./scripts/run_e2e.sh`
    - Быстро: `./scripts/run_e2e.sh --last-failed` или точечно по файлу/grep
4.  **Critical Rule:** Если билд падает или страница даёт 500/краш — Агент ОБЯЗАН:
    - добавить/обновить тест воспроизведения,
    - починить,
    - убедиться, что тест PASS.

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
