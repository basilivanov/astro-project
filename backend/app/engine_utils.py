# ############################################################################
# AI_HEADER: MODULE_ENGINE_UTILS
# ROLE: Shared helpers for StelliumEngine API serialization.
# DEPENDENCIES: stellium_engine.py, stellium.engines.houses.
# GRACE_ANCHORS: [HOUSE_SYSTEMS, SERIALIZATION]
# ############################################################################

from typing import Any, Optional
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    pass # Python < 3.9 fallback if needed

from fastapi import HTTPException
from stellium.engines.houses import EqualHouses, PlacidusHouses, WholeSignHouses

# #START_BLOCK_TIME_UTILS
def normalize_datetime_input(
    dt_input: str,
    tz_str: Optional[str] = None,
    assume_local: bool = False,
) -> str:
    """
    # PURPOSE: Prepare datetime string for Stellium Engine.
    # LOGIC:
    # 1. Parse ISO (handle +/-, Z).
    # 2. If tz_str provided, convert to that timezone (local time).
    #    If assume_local is True, keep wall-clock time and only apply TZ.
    # 3. Return naive ISO string (YYYY-MM-DDTHH:MM:SS) for engine consumption.
    """
    if not dt_input: return ""
    
    try:
        # 1. Parse
        clean_input = dt_input
        if clean_input.endswith("Z"):
            clean_input = clean_input[:-1] + "+00:00"
            
        dt = datetime.fromisoformat(clean_input)
        
        # 2. Convert to target TZ
        if tz_str:
            try:
                target_tz = ZoneInfo(tz_str)
                # If naive, assume it is ALREADY local time in target TZ (Wall clock time)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=target_tz)
                else:
                    if assume_local:
                        dt = dt.replace(tzinfo=target_tz)
                    else:
                        # If aware (e.g. UTC Z), convert to target local
                        dt = dt.astimezone(target_tz)
            except Exception:
                # If TZ invalid, proceed with what we have
                pass
        
        # 3. Return naive ISO string for engine consumption (Stellium expects naive local time)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # Fallback for non-ISO strings or errors
        return dt_input
# #END_BLOCK_TIME_UTILS

# #START_BLOCK_HOUSE_SYSTEMS
EN_RU_SIGNS = {
    "Aries": "Овен",
    "Taurus": "Телец",
    "Gemini": "Близнецы",
    "Cancer": "Рак",
    "Leo": "Лев",
    "Virgo": "Дева",
    "Libra": "Весы",
    "Scorpio": "Скорпион",
    "Sagittarius": "Стрелец",
    "Capricorn": "Козерог",
    "Aquarius": "Водолей",
    "Pisces": "Рыбы"
}

def translate_sign(sign_en: str) -> str:
    return EN_RU_SIGNS.get(sign_en, sign_en)

def resolve_house_system(system_name: Optional[str]):
    """
    # PURPOSE: Convert a string into a house system object.
    # INPUT: system_name (str | None).
    # OUTPUT: House system instance or None for default behavior.
    # CONTEXT: Used to normalize API input.
    """

    if not system_name:
        return None

    normalized = system_name.strip().lower()
    if normalized in {"whole", "wholesign", "whole-sign"}:
        return WholeSignHouses()
    if normalized in {"placidus", "plac"}:
        return PlacidusHouses()
    if normalized in {"equal", "equal-sign"}:
        return EqualHouses()

    raise HTTPException(status_code=400, detail="Unsupported house_system")
# #END_BLOCK_HOUSE_SYSTEMS

def calculate_balances(positions):
    """
    # PURPOSE: Calculate percentage balance of elements and modalities.
    # LOGIC: Assigns weights to planets (Sun/Moon=2, others=1) and aggregates by sign.
    """
    elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    modes = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    
    sign_map = {
        "Aries": ("Fire", "Cardinal"), "Taurus": ("Earth", "Fixed"), 
        "Gemini": ("Air", "Mutable"), "Cancer": ("Water", "Cardinal"),
        "Leo": ("Fire", "Fixed"), "Virgo": ("Earth", "Mutable"),
        "Libra": ("Air", "Cardinal"), "Scorpio": ("Water", "Fixed"),
        "Sagittarius": ("Fire", "Mutable"), "Capricorn": ("Earth", "Cardinal"),
        "Aquarius": ("Air", "Fixed"), "Pisces": ("Water", "Mutable")
    }
    
    major_planets = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
    
    total_weight = 0
    for pos in positions:
        name = pos.get("name")
        sign = pos.get("sign")
        if name in major_planets and sign in sign_map:
            el, md = sign_map[sign]
            weight = 2 if name in ["Sun", "Moon"] else 1
            elements[el] += weight
            modes[md] += weight
            total_weight += weight
            
    if total_weight > 0:
        elements_pct = {k: round((v / total_weight) * 100) for k, v in elements.items()}
        modes_pct = {k: round((v / total_weight) * 100) for k, v in modes.items()}
        return {"elements": elements_pct, "modes": modes_pct}
    return {"elements": {}, "modes": {}}


