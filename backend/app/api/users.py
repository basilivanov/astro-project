"""REST API router for in-memory user CRUD operations."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException

from ..logging_utils import log_grace_event


USER_API_MODULE_ID = "M-ASTRO-USER-API"


def _load_user_model():
    """Load backend/app/models/user.py despite the existing app.models module."""
    model_path = Path(__file__).resolve().parents[1] / "models" / "user.py"
    spec = spec_from_file_location("astro_user_api_model", model_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load user model")

    module_name = "astro_user_api_model"
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.User


User = _load_user_model()

router = APIRouter()
_USERS: dict[str, User] = {}


def clear_user_store() -> None:
    """Clear in-memory storage for isolated tests."""
    _USERS.clear()


def _json_error(status_code: int, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=message)


def _log_user_api_event(level: str, event: str, *, fn: str, **fields: object) -> None:
    log_grace_event(
        level,
        event,
        module=USER_API_MODULE_ID,
        fn=fn,
        block="USER_CRUD",
        **fields,
    )


def _find_by_username(username: str) -> User | None:
    normalized = username.casefold()
    return next((user for user in _USERS.values() if user.username.casefold() == normalized), None)


def _find_by_email(email: str) -> User | None:
    normalized = email.casefold()
    return next((user for user in _USERS.values() if user.email.casefold() == normalized), None)


def _get_user_or_404(user_id: str) -> User:
    try:
        normalized_id = User.validate_user_id(user_id)
    except ValueError as exc:
        raise _json_error(400, str(exc)) from exc

    user = _USERS.get(normalized_id)
    if user is None:
        raise _json_error(404, "User not found")
    return user


def _require_mapping(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise _json_error(400, "Request body must be a JSON object")
    return payload


@router.post("/api/users", status_code=201)
def create_user(payload: dict[str, Any] = Body(...)) -> dict[str, object]:
    """Create a user after validating username and email uniqueness."""
    data = _require_mapping(payload)

    try:
        username = User.validate_username(data.get("username"))
        email = User.validate_email(data.get("email"))
    except ValueError as exc:
        raise _json_error(400, str(exc)) from exc

    if _find_by_username(username) is not None:
        raise _json_error(409, "Username already exists")
    if _find_by_email(email) is not None:
        raise _json_error(409, "Email already exists")

    user = User(
        id=str(uuid4()),
        username=username,
        email=email,
        created_at=datetime.now(timezone.utc),
        is_active=True,
    )
    _USERS[user.id] = user
    _log_user_api_event("info", "user_api.create", fn="create_user", user_id=user.id)
    return user.to_dict()


@router.get("/api/users/{user_id}")
def get_user(user_id: str) -> dict[str, object]:
    """Return a user by UUID."""
    user = _get_user_or_404(user_id)
    _log_user_api_event("info", "user_api.get", fn="get_user", user_id=user.id)
    return user.to_dict()


@router.get("/api/users")
def list_users(active: bool | None = None) -> list[dict[str, object]]:
    """List users, optionally filtering by active account status."""
    users = _USERS.values()
    if active is not None:
        users = [user for user in users if user.is_active is active]
    serialized_users = [user.to_dict() for user in users]
    _log_user_api_event(
        "info",
        "user_api.list",
        fn="list_users",
        active_filter=active,
        count=len(serialized_users),
    )
    return serialized_users


@router.put("/api/users/{user_id}")
def update_user(user_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, object]:
    """Update mutable user fields: email and is_active."""
    user = _get_user_or_404(user_id)
    data = _require_mapping(payload)
    allowed_fields = {"email", "is_active"}
    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise _json_error(400, f"Unsupported update field(s): {fields}")

    changes: dict[str, object] = {}
    if "email" in data:
        try:
            email = User.validate_email(data["email"])
        except ValueError as exc:
            raise _json_error(400, str(exc)) from exc

        existing = _find_by_email(email)
        if existing is not None and existing.id != user.id:
            raise _json_error(409, "Email already exists")
        changes["email"] = email

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            raise _json_error(400, "is_active must be a boolean")
        changes["is_active"] = data["is_active"]

    if not changes:
        raise _json_error(400, "At least one updatable field is required")

    updated_user = replace(user, **changes)
    _USERS[updated_user.id] = updated_user
    _log_user_api_event("info", "user_api.update", fn="update_user", user_id=updated_user.id)
    return updated_user.to_dict()


@router.delete("/api/users/{user_id}")
def delete_user(user_id: str) -> dict[str, object]:
    """Soft-delete a user by marking the account inactive."""
    user = _get_user_or_404(user_id)
    updated_user = replace(user, is_active=False)
    _USERS[updated_user.id] = updated_user
    _log_user_api_event("info", "user_api.delete", fn="delete_user", user_id=updated_user.id)
    return updated_user.to_dict()
