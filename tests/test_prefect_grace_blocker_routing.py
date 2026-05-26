"""Tests for prefect_grace.platform.blocker_routing module."""

import pytest
from prefect_grace.platform.blocker_routing import (
    BlockerRoute,
    route_evidence_blocker,
    BLOCKER_ROUTES,
)


def test_blocker_route_to_dict():
    """Test BlockerRoute serialization."""
    route = BlockerRoute(
        blocker_code="implementation_failed",
        route_to="coder",
        message="Implementation failure",
    )

    data = route.to_dict()

    assert data["blocker_code"] == "implementation_failed"
    assert data["route_to"] == "coder"
    assert data["message"] == "Implementation failure"


def test_route_evidence_blocker_implementation_failed():
    """Test routing implementation_failed to coder."""
    error = {
        "code": "implementation_failed",
        "evidence_id": "EV-TEST-001",
        "message": "Tests failed",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "implementation_failed"
    assert route.route_to == "coder"
    assert "Tests failed" in route.message


def test_route_evidence_blocker_contract_invalid():
    """Test routing evidence_contract_invalid to architect."""
    error = {
        "code": "evidence_contract_invalid",
        "evidence_id": "EV-TEST-001",
        "message": "Invalid contract",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "evidence_contract_invalid"
    assert route.route_to == "architect"
    assert "Invalid contract" in route.message


def test_route_evidence_blocker_artifact_invalid():
    """Test routing artifact_reference_invalid to verifier."""
    error = {
        "code": "artifact_reference_invalid",
        "evidence_id": "EV-TEST-001",
        "message": "Artifact not found",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "artifact_reference_invalid"
    assert route.route_to == "verifier"
    assert "Artifact not found" in route.message


def test_route_evidence_blocker_wave_final_pending():
    """Test routing wave_final_evidence_pending to none (not packet-blocking)."""
    error = {
        "code": "wave_final_evidence_pending",
        "evidence_id": "EV-OBS-001",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "wave_final_evidence_pending"
    assert route.route_to == "none"
    assert "not packet-blocking" in route.message


def test_route_evidence_blocker_verification_failed():
    """Test routing verification_failed to coder."""
    error = {
        "code": "verification_failed",
        "evidence_id": "EV-TEST-001",
        "message": "Verification failed",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "verification_failed"
    assert route.route_to == "coder"


def test_route_evidence_blocker_missing_profile():
    """Test routing missing_verification_profile to architect."""
    error = {
        "code": "missing_verification_profile",
        "evidence_id": "EV-TEST-001",
        "message": "Profile not found",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "missing_verification_profile"
    assert route.route_to == "architect"


def test_route_evidence_blocker_evidence_not_generated():
    """Test routing evidence_not_generated to verifier."""
    error = {
        "code": "evidence_not_generated",
        "evidence_id": "EV-TEST-001",
        "message": "Evidence not generated",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "evidence_not_generated"
    assert route.route_to == "verifier"


def test_route_evidence_blocker_environment_blocker():
    """Test routing environment_blocker to infra."""
    error = {
        "code": "environment_blocker",
        "message": "Environment issue",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "environment_blocker"
    assert route.route_to == "infra"


def test_route_evidence_blocker_scope_violation():
    """Test routing scope_violation to architect."""
    error = {
        "code": "scope_violation",
        "message": "Scope violation",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "scope_violation"
    assert route.route_to == "architect"


def test_route_evidence_blocker_review_rework_required():
    """Test routing review_rework_required to coder."""
    error = {
        "code": "review_rework_required",
        "message": "Review rework required",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "review_rework_required"
    assert route.route_to == "coder"


def test_route_evidence_blocker_missing_id():
    """Test routing missing_id to architect."""
    error = {
        "code": "missing_id",
        "message": "Missing evidence ID",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "missing_id"
    assert route.route_to == "architect"


def test_route_evidence_blocker_duplicate_id():
    """Test routing duplicate_id to architect."""
    error = {
        "code": "duplicate_id",
        "evidence_id": "EV-TEST-001",
        "message": "Duplicate ID",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "duplicate_id"
    assert route.route_to == "architect"


def test_route_evidence_blocker_unknown_kind():
    """Test routing unknown_kind to architect."""
    error = {
        "code": "unknown_kind",
        "evidence_id": "EV-TEST-001",
        "message": "Unknown kind",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "unknown_kind"
    assert route.route_to == "architect"


def test_route_evidence_blocker_wave_final_coder_blocking():
    """Test routing wave_final_coder_blocking to architect."""
    error = {
        "code": "wave_final_coder_blocking",
        "evidence_id": "EV-TEST-001",
        "message": "wave_final cannot be coder_blocking",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "wave_final_coder_blocking"
    assert route.route_to == "architect"


def test_route_evidence_blocker_unknown_code():
    """Test routing unknown blocker code to architect for triage."""
    error = {
        "code": "unknown_blocker_code",
        "message": "Unknown blocker",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "unknown_blocker_code"
    assert route.route_to == "architect"
    assert "Unknown blocker code" in route.message
    assert "triage" in route.message


def test_route_evidence_blocker_no_code():
    """Test routing error without code field."""
    error = {
        "message": "Some error",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "unknown"
    assert route.route_to == "architect"


def test_route_evidence_blocker_uses_custom_message():
    """Test routing uses custom message from error if provided."""
    custom_message = "Custom error message with details"
    error = {
        "code": "implementation_failed",
        "message": custom_message,
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "implementation_failed"
    assert route.route_to == "coder"
    assert route.message == custom_message


def test_route_evidence_blocker_uses_template_message():
    """Test routing uses template message if no custom message."""
    error = {
        "code": "implementation_failed",
    }

    route = route_evidence_blocker(error)

    assert route.blocker_code == "implementation_failed"
    assert route.route_to == "coder"
    # Should use template message from BLOCKER_ROUTES
    assert "Implementation failure" in route.message


def test_blocker_routes_coverage():
    """Test that all expected blocker codes are in routing table."""
    expected_codes = [
        "implementation_failed",
        "verification_failed",
        "failed_verification",
        "evidence_contract_invalid",
        "missing_verification_profile",
        "artifact_reference_invalid",
        "evidence_not_generated",
        "environment_blocker",
        "scope_violation",
        "wave_final_evidence_pending",
        "review_rework_required",
        "packet_local_deferred",
        "unknown_evidence_id",
        "invalid_status",
        "missing_id",
        "duplicate_id",
        "unknown_kind",
        "unknown_stage",
        "unknown_owner",
        "unknown_producer",
        "required_without_owner",
        "required_without_producer",
        "wave_final_coder_blocking",
    ]

    for code in expected_codes:
        assert code in BLOCKER_ROUTES, f"Missing blocker code: {code}"


def test_blocker_routes_all_have_route_to():
    """Test that all blocker routes have route_to field."""
    for code, (route_to, message) in BLOCKER_ROUTES.items():
        assert route_to is not None, f"Blocker {code} missing route_to"
        assert isinstance(route_to, str), f"Blocker {code} route_to not string"
        assert len(route_to) > 0, f"Blocker {code} route_to empty"


def test_blocker_routes_all_have_message():
    """Test that all blocker routes have message template."""
    for code, (route_to, message) in BLOCKER_ROUTES.items():
        assert message is not None, f"Blocker {code} missing message"
        assert isinstance(message, str), f"Blocker {code} message not string"
        assert len(message) > 0, f"Blocker {code} message empty"


def test_route_evidence_blocker_deterministic():
    """Test that routing is deterministic (same input = same output)."""
    error = {
        "code": "implementation_failed",
        "message": "Test error",
    }

    route1 = route_evidence_blocker(error)
    route2 = route_evidence_blocker(error)

    assert route1.blocker_code == route2.blocker_code
    assert route1.route_to == route2.route_to
    assert route1.message == route2.message
