from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class SliceCommands:
    backend: List[str] = field(default_factory=list)
    frontend: List[str] = field(default_factory=list)
    replay: List[str] = field(default_factory=list)


@dataclass
class SliceProfile:
    key: str
    title: str
    description: str
    gate: str
    vm_ids: List[str]
    docs: List[Path]
    commands: SliceCommands
    evidence: List[Path]


@dataclass
class Defaults:
    report_path: Path
    log_dir: Path
    frontend_container: str
    backend_container: str
    repo_root: Path


@dataclass
class GraceConfig:
    defaults: Defaults
    slices: List[SliceProfile]
    watch_flows: List["WatchFlow"]

    def get_slice(self, key: str) -> Optional[SliceProfile]:
        lookup = key.upper()
        for profile in self.slices:
            if profile.key.upper() == lookup:
                return profile
        return None


@dataclass
class CheckResult:
    id: str
    label: str
    status: str
    duration_ms: int
    exit_code: Optional[int] = None
    stdout_path: Optional[Path] = None
    failure_packet: Optional[Path] = None


@dataclass
class CommandSummary:
    command: str
    target: str
    status: str
    passed: int
    failed: int
    skipped: int = 0
    checks: Iterable[CheckResult] = field(default_factory=list)


@dataclass
class WatchFlow:
    id: str
    label: str
    script: str
    args: Dict[str, object] = field(default_factory=dict)
    json_output: bool = False
    stale_after: Optional[str] = None
    slices: List[str] = field(default_factory=list)
