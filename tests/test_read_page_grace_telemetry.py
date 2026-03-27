from pathlib import Path


READ_PAGE = Path('/opt/astro-project/frontend/app/read/[id]/page.tsx')
CATALOG_ANALYTICS = Path('/opt/astro-project/frontend/components/catalog/catalog-analytics.ts')


def test_read_page_declares_module_contract_and_map() -> None:
    source = READ_PAGE.read_text()

    assert 'START_MODULE_CONTRACT: M-READ-REPORT-PAGE' in source
    assert 'END_MODULE_CONTRACT: M-READ-REPORT-PAGE' in source
    assert 'START_MODULE_MAP: M-READ-REPORT-PAGE' in source
    assert 'END_MODULE_MAP: M-READ-REPORT-PAGE' in source


def test_read_page_uses_strict_grace_blocks_and_contracts() -> None:
    source = READ_PAGE.read_text()

    for contract in [
        'FN-TRACK-READ-EVENT',
        'FN-HANDLE-SHARE',
        'FN-HANDLE-RESUME-CTA',
        'FN-HANDLE-REGENERATE',
    ]:
        assert contract in source

    for block in ['LOADING_STATE', 'SHARE_SECTION', 'CTA_TRACKING', 'RESUME_ENTRY']:
        assert block in source

    assert 'surface: READ_SURFACE' in source
    assert 'flow_id: FLOW_FORECAST_CATALOG' in source
    assert 'entryPoint={READ_ENTRY_POINT}' in source
    assert 'READ_DIRECT_ENTRY_POINT' in source


def test_catalog_analytics_hashes_checkout_tokens_before_logging() -> None:
    source = CATALOG_ANALYTICS.read_text()

    assert 'checkout_token_hash = await hashCheckoutToken(checkoutToken)' or 'merged.checkout_token_hash = await hashCheckoutToken(checkoutToken)'
    assert 'delete merged.checkout_token' in source
    assert 'FLOW_FORECAST_CATALOG' in source
