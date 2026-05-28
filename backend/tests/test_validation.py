"""Tests for structured data validation helpers."""

from __future__ import annotations

import pytest

from app.validation.errors import ValidationResult
from app.validation.schema import Field, Schema
from app.validation.validators import (
    email_format,
    in_choices,
    max_length,
    max_value,
    min_length,
    min_value,
    regex_match,
    required,
    type_check,
    url_format,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, False),
        ("", False),
        ("   ", False),
        ([], False),
        ({}, False),
        (0, True),
        (False, True),
        ("value", True),
    ],
)
def test_required_detects_missing_or_empty_values(value, expected):
    assert required(value) is expected


def test_type_check_validates_expected_types():
    assert type_check("abc", str)
    assert type_check(12, int)
    assert type_check(12.5, (int, float))
    assert not type_check(True, int)
    assert not type_check("12", int)


def test_length_validators_check_string_bounds():
    assert min_length("abcd", 3)
    assert not min_length("ab", 3)
    assert max_length("abcd", 4)
    assert not max_length("abcde", 4)
    assert not min_length(["a", "b"], 2)


def test_numeric_validators_check_value_bounds():
    assert min_value(10, 10)
    assert min_value(11.5, 10)
    assert not min_value(9, 10)
    assert max_value(10, 10)
    assert max_value(9.5, 10)
    assert not max_value(11, 10)
    assert not min_value(True, 0)


def test_regex_match_requires_full_match():
    assert regex_match("ABC-123", r"[A-Z]{3}-\d{3}")
    assert not regex_match("ABC-123-extra", r"[A-Z]{3}-\d{3}")
    assert not regex_match(123, r"\d+")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("person@example.com", True),
        ("person.name+tag@example.co.uk", True),
        ("person@", False),
        ("person@example", False),
        (None, False),
    ],
)
def test_email_format_validates_practical_email_shape(value, expected):
    assert email_format(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://example.com/path", True),
        ("http://localhost:8000", True),
        ("ftp://example.com", False),
        ("example.com/path", False),
        (None, False),
    ],
)
def test_url_format_requires_absolute_http_url(value, expected):
    assert url_format(value) is expected


def test_in_choices_checks_allowed_values():
    assert in_choices("draft", ["draft", "published"])
    assert not in_choices("archived", ["draft", "published"])


def test_validation_result_add_error_marks_invalid_and_preserves_details():
    result = ValidationResult()

    result.add_error("email", "Invalid email", "bad")

    assert not result.valid
    assert len(result.errors) == 1
    assert result.errors[0].field == "email"
    assert result.errors[0].message == "Invalid email"
    assert "email: Invalid email" in str(result.errors[0])


def test_schema_accepts_valid_data():
    schema = Schema(
        [
            Field("username", field_type=str, validators=[(min_length, {"length": 3})]),
            Field("age", field_type=int, validators=[(min_value, {"minimum": 18})]),
            Field("email", field_type=str, validators=[(email_format, {})]),
        ]
    )

    result = schema.validate(
        {"username": "grace", "age": 32, "email": "grace@example.com"}
    )

    assert result.valid
    assert result.errors == []


def test_schema_collects_multiple_errors_without_short_circuiting():
    schema = Schema(
        [
            Field("username", field_type=str, validators=[(min_length, {"length": 3})]),
            Field("age", field_type=int, validators=[(min_value, {"minimum": 18})]),
            Field("email", field_type=str, validators=[(email_format, {})]),
        ]
    )

    result = schema.validate({"username": "ab", "age": 16, "email": "invalid"})

    assert not result.valid
    assert [error.field for error in result.errors] == ["username", "age", "email"]
    assert all("Failed validator" in error.message for error in result.errors)


def test_schema_reports_missing_required_fields():
    schema = Schema([Field("username", required=True, field_type=str)])

    result = schema.validate({})

    assert not result.valid
    assert len(result.errors) == 1
    assert result.errors[0].field == "username"
    assert result.errors[0].message == "Field is required"


