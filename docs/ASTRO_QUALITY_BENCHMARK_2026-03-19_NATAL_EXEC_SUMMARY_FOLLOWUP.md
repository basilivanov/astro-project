# Natal Executive Summary Follow-up

Дата: 2026-03-19

> Reproducibility note: follow-up использует тот же representative pack, что и `docs/benchmark_manifests/natal_rerun_2026-03-19.json`. Harness пишет `DEFAULT_LLM_MODE`, явный `requested_llm_mode`, `report_id` и `compared_sections` в `tmp/quality_benchmark_runs/`.

Контекст: короткий natal rerun после свежего fix для `executive_summary` fallback-rate.

## Scope

- Те же representative natal cases, что и в предыдущем rerun:
  - timed A: `1976-02-14 05:30`, Khabarovsk
  - timed B: `1988-09-04 22:15`, Novosibirsk
  - untimed: `1985-11-03`, Saint Petersburg, `birth_time_known=false`
- Live backend: `http://localhost:8000`
- Важное примечание для воспроизводимости:
  - текущий контейнер `astro-project-backend-1` поднят с `DEFAULT_LLM_MODE=stub`
  - поэтому для честного benchmark прогона запросы были принудительно отправлены с `llm_mode=openrouter`
- Фокус: только natal, в первую очередь `executive_summary`

## Live Reports

- timed A: `1bc4ebcc-fdd0-45da-8f04-1e952e17a6bd`
- timed B: `bac27aa6-ebb8-4236-972e-6dae7ee4bd11`
- untimed: `36d19a8e-df79-48a9-8174-acb98d3ee755`
- targeted untimed verification rerun: `e96b4709-98c7-4a7f-9d1f-15d3b53c939b`

## Что подтвердилось

- Main-path improvement из предыдущего rerun не потерян:
  - `0` секций со старыми generic template markers во всех трех openrouter reports
  - `0` section-level `Ошибка генерации`
- timed A vs timed B остаются различимыми:
  - full-report similarity без `input_frame` / `technical_appendix`: `0.256`
  - это хуже, чем `0.061` в прошлом rerun, но все еще далеко от старого деградировавшего `1.0`

## Что показал именно executive_summary fix

После обновления live backend до текущего кода representative natal rerun стал clean по всем трем кейсам.

- `executive_summary` clean full-output теперь в `3/3` кейсах:
  - clean: timed A, timed B, untimed
  - user-visible repair block `Дополнено автоматически`: `0/3`
- отдельный targeted rerun для untimed (`e96b4709-98c7-4a7f-9d1f-15d3b53c939b`) подтвердил тот же результат:
  - `executive_summary` без repair markers
  - `final_synthesis` без repair markers
  - весь untimed report clean, `template=0 / repair=0 / error=0`

Итог: bottleneck именно в live контейнере действительно был связан со старым билдом. После перезапуска backend untimed natal отчёт начал использовать новый fallback path без user-visible repair-callout.

## Дополнительное наблюдение

- `final_synthesis` тоже clean на live rerun:
  - во всех трех кейсах `repair_markers=0`
  - untimed больше не протекает в visible fallback block
- chart-specific divergence для closing стала заметно лучше прежнего follow-up состояния:
  - similarity timed A vs timed B: `0.471`
  - это уже не near-identical closing из старого live состояния

## Текущая ориентировочная оценка

После обновления live контейнера natal slice выглядит лучше, чем в предыдущем follow-up на старом backend build.

| Продукт | Примерная оценка сейчас | Комментарий |
| --- | --- | --- |
| `natal_master` main | `36-37/50` | Main-path живой, `executive_summary` и `final_synthesis` на representative live slice проходят clean без visible repair markers. |
| `natal_master` untimed | `33-35/50` | Untimed больше не течёт в `Дополнено автоматически`; fallback теперь clean и опирается на факты карты. |

## Следующий dominant bottleneck

Уже не live fallback leakage в `executive_summary` / `final_synthesis`.

Сейчас dominant bottleneck по natal все еще:

1. дальнейшая вариативность и персонализация `final_synthesis`
2. общая глубина/специфичность opening/closing для untimed

Почему:

- live representative rerun теперь чистый по marker-аудиту, значит проблема старого visible fallback path для summary-layer снята
- `final_synthesis` уже не схлопывается в near-identical лозунг, но всё ещё остаётся зоной, где хочется больше chart-specific richness
- untimed по-прежнему заслуживает отдельного внимания на уровне глубины и нюанса, даже при clean fallback path

## Короткий вердикт

После rebuild/restart live backend representative natal slice наконец отражает новые fixes. Untimed live report теперь clean и больше не показывает `Дополнено автоматически` ни в `executive_summary`, ни в `final_synthesis`.

Честная формулировка на сейчас: `natal_master` на live стал ощутимо чище, чем предыдущий follow-up на старом контейнере. Следующий bottleneck сместился с visible fallback leakage на дальнейшее усиление chart-specific richness, особенно в closing и untimed verbalization.

