# ############################################################################
# AI_HEADER: MODULE_SECTION_TEMPLATES
# ROLE: Provide canonical section templates by report type.
# DEPENDENCIES: backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [SECTION_TEMPLATES]
# ############################################################################
# START_MODULE_CONTRACT: M-SECTION-TEMPLATES
# ROLE: Define canonical SectionSpec builders and default template registries.
# API:
#   - get_default_sections(report_type: str, mode: str = "full") -> List[SectionSpec]
#   - build_week_sections() -> List[SectionSpec]
#   - build_month_sections() -> List[SectionSpec]
#   - build_year_sections() -> List[SectionSpec]
#   - build_natal_sections() -> List[SectionSpec]
#   - build_solar_sections() -> List[SectionSpec]
#   - build_synastry_sections() -> List[SectionSpec]
#   - build_horary_sections() -> List[SectionSpec]
#   - build_ten_year_sections() -> List[SectionSpec]
# guarantees:
#   - All canonical templates instantiate `SectionSpec` via keyword args only.
#   - Builders return detached list copies preserving canonical section order.
#   - Report type registry stays aligned with workflow canonical builder map.
# END_MODULE_CONTRACT: M-SECTION-TEMPLATES
# START_MODULE_MAP: M-SECTION-TEMPLATES
# purpose: Map canonical report types to deterministic section template builders.
# canonical_blocks:
#   - SECTION_TEMPLATES_COMMON: shared RU/style/JSON prompt contracts.
#   - NATAL_SECTION_LIBRARY: canonical natal_master sections.
#   - YEAR_SECTION_LIBRARY: canonical year_forecast sections.
#   - MONTH_SECTION_LIBRARY: canonical month_forecast sections.
#   - WEEK_SECTION_LIBRARY: canonical week_forecast sections.
#   - HORARY_SECTION_LIBRARY: canonical horary / horary_answer sections.
#   - TEN_YEAR_SECTION_LIBRARY: canonical ten_year_forecast sections.
#   - SOLAR_SECTION_LIBRARY: canonical solar_return sections.
#   - SYNASTRY_SECTION_LIBRARY: canonical synastry sections.
#   - REPORT_TEMPLATE_REGISTRY: report_type -> canonical section library.
# report_types:
#   - natal_master -> NATAL_SECTIONS_BUILDER
#   - week_forecast -> WEEK_SECTIONS_BUILDER
#   - month_forecast -> MONTH_SECTIONS_BUILDER
#   - year_forecast -> YEAR_SECTIONS_BUILDER
#   - ten_year_forecast -> TEN_YEAR_SECTIONS_BUILDER
#   - solar_return -> SOLAR_SECTIONS_BUILDER
#   - synastry -> SYNASTRY_SECTIONS_BUILDER
#   - horary -> HORARY_SECTIONS_BUILDER
#   - horary_answer -> HORARY_SECTIONS_BUILDER
#   - custom -> NATAL_SECTIONS_BUILDER
# owned_tests:
#   - tests/test_one_off_runtime_smoke.py
#   - tests/verify_history_feed.py
# adjacent_modules:
#   - backend/app/services/report_workflow.py
#   - backend/app/llm/orchestrator.py
# END_MODULE_MAP: M-SECTION-TEMPLATES

from typing import List

from ..llm.orchestrator import SectionSpec

# START_BLOCK: SECTION_TEMPLATES_COMMON
# --- COMMON INSTRUCTIONS ---
RU_LANG_INSTRUCTION = (
    "Ответь на русском языке. "
    "КРИТИЧЕСКИ ВАЖНО: Используй пол клиента из поля `client.gender`. "
    "Если пол женский — используй женские окончания (Ты способна, Ты пришла). "
    "Если пол мужской — используй мужские окончания (Ты способен, Ты пришел). "
    "Обращайся к клиенту СТРОГО на 'ТЫ'. "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать имя клиента. "
    "Для анализа используй данные из поля `facts` (структурированный JSON с позициями, домами и аспектами), "
    "а также `chart` (полная JSON структура). Опирайся на факты, не выдумывай положения планет. "
    "Не выполняй собственные расчеты: числа, проценты, сроки, положения и даты бери только из `facts`, `chart` или `*_forecast_data`. "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать английские слова, латиницу и неологизмы. "
    "Если слово на латинице неизбежно — переведи на русский. "
    "ЗАПРЕЩЕНО оставлять пустые маркеры (• • •). "
    "Пиши ясно, по делу, без «розовой воды» и эзотерики. "
    "Если используешь термин — коротко объясни простыми словами в скобках. "
    "Если блок технический — начни с 1-2 предложений, что это значит для человека без астрологии. "
    "Рекомендации: 2-4 коротких действия, без метафор и украшений. "
    "Проверь, что в текстовых полях нет латиницы и случайных символов."
)

