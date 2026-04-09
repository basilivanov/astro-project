import json

from backend.app import logging_utils
from backend.app.logging_utils import (
    build_grace_log_payload,
    correlation_scope,
    resolve_correlation_context,
    set_correlation_ids,
)


def test_build_grace_log_payload_uses_context_correlation_fields():
    previous = set_correlation_ids(correlation_id=None, trace_id=None, correlation_source=None)
    try:
        set_correlation_ids(
            correlation_id='corr-123',
            trace_id='trace-456',
            correlation_source='middleware',
        )
        payload = build_grace_log_payload(
            module='M-TEST',
            fn='demo',
            block='BLOCK',
            amount=42,
            optional=None,
        )
    finally:
        set_correlation_ids(**previous)

    assert payload == {
        'module': 'M-TEST',
        'fn': 'demo',
        'block': 'BLOCK',
        'amount': 42,
        'correlation_id': 'corr-123',
        'trace_id': 'trace-456',
        'correlation_source': 'middleware',
    }


def test_build_grace_log_payload_prefers_explicit_correlation_fields():
    previous = set_correlation_ids(correlation_id=None, trace_id=None, correlation_source=None)
    try:
        set_correlation_ids(
            correlation_id='ctx-corr',
            trace_id='ctx-trace',
            correlation_source='ctx-source',
        )
        payload = build_grace_log_payload(
            module='M-TEST',
            fn='demo',
            block='BLOCK',
            correlation_id='explicit-corr',
            trace_id='explicit-trace',
            correlation_source='explicit-source',
        )
    finally:
        set_correlation_ids(**previous)

    assert payload['correlation_id'] == 'explicit-corr'
    assert payload['trace_id'] == 'explicit-trace'
    assert payload['correlation_source'] == 'explicit-source'


def test_correlation_scope_restores_previous_context_after_exit():
    previous = set_correlation_ids(
        correlation_id='outer-corr',
        trace_id='outer-trace',
        correlation_source='outer-source',
    )
    try:
        with correlation_scope('scheduler', correlation_id='inner-corr', trace_id='inner-trace') as context:
            assert context == {
                'correlation_id': 'inner-corr',
                'trace_id': 'inner-trace',
                'correlation_source': 'scheduler',
                'request_id': 'inner-trace',
            }
            assert resolve_correlation_context() == context

        assert resolve_correlation_context() == {
            'correlation_id': 'outer-corr',
            'trace_id': 'outer-trace',
            'correlation_source': 'outer-source',
            'request_id': None,
        }
    finally:
        set_correlation_ids(**previous)


def test_build_grace_log_payload_accepts_request_id():
    payload = build_grace_log_payload(
        module='M-TEST',
        fn='demo',
        block='BLOCK',
        request_id='req-789',
    )

    assert payload['request_id'] == 'req-789'


def test_feed_admin_sink_routes_week_and_report_workflow_events_to_report_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_utils, "LOG_DIR", tmp_path)

    logging_utils.feed_admin_sink(None, "", {"event": "week_brief_built", "trace_id": "trace-week"})
    logging_utils.feed_admin_sink(None, "", {"event": "report.workflow.run_start", "trace_id": "trace-report"})

    report_log = tmp_path / "report.jsonl"
    rows = [json.loads(line) for line in report_log.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert [row["event"] for row in rows] == ["week_brief_built", "report.workflow.run_start"]
    assert rows[0]["trace_id"] == "trace-week"
    assert rows[1]["trace_id"] == "trace-report"
    assert not (tmp_path / "catalog.jsonl").exists()


from backend.app.logging_utils import bind_correlation_ids


def test_bind_correlation_ids_defaults_request_id_to_trace_id():
    previous = set_correlation_ids(correlation_id=None, trace_id=None, correlation_source=None, request_id=None)
    try:
        context = bind_correlation_ids('fastapi.middleware')
        assert context['request_id'] == context['trace_id']
        assert resolve_correlation_context()['request_id'] == context['request_id']
    finally:
        set_correlation_ids(**previous)

from backend.app.logging_utils import build_grace_log_payload, run_with_correlation


def test_build_grace_log_payload_uses_context_request_id():
    previous = set_correlation_ids(correlation_id=None, trace_id=None, correlation_source=None, request_id=None)
    try:
        set_correlation_ids(
            correlation_id='corr-ctx',
            trace_id='trace-ctx',
            correlation_source='ctx-source',
            request_id='req-ctx',
        )
        payload = build_grace_log_payload(module='M-TEST', fn='demo', block='BLOCK')
    finally:
        set_correlation_ids(**previous)

    assert payload['request_id'] == 'req-ctx'


async def _read_correlation_request_id():
    return resolve_correlation_context()['request_id']


def test_run_with_correlation_preserves_request_id():
    import asyncio

    result = asyncio.run(run_with_correlation(
        _read_correlation_request_id,
        {
            'correlation_id': 'corr-async',
            'trace_id': 'trace-async',
            'correlation_source': 'test',
            'request_id': 'req-async',
        },
    ))

    assert result == 'req-async'
