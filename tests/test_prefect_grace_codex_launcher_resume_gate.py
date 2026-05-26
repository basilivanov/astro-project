import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from prefect_grace.platform.state_store import PacketRegistryStore
from prefect_grace.tasks.codex_launcher import launch_codex_for_packet


def test_launch_codex_blocks_resume_when_registry_disallows(tmp_path, monkeypatch):
    """
    Verify launch_codex_for_packet forces fresh session when resume_allowed=False.
    """
    # Setup state directory
    state_root = tmp_path / "prefect_grace" / "state"
    state_root.mkdir(parents=True)
    runs_dir = tmp_path / "prefect_grace" / "state" / "runs"
    runs_dir.mkdir(parents=True)
    packets_dir = tmp_path / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    # Monkeypatch paths
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", runs_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", packets_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.ROOT_DIR", tmp_path)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.STATE_ROOT", state_root)

    # Create registry with resume blocked
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-P1-W01-IMPL",
        "feature_id": "TEST-P1",
        "role": "coder",
        "source_hash": "sha256:new_hash",
        "last_executed_source_hash": "sha256:old_hash",
        "resume_allowed": False,
        "resume_block_reason": "contract_changed",
        "recommended_rework_mode": "bounded_fresh",
        "execution_hints": {
            "resume_strategy": "packet_parent",
            "resume_parent_packet_id": "TEST-P1-W01-PARENT",
        },
    })

    # Create parent packet with thread_id (would normally allow resume)
    registry.upsert_packet({
        "packet_id": "TEST-P1-W01-PARENT",
        "last_thread_id": "old-thread-123",
    })

    # Mock find_record to return our packet
    def mock_find_record(store, collection, key, value):
        if value == "TEST-P1-W01-IMPL":
            return registry.load_packet("TEST-P1-W01-IMPL")
        elif value == "TEST-P1-W01-PARENT":
            return registry.load_packet("TEST-P1-W01-PARENT")
        raise KeyError(f"Not found: {value}")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.find_record", mock_find_record)

    # Mock update_record
    update_calls = []
    def mock_update_record(store, collection, key, value, patch):
        update_calls.append((value, patch))
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.update_record", mock_update_record)

    # Mock agent config
    mock_config = {
        "codex": {
            "binary": "codex1",
            "shared_model": "gpt-5.4",
            "workdir": str(tmp_path),
            "roles": {
                "coder": {
                    "reasoning": "high",
                    "sandbox": "workspace-write",
                    "approval": "never",
                    "resume_strategy": "packet_parent",
                }
            }
        }
    }
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.load_agent_config", lambda: mock_config)

    # Mock role_prompt_for
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.role_prompt_for", lambda role: "Test prompt")

    # Mock build_packet_prompt
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.build_packet_prompt", lambda p, rp: "Test packet prompt")

    # Mock resolve_execution_workdir
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.resolve_execution_workdir", lambda w: str(tmp_path))

    # Launch with dry_run=True to avoid actual codex execution
    result = launch_codex_for_packet(
        "TEST-P1-W01-IMPL",
        dry_run=True,
        timeout_seconds=60,
    )

    # Verify result
    assert result["packet_id"] == "TEST-P1-W01-IMPL"
    assert result["session_mode"] == "exec"  # Should be exec, not resume
    assert result["resumed_from_thread_id"] is None  # Should NOT resume from parent
    assert result["resume_strategy"] == "packet_parent"  # Strategy is still packet_parent, but not used


def test_launch_codex_allows_resume_when_registry_allows(tmp_path, monkeypatch):
    """
    Verify launch_codex_for_packet allows resume when resume_allowed=True.
    """
    # Setup state directory
    state_root = tmp_path / "prefect_grace" / "state"
    state_root.mkdir(parents=True)
    runs_dir = tmp_path / "prefect_grace" / "state" / "runs"
    runs_dir.mkdir(parents=True)
    packets_dir = tmp_path / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    # Monkeypatch paths
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", runs_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", packets_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.ROOT_DIR", tmp_path)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.STATE_ROOT", state_root)

    # Create registry with resume allowed
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-P2-W01-IMPL",
        "feature_id": "TEST-P2",
        "role": "coder",
        "source_hash": "sha256:same_hash",
        "last_executed_source_hash": "sha256:same_hash",
        "resume_allowed": True,
        "latest_coder_session_id": "session-456",
        "execution_hints": {
            "resume_strategy": "packet_parent",
            "resume_parent_packet_id": "TEST-P2-W01-PARENT",
        },
    })

    # Create parent packet with thread_id
    registry.upsert_packet({
        "packet_id": "TEST-P2-W01-PARENT",
        "last_thread_id": "parent-thread-789",
    })

    # Mock find_record
    def mock_find_record(store, collection, key, value):
        if value == "TEST-P2-W01-IMPL":
            return registry.load_packet("TEST-P2-W01-IMPL")
        elif value == "TEST-P2-W01-PARENT":
            return registry.load_packet("TEST-P2-W01-PARENT")
        raise KeyError(f"Not found: {value}")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.find_record", mock_find_record)

    # Mock update_record
    update_calls = []
    def mock_update_record(store, collection, key, value, patch):
        update_calls.append((value, patch))
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.update_record", mock_update_record)

    # Mock agent config
    mock_config = {
        "codex": {
            "binary": "codex1",
            "shared_model": "gpt-5.4",
            "workdir": str(tmp_path),
            "roles": {
                "coder": {
                    "reasoning": "high",
                    "sandbox": "workspace-write",
                    "approval": "never",
                    "resume_strategy": "packet_parent",
                }
            }
        }
    }
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.load_agent_config", lambda: mock_config)

    # Mock role_prompt_for
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.role_prompt_for", lambda role: "Test prompt")

    # Mock build_packet_prompt
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.build_packet_prompt", lambda p, rp: "Test packet prompt")

    # Mock resolve_execution_workdir
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.resolve_execution_workdir", lambda w: str(tmp_path))

    # Launch with dry_run=True
    result = launch_codex_for_packet(
        "TEST-P2-W01-IMPL",
        dry_run=True,
        timeout_seconds=60,
    )

    # Verify result
    assert result["packet_id"] == "TEST-P2-W01-IMPL"
    assert result["session_mode"] == "resume"  # Should be resume
    assert result["resumed_from_thread_id"] == "parent-thread-789"  # Should resume from parent
    assert result["resume_strategy"] == "packet_parent"