STYLE_CONTRACT_SUMMARY_INSTRUCTION = (
    "Для summary-layer соблюдай STYLE_CONTRACT.md буквально: "
    "тон собранный, факт-first, без лозунгов, без мистического тумана и без универсальных мотивационных концовок. "
    "Каждый тезис должен опираться на конкретный anchor из карты, а не на абстрактный archetype."
)

JSON_FORMAT_INSTRUCTION = (
    "ФОРМАТ ОТВЕТА: СТРОГО JSON МАССИВ БЛОКОВ.\n"
    "Не возвращай Markdown текст. Возвращай ТОЛЬКО валидный JSON массив (Array).\n"
    "Типы блоков:\n"
    "- header {type='header', level=int, text=str}\n"
    "- paragraph {type='paragraph', text=str} (можно использовать **bold** внутри текста)\n"
    "- list {type='list', items=str[], ordered=bool}\n"
    "- table {type='table', columns=[{header:str, width:str}], rows=[[str]]}\n"
    "- key_value {type='key_value', items=[{key:str, value:str}]}\n"
    "- callout {type='callout', variant='info'|'warning'|'error'|'success'|'quote', title=str, content=str}\n"
    "- rating {type='rating', value=float, max=10, label=str}\n"
    "- traffic_lights {type='traffic_lights', items={health:'red'|'yellow'|'green', money:..., love:...}}\n"
    "- divider {type='divider'}"
)

NO_EXTRA_BLOCKS_INSTRUCTION = (
    "ЗАПРЕЩЕНО добавлять служебные хвостовые блоки и новые секции. "
    "Не пиши фразы вроде 'Ключевой фокус', 'Потенциал', 'Риск и зона внимания', "
    "'Ключевые факторы', 'Рекомендации' (если они не запрошены форматом секции). "
    "Выводи только то, что требуется форматом секции."
)

EMOJI_RESTRICTION = (
    "Эмодзи разрешены ТОЛЬКО из списков планет/знаков/стихий и ✅/❌ для вердикта. "
    "Не используй декоративные эмодзи."
)

COSMOGRAM_INSTRUCTION = (
    "Если в поле `client.birth_time_known` стоит `false`, значит время рождения НЕИЗВЕСТНО. "
    "В ЭТОМ СЛУЧАЕ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО упоминать любые дома, куспиды домов и точки ASC, MC, DSC, IC, Вертекс. "
    "Фокусируйся ТОЛЬКО на положениях планет в знаках и аспектах между ними (Космограмма)."
)

REPORT_JSON_COMMON = (
    f"{RU_LANG_INSTRUCTION} "
    f"{JSON_FORMAT_INSTRUCTION} "
    f"{NO_EXTRA_BLOCKS_INSTRUCTION} "
    f"{EMOJI_RESTRICTION} "
    f"{COSMOGRAM_INSTRUCTION}"
)

PLANET_EMOJI_GUIDE = "Используй только уместные астрологические символы планет (☉ ☽ ☿ ♀ ♂ ♃ ♄ ♅ ♆ ♇ ⚷ ⚸ ☊ ☋ ✴️)."
ZODIAC_EMOJI_GUIDE = "Используй символы знаков только если они уже присутствуют в данных карты."
ELEMENT_EMOJI_GUIDE = "Стихии можно маркировать как 🔥 Земля, 🌍 Земля, 🌬️ Воздух, 💧 Вода только если это улучшает читабельность."
NO_REDUNDANT_SECTION_HEADER = "Не повторяй заголовок секции внутри ответа."
PREMIUM_NATAL_NARRATIVE_CONTRACT = "Пиши как редактор смыслового профиля: собранно, точно, без пустой патетики."
CHEAP_FORECAST_VOICE_CONTRACT = "Тон прогноза — прикладной и жизненный: меньше эзотерики, больше практических шагов."
# END_BLOCK: SECTION_TEMPLATES_COMMON

