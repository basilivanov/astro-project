from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from shutil import which


@dataclass(frozen=True)
class CodexHealthStatus:
    ok: bool
    ping_ok: bool
    state_ok: bool
    details: str
    checked_at: float


def _default_codex_home() -> Path:
    env_home = os.environ.get("CODEX_HOME", "").strip()
    if env_home:
        return Path(env_home).expanduser()

    cliproxy_home = Path.home() / ".ductor" / "codex-cliproxy-home"
    if cliproxy_home.exists():
        return cliproxy_home

    return Path.home() / ".codex"


class CodexHealthMonitor:
    def __init__(self, codex_home: Path | None = None, ttl_seconds: float = 15.0) -> None:
        self.codex_home = Path(codex_home) if codex_home is not None else _default_codex_home()
        self.ttl_seconds = ttl_seconds
        self._cached_status: CodexHealthStatus | None = None

    def get_status(self, force: bool = False) -> CodexHealthStatus:
        now = time.time()
        if not force and self._cached_status and now - self._cached_status.checked_at < self.ttl_seconds:
            return self._cached_status

        ping_ok, ping_details = self._check_ping()
        state_ok, state_details = self._check_state()
        details = "; ".join(part for part in (ping_details, state_details) if part)
        status = CodexHealthStatus(
            ok=ping_ok and state_ok,
            ping_ok=ping_ok,
            state_ok=state_ok,
            details=details or "ok",
            checked_at=now,
        )
        self._cached_status = status
        return status

    def ensure_healthy(self) -> CodexHealthStatus:
        status = self.get_status()
        if not status.ok:
            raise RuntimeError(f"Codex CLI is unhealthy: {status.details}")
        return status

    def to_payload(self, force: bool = False) -> dict[str, object]:
        status = self.get_status(force=force)
        return {
            "status": "ready" if status.ok else "error",
            "ok": status.ok,
            "ping_ok": status.ping_ok,
            "state_ok": status.state_ok,
            "details": status.details,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(status.checked_at)),
        }

    def _check_ping(self) -> tuple[bool, str]:
        cli_path = which("codex")
        if not cli_path:
            return False, "codex binary missing"
        try:
            result = subprocess.run(
                [cli_path, "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return False, "codex binary missing"
        except Exception as exc:
            return False, f"codex ping failed: {exc}"
        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "unknown error").strip()
            return False, f"codex ping failed: {error_text}"
        return True, "ping ok"

    def _check_state(self) -> tuple[bool, str]:
        auth_path = self.codex_home / "auth.json"
        if not auth_path.exists():
            return False, "missing auth file"
        try:
            payload = json.loads(auth_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return False, f"bad auth file: {exc}"
        if not payload.get("token"):
            return False, "auth token missing"

        state_files = sorted(self.codex_home.glob("state*.sqlite"))
        if not state_files:
            return False, "missing state sqlite"
        state_path = state_files[0]
        try:
            with sqlite3.connect(state_path) as conn:
                conn.execute("select 1")
        except Exception as exc:
            return False, f"bad state sqlite: {exc}"
        return True, f"state ok: {state_path.name}"
