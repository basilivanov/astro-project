# ############################################################################
# AI_HEADER: MODULE_TELEGRAM_RENDERER
# ROLE: Render JSON report blocks into Telegram-safe HTML text.
# DEPENDENCIES: html, json, re.
# ############################################################################

from __future__ import annotations

import html
import json
import re
from typing import Any, Iterable

TELEGRAM_SAFE_LENGTH = 3500

_BOLD_OPEN = "<b>"
_BOLD_CLOSE = "</b>"
_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_HTML_TAG_SPLIT = re.compile(r"(<\/?b>)")
_ENTITY_OR_CHAR = re.compile(r"&[A-Za-z0-9#]+;|.", re.DOTALL)

_CALLOUT_LABELS = {
    "info": "Инфо",
    "warning": "Внимание",
    "error": "Ошибка",
    "success": "Итог",
    "quote": "Цитата",
}

_TRAFFIC_LIGHT_LABELS = {
    "health": "Здоровье",
    "money": "Финансы",
    "love": "Любовь",
}

_TRAFFIC_LIGHT_DOTS = {
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴",
}


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").strip()


def _format_inline(text: Any) -> str:
    escaped = html.escape(_stringify(text))
    return _BOLD_PATTERN.sub(r"<b>\1</b>", escaped)


def _render_table_row(columns: list[Any], row: Any) -> str:
    headers = []
    for idx, column in enumerate(columns):
        if isinstance(column, dict):
            header = column.get("header") or column.get("key") or f"Колонка {idx + 1}"
        else:
            header = column or f"Колонка {idx + 1}"
        headers.append(_stringify(header))

    pairs = []
    if isinstance(row, dict):
        for idx, header in enumerate(headers):
            value = row.get(header)
            if value not in (None, ""):
                pairs.append(f"{_format_inline(header)}: {_format_inline(value)}")
        if not pairs:
            for key, value in row.items():
                if value not in (None, ""):
                    pairs.append(f"{_format_inline(key)}: {_format_inline(value)}")
    else:
        values = list(row) if isinstance(row, (list, tuple)) else [_stringify(row)]
        for idx, value in enumerate(values):
            if value in (None, ""):
                continue
            header = headers[idx] if idx < len(headers) else f"Колонка {idx + 1}"
            pairs.append(f"{_format_inline(header)}: {_format_inline(value)}")

    if not pairs:
        return ""
    return f"• {'; '.join(pairs)}"


def render_block_to_telegram_html(block: dict[str, Any]) -> str:
    block_type = _stringify(block.get("type")).lower()

    if block_type == "header":
        text = _format_inline(block.get("text"))
        return f"<b>{text}</b>" if text else ""

    if block_type == "paragraph":
        return _format_inline(block.get("text"))

    if block_type == "list":
        items = block.get("items") or []
        lines = []
        for item in items:
            rendered = _format_inline(item)
            if rendered:
                lines.append(f"• {rendered}")
        return "\n".join(lines)

    if block_type == "table":
        columns = block.get("columns") or []
        rows = block.get("rows") or []
        lines = []
        for row in rows:
            rendered = _render_table_row(columns, row)
            if rendered:
                lines.append(rendered)
        return "\n".join(lines)

    if block_type == "key_value":
        items = block.get("items") or []
        lines = []
        for item in items:
            if not isinstance(item, dict):
                rendered = _format_inline(item)
                if rendered:
                    lines.append(rendered)
                continue
            key = _format_inline(item.get("key"))
            value = _format_inline(item.get("value"))
            if key and value:
                lines.append(f"{key}: {value}")
            elif key:
                lines.append(key)
            elif value:
                lines.append(value)
        return "\n".join(lines)

    if block_type == "callout":
        label = _stringify(block.get("title")) or _CALLOUT_LABELS.get(
            _stringify(block.get("variant")).lower(),
            "Заметка",
        )
        content = _format_inline(block.get("content") or block.get("text"))
        label_html = _format_inline(label)
        if label_html and content:
            return f"<b>{label_html}:</b> {content}"
        if label_html:
            return f"<b>{label_html}</b>"
        return content

    if block_type == "rating":
        value = _format_inline(block.get("value"))
        max_value = _format_inline(block.get("max") or 10)
        label = _format_inline(block.get("label"))
        suffix = f" — {label}" if label else ""
        if value:
            return f"Оценка: {value}/{max_value}{suffix}"
        return f"Оценка: -/{max_value}{suffix}"

    if block_type == "traffic_lights":
        items = block.get("items") or {}
        lines = []
        for key in ("health", "money", "love"):
            label = _TRAFFIC_LIGHT_LABELS[key]
            color = _stringify(items.get(key)).lower()
            dot = _TRAFFIC_LIGHT_DOTS.get(color, "⚪")
            lines.append(f"{label}: {dot}")
        return "\n".join(lines)

    if block_type == "divider":
        return "—"

    fallback = _format_inline(block.get("text") or block.get("content"))
    if fallback:
        return fallback
    return _format_inline(json.dumps(block, ensure_ascii=False))


