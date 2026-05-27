"""Tests for E2E packet runner artifact helper."""

import importlib

import prefect_grace.tasks.e2e_packet_artifacts as e2e_artifacts
from prefect_grace.tasks.e2e_packet_artifacts import (
    _build_artifact_markdown,
    _get_create_markdown_artifact,
    publish_e2e_packet_run_artifact,
)


def _sample_result() -> dict:
    return {
        "ok": False,
        "packet_id": "TEST-W01-E2E",
        "attempt": 2,
        "runtime_status": "completed",
        "domain_status": "rework_required",
        "registry_status": "ready_for_retry",
        "registry_reason": "quality_rework",
        "registry_transition": {
            "registry_status": "ready_for_retry",
            "reason": "quality_rework",
            "is_terminal": False,
            "is_failure": False,
        },
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "executor_id": "codex",
        "managed_runner_result": {
            "domain_status": "passed",
            "blocker_reason": None,
        },
        "handoff_result": {
            "domain_status": "rework_required",
            "blocker_reason": "Reviewer requested fixes",
        },
        "artifact_paths": ["/tmp/evidence.json", "/tmp/review.md"],
        "errors": ["Reviewer requested fixes"],
    }


def test_get_create_markdown_artifact_returns_none_when_prefect_unavailable(monkeypatch):
    """Verify lazy Prefect artifact import returns None when unavailable."""
    original_import = importlib.import_module

    def mock_import(name):
        if name == "prefect.artifacts":
            raise ImportError("Prefect not available")
        return original_import(name)

    monkeypatch.setattr(importlib, "import_module", mock_import)

    assert _get_create_markdown_artifact() is None


def test_build_artifact_markdown_includes_operator_fields():
    """Verify E2E artifact markdown includes packet, runtime, registry, and handoff details."""
    markdown = _build_artifact_markdown(_sample_result())

    assert "# E2E Packet Run: REWORK_REQUIRED" in markdown
    assert "**Packet ID:** `TEST-W01-E2E`" in markdown
    assert "**Attempt:** `2`" in markdown
    assert "**Runtime Status:** `completed`" in markdown
    assert "**Domain Status:** `rework_required`" in markdown
    assert "**Registry Status:** `ready_for_retry`" in markdown
    assert "**Registry Reason:** `quality_rework`" in markdown
    assert "**Worktree Path:** `/tmp/worktree`" in markdown
    assert "**Executor ID:** `codex`" in markdown
    assert "**Managed Runner Status:** `passed`" in markdown
    assert "**Handoff Status:** `rework_required`" in markdown
    assert "Reviewer requested fixes" in markdown
    assert "- `/tmp/evidence.json`" in markdown
    assert "- `/tmp/review.md`" in markdown


def test_publish_e2e_packet_run_artifact_returns_empty_when_unavailable(monkeypatch):
    """Verify publish returns [] when Prefect artifacts are unavailable."""
    monkeypatch.setattr(e2e_artifacts, "_get_create_markdown_artifact", lambda: None)

    assert publish_e2e_packet_run_artifact(_sample_result()) == []


def test_publish_e2e_packet_run_artifact_creates_markdown(monkeypatch):
    """Verify publish calls create_markdown_artifact with JSON-safe metadata."""
    created = []

    def fake_create_markdown_artifact(**kwargs):
        created.append(kwargs)
        return "artifact-e2e-1"

    monkeypatch.setattr(
        e2e_artifacts,
        "_get_create_markdown_artifact",
        lambda: fake_create_markdown_artifact,
    )

    artifact_ids = publish_e2e_packet_run_artifact(_sample_result())

    assert artifact_ids == ["artifact-e2e-1"]
    assert created[0]["key"] == "e2e-packet-TEST-W01-E2E-attempt-2"
    assert created[0]["description"] == "E2E packet run: rework_required"
    assert "**Registry Status:** `ready_for_retry`" in created[0]["markdown"]


def test_publish_e2e_packet_run_artifact_returns_empty_on_exception(monkeypatch):
    """Verify publication failure does not raise or mutate domain result."""
    def failing_create_markdown_artifact(**kwargs):
        raise RuntimeError("artifact backend unavailable")

    monkeypatch.setattr(
        e2e_artifacts,
        "_get_create_markdown_artifact",
        lambda: failing_create_markdown_artifact,
    )

    result = _sample_result()
    artifact_ids = publish_e2e_packet_run_artifact(result)

    assert artifact_ids == []
    assert result["domain_status"] == "rework_required"
    assert result["registry_status"] == "ready_for_retry"
