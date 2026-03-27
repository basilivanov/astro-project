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
            }
            assert resolve_correlation_context() == context

        assert resolve_correlation_context() == {
            'correlation_id': 'outer-corr',
            'trace_id': 'outer-trace',
            'correlation_source': 'outer-source',
        }
    finally:
        set_correlation_ids(**previous)
