"""Tests for GRACE status model."""

import pytest
from prefect_grace.platform.status_model import (
    SourcePacketStatus,
    RegistryStatus,
    DomainStatus,
    StatusTransition,
    normalize_source_status,
    normalize_registry_status,
    normalize_domain_status,
    apply_domain_result_to_registry,
    is_terminal_registry_status,
    is_runnable_registry_status,
    is_failure_domain_status,
    is_scope_domain_status,
)


# BEGIN_BLOCK: normalization_tests

def test_normalize_source_status_enum():
    """Test that enum values pass through unchanged."""
    assert normalize_source_status(SourcePacketStatus.READY) == SourcePacketStatus.READY
    assert normalize_source_status(SourcePacketStatus.BLOCKED) == SourcePacketStatus.BLOCKED
    assert normalize_source_status(SourcePacketStatus.ACCEPTED) == SourcePacketStatus.ACCEPTED


def test_normalize_source_status_strings():
    """Test that known strings map to correct enums."""
    assert normalize_source_status("ready") == SourcePacketStatus.READY
    assert normalize_source_status("READY") == SourcePacketStatus.READY
    assert normalize_source_status("blocked") == SourcePacketStatus.BLOCKED
    assert normalize_source_status("accepted") == SourcePacketStatus.ACCEPTED
    assert normalize_source_status("draft") == SourcePacketStatus.DRAFT
    assert normalize_source_status("superseded") == SourcePacketStatus.SUPERSEDED


def test_normalize_source_status_none_defaults_to_ready():
    """Test that None defaults to READY for backward compatibility."""
    assert normalize_source_status(None) == SourcePacketStatus.READY
    assert normalize_source_status("") == SourcePacketStatus.READY


def test_normalize_source_status_unknown_defaults_to_ready():
    """Test that unknown strings default to READY, not ACCEPTED."""
    assert normalize_source_status("unknown") == SourcePacketStatus.READY
    assert normalize_source_status("invalid") == SourcePacketStatus.READY


def test_normalize_registry_status_enum():
    """Test that enum values pass through unchanged."""
    assert normalize_registry_status(RegistryStatus.READY) == RegistryStatus.READY
    assert normalize_registry_status(RegistryStatus.BLOCKED) == RegistryStatus.BLOCKED
    assert normalize_registry_status(RegistryStatus.ACCEPTED) == RegistryStatus.ACCEPTED


def test_normalize_registry_status_strings():
    """Test that known strings map to correct enums."""
    assert normalize_registry_status("ready") == RegistryStatus.READY
    assert normalize_registry_status("ready_for_retry") == RegistryStatus.READY_FOR_RETRY
    assert normalize_registry_status("waiting_for_dependencies") == RegistryStatus.WAITING_FOR_DEPENDENCIES
    assert normalize_registry_status("running") == RegistryStatus.RUNNING
    assert normalize_registry_status("blocked") == RegistryStatus.BLOCKED
    assert normalize_registry_status("cascading_blocked") == RegistryStatus.CASCADING_BLOCKED
    assert normalize_registry_status("accepted") == RegistryStatus.ACCEPTED
    assert normalize_registry_status("changed_after_acceptance") == RegistryStatus.CHANGED_AFTER_ACCEPTANCE


def test_normalize_registry_status_none_defaults_to_ready():
    """Test that None defaults to READY."""
    assert normalize_registry_status(None) == RegistryStatus.READY
    assert normalize_registry_status("") == RegistryStatus.READY


def test_normalize_registry_status_unknown_defaults_to_blocked():
    """Test that unknown strings default to BLOCKED, not ACCEPTED."""
    assert normalize_registry_status("unknown") == RegistryStatus.BLOCKED
    assert normalize_registry_status("invalid") == RegistryStatus.BLOCKED


def test_normalize_domain_status_enum():
    """Test that enum values pass through unchanged."""
    assert normalize_domain_status(DomainStatus.ACCEPTED) == DomainStatus.ACCEPTED
    assert normalize_domain_status(DomainStatus.BLOCKED) == DomainStatus.BLOCKED
    assert normalize_domain_status(DomainStatus.REWORK_REQUIRED) == DomainStatus.REWORK_REQUIRED


