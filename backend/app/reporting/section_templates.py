# ############################################################################
# AI_HEADER: MODULE_SECTION_TEMPLATES
# ROLE: Provide default section templates by report type.
# DEPENDENCIES: backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [SECTION_TEMPLATES]
############################################################################

from typing import List

from ..llm.orchestrator import SectionSpec

# #START_BLOCK_SECTION_TEMPLATES
# --- COMMON INSTRUCTIONS ---
# All prompts now include explicit language instruction.
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
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать английские слова, латиницу и неологизмы (overthinking, overtdumping, rigid, soft skills). "
    "Если слово на латинице неизбежно — переведи на русский. "
    "ЗАПРЕЩЕНО оставлять пустые маркеры (• • •). "
    "Пиши ясно, по делу, без «розовой воды» и эзотерики. "
    "Если используешь термин — коротко объясни простыми словами в скобках. "
    "Если блок технический — начни с 1-2 предложений, что это значит для человека без астрологии. "
    "Рекомендации: 2-4 коротких действия, без метафор и украшений. "
    "Проверь, что в текстовых полях нет латиницы и случайных символов."
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
    "- divider {type='divider'}\n"
    "Пример: [{\"type\": \"header\", \"level\": 2, \"text\": \"Заголовок\"}, {\"type\": \"paragraph\", \"text\": \"Текст\"}]"
)

NO_EXTRA_BLOCKS_INSTRUCTION = (
    "ЗАПРЕЩЕНО добавлять служебные хвостовые блоки и новые секции. "
    "Не пиши фразы вроде 'Ключевой фокус', 'Потенциал', 'Риск и зона внимания', "
    "'Ключевые факторы', 'Рекомендации' (если они не запрошены форматом секции). "
    "Выводи только то, что требуется форматом секции."
)

EMOJI_RESTRICTION = (
    "Эмодзи разрешены ТОЛЬКО из списков планет/знаков/стихий и ✅/❌ для вердикта. "
    "Не используй декоративные эмодзи (🚨, 🔍, 💡 и др.)."
)

COSMOGRAM_INSTRUCTION = (
    "Если в поле `client.birth_time_known` стоит `false`, значит время рождения НЕИЗВЕСТНО. "
    "В ЭТОМ СЛУЧАЕ КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО упоминать любые дома (1-й дом, 7-й дом и т.д.), "
    "куспиды домов и точки ASC, MC, DSC, IC, Вертекс. "
    "Фокусируйся ТОЛЬКО на положениях планет в знаках и аспектах между ними (Космограмма)."
)

REPORT_JSON_COMMON = (
    f"{RU_LANG_INSTRUCTION} "
    f"{JSON_FORMAT_INSTRUCTION} "
    f"{NO_EXTRA_BLOCKS_INSTRUCTION} "
    f"{EMOJI_RESTRICTION} "
    f"{COSMOGRAM_INSTRUCTION} "
    "Не добавляй общие вступления. Фокусируйся на анализе данных. "
    "Используй блоки `header` для подзаголовков, `paragraph` для текста, `list` для списков, `table` для таблиц, `callout` для акцентов."
)

PLANET_EMOJI_GUIDE = (
    "Обязательно ставь эмодзи у каждой планеты при упоминании: "
    "☀️ Солнце, 🌙 Луна, ☿ Меркурий, ♀️ Венера, ♂️ Марс, "
    "♃ Юпитер, ♄ Сатурн, ♅ Уран, ♆ Нептун, ♇ Плутон, "
    "⚷ Хирон, ⚸ Лилит, 🌟 Селена, ☊ Северный узел, ☋ Южный узел. "
    "Для осей используй: ⬆️ ASC, ⬇️ DSC, 🏠 IC, 🏔️ MC, ✴️ Вертекс."
)

ZODIAC_EMOJI_GUIDE = (
    "Всегда используй эмодзи для знаков Зодиака: "
    "♈ Овен, ♉ Телец, ♊ Близнецы, ♋ Рак, ♌ Лев, ♍ Дева, "
    "♎ Весы, ♏ Скорпион, ♐ Стрелец, ♑ Козерог, ♒ Водолей, ♓ Рыбы."
)

ELEMENT_EMOJI_GUIDE = (
    "Всегда используй эмодзи для стихий: 🔥 Огонь, 🌍 Земля, 💨 Воздух, 💧 Вода. "
    "Для модальностей: 🚀 Кардинальность, ⚓ Фиксированность, 🌊 Мутабельность."
)

