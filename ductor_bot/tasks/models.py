from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSubmit:
    chat_id: int
    message_id: int
    parent_agent: str
    name: str
    prompt: str
    provider_override: str | None = None
    model_override: str | None = None
    thinking_override: str | None = None
    thread_id: str | None = None

