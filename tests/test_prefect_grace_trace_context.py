"""Tests for GRACE trace context lifecycle."""

from __future__ import annotations

import threading

from prefect_grace.platform.trace_context import (
    create_trace_context,
    current_trace_context,
    trace_scope,
)


def test_create_trace_context_formats_ids(tmp_path):
    """Trace and scenario IDs follow the packet attempt convention."""
    ctx = create_trace_context(
        packet_id="PACKET-1",
        attempt=7,
        scenario_id="single_astro_pilot",
        artifact_root=tmp_path,
    )

    assert ctx.trace_id == "TRACE-PACKET-1-ATTEMPT-007"
    assert ctx.scenario_id == "SCN-SINGLE-ASTRO-PILOT"
    assert ctx.collector is not None
    assert str(ctx.collector.path).endswith("PACKET-1/execution_trace.jsonl")


def test_trace_scope_supports_nested_contexts(tmp_path):
    """Nested scopes restore the previous thread-local context."""
    outer = create_trace_context(packet_id="OUTER", attempt=1, artifact_root=tmp_path)
    inner = create_trace_context(packet_id="INNER", attempt=2, artifact_root=tmp_path)

    assert current_trace_context() is None
    with trace_scope(outer):
        assert current_trace_context() is outer
        with trace_scope(inner):
            assert current_trace_context() is inner
        assert current_trace_context() is outer
    assert current_trace_context() is None


def test_trace_context_is_thread_local(tmp_path):
    """Concurrent threads keep independent current contexts."""
    results: list[str | None] = []

    def worker(packet_id: str) -> None:
        ctx = create_trace_context(packet_id=packet_id, attempt=1, artifact_root=tmp_path)
        with trace_scope(ctx):
            current = current_trace_context()
            results.append(current.packet_id if current else None)

    threads = [threading.Thread(target=worker, args=(f"PACKET-{index}",)) for index in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == ["PACKET-0", "PACKET-1", "PACKET-2"]
    assert current_trace_context() is None
