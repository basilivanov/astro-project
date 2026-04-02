from backend.app.services.day_brief import _build_supporting_factor_entries


def test_build_supporting_factor_entries_filters_semantic_and_traffic_leakage():
    factor_lookup = {
        "traffic:money": {
            "id": "traffic:money",
            "label": "Рабочий контекст",
            "domain": "money",
            "explanation_human": "Закрой один документ",
            "explanation_astro": "Светофор money: red",
            "impact": "high",
        },
        "semantic:money_admin": {
            "id": "semantic:money_admin",
            "label": "Рабочий контекст",
            "domain": "money",
            "explanation_human": "Закрой один документ",
            "explanation_astro": "личное желание спорит за центр дня",
            "impact": "medium",
        },
        "fast:Venus:MC:Секстиль (60°)": {
            "id": "fast:Venus:MC:Секстиль (60°)",
            "label": "Венера Секстиль (60°) MC",
            "domain": "money",
            "category": "fast_transits",
            "explanation_human": "Венера Секстиль (60°) MC",
            "explanation_astro": None,
            "impact": "medium",
        },
    }

    entries = _build_supporting_factor_entries(
        ["traffic:money", "semantic:money_admin", "fast:Venus:MC:Секстиль (60°)"],
        factor_lookup,
        limit=3,
    )

    assert len(entries) == 1
    assert entries[0]["id"] == "fast:Venus:MC:Секстиль (60°)"
    assert entries[0]["label"] == "Венера Секстиль (60°) MC"
