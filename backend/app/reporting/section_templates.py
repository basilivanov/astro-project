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
    "- rating {type='rating', value=float, max=10, label=str}\n    - traffic_lights {type='traffic_lights', items={health:'red'|'yellow'|'green', money:..., love:...}}\n"
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
    f"{STYLE_CONTRACT_SUMMARY_INSTRUCTION} "
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

PREMIUM_NATAL_NARRATIVE_CONTRACT = (
    "Для этой секции действует канонический tone contract из `STYLE_CONTRACT.md`: "
    "70% премиальный художественный нарратив и 30% практическая навигация. "
    "Пиши по формуле `сцена -> механизм -> зрелый ход`. "
    "Сначала жизнь, потом астрология: raw facts и названия положений используй как якоря и доказательства, "
    "а не как каркас абзаца. "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО строить текст по формуле 'планета/положение в знаке или доме -> значит ты ...'. "
    "Если упоминаешь астрологический якорь, делай это коротко и только после жизненного вывода. "
    "Одна секция = одна центральная мысль. Один точный образ или мини-сцена достаточно; дальше держи язык ясным, взрослым и собранным. "
    "Практический совет должен вырастать из паттерна, а не приклеиваться в конце. "
    "Не используй учебниковый тон, коучинговые клише, повторяющиеся ярлыки и одинаковый ритм пунктов."
)

NO_REDUNDANT_SECTION_HEADER = (
    "Не дублируй название секции отдельным `header`: заголовок уже есть в интерфейсе, начинай сразу со смысла."
)

EXECUTIVE_SUMMARY_EDITORIAL_CONTRACT = (
    "Первая фраза должна звучать как точный редакторский logline карты: одно жизненное напряжение, повторяющаяся сцена или внутренний закон. "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО начинать с общих заходов вроде 'Ты находишься...', 'Ты способен...', 'У тебя есть...', 'Твоя задача...'. "
    "Список здесь не чек-лист, а editorial navigation: короткие строки без двоеточий, без повторяющегося префикса в каждом пункте, без служебных ярлыков. "
    "Пусть пункты звучат как правила игры, закономерности и практические ходы."
)