def test_normalize_domain_status_strings():
    """Test that known strings map to correct enums."""
    assert normalize_domain_status("accepted") == DomainStatus.ACCEPTED
    assert normalize_domain_status("rework_required") == DomainStatus.REWORK_REQUIRED
    assert normalize_domain_status("blocked") == DomainStatus.BLOCKED
    assert normalize_domain_status("scope_blocked") == DomainStatus.SCOPE_BLOCKED
    assert normalize_domain_status("agent_failed") == DomainStatus.AGENT_FAILED
    assert normalize_domain_status("verifier_failed") == DomainStatus.VERIFIER_FAILED
    assert normalize_domain_status("reviewer_failed") == DomainStatus.REVIEWER_FAILED
    assert normalize_domain_status("runner_error") == DomainStatus.RUNNER_ERROR
    assert normalize_domain_status("handoff_error") == DomainStatus.HANDOFF_ERROR
    assert normalize_domain_status("passed") == DomainStatus.CHECK_PASSED


def test_normalize_domain_status_none_defaults_to_runner_error():
    """Test that None defaults to RUNNER_ERROR for safety."""
    assert normalize_domain_status(None) == DomainStatus.RUNNER_ERROR
    assert normalize_domain_status("") == DomainStatus.RUNNER_ERROR


def test_normalize_domain_status_unknown_defaults_to_runner_error():
    """Test that unknown strings default to RUNNER_ERROR, never ACCEPTED."""
    assert normalize_domain_status("unknown") == DomainStatus.RUNNER_ERROR
    assert normalize_domain_status("invalid") == DomainStatus.RUNNER_ERROR

# END_BLOCK: normalization_tests


# BEGIN_BLOCK: transition_tests

def test_apply_domain_result_accepted():
    """Test that accepted domain status maps to accepted registry status."""
    transition = apply_domain_result_to_registry(DomainStatus.ACCEPTED)
    assert transition.registry_status == RegistryStatus.ACCEPTED
    assert transition.reason == "execution_accepted"
    assert transition.is_terminal is True
    assert transition.is_failure is False


def test_apply_domain_result_passed():
    """Test that passed maps to accepted for local gate compatibility."""
    transition = apply_domain_result_to_registry(DomainStatus.CHECK_PASSED)
    assert transition.registry_status == RegistryStatus.ACCEPTED
    assert transition.reason == "local_gate_passed"
    assert transition.is_terminal is True
    assert transition.is_failure is False


def test_apply_domain_result_passed_string():
    """Test that 'passed' string maps to accepted."""
    transition = apply_domain_result_to_registry("passed")
    assert transition.registry_status == RegistryStatus.ACCEPTED
    assert transition.reason == "local_gate_passed"
    assert transition.is_terminal is True
    assert transition.is_failure is False


def test_apply_domain_result_rework_required():
    """Test that rework_required maps to ready_for_retry."""
    transition = apply_domain_result_to_registry(DomainStatus.REWORK_REQUIRED)
    assert transition.registry_status == RegistryStatus.READY_FOR_RETRY
    assert transition.reason == "quality_rework"
    assert transition.is_terminal is False
    assert transition.is_failure is False


def test_apply_domain_result_blocked():
    """Test that blocked maps to blocked registry status."""
    transition = apply_domain_result_to_registry(DomainStatus.BLOCKED)
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert transition.reason == "domain_blocked"
    assert transition.is_terminal is True
    assert transition.is_failure is True


def test_apply_domain_result_scope_blocked():
    """Test that scope_blocked maps to blocked with scope_violation reason."""
    transition = apply_domain_result_to_registry(DomainStatus.SCOPE_BLOCKED)
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert transition.reason == "scope_violation"
    assert transition.is_terminal is True
    assert transition.is_failure is True


def test_apply_domain_result_agent_failed():
    """Test that agent_failed maps to blocked and is not quality rework."""
    transition = apply_domain_result_to_registry(DomainStatus.AGENT_FAILED)
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert transition.reason == "agent_execution_failed"
    assert transition.is_terminal is True
    assert transition.is_failure is True


