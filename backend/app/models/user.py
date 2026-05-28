"""In-memory user model and validation helpers for the user CRUD API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from uuid import UUID


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,50}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class User:
    """User record stored by the user CRUD API."""

    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool

    @staticmethod
    def validate_username(username: object) -> str:
        """Validate and normalize a username value."""
        if not isinstance(username, str):
            raise ValueError("Username must be a string")

        normalized = username.strip()
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Username must be 3-50 characters and contain only letters, "
                "numbers, and underscores"
            )
        return normalized

    @staticmethod
    def validate_email(email: object) -> str:
        """Validate and normalize an email value."""
        if not isinstance(email, str):
            raise ValueError("Email must be a string")

        normalized = email.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Email must be a valid email address")
        return normalized

    @staticmethod
    def validate_user_id(user_id: object) -> str:
        """Validate UUID syntax for a user identifier."""
        if not isinstance(user_id, str):
            raise ValueError("User ID must be a string")

        try:
            return str(UUID(user_id))
        except ValueError as exc:
            raise ValueError("User ID must be a valid UUID") from exc

    def to_dict(self) -> dict[str, object]:
        """Serialize the model to a JSON-ready dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }
