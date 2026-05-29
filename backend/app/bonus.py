def calculate_bonus(is_partner: bool, amount_paid: float) -> dict:
    if is_partner:
        return {"money": amount_paid * 0.2}
    return {"days": 15}
