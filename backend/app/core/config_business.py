# ############################################################################
# AI_HEADER: MODULE_BUSINESS_CONFIG
# ROLE: Single source of truth for pricing, packs, and limits.
# ############################################################################

HORARY_PACKS = {
    "pack_1": {
        "credits": 1,
        "price": 99.0,
        "label": "1 вопрос",
        "description": "Быстрый ответ",
        "discount_percent": 0
    },
    "pack_3": {
        "credits": 3,
        "price": 209.0,
        "label": "3 вопроса",
        "description": "Со скидкой 30%",
        "discount_percent": 30
    },
    "pack_5": {
        "credits": 5,
        "price": 349.0,
        "label": "5 вопросов",
        "description": "Выбор профи",
        "discount_percent": 30
    }
}

SUBSCRIPTION_PRICE = 299.0
SUBSCRIPTION_DAYS = 30
TRIAL_DAYS = 14
REFERRAL_DAYS = 14

REPORT_PRICES = {
    "natal_master": 199.0,
    "year_forecast": 499.0,
    "month_forecast": 199.0,
    "week_forecast": 199.0,
    "horary_answer": 199.0,
    "solar_return": 199.0,
    "synastry": 199.0
}