# START_BLOCK: NATAL_SECTION_LIBRARY
"""Canonical natal section specs for the strict GRACE narrative profile."""
_NATAL_MASTER_SECTIONS = [
    SectionSpec(section_id="executive_summary", title="0. Executive Summary", prompt=(
        f"{REPORT_JSON_COMMON} {STYLE_CONTRACT_SUMMARY_INSTRUCTION} {NO_REDUNDANT_SECTION_HEADER} "
        "Собери краткое summary по already prepared anchors из `section_context.insight_pack`. Используй header, paragraph и list."
    )),
    SectionSpec(section_id="input_frame", title="1. Данные рождения", prompt="Это генерируется программно."),
    SectionSpec(section_id="synthesis", title="2. Синтез (метафора и ядро)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {PREMIUM_NATAL_NARRATIVE_CONTRACT} "
        "Опирайся на `section_context.insight_pack`; собирай связный синтез через callout и paragraph."
    )),
    SectionSpec(section_id="framework_elements_modes", title="3. Каркас (стихии и модальности)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {ELEMENT_EMOJI_GUIDE} "
        "Используй deterministic temperament pack из `section_context.insight_pack`."
    )),
    SectionSpec(section_id="axes_truths", title="4. Оси (две правды)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} Опиши главные оси через header и list."
    )),
    SectionSpec(section_id="aspects_beginner", title="5. Аспекты для новичка", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй только данные из `chart.aspects`; для каждого аспекта header и list."
    )),
    SectionSpec(section_id="configurations_geometry", title="6. Конфигурации (геометрия)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй `configuration_cards` и `absence_summary`."
    )),
    SectionSpec(section_id="dispositor_office", title="7. Диспозиторная логика", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Объясни иерархию через метафору офиса."
    )),
    SectionSpec(section_id="core_triad", title="8. Личное ядро (⬆️ ASC / ☀️ Солнце / 🌙 Луна)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} Три раздела: ASC, Солнце, Луна и интеграция."
    )),
    SectionSpec(section_id="mercury_mind", title="9. Мышление (☿ Меркурий)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} Опиши стиль мышления и когнитивные риски."
    )),
    SectionSpec(section_id="shadow_trauma", title="10. Тень и травма (⚷ Хирон / ⚸ Лилит)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} Два раздела: Хирон и Лилит."
    )),
    SectionSpec(section_id="nodes_growth", title="11. Узлы (☊/☋ вектор взросления)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} Раскрой ось роста через South/North node."
    )),
    SectionSpec(section_id="vertex_fate", title="12. Вертекс (✴️ сюжетные встречи)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Обязательно упомяни ✴️ Вертекс и deterministic pack."
    )),
    SectionSpec(section_id="balance_wheel_1_6", title="13. Колесо баланса (Дома 1-6)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй `house_pack` для домов 1-6."
    )),
    SectionSpec(section_id="balance_wheel_7_12", title="14. Колесо баланса (Дома 7-12)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй `house_pack` для домов 7-12."
    )),
    SectionSpec(section_id="money_realization", title="15. Деньги и реализация", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Опиши денежный паттерн, реализацию и ловушки."
    )),
    SectionSpec(section_id="love_intimacy", title="16. Любовь и близость", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Опиши сценарий близости и зрелый формат отношений."
    )),
    SectionSpec(section_id="final_synthesis", title="17. Финальная сборка", prompt=(
        f"{REPORT_JSON_COMMON} {STYLE_CONTRACT_SUMMARY_INSTRUCTION} Собери итоговый жизненный вектор через paragraph, list и callout."
    )),
]
# END_BLOCK: NATAL_SECTION_LIBRARY

