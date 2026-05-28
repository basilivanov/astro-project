"""Schema-based validation for structured dictionaries."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.validation.errors import ValidationResult
from app.validation.validators import required as required_validator
from app.validation.validators import type_check

ValidatorSpec = tuple[Callable[..., bool], dict[str, Any]]


@dataclass
class Field:
    """Defines validation rules for a single schema field."""

    name: str
    required: bool = True
    field_type: type | tuple[type, ...] | None = None
    validators: list[ValidatorSpec] = field(default_factory=list)
    default: Any = None


class Schema:
    """Validates dictionaries against a collection of field definitions."""

    def __init__(self, fields: list[Field]) -> None:
        self._fields: dict[str, Field] = {}
        for schema_field in fields:
            self.add_field(schema_field)

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data against the schema and collect all failures."""
        result = ValidationResult()

        if not isinstance(data, dict):
            result.add_error("__root__", "Expected data to be a dictionary", data)
            return result

        for schema_field in self._fields.values():
            field_present = schema_field.name in data
            value = data.get(schema_field.name, schema_field.default)

            if not field_present and schema_field.required and schema_field.default is None:
                result.add_error(
                    schema_field.name,
                    "Field is required",
                    None,
                )
                continue

            if not field_present and schema_field.default is not None:
                value = schema_field.default

            if schema_field.required and not required_validator(value):
                result.add_error(
                    schema_field.name,
                    "Field is required and cannot be empty",
                    value,
                )
                continue

            if not schema_field.required and not field_present:
                continue

            if value is None and not schema_field.required:
                continue

            if schema_field.field_type is not None and not type_check(
                value,
                schema_field.field_type,
            ):
                result.add_error(
                    schema_field.name,
                    self._type_error_message(schema_field),
                    value,
                )

            self._run_validators(schema_field, value, result)

        return result

    def add_field(self, schema_field: Field) -> None:
        """Add or replace a field definition by name."""
        self._fields[schema_field.name] = schema_field

    def get_field(self, name: str) -> Field | None:
        """Return a field definition by name, if present."""
        return self._fields.get(name)

    def _run_validators(
        self,
        schema_field: Field,
        value: Any,
        result: ValidationResult,
    ) -> None:
        for validator_func, validator_kwargs in schema_field.validators:
            try:
                is_valid = validator_func(value, **validator_kwargs)
            except (TypeError, ValueError) as exc:
                result.add_error(
                    schema_field.name,
                    f"Validator {validator_func.__name__} failed: {exc}",
                    value,
                )
                continue

            if not is_valid:
                result.add_error(
                    schema_field.name,
                    self._validator_error_message(validator_func, validator_kwargs),
                    value,
                )

    @staticmethod
    def _type_error_message(schema_field: Field) -> str:
        return f"Expected type {Schema._type_name(schema_field.field_type)}"

    @staticmethod
    def _validator_error_message(
        validator_func: Callable[..., bool],
        validator_kwargs: dict[str, Any],
    ) -> str:
        if validator_kwargs:
            constraints = ", ".join(
                f"{key}={value!r}" for key, value in sorted(validator_kwargs.items())
            )
            return f"Failed validator {validator_func.__name__} with {constraints}"
        return f"Failed validator {validator_func.__name__}"

    @staticmethod
    def _type_name(expected_type: type | tuple[type, ...] | None) -> str:
        if expected_type is None:
            return "None"
        if isinstance(expected_type, tuple):
            return " or ".join(type_item.__name__ for type_item in expected_type)
        return expected_type.__name__
