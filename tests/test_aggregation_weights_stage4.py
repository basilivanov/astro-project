from backend.app.services.aggregation_weights import apply_weighted_factors
from backend.app.services.personal_susceptibility import attach_susceptibility, build_susceptibility_profile
from backend.app.models import User


def test_apply_weighted_factors_v2_exposes_reliability_support():
    factors = [
        {
            "id": "fast-1",
            "category": "fast_transits",
            "family": "fast_transits",
            "label": "Fast",
            "weight": 1.0,
            "confidence": 0.8,
            "rarity": "rare",
            "timing_precision": "exact",
            "supporting_factors": ["orb<tight"],
        },
        {
            "id": "slow-1",
            "category": "slow_background",
            "family": "slow_background",
            "label": "Slow",
            "weight": 0.8,
            "confidence": 0.7,
        },
    ]
    weighted = apply_weighted_factors("day_brief", factors, top_n=2)
    assert weighted["weight_profile_version"] == "v2"
    assert len(weighted["reliability_support"]) == 2
    assert weighted["top_factors"][0]["support_trace"]["timing_precision"] in {"exact", "day"}


def test_susceptibility_profile_attaches_deterministic_defaults():
    user = User(telegram_id=777, susceptibility_profile={"version": "v1", "domains": {"money": 1.1}, "categories": {"fast_transits": 1.05}})
    profile = build_susceptibility_profile(user)
    enriched = attach_susceptibility([
        {"id": "f1", "domain": "money", "category": "fast_transits", "metadata": {}},
    ], profile=profile)
    assert profile.source == "user_profile"
    assert enriched[0]["susceptibility_multiplier"] > 1.0
    assert enriched[0]["metadata"]["susceptibility_profile_version"] == "v1"
