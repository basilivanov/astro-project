from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def resolve_execution_workdir(candidate: str | None) -> Path:
    if not candidate:
        return ROOT_DIR
    path = Path(str(candidate)).expanduser()
    if path.exists() and path.is_dir():
        return path.resolve()
    return ROOT_DIR
