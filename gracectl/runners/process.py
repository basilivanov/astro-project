from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional


class ProcessRunner:
    def __init__(self, cwd: Path | None = None) -> None:
        self._cwd = cwd

    def run(self, command: str, log_path: Optional[Path] = None, timeout: Optional[int] = None) -> tuple[int, float]:
        start = time.time()
        log_file = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_file = log_path.open("w", encoding="utf-8")
        try:
            completed = subprocess.run(
                command,
                cwd=self._cwd,
                shell=True,
                stdout=log_file or subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
            code = completed.returncode
        finally:
            if log_file:
                log_file.close()
        duration = time.time() - start
        return code, duration