def test_launch_codex_records_execution_state_after_coder_success(tmp_path, monkeypatch):
    """
    Verify launch_codex_for_packet records last_executed_source_hash and latest_coder_session_id
    after successful coder execution.
    """
    # Setup state directory
    state_root = tmp_path / "prefect_grace" / "state"
    state_root.mkdir(parents=True)
    runs_dir = tmp_path / "prefect_grace" / "state" / "runs"
    runs_dir.mkdir(parents=True)
    packets_dir = tmp_path / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    # Monkeypatch paths
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", runs_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", packets_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.ROOT_DIR", tmp_path)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.STATE_ROOT", state_root)

    # Create registry with coder packet
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-P3-W01-IMPL",
        "feature_id": "TEST-P3",
        "role": "coder",
        "source_hash": "sha256:current_hash_v2",
        "last_executed_source_hash": "sha256:old_hash_v1",
        "resume_allowed": False,
        "resume_block_reason": "contract_changed",
        "execution_hints": {
            "resume_strategy": "none",
        },
    })

    # Mock find_record
    def mock_find_record(store, collection, key, value):
        if value == "TEST-P3-W01-IMPL":
            return registry.load_packet("TEST-P3-W01-IMPL")
        raise KeyError(f"Not found: {value}")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.find_record", mock_find_record)

    # Mock update_record
    update_calls = []
    def mock_update_record(store, collection, key, value, patch):
        update_calls.append((value, patch))
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.update_record", mock_update_record)

    # Mock agent config
    mock_config = {
        "codex": {
            "binary": "codex1",
            "shared_model": "gpt-5.4",
            "workdir": str(tmp_path),
            "roles": {
                "coder": {
                    "reasoning": "high",
                    "sandbox": "workspace-write",
                    "approval": "never",
                    "resume_strategy": "none",
                }
            }
        }
    }
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.load_agent_config", lambda: mock_config)

    # Mock role_prompt_for
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.role_prompt_for", lambda role: "Test prompt")

    # Mock build_packet_prompt
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.build_packet_prompt", lambda p, rp: "Test packet prompt")

    # Mock resolve_execution_workdir
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.resolve_execution_workdir", lambda w: str(tmp_path))

    # Mock _run_codex_process to simulate successful execution with thread_id
    def mock_run_codex_process(command, **kwargs):
        from prefect_grace.tasks.codex_launcher import CodexProcessResult
        # Write fake stdout with thread.started event
        stdout_path = kwargs["stdout_path"]
        stdout_path.write_text(
            json.dumps({"type": "thread.started", "thread_id": "new-thread-abc123"}) + "\n"
            + json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 50, "reasoning_tokens": 0}}) + "\n",
            encoding="utf-8"
        )
        kwargs["stderr_path"].write_text("", encoding="utf-8")
        return CodexProcessResult(returncode=0, termination_reason="completed")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher._run_codex_process", mock_run_codex_process)

    # Track registry update_resume_state calls
    registry_update_calls = []
    original_update_resume_state = PacketRegistryStore.update_resume_state
    def mock_update_resume_state(self, packet_id, **kwargs):
        registry_update_calls.append({
            "packet_id": packet_id,
            **kwargs
        })
        return original_update_resume_state(self, packet_id, **kwargs)

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.PacketRegistryStore.update_resume_state", mock_update_resume_state)

    # Launch with dry_run=False to trigger actual execution path
    result = launch_codex_for_packet(
        "TEST-P3-W01-IMPL",
        dry_run=False,
        timeout_seconds=60,
    )

    # Verify execution succeeded
    assert result["returncode"] == 0
    assert result["thread_id"] == "new-thread-abc123"
    assert result["session_mode"] == "exec"

    # Verify registry.update_resume_state was called with correct values
    assert len(registry_update_calls) == 1
    assert registry_update_calls[0]["packet_id"] == "TEST-P3-W01-IMPL"
    assert registry_update_calls[0]["last_executed_source_hash"] == "sha256:current_hash_v2"
    assert registry_update_calls[0]["latest_coder_session_id"] == "new-thread-abc123"

    # Verify registry state was actually updated
    updated_packet = registry.load_packet("TEST-P3-W01-IMPL")
    assert updated_packet["last_executed_source_hash"] == "sha256:current_hash_v2"
    assert updated_packet["latest_coder_session_id"] == "new-thread-abc123"


