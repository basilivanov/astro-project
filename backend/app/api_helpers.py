# START_MODULE_CONTRACT: M-API-GATEWAY-HELPERS
# purpose: Own pure API gateway serialization and formatting helpers extracted from backend.app.main.
# owns:
#   - backend/app/api_helpers.py
# inputs:
#   - chart objects, timestamps, report labels, birth-date strings, and moon phase angles
# outputs:
#   - JSON-ready chart data, ISO timestamps, report labels, parsed datetimes, and moon labels
# dependencies:
#   - backend.app.engine_utils for existing chart serialization wrappers
# invariants:
#   - helper return values and fallback behavior remain identical to pre-extraction main.py implementations
#   - backend.app.main re-exports helper names for compatibility
# non_goals:
#   - database access, endpoint movement, or report workflow lifecycle changes
# END_MODULE_CONTRACT: M-API-GATEWAY-HELPERS

# START_MODULE_MAP: M-API-GATEWAY-HELPERS
# public_entrypoints:
#   - resolve_house_system
#   - serialize_chart
#   - format_datetime
#   - transliterate_ru_to_en
#   - extract_birth_year
#   - format_report_title
#   - format_report_subtitle
#   - parse_birth_datetime
#   - get_moon_phase_emoji
#   - get_phase_name
# semantic_blocks:
#   - API_HELPER_SERIALIZATION: chart and datetime helpers
#   - API_HELPER_REPORT_FORMATTING: report title/date formatting helpers
#   - API_HELPER_FEED_FORMATTING: moon phase label helpers
# owned_tests:
#   - tests/test_api_contract_wave1.py
#   - tests/test_report_contract.py
# adjacent_modules:
#   - backend/app/main.py
# END_MODULE_MAP: M-API-GATEWAY-HELPERS

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from . import engine_utils

# START_BLOCK: API_HELPER_SERIALIZATION
# START_CONTRACT: FN-RESOLVE-HOUSE-SYSTEM
def resolve_house_system(system_name: Optional[str]):
    """
    # PURPOSE: Convert a string into a house system object.
    # INPUT: system_name (str | None).
    # OUTPUT: House system instance or None for default behavior.
    # CONTEXT: Wrapper over engine_utils.
    """

    return engine_utils.resolve_house_system(system_name)
# END_CONTRACT: FN-RESOLVE-HOUSE-SYSTEM


# START_CONTRACT: FN-SERIALIZE-CHART
def serialize_chart(chart, chart_type: str, fixed_stars=None):
    """
    # PURPOSE: Convert a Chart object into a JSON-ready structure.
    # INPUT: chart (CalculatedChart), chart_type (str), fixed_stars (list|None).
    # OUTPUT: ChartResponse-compatible dict.
    # CONTEXT: Wrapper over engine_utils.
    """

    return engine_utils.serialize_chart(chart, chart_type, fixed_stars=fixed_stars)
# END_CONTRACT: FN-SERIALIZE-CHART


# START_CONTRACT: FN-FORMAT-DATETIME
def format_datetime(value: Optional[datetime]) -> Optional[str]:
    """
    # PURPOSE: Convert datetime values into ISO 8601 strings.
    # INPUT: datetime or None.
    # OUTPUT: ISO 8601 string or None.
    # CONTEXT: Used in admin API responses.
    """

    return value.isoformat() if value else None
# END_CONTRACT: FN-FORMAT-DATETIME

# END_BLOCK: API_HELPER_SERIALIZATION

# START_BLOCK: API_HELPER_REPORT_FORMATTING
# START_CONTRACT: FN-TRANSLITERATE-RU-TO-EN
def transliterate_ru_to_en(value: str) -> str:
    """
    # PURPOSE: Transliterate Russian Cyrillic to Latin for PDF headers.
    # INPUT: raw string.
    # OUTPUT: Latin transliteration string.
    # CONTEXT: Used in PDF export metadata.
    """

    mapping = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
    result = []
    for char in value:
        lower = char.lower()
        if lower in mapping:
            mapped = mapping[lower]
            result.append(mapped.capitalize() if char.isupper() else mapped)
        else:
            result.append(char)
    return "".join(result)
# END_CONTRACT: FN-TRANSLITERATE-RU-TO-EN


# START_CONTRACT: FN-EXTRACT-BIRTH-YEAR
def extract_birth_year(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    for part in value.split("-"):
        if len(part) == 4 and part.isdigit():
            return part
        break
    return value[:4] if len(value) >= 4 else None
# END_CONTRACT: FN-EXTRACT-BIRTH-YEAR


# START_CONTRACT: FN-FORMAT-REPORT-TITLE
def format_report_title(report_type: str) -> str:
    if report_type == "natal_master":
        return "Natal Master · Natal Chart"
    return report_type.replace("_", " ").title()
# END_CONTRACT: FN-FORMAT-REPORT-TITLE


# START_CONTRACT: FN-FORMAT-REPORT-SUBTITLE
def format_report_subtitle(client_name: str) -> str:
    return client_name or "Natal Report"
# END_CONTRACT: FN-FORMAT-REPORT-SUBTITLE


# START_CONTRACT: FN-PARSE-BIRTH-DATETIME
def parse_birth_datetime(value: Optional[str], tz_str: Optional[str] = None) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo:
            return parsed
            
        if tz_str:
            try:
                return parsed.replace(tzinfo=ZoneInfo(tz_str))
            except Exception:
                pass
            
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
# END_CONTRACT: FN-PARSE-BIRTH-DATETIME

# END_BLOCK: API_HELPER_REPORT_FORMATTING

# START_BLOCK: API_HELPER_FEED_FORMATTING
# START_CONTRACT: FN-GET-MOON-PHASE-EMOJI
def get_moon_phase_emoji(phase_angle: float) -> str:
    # 0=New, 90=First Quarter, 180=Full, 270=Last Quarter
    if phase_angle < 45: return "🌑" # New
    if phase_angle < 90: return "🌒" # Waxing Crescent
    if phase_angle < 135: return "🌓" # First Quarter
    if phase_angle < 180: return "🌔" # Waxing Gibbous
    if phase_angle < 225: return "🌕" # Full
    if phase_angle < 270: return "🌖" # Waning Gibbous
    if phase_angle < 315: return "🌗" # Last Quarter
    return "🌘" # Waning Crescent
# END_CONTRACT: FN-GET-MOON-PHASE-EMOJI


# START_CONTRACT: FN-GET-PHASE-NAME
def get_phase_name(phase_angle: float) -> str:
    if phase_angle < 10: return "Новолуние"
    if phase_angle < 90: return "Растущая Луна"
    if phase_angle < 100: return "Первая четверть"
    if phase_angle < 170: return "Растущая Луна"
    if phase_angle < 190: return "Полнолуние"
    if phase_angle < 270: return "Убывающая Луна"
    if phase_angle < 280: return "Последняя четверть"
    return "Убывающая Луна"
# END_CONTRACT: FN-GET-PHASE-NAME
# END_BLOCK: API_HELPER_FEED_FORMATTING
