from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from html import escape
from pathlib import Path
from typing import Any

from prefect_grace.runtime_config import load_runtime_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env_file_value(key: str) -> str | None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value or None
    return None


def _parse_int(raw: object) -> int | None:
    if raw in (None, ""):
        return None
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return value or None


def _parse_int_list(raw: object) -> list[int]:
    if raw in (None, ""):
        return []
    values: list[int] = []
    for item in str(raw).split(","):
        parsed = _parse_int(item)
        if parsed is not None:
            values.append(parsed)
    return values


def _telegram_bot_token() -> str | None:
    return os.environ.get("TELEGRAM_BOT_TOKEN") or _env_file_value("TELEGRAM_BOT_TOKEN")


def _notify_urls() -> list[str]:
    values = [
        os.environ.get("GRACE_NOTIFY_URL"),
        os.environ.get("SUPERVISOR_NOTIFY_URL"),
    ]
    bot_internal_url = os.environ.get("BOT_INTERNAL_URL") or _env_file_value("BOT_INTERNAL_URL")
    if bot_internal_url:
        values.append(f"{str(bot_internal_url).rstrip('/')}/notify")
    values.append("http://127.0.0.1:8001/notify")

    urls: list[str] = []
    for value in values:
        candidate = str(value).strip() if value else ""
        if candidate and candidate not in urls:
            urls.append(candidate)
    return urls


def _notify_url() -> str | None:
    urls = _notify_urls()
    return urls[0] if urls else None


def _notify_chat_id() -> int | None:
    direct = (
        os.environ.get("GRACE_NOTIFY_CHAT_ID")
        or os.environ.get("SUPERVISOR_NOTIFY_CHAT_ID")
        or os.environ.get("DUCTOR_CHAT_ID")
    )
    if direct:
        return _parse_int(direct)

    file_direct = (
        _env_file_value("GRACE_NOTIFY_CHAT_ID")
        or _env_file_value("SUPERVISOR_NOTIFY_CHAT_ID")
        or _env_file_value("DUCTOR_CHAT_ID")
    )
    if file_direct:
        return _parse_int(file_direct)

    admin_ids = os.environ.get("BOT_ADMIN_IDS") or _env_file_value("BOT_ADMIN_IDS")
    parsed_ids = _parse_int_list(admin_ids)
    if parsed_ids:
        return parsed_ids[-1]
    return None


def _flow_run_url(flow_run_id: str | None) -> str | None:
    if not flow_run_id:
        return None
    runtime = load_runtime_config()
    if not runtime.public_ui_url:
        return None
    return f"{runtime.public_ui_url.rstrip('/')}/runs/flow-run/{flow_run_id}"


def _packet_run_url(task_run_id: str | None) -> str | None:
    if not task_run_id:
        return None
    runtime = load_runtime_config()
    if not runtime.public_ui_url:
        return None
    return f"{runtime.public_ui_url.rstrip('/')}/runs/task-run/{task_run_id}"


def _post_json(url: str, payload: dict[str, Any]) -> bool:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            status = getattr(response, "status", 200)
            return 200 <= int(status) < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False


def _send_via_internal_notify(*, chat_id: int, text: str) -> bool:
    payload = {
        "telegram_id": chat_id,
        "text": text,
    }
    for notify_url in _notify_urls():
        if _post_json(notify_url, payload):
            return True
    return False


def _send_via_telegram_api(*, chat_id: int, text: str) -> bool:
    bot_token = _telegram_bot_token()
    if not bot_token:
        return False
    return _post_json(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )


def _send_html_message(text: str) -> bool:
    chat_id = _notify_chat_id()
    if not chat_id:
        return False
    if _send_via_internal_notify(chat_id=chat_id, text=text):
        return True
    return _send_via_telegram_api(chat_id=chat_id, text=text)


def _lines_to_html(lines: list[str]) -> str:
    return "\n".join(lines)


