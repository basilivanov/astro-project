# ############################################################################
# AI_HEADER: MODULE_HORARY_ADAPTERS
# ROLE: Configuration registry for Horary Astrology contexts (A1-A15).
# CONTEXT: Used to inject domain-specific rules into LLM prompts.
# ############################################################################

HORARY_ADAPTERS = {
    "default": {
        "id": "default",
        "name": "Универсальный вопрос",
        "houses": {"querent": 1, "quesited": 7},
        "outcomes": ["Положительный исход", "Отрицательный исход"],
        "timing": "degrees_to_time",
        "keywords": ["событие", "результат"],
        "risks": ["Неверная интерпретация", "Скрытые факторы"]
    },
    
    # A1
    "relationships_general": {
        "id": "relationships_general",
        "name": "Отношения / Любовь",
        "houses": {"querent": 1, "partner": 7, "romance": 5},
        "outcomes": ["Сближение / Встреча", "Разрыв / Холод", "Статус-кво"],
        "timing": "fast (days/weeks)",
        "special_rules": [
            "5 дом - это влюбленность/секс, 7 дом - это партнерство/брак.",
            "Смотри рецепции: кто кого любит (по обители/экзальтации).",
            "Смотри Луну: передает ли она свет?"
        ]
    },

    # A2
    "career_job": {
        "id": "career_job",
        "name": "Работа / Карьера",
        "houses": {"querent": 1, "job": 10, "duty": 6, "money": 2},
        "outcomes": ["Получение работы/Повышение", "Отказ/Увольнение", "Без изменений"],
        "timing": "medium (weeks/months)",
        "special_rules": [
            "L10 - это Начальник или Сама Работа (Должность).",
            "L6 - это условия труда и рутина.",
            "L2 - зарплата."
        ]
    },

    # A3
    "money_personal": {
        "id": "money_personal",
        "name": "Финансы / Покупки",
        "houses": {"querent": 1, "my_money": 2, "other_money": 8, "seller": 7},
        "outcomes": ["Прибыль / Удачная покупка", "Убыток / Плохой товар", "Сделка не состоится"],
        "timing": "depends_on_context",
        "special_rules": [
            "L2 - твои деньги.",
            "L8 - деньги других людей (кредиты, долги).",
            "Луна часто показывает сам товар."
        ]
    },

    # A13 (Critical for current user request)
    "conflict_legal_admin": {
        "id": "conflict_legal_admin",
        "name": "Суд / Конфликт / Штраф",
        "houses": {
            "querent": 1, 
            "opponent": 7, 
            "judge": 10, 
            "law": 9,
            "verdict": 4, # End of matter
            "wallet": 2,
            "fine": 8
        },
        "outcomes": [
            "Победа Кверента (оправдание)",
            "Компромисс / Штраф", 
            "Поражение (лишение прав/свободы)"
        ],
        "timing": "court_dates",
        "special_rules": [
            "L10 (Судья) - ключевая фигура. Его рецепции к L1 и L7 показывают, на чьей он стороне.",
            "L4 - 'конец дела'. Какой там управитель? Благодетель или Вредитель?",
            "L9 - закон/адвокат. ",
            "Сходящийся квадрат часто означает 'Да, но с проблемой' (например, права вернут, но через нервы/штраф)."
        ]
    }
}

def detect_adapter(text: str) -> str:
    """
    Simple heuristic to guess adapter from question text.
    In production this should be an LLM classifier.
    """
    t = text.lower()
    if any(w in t for w in ["суд", "штраф", "прав", "гаи", "полици", "закон", "иск"]):
        return "conflict_legal_admin"
    if any(w in t for w in ["люб", "отношен", "муж", "жен", "парн", "девуш", "чувств", "встреч"]):
        return "relationships_general"
    if any(w in t for w in ["работ", "карьер", "начальн", "бизнес", "проект", "увольн", "найм"]):
        return "career_job"
    if any(w in t for w in ["деньг", "купит", "продат", "долг", "кредит"]):
        return "money_personal"
    
    return "default"
