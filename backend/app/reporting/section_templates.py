# ############################################################################
# AI_HEADER: MODULE_SECTION_TEMPLATES
# ROLE: Provide default section templates by report type.
# DEPENDENCIES: backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [SECTION_TEMPLATES]
# ############################################################################

from typing import List

from ..llm.orchestrator import SectionSpec

# #START_BLOCK_SECTION_TEMPLATES
# --- COMMON INSTRUCTIONS ---
# All prompts now include explicit language instruction.
RU_LANG_INSTRUCTION = (
    "Ответь на русском языке. Используй Markdown. "
    "Не дублируй заголовок раздела. "
    "Структура: короткий вступительный абзац, затем 3-6 буллетов, "
    "затем короткий блок `### 💡 Рекомендации` (2-4 пункта). "
    "Выделяй ключевые слова жирным. Эмодзи допустимы."
)

NATAL_MASTER_COMMON = (
    "Ответь на русском языке. Стиль и структура как в примере "
    "Svetlana_Natal_Report.md. Не добавляй блоки "
    "`О чем этот блок`, `Краткая карта блока`, `Рекомендации`, "
    "если это не указано в задании секции. "
    "Используй подзаголовки, списки и таблицы как в примере."
)

PLANET_EMOJI_GUIDE = (
    "Обязательно ставь эмодзи у каждой планеты при упоминании: "
    "☀️ Солнце, 🌙 Луна, ☿ Меркурий, ♀️ Венера, ♂️ Марс, "
    "♃ Юпитер, ♄ Сатурн, ♅ Уран, ♆ Нептун, ♇ Плутон, "
    "⚷ Хирон, ⚸ Лилит, 🌟 Селена, ☊ Северный узел, ☋ Южный узел. "
    "Для осей используй: ⬆️ ASC, ⬇️ DSC, 🏠 IC, 🏔️ MC, ✴️ Вертекс."
)

