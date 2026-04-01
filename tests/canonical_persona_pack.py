import json
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any


_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "docs" / "regression_fixtures" / "canonical_astrology_fixture_manifest.v1.json"


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    return json.loads(_MANIFEST_PATH.read_text())


@lru_cache(maxsize=1)
def load_persona_pack_v1() -> dict[str, dict[str, Any]]:
    manifest = load_manifest()
    fixtures = manifest.get("fixtures") or []
    return {fixture["id"]: fixture for fixture in fixtures if fixture.get("id")}


def fixture_ids() -> list[str]:
    return list(load_persona_pack_v1().keys())


def get_fixture(fixture_id: str) -> dict[str, Any]:
    pack = load_persona_pack_v1()
    if fixture_id not in pack:
        raise KeyError(f"unknown canonical fixture id: {fixture_id}")
    return pack[fixture_id]


def payload_from_fixture(fixture_id: str, **overrides: Any) -> SimpleNamespace:
    fixture = get_fixture(fixture_id)
    canonical_inputs = dict(fixture.get("canonical_inputs") or {})
    birth_date = canonical_inputs.get("birth_date_local")
    base = dict(
        client_name=canonical_inputs.get("client_name") or fixture.get("persona_name") or fixture_id,
        birth_date=birth_date,
        birth_location=canonical_inputs.get("birth_location"),
        birth_lat=canonical_inputs.get("birth_lat"),
        birth_lon=canonical_inputs.get("birth_lon"),
        birth_timezone=canonical_inputs.get("birth_timezone"),
        birth_time_known=canonical_inputs.get("birth_time_known", True),
        report_type=(canonical_inputs.get("report_types") or ["natal_master"])[0],
        house_system=canonical_inputs.get("house_system_default", "placidus"),
        include_fixed_stars=canonical_inputs.get("include_fixed_stars_default", False),
        fixed_star_orb=1.0,
        client_note="",
        report_id=f"r-{fixture_id.lower()}",
        birth_place_id=None,
        partner_name=None,
        partner_birth_date=None,
        partner_birth_timezone=None,
        partner_birth_location=None,
        partner_birth_lat=None,
        partner_birth_lon=None,
        partner_birth_place_id=None,
        solar_current_location=None,
        solar_current_lat=None,
        solar_current_lon=None,
        solar_current_timezone=None,
        solar_current_place_id=None,
        solar_next_location=None,
        solar_next_lat=None,
        solar_next_lon=None,
        solar_next_timezone=None,
        solar_next_place_id=None,
        canonical_fixture_id=fixture_id,
        canonical_persona_pack="persona_pack_v1",
    )
    base.update(overrides)
    return SimpleNamespace(**base)
