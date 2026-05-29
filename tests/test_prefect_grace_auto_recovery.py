import pytest
from unittest.mock import MagicMock
from prefect_grace.flows.pipeline_phases.context import PipelineRuntime, PipelineDeps, PipelineState
from prefect_grace.models import (
    FeatureStatus,
    PacketStatus,
    ReviewVerdict,
    WaveVerdict,
    TestVerdict,
    ObservabilityVerdict,
    ReasoningProfile,
)
from prefect_grace.flows.pipeline_phases.wave_role_handlers import (
    handle_verifier_packet,
    handle_reviewer_packet,
    _try_verifier_auto_recovery,
)

# Tell pytest not to collect TestVerdict as a test class
TestVerdict.__test__ = False

@pytest.fixture
def mock_runtime():
    return PipelineRuntime(
        feature_id="FEAT-TEST",
        title="Test Feature",
        summary="Test Summary",
        implementation_title="Test Imp",
        implementation_summary="Test Imp Summary",
        dry_run=True,
        timeout_seconds=30,
        verifier_backend_profile="backend_quick",
        verifier_frontend_profile=None,
        verifier_frontend_commands=None,
        verifier_observability_profile=None,
        verifier_observability_commands=None,
        verifier_artifact_globs=None,
        verifier_touches_frontend=False,
        verifier_requires_frontend_visual=False,
        verifier_include_day_live_canary=False,
        agent_workdir=None,
        agent_sandbox=None,
        business_context=None,
        planner_contract=None,
        reviewer_verdict=ReviewVerdict.ACCEPTED.value,
        review_reasons=None,
        verifier_test_verdict=TestVerdict.PASSED.value,
        verifier_observability_verdict=ObservabilityVerdict.CLEAN.value,
        verifier_frontend_visual_verdict=None,
        verifier_commands_run=None,
        verifier_evidence_paths=None,
        verifier_blocking_issues=None,
        wave_verdict=WaveVerdict.ACCEPTED.value,
        wave_reasons=None,
        create_rework=True,
        prefer_agent_output=False,
        run_architect=True,
        run_planner=False,
        commit_hash=None,
        rework_routing_policy="architect_first",
        reviewer_verdict_script=None,
        review_reasons_script=None,
        wave_verdict_script=None,
        wave_reasons_script=None,
    )

@pytest.fixture
def mock_deps():
    deps = MagicMock()
    deps.tags = MagicMock()
    deps.tags.return_value.__enter__ = MagicMock()
    deps.tags.return_value.__exit__ = MagicMock()
    
    # Mock task helpers
    deps.run_verifier_packet_task = MagicMock()
    deps.resolve_verifier_result_task = MagicMock()
    deps.record_verifier_result_task = MagicMock()
    deps.mark_packet_status_task = MagicMock()
    
    # Mock update_record to return a dict with update applied
    def fake_update_record(schema, table, key_name, key_val, updates):
        return {
            "packet_id": key_val,
            "feature_id": "FEAT-TEST",
            "wave_id": "W01",
            "title": "Reviewer Rework",
            "role": "reviewer",
            "dependencies": [],
            "write_scope": [],
            "inputs": [],
            "acceptance_criteria": [],
            "reviewer_gate": [],
            **updates
        }
    deps.update_record = MagicMock(side_effect=fake_update_record)
    
    deps.append_unique_packet = MagicMock(side_effect=lambda q, p: q.append(p))
    deps.packet_result_key = MagicMock(side_effect=lambda role, pid: f"{role}-{pid}")
    deps.reviewer_target_packet_id = MagicMock(return_value="CODER-1")
    deps.classify_rework_route = MagicMock(return_value="self_resolvable_rework")
    deps.classify_rework_mode = MagicMock(return_value="light_resume")
    deps.route_reviewer_verdict_task = MagicMock()
    deps.publish_packet_review_artifacts_task = MagicMock()
    deps.publish_feature_artifacts_task = MagicMock()
    deps.resolve_reviewer_decision_task = MagicMock()
    deps.escalate_repeated_observability_rework_for_pipeline = MagicMock(side_effect=lambda dec, **kwargs: dec)
    deps.normalize_reviewer_decision_for_pipeline = MagicMock(side_effect=lambda dec: dec)
    
    return deps

@pytest.fixture
def mock_state():
    state = PipelineState()
    state.seeded = {"feature": {"feature_id": "FEAT-TEST", "title": "Test"}}
    
    # Setup some dummy packets
    state.packets_by_id = {
        "CODER-1": {
            "packet_id": "CODER-1",
            "feature_id": "FEAT-TEST",
            "wave_id": "W01",
            "title": "Coder Packet",
            "role": "coder",
            "execution_hints": {
                "verifier_rework_attempt": 0,
                "verifier_rework_max_attempts": 3,
            }
        },
        "VERIFIER-1": {
            "packet_id": "VERIFIER-1",
            "parent_packet_id": "CODER-1",
            "feature_id": "FEAT-TEST",
            "wave_id": "W01",
            "title": "Verifier Packet",
            "role": "verifier",
            "dependencies": ["CODER-1"]
        },
        "REVIEWER-1": {
            "packet_id": "REVIEWER-1",
            "parent_packet_id": "CODER-1",
            "feature_id": "FEAT-TEST",
            "wave_id": "W01",
            "title": "Reviewer Packet",
            "role": "reviewer",
            "dependencies": ["CODER-1", "VERIFIER-1"]
        }
    }
    
    return state

