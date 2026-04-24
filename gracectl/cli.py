from __future__ import annotations

import typer

from .commands import env_app, slice_app
from .commands.demo import demo_app
from .commands.evidence import evidence_app
from .commands.watch import watch_app

app = typer.Typer(help="GRACE verification control")
app.add_typer(env_app, name="env")
app.add_typer(slice_app, name="slice")
app.add_typer(watch_app, name="watch")
app.add_typer(demo_app, name="demo")
app.add_typer(evidence_app, name="evidence")


if __name__ == "__main__":
    app()