def test_launch_codex_fails_closed_on_registry_error_for_managed_strategy(tmp_path, monkeypatch):
    """
    Verify launch_codex_for_packet blocks resume when registry fails for managed strategy (packet_parent).
    """
    # Setup state directory
    state_root = tmp_path / "prefect_grace" / "state"
    state_root.mkdir(parents=True)
    runs_dir = tmp_path / "prefect_grace" / "state" / "runs"
    runs_dir.mkdir(parents=True)
    packets_dir = tmp_path / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    # Monkeypatch paths
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", runs_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", packets_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.ROOT_DIR", tmp_path)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.STATE_ROOT", state_root)

    # Create registry with packet
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-P4-W01-IMPL",
        "feature_id": "TEST-P4",
        "role": "coder",
        "source_hash": "sha256:hash_v1",
        "execution_hints": {
            "resume_strategy": "packet_parent",
            "resume_parent_packet_id": "TEST-P4-W01-PARENT",
        },
    })

    # Create parent packet with thread_id
    registry.upsert_packet({
        "packet_id": "TEST-P4-W01-PARENT",
        "last_thread_id": "parent-thread-xyz",
    })

    # Track how many times _check_resume_allowed is called and with what strategy
    check_resume_calls = []

    # Mock _check_resume_allowed to simulate registry error for managed strategy
    def mock_check_resume_allowed(packet_id, resume_strategy, logger=None):
        check_resume_calls.append({"packet_id": packet_id, "resume_strategy": resume_strategy})
        # Simulate registry error for managed strategy - should fail closed
        if resume_strategy in {"feature_role", "packet_parent"}:
            if logger is not None:
                logger.error(
                    "Registry error for managed resume strategy packet=%s strategy=%s error=%s. Blocking resume for safety.",
                    packet_id,
                    resume_strategy,
                    "Simulated registry corruption",
                )
            return False  # Fail closed
        return True  # Fail open for legacy

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher._check_resume_allowed", mock_check_resume_allowed)

    # Mock find_record
    def mock_find_record(store, collection, key, value):
        if value == "TEST-P4-W01-IMPL":
            return registry.load_packet("TEST-P4-W01-IMPL")
        elif value == "TEST-P4-W01-PARENT":
            return registry.load_packet("TEST-P4-W01-PARENT")
        raise KeyError(f"Not found: {value}")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.find_record", mock_find_record)

    # Mock update_record
    update_calls = []
    def mock_update_record(store, collection, key, value, patch):
        update_calls.append((value, patch))
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.update_record", mock_update_record)

    # Mock agent config
    mock_config = {
        "codex": {
            "binary": "codex1",
            "shared_model": "gpt-5.4",
            "workdir": str(tmp_path),
            "roles": {
                "coder": {
                    "reasoning": "high",
                    "sandbox": "workspace-write",
                    "approval": "never",
                    "resume_strategy": "packet_parent",
                }
            }
        }
    }
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.load_agent_config", lambda: mock_config)

    # Mock role_prompt_for
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.role_prompt_for", lambda role: "Test prompt")

    # Mock build_packet_prompt
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.build_packet_prompt", lambda p, rp: "Test packet prompt")

    # Mock resolve_execution_workdir
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.resolve_execution_workdir", lambda w: str(tmp_path))

    # Launch with dry_run=True
    result = launch_codex_for_packet(
        "TEST-P4-W01-IMPL",
        dry_run=True,
        timeout_seconds=60,
    )

    # Verify _check_resume_allowed was called with correct strategy
    assert len(check_resume_calls) == 1
    assert check_resume_calls[0]["packet_id"] == "TEST-P4-W01-IMPL"
    assert check_resume_calls[0]["resume_strategy"] == "packet_parent"

    # Verify result - should force fresh session due to registry error with managed strategy
    assert result["packet_id"] == "TEST-P4-W01-IMPL"
    assert result["session_mode"] == "exec"  # Should be exec, not resume (fail-closed)
    assert result["resumed_from_thread_id"] is None  # Should NOT resume from parent
    assert result["resume_strategy"] == "packet_parent"  # Strategy is still packet_parent, but blocked by registry error