def render_blocks_to_telegram_html(blocks: list[dict[str, Any]]) -> str:
    rendered = []
    for block in blocks:
        if not isinstance(block, dict):
            text = _format_inline(block)
            if text:
                rendered.append(text)
            continue
        block_html = render_block_to_telegram_html(block)
        if block_html:
            rendered.append(block_html)
    return "\n\n".join(rendered).strip()


def render_blocks_to_text(blocks: list[dict[str, Any]]) -> str:
    return render_blocks_to_telegram_html(blocks)


def _visible_text(text: str) -> str:
    return _HTML_TAG_SPLIT.sub("", text).strip()


def _take_prefix(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text

    candidate = text[:limit]
    for separator in ("\n\n", "\n", " "):
        idx = candidate.rfind(separator)
        if idx > max(limit // 3, 0):
            return text[: idx + len(separator)]

    total = 0
    end = 0
    for match in _ENTITY_OR_CHAR.finditer(text):
        token = match.group(0)
        if total + len(token) > limit:
            break
        total += len(token)
        end = match.end()

    if end > 0:
        return text[:end]
    return text[:limit]


def split_telegram_html(text: str, max_length: int = TELEGRAM_SAFE_LENGTH) -> list[str]:
    normalized = _stringify(text)
    if not normalized:
        return []
    if max_length <= len(_BOLD_OPEN) + len(_BOLD_CLOSE):
        raise ValueError("max_length is too small for Telegram HTML splitting")

    messages: list[str] = []
    current = ""
    bold_active = False

    def flush() -> None:
        nonlocal current
        chunk = current
        if bold_active and not chunk.endswith(_BOLD_CLOSE):
            chunk += _BOLD_CLOSE
        if _visible_text(chunk):
            messages.append(chunk.strip())
        current = _BOLD_OPEN if bold_active else ""

    def append_text(text_part: str) -> None:
        nonlocal current
        remaining = text_part
        while remaining:
            reserve = len(_BOLD_CLOSE) if bold_active else 0
            room = max_length - len(current) - reserve
            if room <= 0:
                flush()
                continue

            piece = _take_prefix(remaining, room)
            if current in {"", _BOLD_OPEN}:
                piece = piece.lstrip(" \n")
            if not piece:
                flush()
                remaining = remaining.lstrip(" \n")
                continue

            current += piece
            remaining = remaining[len(piece):]
            if remaining:
                flush()

    for part in _HTML_TAG_SPLIT.split(normalized):
        if not part:
            continue
        if part == _BOLD_OPEN:
            if len(current) + len(_BOLD_OPEN) + len(_BOLD_CLOSE) > max_length and _visible_text(current):
                flush()
            current += _BOLD_OPEN
            bold_active = True
            continue
        if part == _BOLD_CLOSE:
            if len(current) + len(_BOLD_CLOSE) > max_length:
                flush()
            current += _BOLD_CLOSE
            bold_active = False
            continue
        append_text(part)

    if _visible_text(current):
        final_chunk = current
        if bold_active and not final_chunk.endswith(_BOLD_CLOSE):
            final_chunk += _BOLD_CLOSE
        messages.append(final_chunk.strip())

    return messages


def render_plain_text_to_telegram_html(text: Any) -> str:
    return _format_inline(text)


def render_chunk_content(content: Any) -> str:
    return render_chunk_content_to_telegram_html(content)


def render_chunk_content_to_telegram_html(content: Any) -> str:
    normalized = _stringify(content)
    if not normalized:
        return ""

    try:
        parsed = json.loads(normalized)
    except (json.JSONDecodeError, TypeError):
        return render_plain_text_to_telegram_html(normalized)

    if isinstance(parsed, list):
        return render_blocks_to_telegram_html(parsed)
    if isinstance(parsed, dict) and parsed.get("type"):
        return render_blocks_to_telegram_html([parsed])
    if isinstance(parsed, str):
        return render_plain_text_to_telegram_html(parsed)
    return render_plain_text_to_telegram_html(json.dumps(parsed, ensure_ascii=False))


def render_chunk_content_to_telegram_messages(
    content: Any,
    max_length: int = TELEGRAM_SAFE_LENGTH,
) -> list[str]:
    html_text = render_chunk_content_to_telegram_html(content)
    return split_telegram_html(html_text, max_length=max_length)


def render_report_chunks_to_messages(
    chunks: Iterable[Any],
    title: str,
    max_len: int = TELEGRAM_SAFE_LENGTH,
) -> list[str]:
    messages: list[str] = []
    if title:
        messages.append(f"<b>{html.escape(_stringify(title))}</b>")

    for chunk in chunks:
        content = getattr(chunk, "content", None) if chunk is not None else None
        messages.extend(
            render_chunk_content_to_telegram_messages(content, max_length=max_len)
        )

    return [message for message in messages if _visible_text(message)]
