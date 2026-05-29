from app.bonus import calculate_bonus

def test_calculate_bonus_partner():
    assert calculate_bonus(True, 100.0) == {"money": 20.0}

def test_calculate_bonus_non_partner():
    assert calculate_bonus(False, 100.0) == {"days": 15}
