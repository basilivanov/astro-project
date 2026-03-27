from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class FailurePacketWriter:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, slice_key: str, check_id: str, details: Dict[str, Any]) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"{slice_key.lower()}-{check_id}-{timestamp}.json"
        target = self._base_dir / filename
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "slice": slice_key,
            "check_id": check_id,
            "details": details,
        }
        with target.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return target