_NATAL_MASTER_SECTIONS = [
    SectionSpec(
        section_id="input_frame",
        title="1. Входные данные и расчет",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Дай блок как в примере: "
            "Кверент, Дата рождения, Место рождения, Система домов. "
            "Затем подзаголовок `### 🪐 Положение Планет (Фундамент)` и таблицу с колонками "
            "`Планета | Знак Зодиака | Градус | Статус (Сила)`. "
            "Статус указывай, если он известен по данным, иначе оставь пустым. "
            "Затем подзаголовок `### 🏠 Угловые точки и Узлы` и таблицу "
            "`Точка | Знак | Градус` (ASC, MC, Вертекс, Северный узел, Южный узел)."
        ),
    ),
    SectionSpec(
        section_id="synthesis",
        title="2. Синтез (метафора и ядро)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай как в примере: блокquote с `**Метафора:**` и 1-2 абзаца раскрытия, "
            "затем отдельной строкой `**Главный тезис:** ...`."
        ),
    ),
    SectionSpec(
        section_id="framework_elements_modes",
        title="3. Каркас (стихии и модальности)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опиши баланс стихий и модальностей как в примере: "
            "абзац о доминанте, затем буллеты: баланс стихий, дефицит, стиль жизни. "
            "Обязательно строка `**Доминанта: ...**` и строка "
            "`**Твой девиз по Каркасу:** *...*`."
        ),
    ),
    SectionSpec(
        section_id="axes_truths",
        title="4. Оси (две правды)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай 4 оси как в примере, в виде нумерованного списка. "
            "Оси: ⬆️ ASC–⬇️ DSC, 🏠 IC–🏔️ MC, 2–8, 3–9. "
            "Для каждой оси дай буллеты: "
            "`Твоя правда:`, `Правда партнера:`, `Задача:`."
        ),
    ),
    SectionSpec(
        section_id="aspects_beginner",
        title="5. Аспекты для новичка",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай блок как в примере: 4-6 аспектов, каждый с подзаголовком "
            "формата `#### 1. ... — «...»`. "
            "Для каждого аспекта используй строки: "
            "`Якорь:`, `Сценарий:`, `Ресурс:`, `Тень:`, `Ключ:`, `Вопрос:`. "
            "Не используй поле `Перевод`."
        ),
    ),
    SectionSpec(
        section_id="configurations_geometry",
        title="6. Конфигурации (геометрия)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай как в примере: краткий ввод, затем 1-3 конфигурации. "
            "Каждая конфигурация с заголовком `#### **Конфигурация: ...**` и буллетами: "
            "`Геометрия:`, `Дар:`, `Риск:`, `Ключ:`, `Вопрос:`. "
            "В конце блок `#### **Заметки на полях:**`."
        ),
    ),
    SectionSpec(
        section_id="dispositor_office",
        title="7. Диспозиторная логика",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Объясни диспозиторную иерархию через метафору офиса: "
            "сотрудники, отделы, Главный Босс. "
            "Обязательно используй образ «передачи конвертов». "
            "Нужны блоки: `**ГЛАВНЫЙ БОСС...**`, `**Как это работает (Офисная метафора):**`, "
            "`**Твой жизненный алгоритм:**`, `**Сила структуры:**`, `**Риск:**`, `**Ключ к управлению:**`."
        ),
    ),
    SectionSpec(
        section_id="core_triad",
        title="8. Личное ядро (⬆️ ASC / ☀️ Солнце / 🌙 Луна)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай три подпункта как в примере: "
            "`#### 1. ...`, `#### 2. ...`, `#### 3. ...` "
            "В каждом: строки `**Тезис:**` и `**Описание:**`. "
            "В конце блок `#### ⚖️ Сборка Ядра (Главный конфликт)` + строка `**Решение:** ...`."
        ),
    ),
    SectionSpec(
        section_id="mercury_mind",
        title="9. Мышление (☿ Меркурий)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай как в примере: подпункты "
            "`#### **Стиль мышления: ...**`, "
            "`#### **Режим «Гения» ...**`, "
            "`#### **Ментальные ловушки ...**` (нумерованный список), "
            "`#### **Ключ к эффективному мышлению:**` и финальный вопрос."
        ),
    ),
    SectionSpec(
        section_id="shadow_trauma",
        title="10. Тень и травма (⚷ Хирон / ⚸ Лилит)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Два подпункта как в примере: "
            "`#### **⚷ ХИРОН ...**` и `#### **🌑 ЛИЛИТ ...**`. "
            "В каждом: `Якорь:`, `Сценарий:`, `Ресурс:`, `Тень:`, `Ключ:`, `Вопрос:`."
        ),
    ),
    SectionSpec(
        section_id="nodes_growth",
        title="11. Узлы (☊/☋ вектор взросления)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Как в примере: отдельно Южный узел и Северный узел. "
            "Южный: `Якорь:`, `Сценарий:`, `Ловушка:`, `Ресурс:`. "
            "Северный: `Якорь:`, `Сценарий:`, `Миссия:`, `Вызов:`, `Ключ:`, `Вопрос:`."
        ),
    ),
    SectionSpec(
        section_id="vertex_fate",
        title="12. Вертекс (✴️ сюжетные встречи)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Как в примере: подпункт `#### **✴️ ВЕРТЕКС ...**` и строки "
            "`Якорь:`, `Сценарий встреч:`, `Урок судьбы:`, "
            "`Ключ:`, `Вопрос:`."
        ),
    ),
    SectionSpec(
        section_id="balance_wheel",
        title="13. Колесо баланса (12 домов)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Как в примере: 12 домов, каждый в формате "
            "`#### **N ДОМ — ...**` и 6 строк: "
            "`Тема:`, `В плюсе:`, `В минусе:`, `Триггер:`, `Вектор зрелости:`, `Вопрос:`."
        ),
    ),
    SectionSpec(
        section_id="love_intimacy",
        title="14. Любовь и близость (♀️ Венера / ♂️ Марс)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай два подпункта: `### ♀️ ВЕНЕРА ...` и `### ♂️ МАРС ...`, "
            "по 1 абзацу каждый, затем строка "
            "`🔑 **Секрет успеха:** ...`."
        ),
    ),
    SectionSpec(
        section_id="money_realization",
        title="15. Деньги и реализация (2/6/10 + ♃ Юпитер / ♄ Сатурн)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай три подпункта: `#### **💰 2 ДОМ ...**`, "
            "`#### **🛠 6 ДОМ ...**`, `#### **🏔 10 ДОМ ...**`. "
            "В каждом 1-2 строки с ключевыми смысловыми метками "
            "(Доход/Ключ/Стиль/Путь/Миссия). "
            "В конце строка `🔑 **Главная формула:** ...`."
        ),
    ),
    SectionSpec(
        section_id="stars_transuranus",
        title="16. Звезды и Трансураны (♅/♆/♇)",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Короткий ввод и 3 подпункта: "
            "`⚡️ Уран ...`, `🌊 Нептун ...`, `🌋 Плутон ...`. "
            "В каждом: `Дар:` и `Риск:`."
        ),
    ),
    SectionSpec(
        section_id="time_cycles",
        title="17. Время и циклы",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай как в примере: строка о расчете соляра, "
            "затем буллеты `Главный тренд`, `Солярный Асцендент`, "
            "`Наложение на Натал`, `Зенит года`."
        ),
    ),
    SectionSpec(
        section_id="final_synthesis",
        title="18. Финальная сборка",
        prompt=(
            f"{NATAL_MASTER_COMMON} {PLANET_EMOJI_GUIDE} "
            "Сделай финальную сборку как в примере: "
            "1-2 абзаца резюме, затем строка `**Твой девиз:** *...*` "
            "и строка `**Главный совет:** ...`."
        ),
    ),
]