# START_BLOCK: YEAR_FORECAST_SECTION_LIBRARY
"""Canonical year forecast section specs for annual planning outputs."""
_YEAR_FORECAST_SECTIONS = [
    SectionSpec(section_id="year_theme", title="Главная тема года", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй `year_forecast_data` для headline, main lesson и стратегического фокуса."
    )),
    SectionSpec(section_id="year_quarters", title="Квартальная динамика", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Разбей год на 4 квартала с header level 3 и практическими акцентами."
    )),
    SectionSpec(section_id="year_domains", title="Сферы года", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Оцени финансы, отношения, энергию и работу через list или key_value."
    )),
    SectionSpec(section_id="year_strategy", title="Стратегия года", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Дай конкретную стратегию года через callout и короткий list."
    )),
]
# END_BLOCK: YEAR_FORECAST_SECTION_LIBRARY

# START_BLOCK: MONTH_FORECAST_SECTION_LIBRARY
"""Canonical month forecast section specs for monthly operational forecasts."""
_MONTH_FORECAST_SECTIONS = [
    SectionSpec(section_id="month_theme", title="Тема месяца", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {CHEAP_FORECAST_VOICE_CONTRACT} Используй `month_forecast_data.summary` и `semantic_layer` для главной сцены месяца."
    )),
    SectionSpec(section_id="month_weeks", title="Недели месяца", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй `month_forecast_data.weeks` и `semantic_layer`; по неделе дай фокус, риск и зрелый ход."
    )),
    SectionSpec(section_id="month_summary", title="Итог месяца", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй `key_value` для сфер и `callout` для практического хода."
    )),
]
# END_BLOCK: MONTH_FORECAST_SECTION_LIBRARY

# START_BLOCK: WEEK_FORECAST_SECTION_LIBRARY
"""Canonical week forecast section specs for short-horizon weekly guidance."""
_WEEK_FORECAST_SECTIONS = [
    SectionSpec(section_id="week_strategy", title="Стратегия недели", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {CHEAP_FORECAST_VOICE_CONTRACT} "
        "Используй `week_forecast_data.summary`, `days` и `semantic_layer`; дай статус недели, главную тему, подневную стратегию и traffic_lights."
    )),
]
# END_BLOCK: WEEK_FORECAST_SECTION_LIBRARY

# START_BLOCK: HORARY_SECTION_LIBRARY
"""Canonical horary section specs for binary answer and evidentiary reasoning."""
HORARY_COMMON = (
    "Ты — жесткий эксперт-практик. ЗАПРЕЩЕНО использовать слова: 'благоприятный', 'энергетика', 'фон', 'потенциал', 'вселенная', 'вибрации'. "
    "Запрещена латиница и англицизмы. Разрешены только сокращения ASC/MC/DSC/IC и обозначения L1/L7/L9/L10. "
    "Хорар — это прогностика. Ответ должен быть бинарным: либо событие происходит, либо нет. "
    "КРИТИЧЕСКИ ВАЖНО: 'ДА' в ответе — это факт реализации вопроса. Если вопрос негативный, 'ДА' означает реализацию негативного события. "
    "Смотри на аспекты: L1 и Луна против L10, L9 или домов квестита. Если аспекта нет — ответ НЕТ. Если есть препятствие — ответ НЕТ. "
    "Пиши сухо, по делу, без морализаторства. Следуй только формату секции."
)

_HORARY_SECTIONS = [
    SectionSpec(section_id="horary_00_passport", title="0. Паспорт вопроса", prompt="Это генерируется программно."),
    SectionSpec(section_id="horary_00_technical", title="Данные карты", prompt="Это генерируется программно."),
    SectionSpec(section_id="horary_01_verdict", title="1. Ответ сразу", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} Дай итоговый вердикт на основе `chart.horary.aspects`; используй paragraph и callout."
    )),
    SectionSpec(section_id="horary_02_radicality", title="2. Пригодность карты", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} Используй `chart.horary.radicality` и list для флагов."
    )),
    SectionSpec(section_id="horary_03_significators", title="3. Сигнификаторы", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} Используй key_value для ролей."
    )),
    SectionSpec(section_id="horary_04_state", title="4. Состояние сторон", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} Используй table."
    )),
    SectionSpec(section_id="horary_05_mechanics", title="5. Механика исхода", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} Используй list."
    )),
    SectionSpec(section_id="horary_06_moon", title="6. Луна как сценарий", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} Используй list."
    )),
    SectionSpec(section_id="horary_07_timing", title="7. Тайминг", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} Используй paragraph."
    )),
    SectionSpec(section_id="horary_08_conditions", title="8. Условия успеха", prompt=(
        f"{REPORT_JSON_COMMON} {HORARY_COMMON} Используй list."
    )),
    SectionSpec(section_id="horary_09_risks", title="9. Риски и ограничения", prompt=(
        f"{REPORT_JSON_COMMON} {HORARY_COMMON} Используй list."
    )),
    SectionSpec(section_id="horary_10_alternatives", title="10. Альтернативы", prompt=(
        f"{REPORT_JSON_COMMON} {HORARY_COMMON} Используй list."
    )),
    SectionSpec(section_id="horary_11_summary", title="11. Итог", prompt=(
        f"{REPORT_JSON_COMMON} {HORARY_COMMON} Используй paragraph и callout."
    )),
]
# END_BLOCK: HORARY_SECTION_LIBRARY