_NATAL_MASTER_SECTIONS = [
    SectionSpec(
        section_id="executive_summary",
        title="Главное",
        prompt=(
            f"{REPORT_JSON_COMMON} {PREMIUM_NATAL_NARRATIVE_CONTRACT} {EXECUTIVE_SUMMARY_EDITORIAL_CONTRACT} "
            "Сделай краткую, но живую выжимку 'О чем эта карта' для занятого человека. "
            "Опирайся на `section_context.insight_pack`: "
            "`strengths_score`, `risk_score`, `relationship_theme`, `money_theme`, `development_focus`, "
            "`life_manifestations`, `stress_manifestation`, `self_sabotage_pattern`, `compensation_pattern`, "
            "`what_to_do`, `what_not_to_do`, `best_mode_of_action`, `scene_seeds`. "
            "Это уже рассчитанный life-layer карты; модель должна красиво связать его в ясный executive text, а не придумывать новый смысловой каркас. "
            f"{NO_REDUNDANT_SECTION_HEADER} "
            "Первый абзац должен сразу поставить человека внутрь жизненной сцены или внутреннего закона этой карты, а не начинаться с перечисления положений. "
            "Формат: 1 короткий `paragraph` для сцены/внутреннего закона + 1 `list` на 4-6 коротких пунктов + 1 короткий `paragraph` со зрелым режимом действия. "
            "В списке обязательно покрой: опорный паттерн, цену ресурса или перегиб, отношения, деньги/реализацию и один зрелый практический ход. "
            "Не строй список как механический чек-лист, не используй двоеточия внутри `list.items` и не раскладывай секцию по корзинам 'Сильная сторона / Риск / Что делать'. "
            "Не своди список к набору императивов из `what_to_do`: в нем должны доминировать observation-lines про сам паттерн карты, а не только команды. "
            "Каждый пункт должен звучать как редакторская навигация и добавлять новую грань карты."
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
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {PREMIUM_NATAL_NARRATIVE_CONTRACT} "
            "Опирайся на `section_context.insight_pack`: "
            "`identity_vector`, `core_conflict`, `dominant_drives`, `map_metaphor_seed`, "
            "`core_life_story`, `life_manifestations`, `inner_conflict_dynamics`, `self_sabotage_pattern`, "
            "`compensation_pattern`, `what_to_do`, `what_not_to_do`, `best_mode_of_action`, `scene_seeds`. "
            "Это уже рассчитанное ядро смысла и life-layer; модель должна собрать из этого большой связный текст, а не заново синтезировать личность. "
            f"{NO_REDUNDANT_SECTION_HEADER} "
            "Используй блок `callout` (variant='quote') для метафоры. "
            "Затем 2-3 блока `paragraph`, выстроенные по ритму `сцена -> механизм -> зрелый ход`: "
            "первый абзац вводит в жизненное напряжение и главный внутренний закон, "
            "второй раскрывает конфликт, цену ресурса и самосаботаж, "
            "третий показывает зрелый режим действия и практический ход. "
            "Можно естественно вплести 1-2 `scene_seeds` как мини-сцены или точные образные примеры, но не превращай текст в россыпь метафор. "
            "В конце блок `paragraph` со строкой `**Главный тезис:** ...`. "
            "СТРОГО соблюдай знаки Зодиака планет из предоставленных данных."
        ),
    ),
    SectionSpec(
        section_id="framework_elements_modes",
        title="3. Каркас (стихии и модальности)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {ELEMENT_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`element_rank`, `mode_rank`, `dominant_signature`, `deficit_signature`, `lifestyle_vector`, `balance_formula`. "
            "Это уже рассчитанный deterministic temperament pack; не собирай темперамент заново только из raw balance. "
            "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать таблицы (table). "
            "Используй только маркированный список `list` для 'Баланса Сил' (формат: Стихия - %). "
            "Затем добавь блоки `paragraph` для Доминанты, Дефицита, Стиля жизни и Формулы баланса."
        ),
    ),
    SectionSpec(
        section_id="axes_truths",
        title="4. Оси (две правды)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`axis_polarities`, `axis_tasks`, `dominant_axis_tension`. "
            "Это уже рассчитанные полярности карты; не пересобирай их заново от себя. "
            "Опиши 4 главные оси. Для каждой оси используй `header` (level 3) и список `list` с пунктами: Твоя правда, Правда партнера, Задача."
        ),
    ),
    SectionSpec(
        section_id="aspects_beginner",
        title="5. Аспекты для новичка",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack.aspect_cards`. "
            "Это уже рассчитанные aspect cards с полями `anchor`, `scenario`, `resource`, `shadow`, `key`; "
            "не придумывай новые аспекты и не меняй их смысловой каркас. "
            "Используй ТОЛЬКО данные из `chart.aspects`. Выбери 4-6 самых точных аспектов (орбис < 3). "
            "Для каждого аспекта: `header` (level 3) и `list` с пунктами: Якорь, Сценарий, Ресурс, Тень, Ключ. "
            "ВАЖНО: НЕ упоминай знаки Зодиака в этом разделе, фокусируйся только на взаимодействии планет."
        ),
    ),
    SectionSpec(
        section_id="configurations_geometry",
        title="6. Конфигурации (геометрия)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack.configuration_cards`, `dominant_pattern`, `absence_summary`. "
            "Это уже рассчитанный deterministic pattern pack; не пересобирай смысл фигур заново от себя. "
            "Если `configuration_cards` пуст, используй `absence_summary` и напиши один `paragraph`. "
            "Для каждой фигуры: `header` (level 3) и `list` с пунктами: Геометрия, Дар, Риск, Вопрос, Ключ."
        ),
    ),
    SectionSpec(
        section_id="dispositor_office",
        title="7. Диспозиторная логика",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`engine_summary`, `office_map`, `power_centers`, `final_bosses`, `decision_chains`, `office_metaphor_seed`. "
            "Это уже детерминированная иерархия управления карты; не пересобирай ее заново от себя. "
            "Объясни иерархию через метафору офиса. Используй `header`, `paragraph` и `callout` для 'Главного Босса'."
        ),
    ),
    SectionSpec(
        section_id="core_triad",
        title="8. Личное ядро (⬆️ ASC / ☀️ Солнце / 🌙 Луна)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`asc_mask`, `solar_drive`, `lunar_need`, `triad_conflict`, `triad_integration`. "
            "Это уже рассчитанное ядро карты; модель должна verbalize его, а не собирать новый психологический синтез. "
            "Три раздела (header level 3: ⬆️ ASC, ☀️ Солнце, 🌙 Луна). "
            "В каждом: `paragraph` и `list` с пунктами: Режим, Риск/Потребность, Ключ роста. "
            "В конце `callout` (variant='info', title='Сборка ядра') используй `triad_conflict` и `triad_integration`."
        ),
    ),
    SectionSpec(
        section_id="mercury_mind",
        title="9. Мышление (☿ Меркурий)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`thinking_style`, `processing_mode`, `cognitive_risks`, `mind_keys`. "
            "Это уже рассчитанная логика мышления; не замещай ее новой трактовкой. "
            "Используй блоки: `header`, `paragraph` и `list` (пункты: Стиль, Режим, Ловушка, Ключ)."
        ),
    ),
    SectionSpec(
        section_id="shadow_trauma",
        title="10. Тень и травма (⚷ Хирон / ⚸ Лилит)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`chiron_pattern`, `lilith_pattern`, `pain_points`, `compensation_modes`, `integration_task`. "
            "Это уже рассчитанный shadow layer; не заменяй его свободным синтезом. "
            "Два раздела (⚷ Хирон и ⚸ Лилит). Для каждого: header, paragraph и list (Якорь, Сценарий, Ресурс, Тень, Ключ)."
        ),
    ),
    SectionSpec(
        section_id="nodes_growth",
        title="11. Узлы (☊/☋ вектор взросления)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`south_node_habit`, `north_node_direction`, `bridge_task`, `node_drivers`. "
            "Это уже рассчитанная ось роста; модель должна ее раскрыть, а не изобретать заново. "
            "Два раздела (Южный и Северный узел). В каждом: paragraph и list (Ловушка, Миссия)."
        ),
    ),
    SectionSpec(
        section_id="vertex_fate",
        title="12. Вертекс (✴️ сюжетные встречи)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`vertex_signature`, `encounter_triggers`, `relationship_vector`, `fated_lesson`. "
            "Это уже рассчитанный deterministic Vertex pack; не изобретай собственную теорию судьбы поверх него. "
            "Обязательно упомяни ✴️ Вертекс. Используй `header`, `paragraph` и `list` с пунктами: Якорь, Триггеры, Вектор, Урок."
        ),
    ),
    SectionSpec(
        section_id="balance_wheel_1_6",
        title="13. Колесо баланса (Дома 1-6)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack.house_pack` и `zone_summary`. "
            "Для каждого дома используй уже рассчитанные `theme`, `plus`, `minus`, `trigger`, `growth_vector`, `ruler_story`; "
            "не придумывай новые темы вне этого pack. "
            "Для ДОМОВ с 1-го по 6-й: `header` (N Дом) и `list` (Тема, В плюсе, В минусе, Триггер, Вектор зрелости)."
        ),
    ),
    SectionSpec(
        section_id="balance_wheel_7_12",
        title="14. Колесо баланса (Дома 7-12)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack.house_pack` и `zone_summary`. "
            "Для каждого дома используй уже рассчитанные `theme`, `plus`, `minus`, `trigger`, `growth_vector`, `ruler_story`; "
            "не придумывай новые темы вне этого pack. "
            "Для ДОМОВ с 7-го по 12-й: `header` (N Дом) и `list` (Тема, В плюсе, В минусе, Триггер, Вектор зрелости)."
        ),
    ),
    SectionSpec(
        section_id="love_intimacy",
        title="15. Любовь и близость (♀️ Венера / ♂️ Марс)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {PREMIUM_NATAL_NARRATIVE_CONTRACT} "
            "Опирайся на `section_context.insight_pack`: "
            "`attachment_style`, `partnership_needs`, `conflict_style`, `intimacy_risk_flags`, "
            "`relationship_manifestations`, `relationship_triggers`, `self_sabotage_pattern`, `compensation_pattern`, "
            "`what_to_do`, `what_not_to_do`, `best_mode_of_action`, `scene_seeds`. "
            "Это уже рассчитанный relationship life-layer; модель должна verbalize его большим красивым связным текстом, а не пересобирать любовную психологию с нуля. "
            "Не строй текст по схеме '♀️ Венера значит..., ♂️ Марс значит...' как учебник: "
            "упоминай ♀️ Венеру и ♂️ Марс как фактические якоря внутри живой сцены отношений. "
            f"{NO_REDUNDANT_SECTION_HEADER} "
            "Формат: 3 блока `paragraph` и при необходимости 1 короткий `list` на 3 пункта. "
            "Первый абзац — как любовь включается и что человеку нужно для доверия, "
            "второй — что запускает дистанцию, конфликт и самосаботаж, "
            "третий — как выглядит зрелая близость и какой практический ход сохраняет контакт. "
            "Если добавляешь `list`, используй его только для коротких зрелых ходов, а не для пересказа всей секции. "
            "В тексте обязательно покажи: как любовь включается, что триггерит дистанцию/конфликт, где самосаботаж, как человек компенсирует уязвимость, что помогает близости и что её ломает."
        ),
    ),
    SectionSpec(
        section_id="money_realization",
        title="16. Деньги и реализация (2/6/10 + ♃ Юпитер / ♄ Сатурн)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`career_vector`, `money_pattern`, `work_risk_flags`, `realization_mode`. "
            "Это уже рассчитанные выводы; модель должна их упаковать и связать с фактами. "
            "Используй header и list."
        ),
    ),
    SectionSpec(
        section_id="stars_transuranus",
        title="17. Звезды и Трансураны (♅/♆/♇)",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`uranus_vector`, `neptune_vector`, `pluto_vector`, `collective_story`, `fixed_star_hooks`. "
            "Это уже рассчитанный deterministic слой по высшим планетам; не пересобирай его свободным синтезом. "
            "Сделай три блока: ♅ Уран, ♆ Нептун, ♇ Плутон. Для каждого используй `header` и `list` (Режим, Дар, Риск, Ключ). "
            "Если `fixed_star_hooks` пуст, не выдумывай fixed stars. "
            "ВАЖНО: НЕ упоминай знаки Зодиака в этом разделе, фокусируйся на высшем смысле планет."
        ),
    ),
    SectionSpec(
        section_id="time_cycles",
        title="18. Время и циклы",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`current_age`, `cycle_markers`, `maturity_cycle_summary`, `saturn_jupiter_phase`, `growth_tension`. "
            "Если transit/solar pack отсутствует, НЕ ПРИДУМЫВАЙ текущие транзиты, соляр и даты событий: "
            "говори только о том возрастном и циклическом слое, который уже посчитан в insight pack. "
            "Кратко опиши текущий период. Используй 1 `paragraph` и 1 `list` (Соляр, Тренд)."
        ),
        max_tokens=800,
    ),
    SectionSpec(
        section_id="final_synthesis",
        title="19. Финальная сборка",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} "
            "Опирайся на `section_context.insight_pack`: "
            "`final_motto_seed`, `one_sentence_advice`, `top_conflict_vs_top_resource`, "
            "`integration_focus`, `closing_bridge`, `applied_cross_links`. "
            "Это уже детерминированная финальная сборка карты. "
            "КРИТИЧЕСКИ ВАЖНО: Выведи ТОЛЬКО ОДИН блок `callout` (variant='success'). "
            "Внутри callout напиши Девиз и Главный совет так, чтобы они явно собирали work/love cross-links из insight_pack, а не звучали как универсальный мотивационный лозунг. "
            "ЗАПРЕЩЕНО выводить любые другие блоки, заголовки или текст вне callout."
        ),
        max_tokens=1000,
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