_YEAR_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="year_theme",
        title="Центральная тема года",
        prompt=f"{RU_LANG_INSTRUCTION} Identify the main theme of the year based on slow transits (Jupiter, Saturn, Outer Planets) and Solar Return chart (if available).",
    ),
    SectionSpec(
        section_id="year_opportunities",
        title="Возможности и удача (Зеленый свет)",
        prompt=f"{RU_LANG_INSTRUCTION} Describe the biggest opportunities and areas of flow for the year.",
    ),
    SectionSpec(
        section_id="year_challenges",
        title="Вызовы и риски (Красный свет)",
        prompt=f"{RU_LANG_INSTRUCTION} Describe potential obstacles, restrictions, and areas requiring caution.",
    ),
    SectionSpec(
        section_id="q1_forecast",
        title="1 Квартал (Янв-Мар)",
        prompt=f"{RU_LANG_INSTRUCTION} Provide a forecast for the first quarter. Highlight key dates or periods.",
    ),
    SectionSpec(
        section_id="q2_forecast",
        title="2 Квартал (Апр-Июн)",
        prompt=f"{RU_LANG_INSTRUCTION} Provide a forecast for the second quarter. Highlight key dates or periods.",
    ),
    SectionSpec(
        section_id="q3_forecast",
        title="3 Квартал (Июл-Сен)",
        prompt=f"{RU_LANG_INSTRUCTION} Provide a forecast for the third quarter. Highlight key dates or periods.",
    ),
    SectionSpec(
        section_id="q4_forecast",
        title="4 Квартал (Окт-Дек)",
        prompt=f"{RU_LANG_INSTRUCTION} Provide a forecast for the fourth quarter. Highlight key dates or periods.",
    ),
    SectionSpec(
        section_id="love_relationships",
        title="Любовь и отношения",
        prompt=f"{RU_LANG_INSTRUCTION} Forecast for relationships, romance, and partnerships for the year.",
    ),
    SectionSpec(
        section_id="career_finance",
        title="Карьера и финансы",
        prompt=f"{RU_LANG_INSTRUCTION} Forecast for career growth, business, and financial matters.",
    ),
    SectionSpec(
        section_id="health_vitality",
        title="Здоровье и энергия",
        prompt=f"{RU_LANG_INSTRUCTION} Forecast for physical vitality and health (general advice, not medical diagnosis).",
    ),
]

