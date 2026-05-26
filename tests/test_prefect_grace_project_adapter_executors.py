"""
Tests for project adapter executor config extension.

Validates backward compatibility and executors field parsing.
"""

import pytest
from prefect_grace.platform.project_adapter import AgentExecutorConfig


def test_agent_executor_config_without_executors():
    """Verify backward compatibility: executors field is optional."""
    data = {
        "default": "codex-cli",
        "command": "codex1",
    }

    config = AgentExecutorConfig.from_dict(data)

    assert config.default == "codex-cli"
    assert config.command == "codex1"
    assert config.executors is None


def test_agent_executor_config_with_executors():
    """Verify executors field parsing."""
    data = {
        "default": "codex-cli",
        "command": "codex1",
        "executors": [
            {
                "executor_id": "codex-cli",
                "kind": "codex",
                "command": "codex1",
                "enabled": True,
            },
            {
                "executor_id": "claude-sonnet",
                "kind": "claude",
                "command": "claude",
                "enabled": False,
            },
        ],
    }

    config = AgentExecutorConfig.from_dict(data)

    assert config.default == "codex-cli"
    assert config.command == "codex1"
    assert config.executors is not None
    assert len(config.executors) == 2
    assert config.executors[0]["executor_id"] == "codex-cli"
    assert config.executors[1]["executor_id"] == "claude-sonnet"


def test_agent_executor_config_to_dict_without_executors():
    """Verify to_dict() without executors."""
    config = AgentExecutorConfig(
        default="codex-cli",
        command="codex1",
        executors=None,
    )

    result = config.to_dict()

    assert result["default"] == "codex-cli"
    assert result["command"] == "codex1"
    assert "executors" not in result


def test_agent_executor_config_to_dict_with_executors():
    """Verify to_dict() includes executors."""
    executors = [
        {
            "executor_id": "codex-cli",
            "kind": "codex",
            "command": "codex1",
        },
    ]

    config = AgentExecutorConfig(
        default="codex-cli",
        command="codex1",
        executors=executors,
    )

    result = config.to_dict()

    assert result["default"] == "codex-cli"
    assert result["command"] == "codex1"
    assert result["executors"] == executors