CHEAP_FORECAST_VOICE_CONTRACT = (
    "Пиши как персональный редактор-прогностик, а не как учебник и не как шаблонный коуч. "
    "Рабочая пропорция: 70% живая личная навигация, 30% практические действия. "
    "Сначала показывай, где период чувствуется в реальной жизни, затем давай короткий зрелый ход. "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать пустые формулы вроде "
    "'важные дела', 'избегай конфликтов', 'не переутомляйся', 'не распыляйся', "
    "'общий фон месяца' без уточнения, где именно это проявится. "
    "Не пиши благопожелания и мотивационные лозунги в финале."
)

MONTH_FORECAST_VOICE_CONTRACT = (
    "Для month horizon адаптируй направление из `STYLE_CONTRACT.md`: "
    "формула секции = `сцена месяца -> механизм периода -> зрелый ход по фазам`. "
    "Смотри на месяц как на кампанию из четырех фаз, а не как на 'общий фон'. "
    "Показывай, где это чувствуется в реальной жизни: переговоры, деньги, отношения, дедлайны, режим, запуск, пересборка процессов. "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать шаблоны вроде 'новые возможности', 'важные дела', 'не переутомляйся', "
    "'избегай конфликтов', 'не распыляйся' без сцены и без конкретного действия. "
    "Если данных много, собирай их в одну нить: где месяц ускоряет, где заставляет пересчитать курс, где просит закрепить результат. "
    "Для `callout.variant` используй только exact values: `error`, `warning`, `success`, `quote`, `info`. "
    "НЕЛЬЗЯ писать `green`, `yellow`, `red` или другие произвольные варианты."
)