_TEN_YEAR_SECTIONS = [
    SectionSpec(
        section_id="decade_overview",
        title="Обзор десятилетия",
        prompt=f"{RU_LANG_INSTRUCTION} Summarize the major developmental arc for the next 10 years.",
    ),
    SectionSpec(
        section_id="pluto_cycle",
        title="Цикл Плутона",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze Pluto's transit through houses and aspects to natal planets over the next decade.",
    ),
    SectionSpec(
        section_id="neptune_cycle",
        title="Цикл Нептуна",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze Neptune's transit through houses and aspects to natal planets over the next decade.",
    ),
    SectionSpec(
        section_id="uranus_cycle",
        title="Цикл Урана",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze Uranus's transit through houses and aspects to natal planets over the next decade.",
    ),
    SectionSpec(
        section_id="saturn_cycle",
        title="Цикл Сатурна",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze Saturn's movement (major peaks and valleys) over the next decade.",
    ),
    SectionSpec(
        section_id="jupiter_cycle",
        title="Циклы Юпитера",
        prompt=f"{RU_LANG_INSTRUCTION} Highlight major Jupiter return or opposition years and growth periods.",
    ),
    SectionSpec(
        section_id="key_turning_points",
        title="Ключевые поворотные точки",
        prompt=f"{RU_LANG_INSTRUCTION} List specific years/periods that will be most significant.",
    ),
    SectionSpec(
        section_id="strategic_advice",
        title="Стратегический совет",
        prompt=f"{RU_LANG_INSTRUCTION} Provide long-term strategic advice for career and personal life.",
    ),
]

_MONTH_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="month_theme",
        title="Структура месяца",
        prompt=(
            "Ответь на русском языке. Используй Markdown. "
            "Строго следуй этому скелету (13 пунктов) и не добавляй лишних блоков. "
            "Фокус на пользе: деньги, отношения, психическая устойчивость. "
            ""
            "1. Заголовок и метаданные: Период, Локация, Натал, Метод, Слои.\n"
            "2. Статус месяца (Светофор 🟢/🟡/🔴):\n"
            "   * Цветовой индикатор.\n"
            "   * Название месяца (метафорическое).\n"
            "   * Общий фон.\n"
            "   * Цена ошибок.\n"
            "   * Рычаг (на что давить).\n"
            "   * Совет-формула.\n"
            "3. Центральная нить смысла: Метафора + тезис, 3 маркера «в теме».\n"
            "4. Главные активаторы месяца: ТОП-5 факторов "
            "(Фактор → что запускает → сфера → риск/ресурс).\n"
            "5. Карта сфер месяца: ТОП-3 сферы подробно, остальные одной строкой.\n"
            "6. Событийный слой: Ингрессы, Ретроградность, Затмения, Лунации.\n"
            "7. Личный слой (транзиты к наталу): Углы/Светила, Управители, Узлы/Вертекс, Конфигурации.\n"
            "8. Глубинный слой (прогрессии/дирекции): Прогрессивная Луна, Дуги/Дирекции, Итог созревания.\n"
            "9. Солярный контекст: Связь с темой года, наложение домов.\n"
            "10. Тайм-лорды: Годовой управитель в этом месяце.\n"
            "11. Фиксированные звёзды: Точные попадания "
            "(Архетип → Проявление → Дар/Риск).\n"
            "12. Трансураны: Режим края, помощь/перегрев.\n"
            "13. Итог месяца: 3 результата, 3 ловушки, ключ интеграции, переход в следующий месяц.\n"
        ),
    ),
]

_WEEK_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="week_strategy",
        title="Стратегия недели",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze the overall energy of the week. Is it for action, rest, or planning?",
    ),
    SectionSpec(
        section_id="daily_breakdown",
        title="По дням",
        prompt=f"{RU_LANG_INSTRUCTION} Briefly describe the vibe for key days of the week.",
    ),
    SectionSpec(
        section_id="risks_opportunities",
        title="Риски и возможности",
        prompt=f"{RU_LANG_INSTRUCTION} Highlight specific risks ('straws to lay down') and lucky breaks.",
    ),
]

