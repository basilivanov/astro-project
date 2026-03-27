from pathlib import Path


READ_PAGE = Path('/opt/astro-project/frontend/app/read/[id]/page.tsx')
GRACE_DOC = Path('/opt/astro-project/docs/GRACE_ARTIFACTS.md')


def test_read_failure_surface_keeps_resume_cta_and_failure_telemetry_contracts() -> None:
    source = READ_PAGE.read_text()

    assert 'CatalogCheckoutResumeBanner' in source
    assert 'report.report.status === "failed"' in source
    assert 'data-testid="report-failure-surface"' in source
    assert 'data-testid="report-failure-context"' in source
    assert 'data-testid="report-failure-retry-block"' in source
    assert 'data-testid="report-failure-support-block"' in source
    assert 'data-testid="read-regenerate-button"' in source
    assert 'data-testid="read-failure-history-link"' in source
    assert 'data-testid="read-resume-entry"' in source

    for contract in [
        'FN-FETCH-FAILURE-CONTEXT',
        'FN-HANDLE-REGENERATE',
        'FN-HANDLE-SUPPORT-CTA',
        'FN-HANDLE-RESUME-CTA',
    ]:
        assert contract in source

    for block in ['FAILURE_CONTEXT', 'FAILURE_RETRY', 'FAILURE_SUPPORT', 'RESUME_ENTRY']:
        assert block in source

    assert 'entry_point: checkoutToken ? READ_ENTRY_POINT : READ_DIRECT_ENTRY_POINT' in source
    assert 'surface: FAILURE_SURFACE' in source
    assert 'flow_id: FAILURE_FLOW_ID' in source
    assert 'entryPoint={READ_ENTRY_POINT}' in source


def test_grace_artifacts_docs_include_failure_flow_verification_notes() -> None:
    source = GRACE_DOC.read_text()

    assert 'tests/test_read_failure_flow.py' in source
    assert 'frontend/e2e/report-failure.spec.ts' in source
    assert 'failure CTA/resume telemetry' in source