def get_house_for_pos(longitude: float, cusps: list[float]) -> int:
    """
    # PURPOSE: Find house number (1-12) for a given longitude based on cusps.
    """
    for i in range(12):
        c1 = cusps[i]
        c2 = cusps[(i + 1) % 12]
        if c1 < c2:
            if c1 <= longitude < c2:
                return i + 1
        else: # house crosses 0/360
            if longitude >= c1 or longitude < c2:
                return i + 1
    return 0

def get_sign_data(lon: float):
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    idx = int(lon // 30)
    return signs[idx % 12], lon % 30


POINT_NAME_ALIASES = {
    "Mean Apogee": "Lilith",
}

SIGN_RULER_MAP = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Pluto",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Uranus",
    "Pisces": "Neptune",
}

MAJOR_DISPOSITOR_PLANETS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]


def canonicalize_point_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    return POINT_NAME_ALIASES.get(name, name)


def _serialize_position_entry(
    name: str,
    longitude: float,
    latitude: float,
    sign: str,
    sign_degree: float,
    is_retrograde: bool,
    house: int,
) -> dict[str, Any]:
    key = canonicalize_point_name(name)
    item = {
        "name": name,
        "key": key,
        "longitude": longitude,
        "latitude": latitude,
        "sign": sign,
        "sign_degree": sign_degree,
        "is_retrograde": is_retrograde,
        "house": house,
    }
    if key != name:
        item["raw_name"] = name
    return item


def _build_dispositor_summary(positions: list[dict[str, Any]]) -> dict[str, Any]:
    planet_map: dict[str, dict[str, Any]] = {}
    for position in positions:
        normalized_name = canonicalize_point_name(position.get("name"))
        if not normalized_name:
            continue
        planet_map[normalized_name] = {
            **position,
            "name": normalized_name,
        }

    links = []
    link_map: dict[str, str] = {}
    for planet in MAJOR_DISPOSITOR_PLANETS:
        position = planet_map.get(planet)
        if not position:
            continue
        ruler = SIGN_RULER_MAP.get(position.get("sign"))
        if not ruler:
            continue
        link_map[planet] = ruler
        links.append(
            {
                "planet": planet,
                "sign": position.get("sign"),
                "dispositor": ruler,
            }
        )

    loops = []
    loop_keys = set()
    for planet in MAJOR_DISPOSITOR_PLANETS:
        if planet not in link_map:
            continue

        chain = []
        current = planet
        while current not in chain and current in link_map:
            chain.append(current)
            current = link_map[current]

        if current not in chain:
            continue

        loop = chain[chain.index(current):]
        loop_key = tuple(loop)
        if loop_key in loop_keys:
            continue
        loop_keys.add(loop_key)
        loop_type = "loop"
        if len(loop) == 1:
            loop_type = "domicile"
        elif len(loop) == 2:
            loop_type = "mutual_reception"
        loops.append(
            {
                "type": loop_type,
                "planets": loop,
            }
        )

    summary_lines = []
    for loop in loops:
        planets = loop.get("planets", [])
        if len(planets) == 1:
            summary_lines.append(f"**{planets[0]}** в Обители (Конечный диспозитор).")
        elif len(planets) == 2:
            summary_lines.append(f"Взаимная рецепция: **{planets[0]} ↔ {planets[1]}**.")
        elif planets:
            names = " -> ".join(planets) + f" -> {planets[0]}"
            summary_lines.append(f"Цепочка: {names}")

    return {
        "version": "dispositor_summary_v1",
        "summary": "\n".join(summary_lines),
        "links": links,
        "loops": loops,
    }


