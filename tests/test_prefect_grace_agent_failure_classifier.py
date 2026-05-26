"""Tests for prefect_grace.platform.agent_failure_classifier module."""

import pytest
from prefect_grace.platform.agent_failure_classifier import (
    AgentFailureClassification,
    classify_agent_failure,
)


def test_classify_rate_limit_http_429():
    """Test classification of HTTP 429 rate limit error."""
    stderr = "Error: HTTP 429 - Rate limit exceeded"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "rate_limit"
    assert result.retryable is True
    assert result.quality_rework is False
    assert result.operator_action_required is False
    assert "rate limit" in result.reason.lower()
    assert result.matched_pattern == "429"


def test_classify_rate_limit_text_pattern():
    """Test classification of text-based rate limit error."""
    stderr = "API Error: rate_limit_exceeded - Too many requests"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "rate_limit"
    assert result.retryable is True
    assert result.quality_rework is False
    assert result.matched_pattern in ["rate limit", "rate_limit", "too many requests", "rate_limit_exceeded"]


def test_classify_auth_failed_http_401():
    """Test classification of HTTP 401 authentication error."""
    stderr = "Error: HTTP 401 - Unauthorized"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "auth_failed"
    assert result.retryable is False
    assert result.quality_rework is False
    assert result.operator_action_required is True
    assert "authentication" in result.reason.lower() or "credentials" in result.reason.lower()
    assert result.matched_pattern == "401"


def test_classify_auth_failed_invalid_key():
    """Test classification of invalid API key error."""
    stderr = "Authentication failed: invalid api key provided"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "auth_failed"
    assert result.retryable is False
    assert result.quality_rework is False
    assert result.operator_action_required is True
    assert result.matched_pattern in ["invalid api key", "invalid_api_key", "authentication failed"]


def test_classify_quota_exceeded():
    """Test classification of quota exceeded error."""
    stderr = "Error: quota exceeded - insufficient quota for this request"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "quota_exceeded"
    assert result.retryable is False
    assert result.quality_rework is False
    assert result.operator_action_required is True
    assert "quota" in result.reason.lower()
    assert result.matched_pattern in ["quota exceeded", "insufficient quota"]


def test_classify_network_timeout():
    """Test classification of network timeout error."""
    stderr = "Error: connection timeout after 30 seconds"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "network_timeout"
    assert result.retryable is True
    assert result.quality_rework is False
    assert result.operator_action_required is False
    assert "timeout" in result.reason.lower()
    assert result.matched_pattern in ["connection timeout", "timed out"]


def test_classify_provider_unavailable_503():
    """Test classification of HTTP 503 service unavailable error."""
    stderr = "Error: HTTP 503 - Service temporarily unavailable"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "provider_unavailable"
    assert result.retryable is True
    assert result.quality_rework is False
    assert result.operator_action_required is False
    assert "unavailable" in result.reason.lower() or "provider" in result.reason.lower()
    assert result.matched_pattern in ["503", "service unavailable", "temporarily unavailable"]


def test_classify_unknown_api_error():
    """Test classification of unknown error with stderr content."""
    stderr = "Something went wrong with the API call"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "unknown_api_error"
    assert result.retryable is False
    assert result.quality_rework is False
    assert result.operator_action_required is True
    assert "unknown" in result.reason.lower()
    assert result.matched_pattern is None


def test_classify_none_success():
    """Test classification when exit_code is 0 and no patterns match."""
    stdout = "Agent completed successfully"

    result = classify_agent_failure(stdout_text=stdout, exit_code=0)

    assert result.category == "none"
    assert result.retryable is False
    assert result.quality_rework is False
    assert result.operator_action_required is False
    assert "no api failure" in result.reason.lower()
    assert result.matched_pattern is None


def test_classification_to_dict():
    """Test serialization of AgentFailureClassification."""
    classification = AgentFailureClassification(
        category="rate_limit",
        retryable=True,
        quality_rework=False,
        operator_action_required=False,
        reason="Rate limit exceeded",
        matched_pattern="429",
    )

    data = classification.to_dict()

    assert data["category"] == "rate_limit"
    assert data["retryable"] is True
    assert data["quality_rework"] is False
    assert data["operator_action_required"] is False
    assert data["reason"] == "Rate limit exceeded"
    assert data["matched_pattern"] == "429"