_HORARY_SECTIONS = [
    SectionSpec(
        section_id="horary_context",
        title="Контекст вопроса",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze the chart radicality and the context of the question provided by the user. Confirm if the chart is fit to be judged.",
    ),
    SectionSpec(
        section_id="horary_significators",
        title="Сигнификаторы",
        prompt=f"{RU_LANG_INSTRUCTION} Identify the main significators (planets representing the querent and the quesited). Describe their condition (dignities, debilities).",
    ),
    SectionSpec(
        section_id="horary_aspects",
        title="Аспекты и рецепции",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze applying and separating aspects between significators. Check for receptions.",
    ),
    SectionSpec(
        section_id="horary_answer",
        title="Ответ",
        prompt=f"{RU_LANG_INSTRUCTION} Give a clear YES/NO/MAYBE answer based on the analysis. Explain why.",
    ),
    SectionSpec(
        section_id="horary_timing",
        title="Сроки (Тайминг)",
        prompt=f"{RU_LANG_INSTRUCTION} Estimate the timing of the event if applicable (using symbolic time units).",
    ),
]

_SOLAR_RETURN_SECTIONS = [
    SectionSpec(
        section_id="solar_theme",
        title="Главная тема Соляра",
        prompt=f"{RU_LANG_INSTRUCTION} {PLANET_EMOJI_GUIDE} Determine the main theme of the Solar Return year based on the Solar Return Ascendant and Sun house placement.",
    ),
    SectionSpec(
        section_id="solar_money",
        title="Финансы (2/8 дома)",
        prompt=f"{RU_LANG_INSTRUCTION} {PLANET_EMOJI_GUIDE} Analyze financial prospects in the Solar Return chart.",
    ),
    SectionSpec(
        section_id="solar_love",
        title="Отношения (5/7 дома)",
        prompt=f"{RU_LANG_INSTRUCTION} {PLANET_EMOJI_GUIDE} Analyze relationship prospects in the Solar Return chart.",
    ),
    SectionSpec(
        section_id="solar_strategy",
        title="Стратегия года",
        prompt=f"{RU_LANG_INSTRUCTION} {PLANET_EMOJI_GUIDE} Provide a strategic summary for the year.",
    ),
]

_SYNASTRY_SECTIONS = [
    SectionSpec(
        section_id="synastry_overview",
        title="Обзор совместимости",
        prompt=f"{RU_LANG_INSTRUCTION} Provide a high-level summary of the connection.",
    ),
    SectionSpec(
        section_id="emotional_connection",
        title="Эмоциональная связь (Луны)",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze the interaction between the Moons. Describe emotional comfort and safety.",
    ),
    SectionSpec(
        section_id="communication",
        title="Общение (Меркурии)",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze the interaction between Mercuries. Describe intellectual compatibility.",
    ),
    SectionSpec(
        section_id="love_attraction",
        title="Любовь и притяжение (Венера/Марс)",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze Venus and Mars interaspects. Describe romantic and sexual chemistry.",
    ),
    SectionSpec(
        section_id="long_term",
        title="Долгосрочные перспективы (Сатурн/Юпитер)",
        prompt=f"{RU_LANG_INSTRUCTION} Analyze Saturn (glue) and Jupiter (growth) aspects in synastry.",
    ),
    SectionSpec(
        section_id="conflict_resolution",
        title="Конфликты и решение",
        prompt=f"{RU_LANG_INSTRUCTION} Identify potential friction points and how to resolve them.",
    ),
]


_REPORT_TEMPLATES = {
    "natal_master": _NATAL_MASTER_SECTIONS,
    "year_forecast": _YEAR_FORECAST_SECTIONS,
    "ten_year_forecast": _TEN_YEAR_SECTIONS,
    "month_forecast": _MONTH_FORECAST_SECTIONS,
    "week_forecast": _WEEK_FORECAST_SECTIONS,
    "horary_answer": _HORARY_SECTIONS,
    "synastry": _SYNASTRY_SECTIONS,
    "solar_return": _SOLAR_RETURN_SECTIONS,
    "custom": _NATAL_MASTER_SECTIONS, # Default fallback
}


def get_default_sections(report_type: str) -> List[SectionSpec]:
    return list(_REPORT_TEMPLATES.get(report_type, _NATAL_MASTER_SECTIONS))
# #END_BLOCK_SECTION_TEMPLATES
