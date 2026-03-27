from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from ..types import CheckResult, CommandSummary


class ResultStore:
    def __init__(self, report_path: Path, log_dir: Path) -> None:
        self._path = report_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def write(self, summary: CommandSummary) -> None:
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "command": summary.command,
            "target": summary.target,
            "status": summary.status,
            "passed": summary.passed,
            "failed": summary.failed,
            "skipped": summary.skipped,
            "checks": [self._serialize_check(check) for check in summary.checks],
        }
        with self._path.open("a", encoding="utf-8") as handle:
            json.dump(payload, handle)
            handle.write("\n")

    def _serialize_check(self, check: CheckResult) -> dict:
        return {
            "id": check.id,
            "label": check.label,
            "status": check.status,
            "duration_ms": check.duration_ms,
            "exit_code": check.exit_code,
            "stdout_path": str(check.stdout_path) if check.stdout_path else None,
            "failure_packet": str(check.failure_packet) if check.failure_packet else None,
        }

    @property
    def log_dir(self) -> Path:
        return self._log_dir
