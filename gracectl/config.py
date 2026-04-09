from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .types import Defaults, GraceConfig, SliceCommands, SliceProfile, WatchFlow

DEFAULT_CONFIG_PATH = Path("gracectl.yaml")


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing gracectl config: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _path(value: str | Path, base: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path


def _parse_defaults(data: Dict[str, Any], base: Path) -> Defaults:
    report_path = _path(data.get("report_path", "test-results/grace-report.json"), base)
    log_dir = _path(data.get("log_dir", "logs/gracectl"), base)
    frontend_container = data.get("frontend_container", "astro-project-frontend_dev-1")
    backend_container = data.get("backend_container", "astro-project-backend-1")
    repo_root = _path(data.get("repo_root", "."), base)
    return Defaults(
        report_path=report_path,
        log_dir=log_dir,
        frontend_container=frontend_container,
        backend_container=backend_container,
        repo_root=repo_root,
    )


def _parse_commands(data: Dict[str, Any]) -> SliceCommands:
    backend = list(data.get("backend", []) or [])
    frontend = list(data.get("frontend", []) or [])
    replay = list(data.get("replay", []) or [])
    return SliceCommands(backend=backend, frontend=frontend, replay=replay)


def _parse_slices(data: Dict[str, Any], defaults: Defaults) -> List[SliceProfile]:
    slices: List[SliceProfile] = []
    for key, payload in (data or {}).items():
        commands = _parse_commands(payload.get("commands", {}))
        docs = [
            _path(path, defaults.repo_root)
            for path in payload.get("docs", [])
        ]
        evidence = [
            _path(path, defaults.repo_root)
            for path in payload.get("evidence", [])
        ]
        vm_ids = list(payload.get("vm_ids", []))
        slices.append(
            SliceProfile(
                key=key,
                title=payload.get("title", key.title()),
                description=payload.get("description", ""),
                gate=payload.get("gate", ""),
                vm_ids=vm_ids,
                docs=docs,
                commands=commands,
                evidence=evidence,
            )
        )
    return slices


def _parse_watch_flows(data: List[Dict[str, Any]] | None) -> List[WatchFlow]:
    flows: List[WatchFlow] = []
    for entry in data or []:
        if not isinstance(entry, dict):
            raise ValueError(f"watch.flows entries must be mappings, got {entry!r}")
        flow_id = entry.get("id")
        label = entry.get("label")
        script = entry.get("script")
        if not all(isinstance(value, str) and value for value in (flow_id, label, script)):
            raise ValueError(f"watch flow missing required fields: {entry!r}")
        args = entry.get("args") or {}
        if not isinstance(args, dict):
            raise ValueError(f"watch flow args must be a mapping, got {args!r}")
        slices = entry.get("slices") or []
        if not isinstance(slices, list):
            raise ValueError(f"watch flow slices must be a list, got {slices!r}")
        flows.append(
            WatchFlow(
                id=flow_id,
                label=label,
                script=script,
                args=args,
                json_output=bool(entry.get("json_output", False)),
                stale_after=entry.get("stale_after"),
                slices=[str(item) for item in slices],
            )
        )
    return flows


def load_config(path: Path | None = None) -> GraceConfig:
    config_path = path or Path(os.environ.get("GRACECTL_CONFIG", DEFAULT_CONFIG_PATH))
    raw = _read_yaml(config_path)
    defaults = _parse_defaults(raw.get("defaults", {}), config_path.parent)
    slices = _parse_slices(raw.get("slices", {}), defaults)
    watch_flows = _parse_watch_flows(raw.get("watch", {}).get("flows"))
    return GraceConfig(defaults=defaults, slices=slices, watch_flows=watch_flows)
