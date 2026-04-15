from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping, Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("runtime.yaml")


@dataclass(frozen=True)
class PrefectGraceRuntimeConfig:
    api_url: str
    public_ui_url: str | None
    work_pool_name: str
    live_queue_name: str
    live_queue_limit: int | None
    monitoring_queue_name: str
    monitoring_queue_limit: int | None
    monitoring_interval_seconds: int
    working_directory: str


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _normalize_optional_int(value: object) -> int | None:
    if value in (None, "", "none", "null", "None", "Null"):
        return None
    return int(str(value))


def _first_non_empty(*values: object) -> object | None:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def load_runtime_config(
    *,
    config_path: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> PrefectGraceRuntimeConfig:
    env_map = dict(os.environ if env is None else env)
    raw = _load_yaml(config_path or DEFAULT_CONFIG_PATH)

    api_url = str(
        _first_non_empty(
            env_map.get("PREFECT_GRACE_API_URL"),
            env_map.get("PREFECT_API_URL"),
            raw.get("api_url"),
            "http://127.0.0.1:4200/api",
        )
    )
    public_ui_url = _first_non_empty(
        env_map.get("PREFECT_GRACE_PUBLIC_UI_URL"),
        raw.get("public_ui_url"),
        None,
    )
    work_pool_name = str(
        _first_non_empty(
            env_map.get("PREFECT_GRACE_WORK_POOL"),
            raw.get("work_pool_name"),
            "astro-process",
        )
    )
    live_queue_name = str(
        _first_non_empty(
            env_map.get("PREFECT_GRACE_LIVE_QUEUE"),
            raw.get("live_queue_name"),
            "grace-live",
        )
    )
    live_queue_limit = _normalize_optional_int(
        _first_non_empty(
            env_map.get("PREFECT_GRACE_LIVE_QUEUE_LIMIT"),
            raw.get("live_queue_limit"),
            "1",
        )
    )
    monitoring_queue_name = str(
        _first_non_empty(
            env_map.get("PREFECT_GRACE_MONITORING_QUEUE"),
            raw.get("monitoring_queue_name"),
            "grace-monitoring",
        )
    )
    monitoring_queue_limit = _normalize_optional_int(
        _first_non_empty(
            env_map.get("PREFECT_GRACE_MONITORING_QUEUE_LIMIT"),
            raw.get("monitoring_queue_limit"),
            "1",
        )
    )
    monitoring_interval_seconds = int(
        str(
            _first_non_empty(
                env_map.get("PREFECT_GRACE_MONITORING_INTERVAL_SECONDS"),
                raw.get("monitoring_interval_seconds"),
                "300",
            )
        )
    )
    working_directory = str(
        _first_non_empty(
            env_map.get("PREFECT_GRACE_WORKDIR"),
            raw.get("working_directory"),
            str(ROOT_DIR),
        )
    )

    return PrefectGraceRuntimeConfig(
        api_url=api_url,
        public_ui_url=str(public_ui_url) if public_ui_url else None,
        work_pool_name=work_pool_name,
        live_queue_name=live_queue_name,
        live_queue_limit=live_queue_limit,
        monitoring_queue_name=monitoring_queue_name,
        monitoring_queue_limit=monitoring_queue_limit,
        monitoring_interval_seconds=monitoring_interval_seconds,
        working_directory=working_directory,
    )
