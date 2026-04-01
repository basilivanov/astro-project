from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path(os.environ.get("RENDERED_GATE_ARTIFACT_DIR", "test-results/rendered-gate"))


@dataclass(frozen=True)
class RenderedSummaryArtifact:
    flow_id: str
    surface: str
    scenario_id: str
    pass_mode: dict[str, Any]
    status: str
    assertion_class: str
    artifact_refs: list[str]
    details: dict[str, Any]
    recorded_at: str


def build_parity_details(*, counterpart_pass_mode: str | dict[str, Any] | None, parity_status: str, notes: list[str] | None = None) -> dict[str, Any]:
    return {
        "counterpart_pass_mode": counterpart_pass_mode if isinstance(counterpart_pass_mode, dict) else stable_pass_mode(counterpart_pass_mode),
        "parity_status": parity_status,
        "notes": list(notes or []),
    }


def build_parity_pilot_details(
    *,
    counterpart_pass_mode: str | dict[str, Any] | None,
    parity_status: str,
    shared_artifact_refs: list[str] | None = None,
    invariant_groups: list[str] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    payload = build_parity_details(
        counterpart_pass_mode=counterpart_pass_mode,
        parity_status=parity_status,
        notes=notes,
    )
    payload["shared_artifact_refs"] = list(shared_artifact_refs or [])
    payload["invariant_groups"] = list(invariant_groups or [])
    return payload


def stable_pass_mode(value: str | None = None, *, channel: str | None = None) -> dict[str, str]:
    normalized = (value or "site_web").strip().lower().replace("-", "_")
    if normalized in {"both", "both_pass_modes", "site_and_telegram", "site_web+telegram_webapp"}:
        return {"key": "both", "channel": "multi", "path": "site_web+telegram_webapp"}
    if normalized in {"site", "web", "site_web", "site/web"}:
        return {"key": "site_web", "channel": "web", "path": "/" if channel is None else channel}
    if normalized in {"telegram", "telegram_web", "telegram_webapp", "telegram/webapp"}:
        return {"key": "telegram_webapp", "channel": "telegram", "path": "webapp"}
    return {"key": normalized or "site_web", "channel": channel or "web", "path": channel or normalized or "site_web"}


def render_artifact_path(*, flow_id: str, surface: str, scenario_id: str, base_dir: Path | None = None) -> Path:
    root = base_dir or DEFAULT_DIR
    safe_parts = [flow_id, surface, scenario_id]
    filename = "__".join(part.replace("/", "_").replace(" ", "-") for part in safe_parts) + ".json"
    return root / filename


def build_rendered_summary(*, flow_id: str, surface: str, scenario_id: str, pass_mode: str | dict[str, Any] | None, status: str, assertion_class: str, artifact_refs: list[str] | None = None, details: dict[str, Any] | None = None, recorded_at: str | None = None) -> RenderedSummaryArtifact:
    pass_mode_payload = pass_mode if isinstance(pass_mode, dict) else stable_pass_mode(pass_mode)
    return RenderedSummaryArtifact(
        flow_id=flow_id,
        surface=surface,
        scenario_id=scenario_id,
        pass_mode=pass_mode_payload,
        status=status,
        assertion_class=assertion_class,
        artifact_refs=list(artifact_refs or []),
        details=dict(details or {}),
        recorded_at=recorded_at or datetime.now(timezone.utc).isoformat(),
    )


def write_rendered_summary(*, flow_id: str, surface: str, scenario_id: str, pass_mode: str | dict[str, Any] | None, status: str, assertion_class: str, artifact_refs: list[str] | None = None, details: dict[str, Any] | None = None, base_dir: Path | None = None) -> Path:
    artifact = build_rendered_summary(
        flow_id=flow_id,
        surface=surface,
        scenario_id=scenario_id,
        pass_mode=pass_mode,
        status=status,
        assertion_class=assertion_class,
        artifact_refs=artifact_refs,
        details=details,
    )
    target = render_artifact_path(flow_id=flow_id, surface=surface, scenario_id=scenario_id, base_dir=base_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(artifact), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_rendered_summaries(base_dir: Path | None = None) -> list[dict[str, Any]]:
    root = base_dir or DEFAULT_DIR
    if not root.exists():
        return []
    payloads: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads
