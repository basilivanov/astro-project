"""Tests for backend date utility helpers."""

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.date_utils import format_iso_date, get_current_utc, parse_iso_date


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            datetime(2026, 5, 28, 10, 30, 45),
            "2026-05-28T10:30:45",
        ),
        (
            datetime(2026, 5, 28, 10, 30, 45, 123456, tzinfo=timezone.utc),
            "2026-05-28T10:30:45.123456+00:00",
        ),
        (
            datetime(2026, 5, 28, 13, 30, 45, tzinfo=timezone(timedelta(hours=3))),
            "2026-05-28T13:30:45+03:00",
        ),
    ],
)
def test_format_iso_date_handles_datetime_variants(value, expected):
    assert format_iso_date(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "2026-05-28T10:30:45",
            datetime(2026, 5, 28, 10, 30, 45),
        ),
        (
            "2026-05-28T10:30:45.123456+00:00",
            datetime(2026, 5, 28, 10, 30, 45, 123456, tzinfo=timezone.utc),
        ),
        (
            "2026-05-28T10:30:45Z",
            datetime(2026, 5, 28, 10, 30, 45, tzinfo=timezone.utc),
        ),
    ],
)
def test_parse_iso_date_handles_valid_iso_strings(value, expected):
    assert parse_iso_date(value) == expected


@pytest.mark.parametrize("value", ["", "not-a-date", "2026-13-01T00:00:00"])
def test_parse_iso_date_rejects_invalid_strings(value):
    with pytest.raises(ValueError):
        parse_iso_date(value)


def test_get_current_utc_returns_utc_timezone():
    current = get_current_utc()

    assert current.tzinfo is timezone.utc
    assert current.utcoffset() == timedelta(0)