def test_classify_multiple_patterns_priority():
    """Test that rate_limit has priority over other patterns."""
    # Both rate_limit and auth patterns present
    stderr = "HTTP 429 rate limit exceeded. Authentication token: invalid"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    # rate_limit should win due to priority
    assert result.category == "rate_limit"
    assert result.matched_pattern == "429"


def test_classify_case_insensitive():
    """Test that pattern matching is case-insensitive."""
    stderr = "ERROR: RATE LIMIT EXCEEDED"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "rate_limit"
    assert result.retryable is True


def test_classify_stdout_patterns():
    """Test that patterns are detected in stdout as well as stderr."""
    stdout = "Agent output: HTTP 429 - Too many requests"

    result = classify_agent_failure(stdout_text=stdout, exit_code=1)

    assert result.category == "rate_limit"
    assert result.matched_pattern == "429"


def test_classify_combined_stderr_stdout():
    """Test classification with both stderr and stdout."""
    stderr = "Connection failed"
    stdout = "Error: read timeout after 60s"

    result = classify_agent_failure(
        stderr_text=stderr,
        stdout_text=stdout,
        exit_code=1,
    )

    assert result.category == "network_timeout"
    assert result.retryable is True


def test_classify_exit_code_zero_no_error():
    """Test that exit_code=0 with no error patterns returns none."""
    stderr = "Some debug output"
    stdout = "Process completed"

    result = classify_agent_failure(
        stderr_text=stderr,
        stdout_text=stdout,
        exit_code=0,
    )

    assert result.category == "none"
    assert result.operator_action_required is False


def test_classify_nonzero_exit_no_stderr():
    """Test that exit_code != 0 with empty stderr triggers unknown_api_error (fail-closed)."""
    result = classify_agent_failure(stderr_text="", stdout_text="", exit_code=1)

    # Fail-closed: any non-zero exit without recognized pattern is unknown_api_error
    assert result.category == "unknown_api_error"
    assert result.operator_action_required is True
    assert result.retryable is False


def test_classify_nonzero_exit_with_error_keyword():
    """Test that exit_code != 0 with 'error' keyword triggers unknown_api_error."""
    stdout = "Process failed with error code 1"

    result = classify_agent_failure(stdout_text=stdout, exit_code=1)

    assert result.category == "unknown_api_error"
    assert result.operator_action_required is True


def test_classify_auth_failed_http_403():
    """Test classification of HTTP 403 forbidden error."""
    stderr = "Error: HTTP 403 - Forbidden"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "auth_failed"
    assert result.retryable is False
    assert result.operator_action_required is True


def test_classify_provider_unavailable_502():
    """Test classification of HTTP 502 bad gateway error."""
    stderr = "Error: HTTP 502 - Bad Gateway"

    result = classify_agent_failure(stderr_text=stderr, exit_code=1)

    assert result.category == "provider_unavailable"
    assert result.retryable is True


def test_classify_with_termination_reason():
    """Test classification with termination_reason parameter."""
    stderr = "Connection timeout"

    result = classify_agent_failure(
        stderr_text=stderr,
        exit_code=1,
        termination_reason="timeout",
    )

    assert result.category == "network_timeout"
    assert result.retryable is True


def test_quality_rework_always_false_for_api_errors():
    """Test that quality_rework is always False for all API error categories."""
    test_cases = [
        ("HTTP 429", "rate_limit"),
        ("HTTP 401", "auth_failed"),
        ("quota exceeded", "quota_exceeded"),
        ("connection timeout", "network_timeout"),
        ("HTTP 503", "provider_unavailable"),
        ("unknown error", "unknown_api_error"),
    ]

    for stderr, expected_category in test_cases:
        result = classify_agent_failure(stderr_text=stderr, exit_code=1)
        assert result.category == expected_category
        assert result.quality_rework is False, f"quality_rework should be False for {expected_category}"