def test_apply_domain_result_verifier_failed():
    """Test that verifier_failed maps to blocked."""
    transition = apply_domain_result_to_registry(DomainStatus.VERIFIER_FAILED)
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert transition.reason == "verifier_failed"
    assert transition.is_terminal is True
    assert transition.is_failure is True


def test_apply_domain_result_reviewer_failed():
    """Test that reviewer_failed maps to blocked."""
    transition = apply_domain_result_to_registry(DomainStatus.REVIEWER_FAILED)
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert transition.reason == "reviewer_failed"
    assert transition.is_terminal is True
    assert transition.is_failure is True


def test_apply_domain_result_runner_error():
    """Test that runner_error maps to blocked."""
    transition = apply_domain_result_to_registry(DomainStatus.RUNNER_ERROR)
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert transition.reason == "runner_error"
    assert transition.is_terminal is True
    assert transition.is_failure is True


def test_apply_domain_result_handoff_error():
    """Test that handoff_error maps to blocked."""
    transition = apply_domain_result_to_registry(DomainStatus.HANDOFF_ERROR)
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert transition.reason == "handoff_error"
    assert transition.is_terminal is True
    assert transition.is_failure is True


def test_apply_domain_result_unknown_string():
    """Test that unknown domain status maps to blocked, never accepted."""
    transition = apply_domain_result_to_registry("unknown_status")
    assert transition.registry_status == RegistryStatus.BLOCKED
    assert "unknown_domain_status" in transition.reason
    assert transition.is_terminal is True
    assert transition.is_failure is True

# END_BLOCK: transition_tests


# BEGIN_BLOCK: predicate_tests

def test_is_terminal_registry_status():
    """Test terminal registry status detection."""
    assert is_terminal_registry_status(RegistryStatus.ACCEPTED) is True
    assert is_terminal_registry_status(RegistryStatus.BLOCKED) is True
    assert is_terminal_registry_status(RegistryStatus.CASCADING_BLOCKED) is True
    assert is_terminal_registry_status(RegistryStatus.CHANGED_AFTER_ACCEPTANCE) is True

    assert is_terminal_registry_status(RegistryStatus.READY) is False
    assert is_terminal_registry_status(RegistryStatus.READY_FOR_RETRY) is False
    assert is_terminal_registry_status(RegistryStatus.WAITING_FOR_DEPENDENCIES) is False
    assert is_terminal_registry_status(RegistryStatus.RUNNING) is False


def test_is_terminal_registry_status_strings():
    """Test terminal registry status detection with strings."""
    assert is_terminal_registry_status("accepted") is True
    assert is_terminal_registry_status("blocked") is True
    assert is_terminal_registry_status("ready") is False
    assert is_terminal_registry_status("running") is False


def test_is_runnable_registry_status():
    """Test runnable registry status detection."""
    assert is_runnable_registry_status(RegistryStatus.READY) is True
    assert is_runnable_registry_status(RegistryStatus.READY_FOR_RETRY) is True

    assert is_runnable_registry_status(RegistryStatus.WAITING_FOR_DEPENDENCIES) is False
    assert is_runnable_registry_status(RegistryStatus.RUNNING) is False
    assert is_runnable_registry_status(RegistryStatus.BLOCKED) is False
    assert is_runnable_registry_status(RegistryStatus.ACCEPTED) is False


def test_is_runnable_registry_status_strings():
    """Test runnable registry status detection with strings."""
    assert is_runnable_registry_status("ready") is True
    assert is_runnable_registry_status("ready_for_retry") is True
    assert is_runnable_registry_status("blocked") is False
    assert is_runnable_registry_status("running") is False


