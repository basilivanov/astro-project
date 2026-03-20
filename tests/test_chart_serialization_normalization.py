import os
import sys
from datetime import datetime, timezone

sys.path.append(os.getcwd())

from backend.app import engine_utils
from backend.app.services.report_workflow import (
    _build_dispositor_office_insight_pack,
    _build_section_chart_pack,
)


SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


class _DummyPosition:
    def __init__(self, name, longitude, sign, sign_degree, latitude=0.0, is_retrograde=False):
        self.name = name
        self.longitude = longitude
        self.latitude = latitude
        self.sign = sign
        self.sign_degree = sign_degree
        self.is_retrograde = is_retrograde


class _DummyLocation:
    name = "Test City"
    latitude = 55.75
    longitude = 37.61
    timezone = "Europe/Moscow"


class _DummyDateTime:
    utc_datetime = datetime(1990, 1, 1, 9, 0, tzinfo=timezone.utc)
    local_datetime = datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc)


class _DummyHouses:
    system = "Placidus"
    cusps = [index * 30.0 for index in range(12)]
    signs = SIGNS
    sign_degrees = [0.0] * 12


class _DummyChart:
    metadata = {"name": "Test User"}
    location = _DummyLocation()
    datetime = _DummyDateTime()

    def __init__(self):
        self.positions = [
            _DummyPosition("Sun", 280.0, "Capricorn", 10.0),
            _DummyPosition("Saturn", 285.0, "Capricorn", 15.0),
            _DummyPosition("Mean Apogee", 43.5, "Taurus", 13.5),
        ]

    def get_houses(self):
        return _DummyHouses()


def test_serialize_chart_adds_normalized_point_and_fixed_star_fields():
    chart = _DummyChart()

    result = engine_utils.serialize_chart(
        chart,
        chart_type="natal",
        fixed_stars=[
            {
                "star": "Algol",
                "planet": "Mean Apogee",
                "orb": 0.49,
                "star_lon": 33.1,
            }
        ],
        aspects=[
            {
                "p1": "Mean Apogee",
                "p2": "Sun",
                "type": "conjunction",
                "orb": 0.8,
            }
        ],
        patterns=[
            {
                "type": "Kite",
                "points": ["Mean Apogee", "Sun"],
            }
        ],
    )

    lilith = next(item for item in result["positions"] if item["name"] == "Mean Apogee")
    assert lilith["key"] == "Lilith"
    assert lilith["raw_name"] == "Mean Apogee"

    fixed_star = result["fixed_stars"][0]
    assert fixed_star["name"] == "Algol"
    assert fixed_star["point"] == "Lilith"
    assert fixed_star["raw_point"] == "Mean Apogee"
    assert fixed_star["sign"] == "Taurus"

    assert result["aspects"][0]["p1_key"] == "Lilith"
    assert result["patterns"][0]["point_keys"] == ["Lilith", "Sun"]

    summary = result["dispositor_summary"]
    assert summary["version"] == "dispositor_summary_v1"
    assert any(link["planet"] == "Sun" and link["dispositor"] == "Saturn" for link in summary["links"])
    assert summary["summary"] == result["dispositors"]


def test_section_chart_pack_prefers_upstream_normalized_keys():
    chart_data = {
        "house_system": "Placidus",
        "datetime_utc": "1990-01-01T09:00:00+00:00",
        "datetime_local": "1990-01-01T12:00:00+03:00",
        "location": {"name": "Test City", "latitude": 55.75, "longitude": 37.61, "timezone": "Europe/Moscow"},
        "positions": [
            {
                "name": "Mean Apogee",
                "key": "Lilith",
                "raw_name": "Mean Apogee",
                "longitude": 43.5,
                "latitude": 0.0,
                "sign": "Taurus",
                "sign_degree": 13.5,
                "is_retrograde": False,
                "house": 2,
            }
        ],
        "houses": [],
        "aspects": [
            {
                "p1": "Mean Apogee",
                "p1_key": "Lilith",
                "p2": "Sun",
                "p2_key": "Sun",
                "type": "conjunction",
                "orb": 0.8,
            }
        ],
        "patterns": [
            {
                "type": "Kite",
                "points": ["Mean Apogee", "Sun"],
                "point_keys": ["Lilith", "Sun"],
            }
        ],
        "dispositor_summary": {
            "version": "dispositor_summary_v1",
            "summary": "**Saturn** в Обители (Конечный диспозитор).",
            "links": [],
            "loops": [{"type": "domicile", "planets": ["Saturn"]}],
        },
    }

    pack = _build_section_chart_pack(
        {
            "positions": ["Lilith"],
            "aspect_points": ["Lilith"],
            "aspect_limit": 3,
            "include_patterns": True,
        },
        chart_data,
    )

    assert pack["positions"][0]["name"] == "Lilith"
    assert pack["positions"][0]["key"] == "Lilith"
    assert pack["aspects"][0]["p1"] == "Lilith"
    assert pack["patterns"][0]["points"][0] == "Lilith"


def test_dispositor_insight_pack_prefers_structured_summary():
    chart_data = {
        "positions": [
            {"name": "Sun", "key": "Sun", "sign": "Capricorn", "house": 10},
            {"name": "Saturn", "key": "Saturn", "sign": "Capricorn", "house": 10},
        ],
        "dispositors": "  legacy text with   uneven spacing  ",
        "dispositor_summary": {
            "version": "dispositor_summary_v1",
            "summary": "**Saturn** в Обители (Конечный диспозитор).",
            "links": [{"planet": "Sun", "sign": "Capricorn", "dispositor": "Saturn"}],
            "loops": [{"type": "domicile", "planets": ["Saturn"]}],
        },
    }
    position_lookup = {
        "Sun": {"p": "Sun", "s": "Capricorn", "h": 10, "r": False},
        "Saturn": {"p": "Saturn", "s": "Capricorn", "h": 10, "r": False},
    }

    insight_pack = _build_dispositor_office_insight_pack(
        facts={},
        chart_data=chart_data,
        position_lookup=position_lookup,
        house_lookup={},
    )

    assert insight_pack["engine_summary"] == "**Saturn** в Обители (Конечный диспозитор)."
