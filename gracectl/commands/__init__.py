"""Command registrations for gracectl."""

from .env import env_app
from .slice_verify import slice_app  # shared Typer app that other commands extend

__all__ = ["env_app", "slice_app"]
