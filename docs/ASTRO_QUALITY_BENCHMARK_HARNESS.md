# Live Quality Benchmark Harness

Дата: 2026-03-19

Этот harness закрывает главную операционную ловушку из benchmark/rerun цикла: backend-контейнер может жить с `DEFAULT_LLM_MODE=stub`, а человек при этом думать, что только что мерил live `openrouter`.

Что теперь делает `scripts/live_quality_benchmark.py`:

- не дает запускать benchmark без явного `llm_mode` на кейс, через `--llm-mode` или через manifest
- по умолчанию отказывается от `stub`/`mock`/`local`/`fallback`, пока это не подтверждено флагом `--allow-stub-benchmark`
- перед стартом читает runtime env именно из live контейнера `astro-project-backend-1` и пишет в артефакт `DEFAULT_LLM_MODE` плюс `LLM_SMOKE`
- сохраняет `report_id`, `client_id`, длительность, marker summary по секциям и список реально сравненных секций
- пишет два артефакта в `tmp/quality_benchmark_runs/`: подробный `.json` и читаемый `.md`
- автоматически помечает `client_note` тегом `[benchmark:<run_id>:<case_id>]`, чтобы не путать benchmark reports с обычными прогонами

## Каноничные команды

Representative natal pack из rerun/follow-up docs:

```bash
python3 scripts/live_quality_benchmark.py \
  --manifest docs/benchmark_manifests/natal_rerun_2026-03-19.json \
  --llm-mode openrouter
```

Forecast spot-check pack c явным mode drift:

```bash
python3 scripts/live_quality_benchmark.py \
  --manifest docs/benchmark_manifests/forecast_spotcheck_2026-03-19.json
```

Запустить только часть manifest-а:

```bash
python3 scripts/live_quality_benchmark.py \
  --manifest docs/benchmark_manifests/forecast_spotcheck_2026-03-19.json \
  --case week_openrouter \
  --case month_openrouter
```

## Что смотреть в артефакте

- `metadata.backend_runtime.default_llm_mode`: с каким default реально живет контейнер
- `cases[].requested_llm_mode`: какой mode был принудительно отправлен в payload
- `cases[].report_id`: какие live reports легли в benchmark вывод
- `cases[].marker_summary`: не протекли ли template/repair/error markers
- `comparisons[].compared_sections`: какие секции реально попали в similarity, а не были “по умолчанию исключены”
- `comparisons[].excluded_sections`: чем именно был отрезан `input_frame` / `technical_appendix` и любые дополнительные exclusions

## Привязка к существующим документам

- `docs/ASTRO_QUALITY_BENCHMARK_2026-03-19.md`
- `docs/ASTRO_QUALITY_BENCHMARK_2026-03-19_NATAL_RERUN.md`
- `docs/ASTRO_QUALITY_BENCHMARK_2026-03-19_NATAL_EXEC_SUMMARY_FOLLOWUP.md`

Исторические выводы в этих документах остаются как есть. Новый harness просто переводит их representative packs из “ручного знания оператора” в явные manifests и auditable benchmark artifacts.