def test_is_failure_domain_status():
    """Test failure domain status detection."""
    assert is_failure_domain_status(DomainStatus.BLOCKED) is True
    assert is_failure_domain_status(DomainStatus.SCOPE_BLOCKED) is True
    assert is_failure_domain_status(DomainStatus.AGENT_FAILED) is True
    assert is_failure_domain_status(DomainStatus.VERIFIER_FAILED) is True
    assert is_failure_domain_status(DomainStatus.REVIEWER_FAILED) is True
    assert is_failure_domain_status(DomainStatus.RUNNER_ERROR) is True
    assert is_failure_domain_status(DomainStatus.HANDOFF_ERROR) is True

    assert is_failure_domain_status(DomainStatus.ACCEPTED) is False
    assert is_failure_domain_status(DomainStatus.REWORK_REQUIRED) is False
    assert is_failure_domain_status(DomainStatus.CHECK_PASSED) is False


def test_is_failure_domain_status_strings():
    """Test failure domain status detection with strings."""
    assert is_failure_domain_status("blocked") is True
    assert is_failure_domain_status("scope_blocked") is True
    assert is_failure_domain_status("agent_failed") is True
    assert is_failure_domain_status("accepted") is False
    assert is_failure_domain_status("rework_required") is False


def test_is_scope_domain_status():
    """Test scope domain status detection."""
    assert is_scope_domain_status(DomainStatus.SCOPE_BLOCKED) is True

    assert is_scope_domain_status(DomainStatus.ACCEPTED) is False
    assert is_scope_domain_status(DomainStatus.BLOCKED) is False
    assert is_scope_domain_status(DomainStatus.REWORK_REQUIRED) is False


def test_is_scope_domain_status_strings():
    """Test scope domain status detection with strings."""
    assert is_scope_domain_status("scope_blocked") is True
    assert is_scope_domain_status("blocked") is False
    assert is_scope_domain_status("accepted") is False

# END_BLOCK: predicate_tests


# BEGIN_BLOCK: enum_string_output_tests

def test_enum_values_are_strings():
    """Test that enum values are strings for JSON serialization."""
    assert isinstance(SourcePacketStatus.READY.value, str)
    assert isinstance(RegistryStatus.READY.value, str)
    assert isinstance(DomainStatus.ACCEPTED.value, str)

    assert SourcePacketStatus.READY.value == "ready"
    assert RegistryStatus.BLOCKED.value == "blocked"
    assert DomainStatus.ACCEPTED.value == "accepted"


def test_status_transition_contains_enum():
    """Test that StatusTransition contains enum, not raw string."""
    transition = apply_domain_result_to_registry(DomainStatus.ACCEPTED)
    assert isinstance(transition.registry_status, RegistryStatus)
    assert transition.registry_status == RegistryStatus.ACCEPTED


def test_status_transition_to_dict_compatibility():
    """Test that StatusTransition can be serialized to dict with string values."""
    transition = apply_domain_result_to_registry(DomainStatus.ACCEPTED)

    # Simulate dict serialization
    result_dict = {
        "registry_status": transition.registry_status.value,
        "reason": transition.reason,
        "is_terminal": transition.is_terminal,
        "is_failure": transition.is_failure,
    }

    assert result_dict["registry_status"] == "accepted"
    assert isinstance(result_dict["registry_status"], str)

# END_BLOCK: enum_string_output_tests


# BEGIN_BLOCK: transition_table_tests

def test_transition_table_completeness():
    """Test that all domain statuses have defined transitions."""
    all_domain_statuses = [
        DomainStatus.ACCEPTED,
        DomainStatus.REWORK_REQUIRED,
        DomainStatus.BLOCKED,
        DomainStatus.SCOPE_BLOCKED,
        DomainStatus.AGENT_FAILED,
        DomainStatus.VERIFIER_FAILED,
        DomainStatus.REVIEWER_FAILED,
        DomainStatus.RUNNER_ERROR,
        DomainStatus.HANDOFF_ERROR,
        DomainStatus.CHECK_PASSED,
    ]

    for domain_status in all_domain_statuses:
        transition = apply_domain_result_to_registry(domain_status)
        assert isinstance(transition, StatusTransition)
        assert isinstance(transition.registry_status, RegistryStatus)
        assert isinstance(transition.reason, str)
        assert isinstance(transition.is_terminal, bool)
        assert isinstance(transition.is_failure, bool)

# END_BLOCK: transition_table_tests
