# Astro Quality Benchmark

Дата: 2026-03-19

> Reproducibility note: этот historical pack теперь зафиксирован через `scripts/live_quality_benchmark.py` и manifests в `docs/benchmark_manifests/`. Для safe rerun с явным `llm_mode` и артефактами по `report_id`/`compared_sections` см. `docs/ASTRO_QUALITY_BENCHMARK_HARNESS.md`.

Короткий вывод: forecast slice уже выглядит как сильный автоматический продукт, но natal slice в текущем live runtime не проходит даже минимальный честный бар на claim "глубже большинства астрологов". Главная причина не в стиле как таковом, а в том, что значимая часть long-form natal в боевом режиме уходит в generic validation/template fallback, оставаясь при этом со статусом `completed`.

## Как смотрел

- Рубрика: `GRACE_SLICE_ASTRO_QUALITY_RUBRIC.md`
- Live runtime: `http://localhost:8000`, текущий backend/container, без mock/stub
- Daily: `GET /api/feed/today`
- Natal / Week / Month: `POST /api/workflows/report`
- Cases:
  - timed case A: `1976-02-14 05:30`, Khabarovsk, current Moscow
  - timed case B: `1988-09-04 22:15`, Novosibirsk, current Moscow
  - untimed natal edge case: `1985-11-03`, Saint Petersburg, no birth time
- Cheap spot-check: same case A for `natal_master`, `week_forecast`, `month_forecast`
- Heuristic baseline without internet:
  - archived local natal: `Svetlana_Natal_Report.md`
  - generic market-style baseline for forecast: sign/aspect-heavy report without per-user tactical layer

## Главное наблюдение

`natal_master` сейчас является bottleneck всего claim.

По двум timed live cases у main natal:

- `15/21` секций попали в generic template-ветку с маркерами `🧭 О чем этот блок`, `Настройка этого блока дает устойчивую опору`, `Сформулируйте 1-2 практичных шага`
- текст timed natal почти полностью совпал между двумя разными картами: similarity `1.0` при исключении `input_frame` и `technical_appendix`
- untimed natal деградирует аналогично
- это hard-gate failure по рубрике: секции, которые должны быть facts-first, не отыгрывают `insight_pack` / `cross_links` на пользовательском surface

Техническая зацепка в коде:

- `build_section_validation_fallback_content()` для non-forecast natal ведет в `build_section_template_content()` в `backend/app/services/report_workflow.py`
- generic template находится там же, включая строки `🧭 О чем этот блок...`
- user-visible chunk при этом остается `completed`, что маскирует проблему в обычном smoke-потоке

## Примерные оценки по рубрике

| Продукт | Оценка | Вердикт |
| --- | --- | --- |
| `natal_master` main | `19/50` | Ниже ship-level claim. Opening стал чище, но long-form почти развален template fallback'ом. |
| `natal_master` untimed | `17/50` | Аккуратная деградация по форме, но почти те же generic секции. |
| `daily` | `34/50` | Полезно и реально персонализировано, но редакторски шероховато. |
| `week_forecast` | `40/50` | Сильный навигатор недели. Практичен, факт-anchored, хорошо держит horizon. |
| `month_forecast` | `40/50` | Лучший текущий slice: хороший planning rhythm, понятный campaign arc, strong cheap robustness. |

Расшифровка:

- Natal main силен только в opening-слое: `executive_summary`, `synthesis`, частично `framework_elements_modes`.
- Daily выигрывает у типового "Луна в знаке + общий совет" за счет fast hits, traffic lights и конкретного tactical move.
- Week хорошо переводит данные в ритм недели, но повторяет одинаковые focus/risk формулы чаще, чем хотелось бы.
- Month уже ощущается как planning product, а не как mini-natal.

## Что уже сильно

- `week_forecast` и `month_forecast` реально опираются на факты, даты и pacing.
- Forecast cheap robustness очень хорошая:
  - `week` main vs cheap similarity: `0.965`
  - `month` main vs cheap similarity: `0.988`
