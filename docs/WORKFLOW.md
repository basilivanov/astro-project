# Workflow Example

## Request

```bash
curl -X POST http://localhost:8000/api/workflows/report \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Demo Client",
    "birth_date": "1990-01-15 12:00",
    "birth_location": "Sochi, Russia",
    "report_type": "natal_master"
  }'
```

## Async Request (UI friendly)

```bash
curl -X POST http://localhost:8000/api/workflows/report/async \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Demo Client",
    "birth_date": "1990-01-15 12:00",
    "birth_location": "Sochi, Russia",
    "report_type": "natal_master"
  }'
```

## Async Response (shape)

```json
{
  "report_id": "uuid",
  "client_id": "uuid",
  "status": "in_progress"
}
```

Check progress via `/api/admin/reports/{id}`.

## Response (shape)

```json
{
  "report_id": "uuid",
  "client_id": "uuid",
  "markdown": "# Report: natal_master\n\n## Core Profile\n\n...",
  "sections": [
    {
      "section_id": "core",
      "title": "Core Profile",
      "content": "..."
    }
  ],
  "chart": {
    "chart_type": "natal",
    "name": "Demo Client",
    "datetime_utc": "1990-01-15T12:00:00+00:00",
    "datetime_local": "1990-01-15T12:00:00+00:00",
    "location": {
      "name": "Sochi, Russia",
      "latitude": 43.6028,
      "longitude": 39.7342,
      "timezone": "Europe/Moscow"
    },
    "house_system": "Placidus",
    "houses": [
      {
        "house": 1,
        "longitude": 0.0,
        "sign": "Aries",
        "sign_degree": 0.0
      }
    ],
    "positions": [
      {
        "name": "Sun",
        "key": "Sun",
        "longitude": 0.0,
        "latitude": 0.0,
        "sign": "Aries",
        "sign_degree": 0.0,
        "is_retrograde": false
      }
    ],
    "fixed_stars": [],
    "dispositor_summary": {
      "version": "dispositor_summary_v1",
      "summary": "",
      "links": [],
      "loops": []
    }
  }
}
```

Optional normalization fields exposed by serialization:
- `positions[].key`: canonical point key for report consumers. Example: raw `Mean Apogee` keeps `name`, but `key` is `Lilith`.
- `positions[].raw_name`: original engine label when `key` is an alias.
- `fixed_stars[].point`: canonical point key for the conjunction target.
- `fixed_stars[].raw_point`: original engine label for the same target.
- `fixed_stars[].sign`: zodiac sign of the fixed star longitude.
- `chart.dispositor_summary`: structured dispositor summary kept alongside legacy text used internally.

## LLM Modes (Local CLI vs OpenRouter)

Set the default LLM mode via env:

```
DEFAULT_LLM_MODE=openrouter
```

### Supported Modes:
- `openrouter`: (Default) Uses OpenRouter API. Best for production.
- `cheap`: Uses a low-cost model via OpenRouter (e.g., GPT-4o-mini).
- `cli`: Uses locally authenticated CLI models.
- `gemini`: Specific CLI provider (Shortcut for mode=cli + provider=gemini).
- `codex`: Specific CLI provider (Shortcut for mode=cli + provider=codex).
- `stub`: Returns static placeholder JSON. Use for UI/Logic development without LLM costs.
- `mock`: Similar to stub, used in automated tests.
- `fallback`: Internal mode for automatic retry chain.

### Model Selection Policy:
- **Development/Test/CI:** Always use free models (with `:free` suffix) or `stub` mode. 
- **Production:** Use high-quality models (e.g., Claude 3.5 Sonnet) by setting `OPENROUTER_MODEL_*` variables in the production environment.
- **Default:** If no specific model is set, the system defaults to `meta-llama/llama-3.3-70b-instruct:free`.

### CLI provider selection (for local authenticated CLIs):

```
LLM_CLI_PROVIDER=codex
LLM_CLI_MODEL=gpt-5.2
LLM_CLI_REASONING=xhigh
LLM_CLI_CONCURRENCY=10
LLM_CLI_ARGS=--skip-git-repo-check
```