_MONTH_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="month_full_forecast",
        title="Прогноз на месяц",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {CHEAP_FORECAST_VOICE_CONTRACT} {MONTH_FORECAST_VOICE_CONTRACT} "
            "Дай полный прогноз на месяц. "
            "ИСПОЛЬЗУЙ `month_forecast_data`. В нем уже есть `month_label`, `status`, `status_summary`, `central_task`, `event_cards`, `phases`, `semantic_layer`, `campaign_arc`. "
            "Собери из них один внятный личный сценарий месяца, а не россыпь общих советов. "
            "`semantic_layer` — это канонический deterministic micro-pattern pack месяца (tone, pacing, friction, money/admin focus, relationship softness); verbalize его, а не подменяй новыми общими теориями. "
            "`campaign_arc` задает dramaturгию месяца: `opening_scene`, `phase_sequence`, `close_focus`. Используй его как каркас связности между неделями. "
            "У каждой записи в `phases` уже есть `phase_role`, `scene_hint`, `transition_hint`, `focus_hint`, `push_hint`, `restraint_hint`, `events`. Не делай недели взаимозаменяемыми. "
            "Структура ответа (JSON):\\n"
            "1. `header` (level 2) '📅 ПРОГНОЗ НА МЕСЯЦ'.\\n"
            "2. `callout` (variant по цвету status: RED=error, YELLOW=warning, GREEN=success) с заголовком 'СТАТУС МЕСЯЦА'. "
            "Внутри 2-3 короткие фразы: где месяц давит или открывает окно, в каких человеческих сценах это чувствуется и какая главная практическая задача. Используй `status_summary`, `central_task`, `semantic_layer.headline`, `semantic_layer.scene_seed`; variant должен быть exact `error|warning|success`. "
            "Обязательно назови 1-2 конкретные жизненные сцены из набора: переговоры, деньги, отношения, документы, дедлайны, рабочий ритм, запуск, пересборка процесса. "
            "ЗАПРЕЩЕНЫ формулы 'новые возможности', 'важные задачи', 'новые инициативы' без уточнения сцены.\\n"
            "3. `header` (level 2) 'Ключевые события'.\\n"
            "4. `list` (5-8 пунктов, формат: Дата - Событие - жизненное проявление). Бери из `event_cards`, используй их `date_label`, `event`, `life_signal`; не выдумывай новые даты.\\n"
            "5. `header` (level 2) 'Стратегия по неделям'.\\n"
            "6. `paragraph` на 2-3 предложения: как проживать месяц как единую кампанию, а не как набор разрозненных советов. Обязательно покажи переход `сначала -> затем -> к середине -> в финале`. Опирайся на `campaign_arc.phase_sequence`, `semantic_layer.money_admin_focus`, `semantic_layer.relationship_softness`.\\n"
            "7. Для каждой записи из `phases` создай блок:\\n"
            "   - `header` (level 3): '`label`. `phase_role` (`date_range_label`)'.\\n"
            "   - `paragraph` на 1-2 предложения: сначала `transition_hint`, затем `scene_hint`; если есть `events`, вплети один якорь-дату без перечисления всего списка.\\n"
            "   - `list` ровно из трех пунктов: '**Фокус:** ...', '**Что продвигать:** ...', '**Где не форсировать:** ...'. "
            "Опирайся на `focus_hint`, `push_hint`, `restraint_hint` и `events`; не изобретай пятую фазу и не повторяй одни и те же формулы во всех неделях.\\n"
            "8. `header` (level 2) 'Итог месяца'.\\n"
            "9. `key_value` (Финансы, Отношения, Энергия). Каждый value короткий, конкретный, жизненный и без общих лозунгов; опирайся на `semantic_layer.money_admin_focus`, `semantic_layer.relationship_softness`, `semantic_layer.rest`.\\n"
            "10. `callout` (variant='success') с заголовком 'Практический ход' и одной конкретной ставкой на месяц. Используй `semantic_layer.practical_move` и `campaign_arc.close_focus`."
        ),
    ),
]

