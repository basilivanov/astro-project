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
            "Оси: ⬆️ ASC-⬇️ DSC, 🏠 IC-🏔️ MC, 2-8, 3-9. "
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
        section_id="year_meta",
        title="0. Метафора Года",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Определи главную метафору года на основе транзитов медленных планет (Юпитер, Сатурн, Уран, Нептун, Плутон) по домам и аспектам. "
            "Дай образ (например, 'Год Строительства Замка') и девиз."
        ),
    )
] + [
    SectionSpec(
        section_id=f"month_{i}_forecast",
        title=f"{i}. Месяц {i}",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Проанализируй {i}-й месяц года (считая от даты старта). "
            "Строго следуй структуре (13 пунктов): "
            "1. Заголовок и метаданные. "
            "2. Статус месяца (Светофор 🟢/🟡/🔴): Цветовой индикатор, Название, Фон, Цена ошибок, Рычаг, Совет. "
            "3. Центральная нить смысла: Метафора + тезис. "
            "4. Главные активаторы месяца (ТОП-5). "
            "5. Карта сфер месяца (ТОП-3). "
            "6. Событийный слой (Ингрессы, Ретро, Лунации). "
            "7. Личный слой (Транзиты к наталу). "
            "8. Глубинный слой (Прогрессии/Дирекции). "
            "9. Солярный контекст. "
            "10. Тайм-лорды. "
            "11. Фиксированные звёзды. "
            "12. Трансураны. "
            "13. Итог месяца (3 результата, 3 ловушки, ключ)."
        ),
    ) for i in range(1, 13)
]

_MONTH_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="month_overview",
        title="Обзор месяца",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Дай общий прогноз на месяц. "
            "Структура: "
            "1. Статус месяца (Светофор 🟢/🟡/🔴) + Метафора + Рычаг. "
            "2. Главные темы и задачи. "
            "3. Итог по сферам: Финансы, Отношения, Энергия."
        ),
    ),
    SectionSpec(
        section_id="week_1",
        title="Неделя 1",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Прогноз на 1-ю неделю. "
            "Формат: Фокус недели (одной фразой), Светофор (🟢/🟡/🔴), Риск/Ресурс."
        ),
    ),
    SectionSpec(
        section_id="week_2",
        title="Неделя 2",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Прогноз на 2-ю неделю. "
            "Формат: Фокус недели (одной фразой), Светофор (🟢/🟡/🔴), Риск/Ресурс."
        ),
    ),
    SectionSpec(
        section_id="week_3",
        title="Неделя 3",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Прогноз на 3-ю неделю. "
            "Формат: Фокус недели (одной фразой), Светофор (🟢/🟡/🔴), Риск/Ресурс."
        ),
    ),
    SectionSpec(
        section_id="week_4",
        title="Неделя 4",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Прогноз на 4-ю неделю. "
            "Формат: Фокус недели (одной фразой), Светофор (🟢/🟡/🔴), Риск/Ресурс."
        ),
    ),
]

_WEEK_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="week_strategy",
        title="Стратегия недели",
        prompt=(
            f"{RU_LANG_INSTRUCTION} "
            "1. Главная тема: Метафора недели. "
            "2. Статус недели: Светофор (🟢/🟡/🔴) + Общий фон и цена ошибки. "
            "3. Подневная стратегия (7 дней): Для каждого дня (Пн-Вс) укажи: "
            "   - Индикатор (🟢/🟡/🔴). "
            "   - Ощущения (психологический фон). "
            "   - Риски (где споткнуться). "
            "   - Стратегия/Соломка (конкретные действия). "
            "4. Резюме по срезам: Финансы, Энергия, Отношения, Магия."
        ),
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

_TEN_YEAR_SECTIONS = [
    SectionSpec(
        section_id="decade_overview",
        title="Обзор 10 лет",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Дай общий обзор десятилетия: главный тренд, "
            "ключевые темы и общий вектор развития."
        ),
    ),
    SectionSpec(
        section_id="decade_storylines",
        title="Сюжетные линии (10 лет)",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Сгруппируй ключевые события и темы на 10 лет "
            "в 3-5 сюжетных линий (личность/цели, отношения, финансы, судьба)."
        ),
    ),
    SectionSpec(
        section_id="decade_risks_resources",
        title="Риски и ресурсы десятилетия",
        prompt=(
            f"{RU_LANG_INSTRUCTION} Выдели главные риски, ресурсы и "
            "рекомендации по стратегии на 10 лет."
        ),
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
