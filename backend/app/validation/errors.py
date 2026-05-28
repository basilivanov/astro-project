"""Validation error and result types."""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any


class ValidationError(Exception):
    """Represents a single validation failure for one field."""

    def __init__(self, field: str, message: str, value: Any) -> None:
        self.field = field
        self.message = message
        self.value = value
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"{self.field}: {self.message} (value={self.value!r})"


@dataclass
class ValidationResult:
    """Collects validation status and all field errors."""

    valid: bool = True
    errors: list[ValidationError] = dataclass_field(default_factory=list)

    def add_error(self, field_name: str, message: str, value: Any) -> None:
        """Append a validation error and mark the result invalid."""
        self.valid = False
        self.errors.append(ValidationError(field_name, message, value))
