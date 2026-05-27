#!/usr/bin/env python3
"""Send a Telegram notification when an agent finishes a work step."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prefect_grace.tasks.telegram_notify import notify_agent_work_event  # noqa: E402


def _read_message(args: argparse.Namespace) -> str | None:
    if args.message:
        return args.message
    if args.message_file:
        if args.message_file == "-":
            try:
                return sys.stdin.read().strip() or None
            except OSError:
                return None
        return Path(args.message_file).read_text(encoding="utf-8").strip() or None
    if not sys.stdin.isatty():
        try:
            return sys.stdin.read().strip() or None
        except OSError:
            return None
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notify the operator that an agent work step finished.")
    parser.add_argument("--status", choices=["started", "done", "blocked", "failed", "info"], default="done")
    parser.add_argument("--title", required=True)
    parser.add_argument("--message")
    parser.add_argument("--message-file", help="Path to text file, or '-' for stdin.")
    parser.add_argument("--packet-id")
    parser.add_argument("--next-action")
    parser.add_argument("--link")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = _read_message(args)
    if args.dry_run:
        ok = True
    else:
        ok = notify_agent_work_event(
            status=args.status,
            title=args.title,
            summary=summary,
            packet_id=args.packet_id,
            next_action=args.next_action,
            link=args.link,
        )

    if args.json:
        print(json.dumps({
            "ok": ok,
            "dry_run": bool(args.dry_run),
            "status": args.status,
            "title": args.title,
            "packet_id": args.packet_id,
        }, ensure_ascii=False))
    else:
        print("agent notify: sent" if ok else "agent notify: not sent")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