_NATAL_MASTER_SECTIONS = [
    SectionSpec(
        section_id="executive_summary",
        title="Главное",
        prompt=(
            f"{REPORT_JSON_COMMON} "
            "Сделай краткую выжимку 'О чем эта карта' для занятого человека. "
            "Формат: 5-7 пунктов (используй блок list). "
            "2 Сильные стороны (Суперсилы). "
            "2 Риска/Ловушки (Где теряешь энергию). "
            "1 Ключ к отношениям. "
            "1 Ключ к деньгам. "
            "1 Главный фокус развития."
        )
    ),
    SectionSpec(
        section_id="input_frame",
        title="1. Данные рождения",
        prompt="Это генерируется программно."
    ),
    SectionSpec(
        section_id="synthesis",
        title="2. Синтез (метафора и ядро)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Используй блок `callout` (variant='quote') для метафоры. "
            "Затем 1-2 абзаца раскрытия (блок paragraph). "
            "В конце блок paragraph со строкой `**Главный тезис:** ...`."
        ),
    ),
    SectionSpec(
        section_id="framework_elements_modes",
        title="3. Каркас (стихии и модальности)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {ELEMENT_EMOJI_GUIDE} "
            "Опиши темперамент. Используй блок `table` для 'Баланса Сил':\n"
            "Колонки: Стихия/Модальность, %, Характеристика.\n"
            "Затем добавь блоки `paragraph` для Доминанты, Баланса, Дефицита и Стиля жизни."
        ),
    ),
    SectionSpec(
        section_id="axes_truths",
        title="4. Оси (две правды)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Опиши 4 главные оси. Для каждой оси используй `header` (level 3) и список `list` с пунктами: Твоя правда, Правда партнера, Задача."
        ),
    ),
    SectionSpec(
        section_id="aspects_beginner",
        title="5. Аспекты для новичка",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй ТОЛЬКО данные из `chart.aspects`. Выбери 4-6 самых точных аспектов (орбис < 3). "
            "Для каждого аспекта: `header` (level 3) и `list` с пунктами: Якорь, Сценарий, Ресурс, Тень, Ключ."
        ),
    ),
    SectionSpec(
        section_id="configurations_geometry",
        title="6. Конфигурации (геометрия)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй ТОЛЬКО данные из `chart.patterns`. Если список пуст, напиши в `paragraph`, что жестких конфигураций нет. "
            "Для каждой фигуры: `header` (level 3) и `list` с пунктами: Геометрия, Дар, Риск, Ключ."
        ),
    ),
    SectionSpec(
        section_id="dispositor_office",
        title="7. Диспозиторная логика",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Объясни иерархию через метафору офиса. Используй `header`, `paragraph` и `callout` для 'Главного Босса'."
        ),
    ),
    SectionSpec(
        section_id="core_triad",
        title="8. Личное ядро (⬆️ ASC / ☀️ Солнце / 🌙 Луна)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Три раздела (header level 3). В каждом: paragraph с тезисом и описанием. В конце callout 'Главный конфликт'."
        ),
    ),
    SectionSpec(
        section_id="mercury_mind",
        title="9. Мышление (☿ Меркурий)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Используй блоки: `header`, `paragraph` и `list` для ментальных ловушек."
        ),
    ),
    SectionSpec(
        section_id="shadow_trauma",
        title="10. Тень и травма (⚷ Хирон / ⚸ Лилит)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Два раздела. Для каждого: header, paragraph и list (Якорь, В жизни, Ресурс, Тень, Ключ)."
        ),
    ),
    SectionSpec(
        section_id="nodes_growth",
        title="11. Узлы (☊/☋ вектор взросления)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Два раздела (header). В каждом: paragraph и list."
        ),
    ),
    SectionSpec(
        section_id="vertex_fate",
        title="12. Вертекс (✴️ сюжетные встречи)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй header и list (Якорь, Сценарий, Урок, Рост, Ключ)."
        ),
    ),
    SectionSpec(
        section_id="balance_wheel",
        title="13. Колесо баланса (12 домов)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Для каждого из 12 домов: `header` (N Дом) и `list` (Тема, В плюсе, В минусе, Триггер, Вектор)."
        ),
    ),
    SectionSpec(
        section_id="love_intimacy",
        title="14. Любовь и близость (♀️ Венера / ♂️ Марс)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй header и paragraph."
        ),
    ),
    SectionSpec(
        section_id="money_realization",
        title="15. Деньги и реализация (2/6/10 + ♃ Юпитер / ♄ Сатурн)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй header и list."
        ),
    ),
    SectionSpec(
        section_id="stars_transuranus",
        title="16. Звезды и Трансураны (♅/♆/♇)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй header и list (Режим, Дар, Риск)."
        ),
    ),
    SectionSpec(
        section_id="time_cycles",
        title="17. Время и циклы",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Кратко опиши текущий период. Используй 1 `paragraph` и 1 `list` (Соляр, Тренд)."
        ),
    ),
    SectionSpec(
        section_id="final_synthesis",
        title="18. Финальная сборка",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Итог в одной фразе. Используй `callout` (variant='success') с Девизом и Главным советом."
        ),
    ),
    SectionSpec(
        section_id="technical_appendix",
        title="Приложение: Технические данные",
        prompt="Это генерируется программно."
    ),
]