# START_BLOCK: TEN_YEAR_SECTION_LIBRARY
"""Canonical ten-year forecast section specs for decade-level narrative planning."""
_TEN_YEAR_SECTIONS = [
    SectionSpec(section_id="decade_overview", title="Обзор 10 лет", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Дай общий обзор десятилетия по `decade_forecast_data`; используй paragraph и list."
    )),
    SectionSpec(section_id="decade_timeline", title="Хронология (10 лет)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Пройдись по годам, используя `decade_forecast_data`; применяй header level 4 для каждого года."
    )),
    SectionSpec(section_id="decade_storylines", title="Сюжетные линии", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Сгруппируй события из `decade_forecast_data` в 3 сюжетные линии."
    )),
]
# END_BLOCK: TEN_YEAR_SECTION_LIBRARY

# START_BLOCK: SOLAR_SECTION_LIBRARY
"""Canonical solar return section specs for solar-year planning."""
_SOLAR_RETURN_SECTIONS = [
    SectionSpec(section_id="solar_theme", title="Главная тема Соляра", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй paragraph и callout."
    )),
    SectionSpec(section_id="solar_money", title="Финансы (2/8 дома)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй paragraph и list."
    )),
    SectionSpec(section_id="solar_love", title="Отношения (5/7 дома)", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй paragraph и list."
    )),
    SectionSpec(section_id="solar_strategy", title="Стратегия года", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй callout."
    )),
]
# END_BLOCK: SOLAR_SECTION_LIBRARY

# START_BLOCK: SYNASTRY_SECTION_LIBRARY
"""Canonical synastry section specs for compatibility analysis."""
_SYNASTRY_SECTIONS = [
    SectionSpec(section_id="synastry_overview", title="Обзор совместимости", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй paragraph и callout для скора."
    )),
    SectionSpec(section_id="synastry_categories", title="Анализ по сферам", prompt=(
        f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй header level 3 для каждой сферы."
    )),
    SectionSpec(section_id="synastry_advice", title="Советы и решения", prompt=(
        f"{REPORT_JSON_COMMON} Используй list."
    )),
]
# END_BLOCK: SYNASTRY_SECTION_LIBRARY

# START_BLOCK: REPORT_TEMPLATE_REGISTRY
_REPORT_TEMPLATES = {
    "natal_master": _NATAL_MASTER_SECTIONS,
    "year_forecast": _YEAR_FORECAST_SECTIONS,
    "ten_year_forecast": _TEN_YEAR_SECTIONS,
    "month_forecast": _MONTH_FORECAST_SECTIONS,
    "week_forecast": _WEEK_FORECAST_SECTIONS,
    "horary": _HORARY_SECTIONS,
    "horary_answer": _HORARY_SECTIONS,
    "synastry": _SYNASTRY_SECTIONS,
    "solar_return": _SOLAR_RETURN_SECTIONS,
    "custom": _NATAL_MASTER_SECTIONS,
}
# END_BLOCK: REPORT_TEMPLATE_REGISTRY

# START_CONTRACT: NATAL_SECTIONS_BUILDER
# START_BLOCK: NATAL_SECTIONS_BUILDER
def build_natal_sections() -> List[SectionSpec]:
    """Return canonical natal report section specs in stable GRACE order."""
    return get_default_sections("natal_master")