_WEEK_FORECAST_SECTIONS = [
    SectionSpec(
        section_id="week_strategy",
        title="Стратегия недели",
        prompt=(
            f"{REPORT_JSON_COMMON} {PLANET_EMOJI_GUIDE} {ZODIAC_EMOJI_GUIDE} {CHEAP_FORECAST_VOICE_CONTRACT} "
            "Используй `week_forecast_data`. В нем есть `summary` (общий статус), `days` (список дней) и `semantic_layer`. "
            "Для каждого дня в `days` уже подготовлены `weekday_ru`, `date_label`, `traffic_desc`, `moon_label`, `events`. "
            "БЕРИ их как есть: не меняй даты, weekday, `traffic_desc`, знак Луны и не переводи их в другой формат. "
            "`semantic_layer` — это канонический deterministic micro-pattern pack недели. Используй его, чтобы текст звучал через жизненные паттерны, а не через механическое перечисление фактов. "
            "Структура ответа (JSON):\n"
            "1. `header` (level 2) '📅 ПРОГНОЗ НА НЕДЕЛЮ' (добавь даты из первого и последнего дня).\n"
            "2. `callout` (variant по цвету summary.traffic_light: RED=error, YELLOW=warning, GREEN=success) с заголовком 'СТАТУС НЕДЕЛИ'. "
            "В тексте: одна главная сцена недели и один зрелый способ ее пройти. Опирайся на `semantic_layer.headline`, `semantic_layer.pacing`, `semantic_layer.negotiation`. Variant должен быть exact `error|warning|success`; НЕЛЬЗЯ писать `green|yellow|red`.\n"
            "3. `header` (level 2) 'Главная тема'.\n"
            "4. `paragraph` на 2-3 предложения: где эта неделя бьет по жизни человека и что реально даст результат. Используй `semantic_layer.relationship_softness` и `semantic_layer.money_admin_focus`, если они релевантны.\n"
            "5. `header` (level 2) 'Подневная стратегия'.\n"
            "Для каждого дня создай блок:\n"
            "   - `header` (level 3) Формат: '`weekday_ru`, `date_label` (`traffic_desc`)'.\n"
            "   - `list` со следующими пунктами:\n"
            "     - **Луна:** используй `moon_label`.\n"
            "     - **Астро-события:** перечисли `events`; если пусто, напиши 'Без новых триггеров'.\n"
            "     - **Фокус:** одно жизненное действие, а не абстракция.\n"
            "     - **Риск:** одна конкретная ловушка дня.\n"
            "6. `header` (level 2) 'Резюме по срезам'.\n"
            "7. `traffic_lights` блок (items: {money, health, love}). Оцени цвета по анализу недели."
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


def get_default_sections(report_type: str, mode: str = "full") -> List[SectionSpec]:
    sections = list(_REPORT_TEMPLATES.get(report_type, _NATAL_MASTER_SECTIONS))
    
    if mode == "short" and report_type == "natal_master":
        # Keep only essential sections for short report
        essential = {
            "executive_summary", "input_frame", "synthesis", 
            "core_triad", "money_realization", "love_intimacy", 
            "final_synthesis"
        }
        sections = [s for s in sections if s.section_id in essential]
        
    return sections
# #END_BLOCK_SECTION_TEMPLATES
