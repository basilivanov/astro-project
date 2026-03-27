from __future__ import annotations

from ductor_bot.cli.codex_health import CodexHealthMonitor

_CODEX_HEALTH = CodexHealthMonitor()


class TaskHub:
    def __init__(self, registry, paths, cli_service, config) -> None:
        self.registry = registry
        self.paths = paths
        self.cli_service = cli_service
        self.config = config

    def submit(self, submit) -> object:
        if (submit.provider_override or "").lower() == "codex":
            _CODEX_HEALTH.ensure_healthy()
        return submit
