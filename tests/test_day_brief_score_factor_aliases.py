from backend.app.services.day_brief import _collect_local_score_factor_ids


def test_collect_local_score_factor_ids_accepts_week_aliases_for_money_and_love():
    factor_refs = [
        {"id": "money-factor", "domain": "work_money", "polarity": "positive"},
        {"id": "love-factor", "domain": "relationships", "polarity": "positive"},
    ]
    factor_lookup = {
        "money-factor": {"label": "Юпитер", "explanation_human": "денежный сигнал"},
        "love-factor": {"label": "Венера", "explanation_human": "контакт и близость"},
    }

    money_item = {
        "key": "money",
        "title": "Работа и деньги",
        "advice": "Проверьте цифры",
        "details": {"why_title": "Почему", "why_text": "важны договорённости"},
    }
    love_item = {
        "key": "love",
        "title": "Чувства",
        "advice": "Говорите мягче",
        "details": {"why_title": "Почему", "why_text": "важен контакт"},
    }

    assert _collect_local_score_factor_ids(
        factor_refs,
        domain="money",
        factor_lookup=factor_lookup,
        score_item=money_item,
        explainability_factors=[{"id": "money-factor", "domain": "work_money"}],
    ) == ["money-factor"]
    assert _collect_local_score_factor_ids(
        factor_refs,
        domain="love",
        factor_lookup=factor_lookup,
        score_item=love_item,
        explainability_factors=[{"id": "love-factor", "domain": "relationships"}],
    ) == ["love-factor"]
