"""Built-in validation predicate functions."""

from __future__ import annotations

import re
from numbers import Real
from typing import Any
from urllib.parse import urlparse


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def required(value: Any) -> bool:
    """Return True when a value is present and non-empty."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return bool(value)
    return True


def type_check(value: Any, expected_type: type | tuple[type, ...]) -> bool:
    """Return True when value is an instance of expected_type."""
    if isinstance(value, bool) and _expects_number_without_bool(expected_type):
        return False
    return isinstance(value, expected_type)


def min_length(value: str, length: int) -> bool:
    """Return True when a string has at least length characters."""
    return isinstance(value, str) and len(value) >= length


def max_length(value: str, length: int) -> bool:
    """Return True when a string has no more than length characters."""
    return isinstance(value, str) and len(value) <= length


def min_value(value: int | float, minimum: int | float) -> bool:
    """Return True when a numeric value is greater than or equal to minimum."""
    return _is_number(value) and value >= minimum


def max_value(value: int | float, maximum: int | float) -> bool:
    """Return True when a numeric value is less than or equal to maximum."""
    return _is_number(value) and value <= maximum


def regex_match(value: str, pattern: str) -> bool:
    """Return True when a string fully matches the regex pattern."""
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def email_format(value: str) -> bool:
    """Return True when a string has a practical email address format."""
    return isinstance(value, str) and EMAIL_PATTERN.fullmatch(value) is not None


def url_format(value: str) -> bool:
    """Return True when a string is an absolute HTTP or HTTPS URL."""
    if not isinstance(value, str):
        return False

    parsed_url = urlparse(value)
    return parsed_url.scheme in {"http", "https"} and bool(parsed_url.netloc)


def in_choices(value: Any, choices: list) -> bool:
    """Return True when value is one of the allowed choices."""
    return value in choices


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _expects_number_without_bool(expected_type: type | tuple[type, ...]) -> bool:
    if isinstance(expected_type, tuple):
        return any(type_item in {int, float, Real} for type_item in expected_type)
    return expected_type in {int, float, Real}