- Read contract и mobile scan хорошие: блоки короткие, иерархия читается, первый экран обычно понятен.
- Daily personalization живая:
  - два пользователя получили разные `general_vibe`
  - разные `traffic_lights`
  - разные fast transit anchors

## Где продукт еще слаб

- Natal main не держит core claim вообще.
- Daily формально facts-first, но текст местами ломается редакторски:
  - awkward phrasing
  - `fallback_detail`/fact leakage прямо в пользовательскую фразу
  - по факту выходит 3 фразы вместо желаемых 2 коротких предложений
- Month и week пока местами слишком повторяют skeleton:
  - полезно, но местами слышно внутреннюю "матрицу"
  - personalization заметно сильнее в событиях, чем в narrative voice

## Сравнение с heuristic baseline

### Natal vs archived local astrologer-style baseline

С `Svetlana_Natal_Report.md` текущий live natal проигрывает по:

- глубине
- персонализации
- cross-linking
- ощущению цельного портрета

Текущий natal выигрывает только по:

- компактности
- mobile readability
- меньшей эзотерической перегрузке

Итог: старый/архивный стиль местами слишком рыночный и раздутый, но он хотя бы реально говорит "про эту карту". Текущий live natal main в середине и хвосте звучит как generic skeleton.

### Forecast vs typical market-style forecast

Week/month уже лучше типового "аспект дня -> общий совет":

- больше фактической опоры
- лучше fit по горизонту
- лучше practical utility
- лучше mobile contract

Но пока еще не на уровне "выше большинства" из рубрики, потому что voice и non-template factor не везде дотянуты.

## Единственный highest-ROI next step

Починить `natal_master` main-path так, чтобы секции `axes_truths` ... `time_cycles` перестали тихо падать в validation/template fallback и снова verbalize'или `insight_pack` / `cross_links` на user-visible surface.

Почему это самый выгодный следующий шаг:

- это самый большой разрыв между текущим claim и реальным output
- это флагманский продукт и главный premium anchor
- один фикс здесь поднимет сразу `Глубину`, `Персонализацию`, `Cross-linking`, `Не-шаблонность`, `Fit по горизонту`
- пока этот провал жив, формулировку "глубже большинства астрологов" использовать нельзя независимо от силы forecast slice

Практически это значит:

- сначала убрать silent success для generic validation fallback в natal QA
- потом восстановить содержательный output для mid/late natal sections
- только после этого повторять benchmark и думать о polishing daily voice

## Честный продуктовый вердикт на сегодня

Не "глубже большинства астрологов".

Честная формула на текущий момент:

"Сильный автоматический forecast-продукт с хорошим week/month слоем и заметно улучшенным daily, но natal flagship в live main runtime еще не дотягивает из-за template fallback в ключевых секциях."


## Daily Feed
- `GET /api/feed/today` supports two safe modes: anonymous general fallback and authenticated personalized v2.
- Prompt contract is pinned in `backend/app/services/feed_service.py` as registry entry `personalized_daily_v2`; it explicitly forbids invented aspects/events and keeps output at 2 short sentences.
- Internal debug: add `?debug=true` or header `X-Feed-Debug: 1` together with `X-Telegram-Auth`; response includes `meta.cache_scope`, personalization mode, fact lines, and fallback markers.
- Production frontend now sends debug headers only in mock mode; regular authenticated traffic keeps personalization without leaking debug payload by default.
- Example anon curl: `curl http://localhost:8000/api/feed/today`
- Example auth curl: `curl -H "X-Telegram-Auth: <token>" "http://localhost:8000/api/feed/today?debug=true"`
- Example auth shape excerpt: `{"moon_sign":"Рыбы","traffic_lights":{"health":"yellow","money":"green","love":"green"},"fast_hits":[{"summary":"Венера Соединение Солнце"}],"meta":{"cache_scope":"...","personalization_level":"personalized_v2"}}`
- Quick QA commands: `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_daily_feed_robustness.py tests/test_personalized_daily_service.py tests/verify_daily_feed.py`, `docker exec astro-project-backend-1 python3 scripts/pipeline.py`, `./scripts/run_e2e.sh e2e/core-ux.spec.ts`.