# END_BLOCK: NATAL_SECTIONS_BUILDER
# END_CONTRACT: NATAL_SECTIONS_BUILDER

# START_CONTRACT: WEEK_SECTIONS_BUILDER
# START_BLOCK: WEEK_SECTIONS_BUILDER
def build_week_sections() -> List[SectionSpec]:
    """Return canonical weekly forecast section specs."""
    return get_default_sections("week_forecast")
# END_BLOCK: WEEK_SECTIONS_BUILDER
# END_CONTRACT: WEEK_SECTIONS_BUILDER

# START_CONTRACT: MONTH_SECTIONS_BUILDER
# START_BLOCK: MONTH_SECTIONS_BUILDER
def build_month_sections() -> List[SectionSpec]:
    """Return canonical monthly forecast section specs."""
    return get_default_sections("month_forecast")
# END_BLOCK: MONTH_SECTIONS_BUILDER
# END_CONTRACT: MONTH_SECTIONS_BUILDER

# START_CONTRACT: YEAR_SECTIONS_BUILDER
# START_BLOCK: YEAR_SECTIONS_BUILDER
def build_year_sections() -> List[SectionSpec]:
    """Return canonical yearly forecast section specs."""
    return get_default_sections("year_forecast")
# END_BLOCK: YEAR_SECTIONS_BUILDER
# END_CONTRACT: YEAR_SECTIONS_BUILDER

# START_CONTRACT: TEN_YEAR_SECTIONS_BUILDER
# START_BLOCK: TEN_YEAR_SECTIONS_BUILDER
def build_ten_year_sections() -> List[SectionSpec]:
    """Return canonical decade forecast section specs."""
    return get_default_sections("ten_year_forecast")
# END_BLOCK: TEN_YEAR_SECTIONS_BUILDER
# END_CONTRACT: TEN_YEAR_SECTIONS_BUILDER

# START_CONTRACT: SOLAR_SECTIONS_BUILDER
# START_BLOCK: SOLAR_SECTIONS_BUILDER
def build_solar_sections() -> List[SectionSpec]:
    """Return canonical solar return section specs."""
    return get_default_sections("solar_return")
# END_BLOCK: SOLAR_SECTIONS_BUILDER
# END_CONTRACT: SOLAR_SECTIONS_BUILDER

# START_CONTRACT: SYNASTRY_SECTIONS_BUILDER
# START_BLOCK: SYNASTRY_SECTIONS_BUILDER
def build_synastry_sections() -> List[SectionSpec]:
    """Return canonical synastry section specs."""
    return get_default_sections("synastry")
# END_BLOCK: SYNASTRY_SECTIONS_BUILDER
# END_CONTRACT: SYNASTRY_SECTIONS_BUILDER

# START_CONTRACT: HORARY_SECTIONS_BUILDER
# START_BLOCK: HORARY_SECTIONS_BUILDER
def build_horary_sections() -> List[SectionSpec]:
    """Return canonical horary section specs."""
    return get_default_sections("horary")
# END_BLOCK: HORARY_SECTIONS_BUILDER
# END_CONTRACT: HORARY_SECTIONS_BUILDER

# START_CONTRACT: DEFAULT_SECTION_RESOLUTION
# START_BLOCK: DEFAULT_SECTION_RESOLUTION
def get_default_sections(report_type: str, mode: str = "full") -> List[SectionSpec]:
    """Return detached default sections for a report type with short natal fallback rules."""
    sections = [
        SectionSpec(section_id=section.section_id, title=section.title, prompt=section.prompt)
        for section in _REPORT_TEMPLATES.get(report_type, _NATAL_MASTER_SECTIONS)
    ]
    if mode == "short" and report_type == "natal_master":
        essential = {
            "executive_summary",
            "input_frame",
            "synthesis",
            "core_triad",
            "money_realization",
            "love_intimacy",
            "final_synthesis",
        }
        sections = [section for section in sections if section.section_id in essential]
    return sections
# END_BLOCK: DEFAULT_SECTION_RESOLUTION
# END_CONTRACT: DEFAULT_SECTION_RESOLUTION