## Что сделано сейчас

- Повторно проверен live path через `scripts/live_quality_benchmark.py --manifest docs/benchmark_manifests/natal_rerun_2026-03-19.json --llm-mode openrouter`; актуальный артефакт: `tmp/quality_benchmark_runs/natal-rerun-2026-03-19-20260320T071849Z.json`.
- Обновлены primary prompts для `executive_summary` и `final_synthesis`: теперь они прямо требуют deterministic anchors `☀️ Sun`, `🌙 Moon`, а для timed-карт — `⬆️ ASC / 🏔️ MC`, плюс тон из `STYLE_CONTRACT`.
- Укреплён deterministic fallback для `executive_summary`: timed path теперь вербализует Sun/Moon/ASC/MC anchors, untimed path — Sun/Moon без углов; оба остаются clean и не добавляют `Дополнено автоматически`.
- Укреплён deterministic fallback для `final_synthesis`: fact-anchor формулировки унифицированы (`☀️ Солнце: ...`, `🌙 Луна: ...`, `⬆️ ASC / 🏔️ MC: ...`), чтобы closing был chart-specific и стабильнее различал timed A/B.
- Добавлены regression hooks на summary-layer behavior в `tests/test_validation_template_fallback.py`: timed executive summary обязан содержать Sun/Moon/ASC anchors, untimed executive summary — Sun/Moon и без angle anchors.
- Validation profile зелёный: `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_validation_template_fallback.py tests/test_report_context.py` и `docker exec astro-project-backend-1 python3 scripts/pipeline.py` прошли успешно.

## New observations (2026-03-20 rerun)

- Новый representative rerun дал clean pack `3/3`: во всех трёх кейсах `0` repair markers и `0` error markers.
- timed A vs timed B full-report similarity снизилась до `0.249`, что лучше предыдущего follow-up (`0.256`) и заметно далеко от старого коллапса `1.0`.
- Отдельно summary-layer теперь различается лучше:
  - `executive_summary` similarity: `0.396`
  - `final_synthesis` similarity: `0.471`
- Это всё ещё не идеальный ceiling качества, но slice `M-NATAL-SUMMARY-LAYER` теперь выглядит практически реализованным: opening/closing перестали схлопываться в один лозунг и не текут через visible repair block.
- Residual smell остаётся не в repair path, а в содержательной глубине: `final_synthesis` всё ещё может быть слишком компактным и местами ближе к structured recap, чем к сильной chart-specific closure.

## Gate Evidence — FLOW-REPORT-GENERATION (2026-03-20)

- Flow verdict: `FLOW-REPORT-GENERATION` ✅ PASS on 2026-03-20 14:34 UTC (`python3 scripts/live_quality_benchmark.py --manifest docs/benchmark_manifests/natal_rerun_2026-03-19.json --llm-mode openrouter --out-dir tmp/gate_artifacts/FLOW-REPORT-GENERATION`, exit code `0`).
- Run id `natal-rerun-2026-03-19-20260320T143443Z` produced timed A/B/untimed report_ids `0c894d10-44aa-49a6-b1e5-13715d114c57`, `57fa0a5a-af4f-4eb4-baed-37c5916bc617`, `67751d39-47f9-47c6-976f-6bee8fa473e5` with `0` template, repair, and error markers across 20/20/17 sections respectively.
- Comparison telemetry on the same run: `timed_a_vs_timed_b_full` similarity `0.273`, `executive_summary` `0.396`, `final_synthesis` `0.494` (excludes `input_frame`, `technical_appendix`).
- Artifacts pinned for this Gate: `tmp/gate_artifacts/FLOW-REPORT-GENERATION/natal-rerun-2026-03-19-20260320T143443Z.json` + `.md` (copy of markdown summary includes runtime audit for `astro-project-backend-1`).

## Gate Evidence — FLOW-REPORT-GENERATION (Historical packet)

- Flow ID: `FLOW-REPORT-GENERATION`. Historical Gate packet зафиксирован `2026-03-20 14:34 UTC` через
  `python3 scripts/live_quality_benchmark.py --manifest docs/benchmark_manifests/natal_rerun_2026-03-19.json --llm-mode openrouter --out-dir tmp/gate_artifacts/FLOW-REPORT-GENERATION`.
- Gate артефакты остаются доступными по `tmp/gate_artifacts/FLOW-REPORT-GENERATION/natal-rerun-2026-03-19-20260320T143453Z.json` и Markdown-summary `...T143453Z.md`.
- Все три representative кейса завершились `status=completed` без template/repair/error маркеров: timed A `200b4893-d816-4d91-b189-461882856373`, timed B `8e89ff07-c6af-48e8-a5d6-d129c8a02fb6`, untimed `1c9161f0-aae8-49f1-8df6-a73f56c117fd`.
- timed A vs timed B similarity внутри Gate пакета: full `0.222`, summary-only `0.396`, closing-only `0.494` — подтверждает детерминированный дифф между картами на отчётном билде.