_YEAR_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="year_meta",
        title="0. Метафора Года",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Используй данные из `year_forecast_data` (Profection, Solar Return, slow transits). "
            "Используй блок `callout` (variant='quote') для Метафоры и Девиза года."
        ),
    )
] + [
    SectionSpec(
        section_id=f"month_{i}_forecast",
        title=f"{i}. Месяц {i}",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} Проанализируй {i}-й месяц года. "
            f"ИСПОЛЬЗУЙ данные из `year_forecast_data.months` (объект с month={i}). "
            "Используй блоки `header` (level 3) для: Статус, Нить смысла, Активаторы, Карта сфер, События, Личный слой, Итог."
        ),
    ) for i in range(1, 13)
]

_MONTH_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="month_full_forecast",
        title="Прогноз на месяц",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} Дай полный прогноз на месяц. "
            "ИСПОЛЬЗУЙ `month_forecast_data`. "
            "Используй блоки:\n"
            "1. `header` (level 2) 'Статус месяца' + `callout` с метафорой и рычагом.\n"
            "2. `header` (level 2) 'Ключевые события' + `list` (Дата: Событие).\n"
            "3. `header` (level 2) 'Стратегия по неделям'. Для каждой недели (4 шт): `header` (level 3) + `list` (Фокус, Риск, Ресурс).\n"
            "4. `header` (level 2) 'Итог месяца' + `key_value` (Финансы, Отношения, Энергия).\n"
            "5. `callout` (variant='success') с финальными рекомендациями."
        ),
    ),
]

_WEEK_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="week_strategy",
        title="Стратегия недели",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Используй `week_forecast_data.days`. "
            "Используй блоки:\n"
            "1. `header` (level 2) 'Главная тема' + `callout` с метафорой.\n"
            "2. `header` (level 2) 'Статус недели' + `paragraph` (Светофор, Фон).\n"
            "3. `header` (level 2) 'Подневная стратегия'. Для каждого дня: `header` (level 3) + `list` (Астро-фактор, Ощущения, Риски, СТРАТЕГИЯ).\n"
            "4. `header` (level 2) 'Резюме по срезам' + `key_value` (Финансы, Энергия, Отношения, Магия)."
        ),
    ),
]

HORARY_COMMON = (
    "Ты — жесткий эксперт-практик. ЗАПРЕЩЕНО использовать слова: 'благоприятный', 'энергетика', 'фон', 'потенциал', 'вселенная', 'вибрации'. "
    "Запрещена латиница и англицизмы. Разрешены только сокращения ASC/MC/DSC/IC и обозначения L1/L7/L9/L10. "
    "Хорар — это прогностика. Ответ должен быть бинарным: либо событие происходит, либо нет. "
    "КРИТИЧЕСКИ ВАЖНО: 'ДА' в ответе — это факт реализации вопроса. Если вопрос негативный ('Заберут ли права?'), то 'ДА' означает потерю прав. "
    "Смотри на аспекты: L1 (Кверент) и Луна против L10 (Судья/Власть), L9 (Закон) или дома Квестита. "
    "Если аспекта нет — ответ НЕТ. Если есть препятствие (запрет, фрустрация) — ответ НЕТ. "
    "Пиши сухо, по делу, без морализаторства. "
    "Игнорируй общую структуру с буллетами и рекомендациями — следуй только формату секции. "
    "ЗАПРЕЩЕНО добавлять блоки вроде 'Ключевой фокус', 'Потенциал', 'Риски', 'Ключевые факторы', 'Рекомендации' в конце."
)

