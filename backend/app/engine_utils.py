# ############################################################################
# AI_HEADER: MODULE_ENGINE_UTILS
# ROLE: Shared helpers for StelliumEngine API serialization.
# DEPENDENCIES: stellium_engine.py, stellium.engines.houses.
# GRACE_ANCHORS: [HOUSE_SYSTEMS, SERIALIZATION]
# ############################################################################

from typing import Optional

from fastapi import HTTPException
from stellium.engines.houses import EqualHouses, PlacidusHouses, WholeSignHouses

# #START_BLOCK_HOUSE_SYSTEMS
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

# #START_BLOCK_SERIALIZATION
def serialize_chart(chart, chart_type: str, fixed_stars=None):
    """
    # PURPOSE: Convert a Chart object into a JSON-ready structure.
    # INPUT: chart (CalculatedChart), chart_type (str), fixed_stars (list|None).
    # OUTPUT: ChartResponse-compatible dict.
    # CONTEXT: Shared helper for all endpoints and workflows.
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
        {
            "name": pos.name,
            "longitude": pos.longitude,
            "latitude": pos.latitude,
            "sign": pos.sign,
            "sign_degree": pos.sign_degree,
            "is_retrograde": pos.is_retrograde,
        }
        for pos in chart.positions
    ]

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
        "fixed_stars": fixed_stars or [],
    }
# #END_BLOCK_SERIALIZATION