def notify_feature_event(
    *,
    feature_id: str,
    title: str | None,
    status: str,
    summary: str | None = None,
    wave_id: str | None = None,
    flow_run_id: str | None = None,
    blockers: list[str] | None = None,
    next_action: str | None = None,
) -> bool:
    icon = {
        "in_progress": "🚀",
        "accepted": "🏁",
        "completed": "🏁",
        "blocked": "⛔",
        "pipeline_invalid": "🧯",
        "verification_blocked": "🔬",
        "environment_blocked": "🛠",
        "product_blocked": "📌",
        "architect_ready": "🧠",
    }.get(status, "📣")
    lines = [
        f"{icon} <b>Feature {escape(status)}</b>",
        f"<b>{escape(feature_id)}</b>" + (f" — {escape(title)}" if title else ""),
    ]
    if wave_id:
        lines.append(f"Wave: <b>{escape(wave_id)}</b>")
    if summary:
        lines.append(f"Summary: {escape(summary)}")
    if next_action:
        lines.append(f"Next: <code>{escape(next_action)}</code>")
    if blockers:
        for blocker in blockers[:5]:
            lines.append(f"• {escape(blocker)}")
    url = _flow_run_url(flow_run_id)
    if url:
        lines.append(f"<a href=\"{escape(url)}\">Open Prefect run</a>")
    return _send_html_message(_lines_to_html(lines))


def notify_packet_event(
    *,
    feature_id: str,
    packet_id: str,
    role: str,
    status: str,
    wave_id: str | None = None,
    title: str | None = None,
    reasons: list[str] | None = None,
    task_run_id: str | None = None,
    flow_run_id: str | None = None,
) -> bool:
    icon = {
        "accepted": "✅",
        "review": "🧪",
        "rework_required": "🔁",
        "blocked": "⛔",
        "escalate_to_architect": "🧠",
        "running": "🏃",
    }.get(status, "📦")
    lines = [
        f"{icon} <b>Packet {escape(status)}</b>",
        f"Feature: <b>{escape(feature_id)}</b>",
        f"Wave: <b>{escape(wave_id or '-')}</b>",
        f"Role: <b>{escape(role)}</b>",
        f"Packet: <code>{escape(packet_id)}</code>",
    ]
    if title:
        lines.append(f"Title: {escape(title)}")
    if reasons:
        for reason in reasons[:5]:
            lines.append(f"• {escape(reason)}")
    task_url = _packet_run_url(task_run_id)
    if task_url:
        lines.append(f"<a href=\"{escape(task_url)}\">Open task run</a>")
    flow_url = _flow_run_url(flow_run_id)
    if flow_url:
        lines.append(f"<a href=\"{escape(flow_url)}\">Open feature run</a>")
    return _send_html_message(_lines_to_html(lines))


def notify_wave_event(
    *,
    feature_id: str,
    wave_id: str,
    verdict: str,
    reasons: list[str] | None = None,
    flow_run_id: str | None = None,
) -> bool:
    icon = {
        "accepted": "🌊",
        "rework_required": "🔁",
        "blocked": "⛔",
    }.get(verdict, "🌊")
    lines = [
        f"{icon} <b>Wave {escape(verdict)}</b>",
        f"Feature: <b>{escape(feature_id)}</b>",
        f"Wave: <b>{escape(wave_id)}</b>",
    ]
    if reasons:
        for reason in reasons[:5]:
            lines.append(f"• {escape(reason)}")
    url = _flow_run_url(flow_run_id)
    if url:
        lines.append(f"<a href=\"{escape(url)}\">Open Prefect run</a>")
    return _send_html_message(_lines_to_html(lines))


def notify_submission_event(
    *,
    feature_id: str,
    title: str,
    execute: bool,
    brief_path: str | None = None,
) -> bool:
    mode = "live" if execute else "dry-run"
    icon = "🧾" if execute else "⚠️"
    lines = [
        f"{icon} <b>Feature submitted</b>",
        f"<b>{escape(feature_id)}</b> — {escape(title)}",
        f"Mode: <b>{escape(mode)}</b>",
    ]
    if not execute:
        lines.append("Codex agents will not run until <code>execute: true</code> is set.")
    if brief_path:
        lines.append(f"Brief: <code>{escape(brief_path)}</code>")
    return _send_html_message(_lines_to_html(lines))
