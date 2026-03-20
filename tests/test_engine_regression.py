# ############################################################################
# AI_HEADER: TEST_ENGINE_REGRESSION
# ROLE: Verify time normalization and facts generation logic.
# ############################################################################

import sys
from unittest.mock import MagicMock

# Mock stellium BEFORE importing backend modules
mock_stellium = MagicMock()
sys.modules["stellium"] = mock_stellium
sys.modules["stellium.engines"] = MagicMock()
sys.modules["stellium.engines.houses"] = MagicMock()

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from backend.app.engine_utils import normalize_datetime_input
from backend.app.reporting.markdown_helpers import format_chart_facts

def test_normalize_naive_input():
    """
    User inputs '12:00'. We want to treat it as '12:00 Local'.
    Engine expects naive ISO string 'YYYY-MM-DDTHH:MM:SS'.
    """
    inp = "2000-01-01T12:00:00"
    tz = "Europe/Moscow"
    
    # normalize_datetime_input uses logic:
    # if naive -> replace(tz).strftime(iso) -> returns naive string (Wait?)
    # Let's check implementation again.
    # It returns `dt.strftime("%Y-%m-%dT%H:%M:%S")` which is naive.
    
    # If we pass naive input, it just returns it as is if we don't do anything special?
    # BUT! If we pass tz, it attaches TZ. Then it formats it.
    # The output format is naive string. So it just strips offset?
    # NO. If we do `dt.astimezone(target)`, the hour changes.
    # If we do `dt.replace(tzinfo=target)`, the hour stays.
    
    # Case 1: Naive input. assume_local=True (old) vs False (new).
    # If naive, `if dt.tzinfo is None` -> `dt.replace(tzinfo=target_tz)`. 
    # This logic is SAME for assume_local=True or False.
    
    out = normalize_datetime_input(inp, tz, assume_local=False)
    assert out == "2000-01-01T12:00:00"

def test_normalize_utc_from_db():
    """
    DB returns '09:00+00:00'. We want '12:00 Local'.
    """
    inp = "2000-01-01T09:00:00+00:00" # 12:00 MSK
    tz = "Europe/Moscow"
    
    # assume_local=False -> astimezone -> 12:00+03:00 -> strftime -> 12:00
    out = normalize_datetime_input(inp, tz, assume_local=False)
    assert out == "2000-01-01T12:00:00"

def test_normalize_utc_assume_local_true():
    """
    Legacy/Force behavior: '09:00+00:00' treated as '09:00 Local'.
    """
    inp = "2000-01-01T09:00:00+00:00"
    tz = "Europe/Moscow"
    
    # assume_local=True -> replace -> 09:00+03:00 -> strftime -> 09:00
    out = normalize_datetime_input(inp, tz, assume_local=True)
    assert out == "2000-01-01T09:00:00"

def test_facts_generation():
    """
    Verify format_chart_facts produces readable text.
    """
    chart_data = {
        "positions": [
            {"name": "Sun", "sign": "Aries", "sign_degree": 10.5, "house": 1, "is_retrograde": False},
            {"name": "Moon", "sign": "Taurus", "sign_degree": 5.0, "house": 2, "is_retrograde": False}
        ],
        "houses": [
            {"house": 1, "sign": "Aries", "sign_degree": 0.0},
            {"house": 2, "sign": "Taurus", "sign_degree": 0.0}
        ],
        "aspects": [
            {"p1": "Sun", "p2": "Moon", "type": "Conjunction", "orb": 5.0}
        ],
        "balances": {
            "elements": {"Fire": 50, "Earth": 50},
            "modes": {"Cardinal": 50, "Fixed": 50}
        }
    }
    
    facts = format_chart_facts(chart_data)
    
    assert "Sun: Aries 10°, House 1" in facts
    assert "Moon: Taurus 5°, House 2" in facts
    assert "House 1: Aries 0°" in facts
    assert "Sun Conjunction Moon (orb 5.0°)" in facts
    assert "Elements: Fire=50%" in facts