Recommended model policy by task:
- Architecture/design decisions: Codex `gpt-5.2` with `LLM_CLI_REASONING=xhigh`.
- Code writing/refactors: Gemini `gemini-3-pro-preview`.
- Logs/tests/quick fixes: Gemini `gemini-3-flash-preview`.

Gemini default model is `gemini-3-pro-preview` if `LLM_CLI_MODEL` is not set.
`LLM_CLI_REASONING` is used only by the Codex CLI.

Gemini CLI example:

```
LLM_CLI_PROVIDER=gemini
LLM_CLI_MODEL=gemini-3-pro-preview
LLM_CLI_CONCURRENCY=10
```

Gemini fast mode:

```
LLM_CLI_PROVIDER=gemini
LLM_CLI_MODEL=gemini-3-flash-preview
LLM_CLI_CONCURRENCY=10
```

To override per request:
```
"llm_mode": "cli"
```

Feed endpoint uses `FEED_LLM_MODE` if set, otherwise `DEFAULT_LLM_MODE`.

## Engine-First Policy (Facts Only)

We strictly follow the **"LLM Interprets, Engine Calculates"** rule.

### Core Principles
1.  **Never ask LLM to calculate.**
    *   Do not ask "Where is Mars?".
    *   Do not ask "Is there a square between Sun and Moon?".
2.  **Provide Facts.**
    *   The backend calculates all positions, aspects, ingresses, and lunations.
    *   These are passed to the prompt as a structured JSON in `facts` (facts_v1 schema) or specialized data (`month_forecast_data`).
3.  **LLM Responsibility.**
    *   The LLM must ONLY interpret the provided facts.
    *   The LLM must return the response as a **JSON array of blocks** (see `BLOCKS_SCHEMA.md`).

### Data Layers (facts_v1)

Context field `facts` contains:
- `v`: "facts_v1" (version)
- `pos`: List of planet positions `{"p": name, "s": sign, "deg": deg, "h": house, "r": is_retro}`.
- `houses`: List of house cusps `{"h": num, "s": sign, "deg": deg}`.
- `aspects`: List of major aspects `{"p1": p1, "t": type, "p2": p2, "o": orb}`.
- `balance`: Elemental and modality balances.

Example:
```json
{
  "v": "facts_v1",
  "pos": [{"p": "Sun", "s": "Aries", "deg": 10, "h": 1, "r": false}],
  "aspects": [{"p1": "Sun", "t": "trine", "p2": "Mars", "o": 2.5}]
}
```

### Validation
Responses are automatically validated for "Hallucination Control". If the LLM mentions a planet in a sign that contradicts `facts`, the section is rejected and retried.

## Referral Standard (MVP)

- `referral_code` is stored as `u_xxxxxx` (lowercase) in the database.
- Web links must use the stored `referral_code` as-is (no extra prefixes).
- Resolver accepts `u_`, `ref_`, and bare codes for backward compatibility.


## Playwright upkeep
- Запускайте E2E только через `./scripts/run_e2e.sh`, включая `--last-failed`: скрипт всегда использует `frontend_e2e` container и проверяет backend/frontend health перед стартом.
- Для стабильности Playwright используйте `data-testid` на критичных элементах UI: daily feed (`feed-page`, `moon-card`, `traffic-lights`, `daily-feed-debug`), read (`read-sticky-panel`, `read-overview-panel`), admin (`admin-dashboard-page`, `admin-reports-page`, `admin-reports-queue`).
- Общие моки держите консистентными через `frontend/e2e/utils.ts`: mock Telegram auth, personalized daily feed states, profile overrides.
- При появлении нового UI в daily/admin/report flows сначала добавляйте стабильный `data-testid`, затем обновляйте точечные E2E-спеки вместо расширения хрупких текстовых локаторов.

## Админский workflow natal_master

- Страница `frontend/app/admin/reports/[id]/page.tsx:1` собирает очередь natal_master, липкую панель действий, покомпонентную генерацию и экспорт Markdown/PDF.
- Первые три секции раскрываются сразу, `executive_summary` и `final_synthesis` вынесены в компактный верхний блок с подсветкой fallback-маркеров.
- Внизу страницы показан журнал запусков LLM с краткой телеметрией и ошибками.
