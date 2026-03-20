# Natal Benchmark Rerun

Дата: 2026-03-19

> Reproducibility note: representative natal pack этого rerun теперь вынесен в `docs/benchmark_manifests/natal_rerun_2026-03-19.json`. Каноничный safe rerun: `python3 scripts/live_quality_benchmark.py --manifest docs/benchmark_manifests/natal_rerun_2026-03-19.json --llm-mode openrouter`.

Контекст: повторный live-check `natal_master` после runtime-фиксов для `balance_wheel` validator misses и `insight_pack` validation fallback formatting.

## Scope

- Рубрика: `GRACE_SLICE_ASTRO_QUALITY_RUBRIC.md`
- Режим: live `http://localhost:8000`, `DEFAULT_LLM_MODE=openrouter`
- Фокус: только natal
- Кейсы:
  - timed A: `1976-02-14 05:30`, Khabarovsk
  - timed B: `1988-09-04 22:15`, Novosibirsk
  - untimed: `1985-11-03`, Saint Petersburg, `birth_time_known=false`

## Live Reports

- timed A: `17da3edc-45d3-4bb3-9d13-3f5266f58fb2`
- timed B: `2ddda3db-b0c0-44df-a8a3-0f30ac4e9f66`
- untimed: `be738734-b337-4589-945c-8ca915932532`

## Что изменилось относительно benchmark 2026-03-19

Сильное улучшение реально есть.

Что было раньше:

- по timed cases `15/21` natal sections уходили в generic template fallback
- timed A vs timed B давали почти одинаковый текст (`similarity 1.0` без `input_frame` / `technical_appendix`)
- untimed деградировал почти тем же способом

Что в rerun сейчас:

- `0` chunk-level `error_message` во всех трех live reports
- `0` секций со старыми generic template markers:
  - `🧭 О чем этот блок`
  - `Настройка этого блока дает устойчивую опору`
  - `Сформулируйте 1-2 практичных шага`
- timed A vs timed B similarity упала до `0.061` без `input_frame` / `technical_appendix`
- почти все mid/late natal sections снова реально различаются между картами

Итог: основной main-path bottleneck из предыдущего документа закрыт materially, а не косметически.

## Что все еще видно в live output

- `executive_summary` у `timed A` и `untimed` показывает user-visible repair block `Дополнено автоматически`
- `final_synthesis` почти статичен между timed A и timed B:
  - section similarity `0.986`
  - у обеих карт один и тот же девиз уровня `делай глубже и конкретнее`
- closing voice местами грамматически сырой:
  - `Проверь/Проверяй интуицию фактами`
  - `переводить сложность`
- untimed теперь не разваливается, но все еще звучит слабее timed:
  - есть sections без прежнего template fallback
  - но часть phrasing остается полу-заготовочной и хуже держит цельный портрет

## Краткая оценка по рубрике

Это не blind benchmark и не полный 8-case pack, поэтому оценки ниже только ориентировочные.

| Продукт | Примерная оценка | Комментарий |
| --- | --- | --- |
| `natal_master` main | `35/50` | Уже не проваленный flagship: есть реальная персонализация, facts-first и рабочий mid-report. До claim-level еще не хватает сильной summary/compression layer и более человеческой финальной сборки. |
| `natal_master` untimed | `30/50` | Больше не ломается как generic skeleton, но все еще заметно слабее timed: opening/closing хуже и ощущение цельного портрета ниже. |

Сравнение с прошлым benchmark:

- main: было около `19/50` -> сейчас около `35/50`
- untimed: было около `17/50` -> сейчас около `30/50`

## Следующий highest-ROI bottleneck

Не `axes_truths` / `balance_wheel` fallback: это уже не главная проблема.

Следующий bottleneck сейчас: summary-compression layer, в первую очередь `final_synthesis`, а затем `executive_summary`.

Почему именно это:

- именно здесь еще остается самый явный template smell после починки main-path
- `final_synthesis` почти одинаков между разными картами и не дает earned ending
- `executive_summary` в двух из трех кейсов протекает user-visible repair blocks `Дополнено автоматически`
- этот слой напрямую бьет по `Narrative quality`, `Не-шаблонность`, `Cross-linking`, `Mobile readability`

Практически это значит:

- сначала убрать user-visible validator repair leakage из `executive_summary`
- затем сделать `final_synthesis` реально chart-specific, а не fallback-branch с почти одинаковым motto/advice

## Честный вердикт

Natal materially improved.

После `codex-natal-mainpath-fix` `natal_master` больше не выглядит сломанным template product. Но до формулировок уровня `выше большинства астрологов` еще рано: следующий узкий и самый выгодный фронт работы сейчас не runtime fallback, а слабая summary/compression layer, особенно `final_synthesis`.