def test_schema_reports_empty_required_field():
    schema = Schema([Field("username", required=True, field_type=str)])

    result = schema.validate({"username": "   "})

    assert not result.valid
    assert result.errors[0].message == "Field is required and cannot be empty"


def test_schema_reports_type_errors_and_still_runs_validators():
    schema = Schema(
        [
            Field(
                "username",
                field_type=str,
                validators=[(min_length, {"length": 3})],
            )
        ]
    )

    result = schema.validate({"username": 12})

    assert not result.valid
    assert len(result.errors) == 2
    assert result.errors[0].message == "Expected type str"
    assert result.errors[1].message == "Failed validator min_length with length=3"


def test_optional_missing_field_is_valid():
    schema = Schema([Field("nickname", required=False, field_type=str)])

    result = schema.validate({})

    assert result.valid
    assert result.errors == []


def test_default_value_is_validated_when_field_is_missing():
    schema = Schema(
        [
            Field(
                "role",
                required=True,
                field_type=str,
                validators=[(in_choices, {"choices": ["user", "admin"]})],
                default="user",
            )
        ]
    )

    result = schema.validate({})

    assert result.valid
    assert result.errors == []


def test_invalid_default_value_reports_error():
    schema = Schema(
        [
            Field(
                "role",
                required=True,
                field_type=str,
                validators=[(in_choices, {"choices": ["user", "admin"]})],
                default="owner",
            )
        ]
    )

    result = schema.validate({})

    assert not result.valid
    assert result.errors[0].field == "role"
    assert "choices" in result.errors[0].message


def test_custom_validator_integration():
    def starts_with_prefix(value, prefix):
        return isinstance(value, str) and value.startswith(prefix)

    schema = Schema(
        [
            Field(
                "report_id",
                field_type=str,
                validators=[(starts_with_prefix, {"prefix": "rpt_"})],
            )
        ]
    )

    result = schema.validate({"report_id": "bad_123"})

    assert not result.valid
    assert result.errors[0].message == "Failed validator starts_with_prefix with prefix='rpt_'"


def test_validator_exceptions_are_reported_as_validation_errors():
    def unsafe_validator(value):
        if value == "boom":
            raise ValueError("bad value")
        return True

    schema = Schema([Field("code", field_type=str, validators=[(unsafe_validator, {})])])

    result = schema.validate({"code": "boom"})

    assert not result.valid
    assert result.errors[0].message == "Validator unsafe_validator failed: bad value"


def test_add_field_and_get_field_manage_schema_fields():
    schema = Schema([])
    schema.add_field(Field("email", field_type=str, validators=[(email_format, {})]))

    field = schema.get_field("email")

    assert field is not None
    assert field.name == "email"
    assert schema.get_field("missing") is None


def test_schema_rejects_non_dictionary_root_data():
    schema = Schema([Field("email", field_type=str)])

    result = schema.validate(["not", "a", "dict"])

    assert not result.valid
    assert result.errors[0].field == "__root__"
    assert result.errors[0].message == "Expected data to be a dictionary"


def test_complex_nested_validation_with_custom_validator():
    def has_nested_timezone(value):
        return (
            isinstance(value, dict)
            and isinstance(value.get("birth"), dict)
            and required(value["birth"].get("timezone"))
        )

    schema = Schema(
        [
            Field("profile", field_type=dict, validators=[(has_nested_timezone, {})]),
            Field("tags", required=False, field_type=list, default=[]),
        ]
    )

    valid_result = schema.validate(
        {"profile": {"birth": {"timezone": "Europe/Moscow"}}}
    )
    invalid_result = schema.validate({"profile": {"birth": {"timezone": ""}}})

    assert valid_result.valid
    assert not invalid_result.valid
    assert invalid_result.errors[0].field == "profile"
