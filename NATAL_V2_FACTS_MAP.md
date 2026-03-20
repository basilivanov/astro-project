# Natal V2 Facts-First Map

## Goal

Перевести `natal_master` на схему, где:

- движок и код считают астрологические данные и смысловые связки;
- LLM только вербализует и упаковывает выводы;
- дешевые модели не принимают на себя ключевую аналитическую нагрузку.

## Current State

Сейчас пайплайн уже частично facts-first:

- базовая карта, дома, аспекты, паттерны и баланс считаются детерминированно;
- `facts_v1` и `section_context` уже режут общий контекст по секциям;
- LLM-validators проверяют в основном формат, обязательные токены и минимальную полноту.

Слабое место: для многих секций код пока отдает только сырье и релевантный срез, а смысловая сборка остается на модели.

## Section Map

### Group 1. High-Value Synthesis

#### `executive_summary` / `Главное`

- Code now:
  - основные позиции: `Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, `Jupiter`, `Saturn`, `ASC`, `MC`, `North Node`, `Chiron`
  - дома `1,2,5,6,7,8,10`
  - tight аспекты и баланс
  - паттерны, если есть
- LLM still does:
  - выбор суперсил
  - выбор рисков
  - ключ к отношениям
  - ключ к деньгам
  - главный фокус развития
- Move to code next:
  - `strengths_score`
  - `risk_score`
  - `relationship_theme`
  - `money_theme`
  - `development_focus`
- Priority: `P0`

#### `synthesis` / `Синтез`

- Code now:
  - ядро через `Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn/ASC/MC`
  - осевые дома `1/4/7/10`
  - tight аспекты, баланс, паттерны
- LLM still does:
  - центральный образ карты
  - главный конфликт
  - главный тезис
- Move to code next:
  - `identity_vector`
  - `core_conflict`
  - `dominant_drives`
  - `map_metaphor_seed`
- Priority: `P0`

#### `final_synthesis` / `Финальная сборка`

- Code now:
  - широкий финальный срез по ключевым планетам, домам, паттернам и балансу
- LLM still does:
  - финальный девиз
  - главный совет
  - общую сборку всей карты
- Move to code next:
  - `final_motto_seed`
  - `one_sentence_advice`
  - `top_conflict_vs_top_resource`
- Priority: `P0`

### Group 2. Money / Love / Life Application

#### `money_realization`

- Code now:
  - дома `2/6/10`
  - `Jupiter`, `Saturn`, `Venus`, `Mars`, `Sun`, `ASC`, `MC`
  - релевантные аспекты
- LLM still does:
  - финансовый сценарий
  - стиль реализации
  - узкое место в работе и деньгах
- Move to code next:
  - `career_vector`
  - `money_pattern`
  - `work_risk_flags`
  - `realization_mode`
- Priority: `P0`

#### `love_intimacy`

- Code now:
  - `Venus`, `Mars`, `Moon`, `Sun`, `Saturn`
  - дома `5/7/8`
  - релевантные аспекты
- LLM still does:
  - стиль любви
  - интимный паттерн
  - страхи/зажимы в близости
- Move to code next:
  - `attachment_style`
  - `intimacy_risk_flags`
  - `partnership_needs`
  - `conflict_style`
- Priority: `P0`

#### `time_cycles`

- Code now:
  - `Sun`, `Moon`, `Saturn`, `Jupiter`, `North Node`, `ASC`, `MC`
  - дома `1/10`
  - релевантные аспекты
- LLM still does:
  - вывод о жизненном периоде
  - текст о циклах взросления
- Move to code next:
  - `maturity_cycle_summary`
  - `saturn_jupiter_phase`
  - `growth_tension`
- Priority: `P1`

### Group 3. Structural Sections

#### `framework_elements_modes`

- Code now:
  - баланс стихий и модальностей уже считается
- LLM still does:
  - интерпретацию доминанты/дефицита
- Move to code next:
  - `temperament_summary`
  - `dominant_element_meaning`
  - `deficit_compensation`
- Priority: `P1`

#### `axes_truths`

- Code now:
  - оси `ASC/DSC`, `IC/MC`
  - позиции и дома по осевому каркасу
- LLM still does:
  - "твоя правда / правда партнера / задача"
- Move to code next:
  - `axis_polarities`
  - `axis_tasks`
- Priority: `P1`

#### `balance_wheel_1_6`, `balance_wheel_7_12`

- Code now:
  - дома и house context
  - релевантные планеты и аспекты
- LLM still does:
  - плюсы/минусы/триггеры/вектор зрелости по каждому дому
- Move to code next:
  - `house_themes`
  - `house_risk_flags`
  - `house_growth_actions`
- Priority: `P1`

### Group 4. Mostly Deterministic, Need Better Packaging

#### `aspects_beginner`

- Code now:
  - tight аспекты уже считаются и режутся
- LLM still does:
  - бытовую интерпретацию аспекта
- Move to code next:
  - `aspect_templates`
  - `aspect_keywords`
- Priority: `P1`

#### `configurations_geometry`

- Code now:
  - паттерны и фигуры уже считаются
- LLM still does:
  - "дар / риск / ключ" по фигуре
- Move to code next:
  - `pattern_interpretation_map`
- Priority: `P1`

#### `core_triad`

- Code now:
  - `ASC`, `Sun`, `Moon`, `Mercury`
  - аспекты по триаде
- LLM still does:
  - тезис по каждому элементу триады
  - финальную сборку ядра
- Move to code next:
  - `asc_mask`
  - `solar_drive`
  - `lunar_need`
  - `triad_conflict`
- Priority: `P1`

#### `mercury_mind`

- Code now:
  - `Mercury`, `Moon`, `Saturn`, `Uranus`
  - аспекты по мышлению
- LLM still does:
  - стиль мышления
  - ловушки мышления
- Move to code next:
  - `thinking_style`
  - `processing_mode`
  - `cognitive_risks`
- Priority: `P1`

#### `shadow_trauma`

- Code now:
  - `Chiron`, `Lilith`, `Moon`, `Saturn`, `Pluto`
- LLM still does:
  - сборку травматического паттерна
  - язык тени и компенсации
- Move to code next:
  - `shadow_flags`
  - `pain_points`
  - `compensation_modes`
- Priority: `P1`

#### `nodes_growth`

- Code now:
  - `North Node`, `South Node`, `Sun`, `Moon`, `Saturn`
- LLM still does:
  - narrative про прошлый и новый сценарий
- Move to code next:
  - `south_node_habit`
  - `north_node_direction`
  - `growth_task`
- Priority: `P1`

#### `vertex_fate`

- Code now:
  - `Vertex`, `Venus`, `Mars`, `Moon`, `DSC`
  - дома `5/7/8`
- LLM still does:
  - сюжетную интерпретацию встреч
- Move to code next:
  - `fated_meeting_pattern`
  - `relationship_trigger_type`
- Priority: `P2`

### Group 5. Lower Refactor Priority

#### `dispositor_office`

- Code now:
  - уже есть сильный prompt и отдельные проверки на "офис/босс/конверт"
  - данные по ключевым планетам и аспектам отдаются
- LLM still does:
  - собственно офисную метафору
- Move to code next:
  - `dispositor_graph`
  - `command_chain`
  - `boss_planet`
- Priority: `P2`

#### `stars_transuranus`

- Code now:
  - `Uranus`, `Neptune`, `Pluto`, `Sun`, `Moon`, `Saturn`
- LLM still does:
  - философскую интерпретацию "высших смыслов"
- Move to code next:
  - `transpersonal_themes`
- Priority: `P2`

#### `input_frame`, `technical_appendix`

- Already deterministic.
- Priority: `done`

## Highest-Value Refactor Tasks

### 1. Add `insight_pack_v1`

Собрать в коде канонический слой между `facts_v1` и LLM:

- `strengths`
- `risks`
- `identity_vector`
- `money_vector`
- `love_vector`
- `growth_vector`
- `final_motto_seed`

### 2. Add section-level DTOs

Для P0/P1 секций завести отдельные payload-структуры:

- `ExecutiveSummaryPack`
- `SynthesisPack`
- `MoneyPack`
- `LovePack`
- `FinalSynthesisPack`

### 3. Move cross-links to code

Не давать модели самой угадывать связи:

- ресурс vs риск
- отношения vs границы
- деньги vs реализация
- Солнце/Луна/ASC conflict

### 4. Strengthen validators from shape-check to evidence-check

Текущие валидаторы в основном следят за словами и длиной.
Следующий шаг:

- проверка, что финальный вывод использует реальные anchors из `insight_pack`
- проверка, что money/love/synthesis не выходят за рамки supplied facts

### 5. Keep fallback deterministic

Для P0 секций нужен не общий fallback-текст, а section-specific deterministic renderer.

## Recommended Implementation Order

1. `executive_summary`
2. `synthesis`
3. `money_realization`
4. `love_intimacy`
5. `final_synthesis`
6. `core_triad`
7. `framework_elements_modes`
8. `balance_wheel_*`

## Key Principle

`facts_v1` и `section_context` уже есть, но это еще не конечная цель.

Следующий этап:

- не просто "порезать контекст",
- а заранее посчитать "что это значит",
- и уже этот смысл отдавать модели для вербализации.
