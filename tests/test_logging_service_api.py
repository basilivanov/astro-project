from pathlib import Path


SERVICE_FILES = [
    Path('/app/backend/app/services/billing.py'),
    Path('/app/backend/app/services/notification.py'),
    Path('/app/backend/app/services/one_off_entitlements.py'),
    Path('/app/backend/app/services/personalized_daily.py'),
    Path('/app/backend/app/services/report_workflow.py'),
]


def test_services_use_canonical_correlation_source_key():
    for path in SERVICE_FILES:
        source = path.read_text()
        assert 'correlation_source' in source
        assert 'get("source")' not in source
        assert '["source"]' not in source


def test_services_propagate_trace_context_into_grace_logs():
    expected_snippets = {
        Path('/app/backend/app/services/billing.py'): [
            'trace_context = get_correlation_ids()',
            'correlation_source=trace_context["correlation_source"]',
        ],
        Path('/app/backend/app/services/notification.py'): [
            'trace_context = get_correlation_ids()',
            'correlation_source=trace_context["correlation_source"]',
        ],
        Path('/app/backend/app/services/one_off_entitlements.py'): [
            'trace_context = get_correlation_ids()',
            'correlation_source=trace_context["correlation_source"]',
        ],
        Path('/app/backend/app/services/personalized_daily.py'): [
            'context = get_correlation_ids()',
            'correlation_source=context.get("correlation_source")',
        ],
        Path('/app/backend/app/services/report_workflow.py'): [
            'trace_context = get_correlation_ids()',
            'correlation_source=trace_context["correlation_source"]',
        ],
    }

    for path, snippets in expected_snippets.items():
        source = path.read_text()
        for snippet in snippets:
            assert snippet in source
