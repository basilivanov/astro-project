from __future__ import annotations

from typing import Dict, Iterable, List

from .config import load_config
from .types import GraceConfig, SliceProfile, WatchFlow


class SliceRegistry:
    def __init__(self, config: GraceConfig | None = None) -> None:
        self._config = config or load_config()
        self._map: Dict[str, SliceProfile] = {
            profile.key.upper(): profile for profile in self._config.slices
        }

    @property
    def config(self) -> GraceConfig:
        return self._config

    @property
    def watch_flows(self) -> List[WatchFlow]:
        return self._config.watch_flows

    def get(self, key: str) -> SliceProfile:
        lookup = key.upper()
        if lookup not in self._map:
            raise KeyError(f"Unknown slice '{key}'. Available: {', '.join(self._map)}")
        return self._map[lookup]

    def all(self) -> Iterable[SliceProfile]:
        return self._map.values()