def _normalize_fixed_star_entry(star: Any) -> dict[str, Any]:
    if not isinstance(star, dict):
        name = str(star).strip()
        return {
            "name": name,
            "star": name,
            "point": None,
            "planet": None,
            "raw_point": None,
            "orb": None,
            "star_lon": None,
            "sign": None,
        }

    raw_point = star.get("planet") or star.get("point") or star.get("body") or star.get("target")
    point = canonicalize_point_name(raw_point)
    star_name = str(star.get("name") or star.get("star") or "Fixed star").strip()
    orb = star.get("orb")
    try:
        orb = round(float(orb), 2)
    except (TypeError, ValueError):
        orb = None

    star_lon = star.get("star_lon")
    try:
        star_lon = float(star_lon) if star_lon is not None else None
    except (TypeError, ValueError):
        star_lon = None

    sign = star.get("sign")
    if sign is None and star_lon is not None:
        sign, _ = get_sign_data(star_lon)

    normalized = dict(star)
    normalized.update(
        {
            "name": star_name,
            "star": star_name,
            "point": point,
            "planet": raw_point,
            "raw_point": raw_point,
            "orb": orb,
            "star_lon": star_lon,
            "sign": sign,
        }
    )
    return normalized

def calculate_dispositors(positions):
    """
    # PURPOSE: Calculate dispositor chains and final dispositors.
    """
    return _build_dispositor_summary(positions).get("summary", "")

# #START_BLOCK_SERIALIZATION
def serialize_chart(chart, chart_type: str, fixed_stars=None, aspects=None, patterns=None, extra_points=None):
    """
    # PURPOSE: Convert a Chart object into a JSON-ready structure.
    # INPUT: chart, chart_type, fixed_stars, aspects, patterns, extra_points.
    # OUTPUT: ChartResponse-compatible dict.
    """

    location = chart.location
    house_data = chart.get_houses()
    houses = [
        {
            "house": i + 1,
            "longitude": house_data.cusps[i],
            "sign": house_data.signs[i],
            "sign_degree": house_data.sign_degrees[i],
        }
        for i in range(12)
    ]

    positions = [
        _serialize_position_entry(
            name=pos.name,
            longitude=pos.longitude,
            latitude=pos.latitude,
            sign=pos.sign,
            sign_degree=pos.sign_degree,
            is_retrograde=pos.is_retrograde,
            house=get_house_for_pos(pos.longitude, house_data.cusps),
        )
        for pos in chart.positions
    ]
    
    if extra_points:
        for p in extra_points:
            sign_name, sign_deg = get_sign_data(p["longitude"])
            positions.append(
                _serialize_position_entry(
                    name=p["name"],
                    longitude=p["longitude"],
                    latitude=0.0,
                    sign=sign_name,
                    sign_degree=sign_deg,
                    is_retrograde=False,
                    house=get_house_for_pos(p["longitude"], house_data.cusps),
                )
            )
    
    balances = calculate_balances(positions)
    dispositor_summary = _build_dispositor_summary(positions)
    normalized_fixed_stars = [_normalize_fixed_star_entry(star) for star in (fixed_stars or [])]
    normalized_aspects = []
    for aspect in aspects or []:
        normalized_aspect = dict(aspect)
        normalized_aspect["p1_key"] = canonicalize_point_name(aspect.get("p1"))
        normalized_aspect["p2_key"] = canonicalize_point_name(aspect.get("p2"))
        normalized_aspects.append(normalized_aspect)
    normalized_patterns = []
    for pattern in patterns or []:
        normalized_pattern = dict(pattern)
        normalized_pattern["point_keys"] = [
            canonicalize_point_name(point) for point in pattern.get("points", [])
        ]
        normalized_patterns.append(normalized_pattern)

    return {
        "chart_type": chart_type,
        "name": chart.metadata.get("name") if hasattr(chart, "metadata") else None,
        "datetime_utc": chart.datetime.utc_datetime.isoformat(),
        "datetime_local": chart.datetime.local_datetime.isoformat()
        if chart.datetime.local_datetime
        else None,
        "location": {
            "name": location.name or "",
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": location.timezone or "",
        },
        "house_system": house_data.system,
        "houses": houses,
        "positions": positions,
        "balances": balances,
        "dispositors": dispositor_summary.get("summary", ""),
        "dispositor_summary": dispositor_summary,
        "fixed_stars": normalized_fixed_stars,
        "aspects": normalized_aspects,
        "patterns": normalized_patterns,
    }
# #END_BLOCK_SERIALIZATION
