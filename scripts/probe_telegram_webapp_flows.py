#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import urllib.parse
from dataclasses import asdict, dataclass
from typing import Any

from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotAppRequest, RequestAppWebViewRequest, RequestSimpleWebViewRequest, RequestWebViewRequest
try:
    from telethon.tl.functions.messages import RequestMainWebViewRequest
except ImportError:
    RequestMainWebViewRequest = None
from telethon.tl.types import InputBotAppShortName


@dataclass
class FlowResult:
    flow: str
    ok: bool
    error: str | None
    url: str | None
    tg_webapp_data_len: int | None
    tg_webapp_data_preview: str | None
    extras: dict[str, Any]


def extract_webapp_data(url: str | None) -> tuple[int | None, str | None, dict[str, Any]]:
    if not url:
        return None, None, {}
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.fragment) or urllib.parse.parse_qs(parsed.query)
    extras: dict[str, Any] = {}
    for key in ("tgWebAppVersion", "tgWebAppPlatform", "tgWebAppStartParam"):
        if key in query and query[key]:
            extras[key] = query[key][0]
    payload = query.get("tgWebAppData", [None])[0]
    if not payload:
        return None, None, extras
    decoded = urllib.parse.unquote(payload)
    return len(decoded), decoded[:220], extras


async def run_probe(args: argparse.Namespace) -> list[FlowResult]:
    client = TelegramClient(args.session, int(args.api_id), args.api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError("Telethon session is not authorized")

    bot = await client.get_entity(args.bot_username)
    results: list[FlowResult] = []

    async def capture(flow: str, coro, extras: dict[str, Any] | None = None):
        meta = {"bot_id": bot.id, "bot_username": getattr(bot, "username", None), **(extras or {})}
        try:
            response = await coro
            url = getattr(response, "url", None)
            length, preview, parsed_extras = extract_webapp_data(url)
            meta.update(parsed_extras)
            results.append(FlowResult(flow=flow, ok=True, error=None, url=url, tg_webapp_data_len=length, tg_webapp_data_preview=preview, extras=meta))
        except Exception as exc:
            results.append(FlowResult(flow=flow, ok=False, error=repr(exc), url=None, tg_webapp_data_len=None, tg_webapp_data_preview=None, extras=meta))

    for from_bot_menu in (False, True):
        await capture(
            f"requestWebView[from_bot_menu={from_bot_menu}]",
            client(RequestWebViewRequest(
                peer="me",
                bot=bot,
                platform=args.platform,
                from_bot_menu=from_bot_menu,
                url=f"https://t.me/{args.bot_username}",
                start_param=args.start_param,
            )),
            {"from_bot_menu": from_bot_menu},
        )

    await capture(
        "requestSimpleWebView",
        client(RequestSimpleWebViewRequest(
            bot=bot,
            url=f"https://t.me/{args.bot_username}",
            platform=args.platform,
            from_switch_webview=False,
            start_param=args.start_param,
        )),
    )

    if RequestMainWebViewRequest is not None:
        await capture(
            "requestMainWebView",
            client(RequestMainWebViewRequest(
                peer="me",
                bot=bot,
                platform=args.platform,
                start_param=args.start_param,
            )),
        )
    else:
        results.append(FlowResult(flow="requestMainWebView", ok=False, error="ImportError(\'RequestMainWebViewRequest unavailable in installed Telethon\')", url=None, tg_webapp_data_len=None, tg_webapp_data_preview=None, extras={"reason": "telethon_version_missing_method", "bot_id": bot.id, "bot_username": getattr(bot, "username", None)}))

    for short_name in args.short_names:
        app_input = InputBotAppShortName(bot_id=bot, short_name=short_name)
        await capture(
            f"getBotApp[{short_name}]",
            client(GetBotAppRequest(app=app_input, hash=0)),
            {"short_name": short_name},
        )
        await capture(
            f"requestAppWebView[{short_name}]",
            client(RequestAppWebViewRequest(
                peer="me",
                app=app_input,
                platform=args.platform,
                write_allowed=True,
                start_param=args.start_param,
            )),
            {"short_name": short_name},
        )

    await client.disconnect()
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe Telegram Mini App MTProto flows and extract tgWebAppData/initData when available")
    parser.add_argument("--session", required=True)
    parser.add_argument("--api-id", required=True)
    parser.add_argument("--api-hash", required=True)
    parser.add_argument("--bot-username", required=True)
    parser.add_argument("--platform", default="android")
    parser.add_argument("--start-param", default="live_canary")
    parser.add_argument("--short-name", dest="short_names", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.short_names:
        args.short_names = ["app", "webapp", "miniapp", "main", "start"]
    results = asyncio.run(run_probe(args))
    print(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
