from __future__ import annotations

from pathlib import Path

import typer

from .env import env_check
from .slice_replay import slice_replay
from .slice_verify import slice_verify


demo_app = typer.Typer(help="End-to-end slice demo")


@demo_app.command("run")
def demo_run(
    slice_key: str = typer.Argument(..., help="Slice identifier"),
    fast: bool = typer.Option(False, "--fast", help="Skip env check"),
    backend: bool = typer.Option(True, "--backend/--no-backend"),
    frontend: bool = typer.Option(True, "--frontend/--no-frontend"),
    replay: bool = typer.Option(True, "--replay/--no-replay"),
    config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml"),
) -> None:
    if not fast:
        env_check(config_path=config_path)
    slice_verify(
        slice_key=slice_key,
        run_backend=backend,
        run_frontend=frontend,
        run_replay=False,
        config_path=config_path,
    )
    if replay:
        slice_replay(slice_key=slice_key, config_path=config_path)