def test_verifier_run_failed_triggers_recovery(mock_runtime, mock_deps, mock_state):
    """Test that when a verifier run fails (returncode != 0), auto-recovery is initiated if attempts remain."""
    mock_deps.run_verifier_packet_task.return_value = {"returncode": 1}
    
    queue_packets = []
    queue_ids = set()
    
    res = handle_verifier_packet(
        mock_runtime,
        mock_deps,
        mock_state,
        packet_id="VERIFIER-1",
        wave_id="W01",
        queue_packets=queue_packets,
        queue_ids=queue_ids,
    )
    
    # handle_verifier_packet should return None since execution continues due to auto-recovery retry enqueuing
    assert res is None
    assert mock_deps.mark_packet_status_task.call_count > 0
    
    # 3 new packets (rework coder, verifier, reviewer) should be enqueued
    assert len(queue_packets) == 3
    assert len(queue_ids) == 3
    
    # Coder packet attempt counter should be updated
    coder_hints = mock_state.packets_by_id["CODER-1"]["execution_hints"]
    assert coder_hints["verifier_rework_attempt"] == 1

def test_verifier_run_failed_max_attempts_exceeded(mock_runtime, mock_deps, mock_state):
    """Test that when verifier fails and max attempts is reached, recovery is NOT triggered and it fails closed."""
    mock_deps.run_verifier_packet_task.return_value = {"returncode": 1}
    mock_deps.final_failure.return_value = {"outcome": "failed"}
    
    mock_state.packets_by_id["CODER-1"]["execution_hints"]["verifier_rework_attempt"] = 3
    
    queue_packets = []
    queue_ids = set()
    
    res = handle_verifier_packet(
        mock_runtime,
        mock_deps,
        mock_state,
        packet_id="VERIFIER-1",
        wave_id="W01",
        queue_packets=queue_packets,
        queue_ids=queue_ids,
    )
    
    # Recovery should not happen, should return final failure dict
    assert res is not None
    assert res["final_status"]["outcome"] == "failed"
    assert len(queue_packets) == 0

def test_verifier_test_verdict_failed_triggers_recovery(mock_runtime, mock_deps, mock_state):
    """Test that when verifier run succeeds but test verdict is FAILED, auto-recovery is initiated."""
    mock_deps.run_verifier_packet_task.return_value = {"returncode": 0}
    mock_deps.resolve_verifier_result_task.return_value = {
        "test_verdict": TestVerdict.FAILED.value,
        "observability_verdict": ObservabilityVerdict.CLEAN.value,
        "blocking_issues": ["Assertion failed"]
    }
    
    queue_packets = []
    queue_ids = set()
    
    res = handle_verifier_packet(
        mock_runtime,
        mock_deps,
        mock_state,
        packet_id="VERIFIER-1",
        wave_id="W01",
        queue_packets=queue_packets,
        queue_ids=queue_ids,
    )
    
    assert res is None
    assert len(queue_packets) == 3
    assert mock_state.packets_by_id["CODER-1"]["execution_hints"]["verifier_rework_attempt"] == 1

def test_reviewer_write_scope_block_triggers_recovery(mock_runtime, mock_deps, mock_state):
    """Test that when a reviewer verdict is BLOCKED because of write scope, auto-recovery is initiated."""
    mock_deps.resolve_reviewer_decision_task.return_value = {
        "packet_verdict": ReviewVerdict.BLOCKED.value,
        "reasons": ["insufficient write scope allowed for this feature"]
    }
    mock_deps.route_reviewer_verdict_task.return_value = {
        "reviewer_verdict": ReviewVerdict.BLOCKED.value,
        "review": {
            "reasons": ["insufficient write scope allowed for this feature"]
        }
    }
    
    queue_packets = []
    queue_ids = set()
    
    res = handle_reviewer_packet(
        mock_runtime,
        mock_deps,
        mock_state,
        packet=mock_state.packets_by_id["REVIEWER-1"],
        packet_id="REVIEWER-1",
        packet_run={},
        wave_id="W01",
        queue_packets=queue_packets,
        queue_ids=queue_ids,
    )
    
    assert res is None
    assert len(queue_packets) == 3
    assert mock_state.packets_by_id["CODER-1"]["execution_hints"]["verifier_rework_attempt"] == 1