_HORARY_SECTIONS = [
    SectionSpec(
        section_id="horary_00_passport",
        title="0. Паспорт вопроса",
        prompt="Это генерируется программно."
    ),
    SectionSpec(
        section_id="horary_00_technical",
        title="Данные карты",
        prompt="Это генерируется программно."
    ),
    SectionSpec(
        section_id="horary_01_verdict",
        title="1. Ответ сразу",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} "
            "Дай итоговый вердикт на основе `chart.horary.aspects`. "
            "Используй блоки paragraph и callout.\n\n"
            "**Вердикт:** ...\n"
            "**Причина:** ...\n"
            "**Срок:** ...\n"
            "**Главный риск:** ..."
        )
    ),
    SectionSpec(
        section_id="horary_02_radicality",
        title="2. Пригодность карты",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} "
            "Используй `chart.horary.radicality`. Используй list для флагов."
        )
    ),
    SectionSpec(
        section_id="horary_03_significators",
        title="3. Сигнификаторы",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} "
            "Используй key_value для ролей."
        )
    ),
    SectionSpec(
        section_id="horary_04_state",
        title="4. Состояние сторон",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} "
            "Используй table."
        )
    ),
    SectionSpec(
        section_id="horary_05_mechanics",
        title="5. Механика исхода",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} "
            "Используй list."
        )
    ),
    SectionSpec(
        section_id="horary_06_moon",
        title="6. Луна как сценарий",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} "
            "Используй list."
        )
    ),
    SectionSpec(
        section_id="horary_07_timing",
        title="7. Тайминг",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {HORARY_COMMON} "
            "Используй paragraph."
        )
    ),
    SectionSpec(
        section_id="horary_08_conditions",
        title="8. Условия успеха",
        prompt=(f"{REPORT_JSON_COMMON} {HORARY_COMMON} "
            "Используй list."
        )
    ),
    SectionSpec(
        section_id="horary_09_risks",
        title="9. Риски и ограничения",
        prompt=(f"{REPORT_JSON_COMMON} {HORARY_COMMON} "
            "Используй list."
        )
    ),
    SectionSpec(
        section_id="horary_10_alternatives",
        title="10. Альтернативы",
        prompt=(f"{REPORT_JSON_COMMON} {HORARY_COMMON} "
            "Используй list."
        )
    ),
    SectionSpec(
        section_id="horary_11_summary",
        title="11. Итог",
        prompt=(f"{REPORT_JSON_COMMON} {HORARY_COMMON} "
            "Используй paragraph и callout."
        )
    ),
]

_TEN_YEAR_SECTIONS = [
    SectionSpec(
        section_id="decade_overview",
        title="Обзор 10 лет",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Дай общий обзор десятилетия. "
            "ИСПОЛЬЗУЙ данные из `decade_forecast_data` (транзиты медленных планет по годам). "
            "Используй paragraph и list."
        ),
    ),
    SectionSpec(
        section_id="decade_timeline",
        title="Хронология (10 лет)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Пройдись по годам, используя `decade_forecast_data`. "
            "Используй header level 4 для каждого года."
        ),
    ),
    SectionSpec(
        section_id="decade_storylines",
        title="Сюжетные линии",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} Сгруппируй события из `decade_forecast_data` в 3 сюжетные линии."
        ),
    ),
]

_SOLAR_RETURN_SECTIONS = [
    SectionSpec(
        section_id="solar_theme",
        title="Главная тема Соляра",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй paragraph и callout."
        ),
    ),
    SectionSpec(
        section_id="solar_money",
        title="Финансы (2/8 дома)",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй paragraph и list."
        ),
    ),
    SectionSpec(
        section_id="solar_love",
        title="Отношения (5/7 дома)",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй paragraph и list."
        ),
    ),
    SectionSpec(
        section_id="solar_strategy",
        title="Стратегия года",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй callout."
        ),
    ),
]

_SYNASTRY_SECTIONS = [
    SectionSpec(
        section_id="synastry_overview",
        title="Обзор совместимости",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй paragraph и callout для скора."
        ),
    ),
    SectionSpec(
        section_id="synastry_categories",
        title="Анализ по сферам",
        prompt=(f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Используй header level 3 для каждой сферы."
        ),
    ),
    SectionSpec(
        section_id="synastry_advice",
        title="Советы и Решения",
        prompt=(f"{REPORT_JSON_COMMON} "
            "Используй list."
        ),
    ),
]


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
    "custom": _NATAL_MASTER_SECTIONS, # Default fallback
}


def get_default_sections(report_type: str) -> List[SectionSpec]:
    return list(_REPORT_TEMPLATES.get(report_type, _NATAL_MASTER_SECTIONS))
# #END_BLOCK_SECTION_TEMPLATES
