from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def app_compat_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    if candidate.is_absolute() and candidate.parts[:2] == ('/', 'app'):
        return REPO_ROOT.joinpath(*candidate.parts[2:])
    return candidate
