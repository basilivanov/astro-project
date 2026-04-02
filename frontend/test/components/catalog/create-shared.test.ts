import {
  buildMockProfile,
  CATALOG_GRACE_BLOCKS,
  CATALOG_GRACE_MODULES,
  EMPTY_PRODUCT_INPUT_DRAFT,
  formatCreateAccessError,
  getDraftStorageKey,
  MOCK_INIT_DATA,
  PRODUCT_META,
  withCatalogTrace,
} from '../../../components/catalog/create-shared';

describe('catalog create shared helpers', () => {
  it('exposes stable catalog labels and defaults', () => {
    expect(PRODUCT_META.natal_master.label).toBe('Натал (базовый)');
    expect(PRODUCT_META.horary.label).toBe('Вопрос (Хорар)');
    expect(PRODUCT_META.horary_answer.label).toBe('Вопрос (Хорар)');
    expect(MOCK_INIT_DATA).toBe('123456789');
    expect(EMPTY_PRODUCT_INPUT_DRAFT).toEqual({
      partnerName: '',
      partnerBirthDate: '',
      partnerBirthLocation: '',
      solarCurrentLocation: '',
    });
  });

  it('builds draft storage keys by report type', () => {
    expect(getDraftStorageKey('synastry')).toBe('create:draft:synastry');
    expect(getDraftStorageKey('year_forecast')).toBe('create:draft:year_forecast');
  });

  it('builds a deterministic mock profile with expected access flags', () => {
    const profile = buildMockProfile();

    expect(profile.full_name).toBe('Debug User');
    expect(profile.can_ask_horary).toBe(true);
    expect(profile.can_access_premium).toBe(true);
    expect(profile.horary_balance).toBe(1);
    expect(profile.birth_place).toBe('Moscow');
    expect(profile.current_timezone).toBe('Europe/Moscow');
    expect(profile.report_unlocks).toMatchObject({
      natal_master: 0,
      month_forecast: 0,
      year_forecast: 0,
      solar_return: 0,
      synastry: 0,
    });
    expect(profile.report_access?.natal_master).toEqual({
      allowed: true,
      granted_via: 'subscription',
      remaining_unlocks: 0,
      reason_code: 'ok',
      legacy_subscription_applied: true,
    });
    expect(profile.feature_flags).toEqual({
      enable_one_off_entitlements_runtime: false,
      enable_persistent_checkout_sessions: false,
      legacy_premium_subscription_access: true,
    });
  });

  it('formats access errors for one-off and subscription flows', () => {
    expect(formatCreateAccessError(true)).toContain('Разовый доступ');
    expect(formatCreateAccessError(false)).toContain('нет активной подписки');
  });

  it('exports GRACE module and block identifiers for catalog telemetry', () => {
    expect(CATALOG_GRACE_MODULES).toMatchObject({
      analytics: 'M-CATALOG-ANALYTICS',
      checkoutResume: 'M-CATALOG-CHECKOUT-RESUME',
      reportsCatalog: 'M-REPORTS-CATALOG',
      reportsHistory: 'M-REPORTS-HISTORY',
      readReport: 'M-READ-REPORT-PAGE',
      createCheckout: 'M-CREATE-CHECKOUT',
      homeFeed: 'M-HOME-FEED',
    });
    expect(CATALOG_GRACE_BLOCKS.catalog).toEqual({
      analyticsBootstrap: 'ANALYTICS_CONTEXT_BOOTSTRAP',
      ctaTracking: 'CTA_TRACKING',
      catalogSection: 'CATALOG_SECTION',
      billingNote: 'BILLING_NOTE',
    });
    expect(CATALOG_GRACE_BLOCKS.create.checkoutError).toBe('CHECKOUT_ERROR');
    expect(CATALOG_GRACE_BLOCKS.checkoutResume.resumeState).toBe('RESUME_STATE');
  });

  it('merges trace metadata and defaults semantic block to block', () => {
    expect(
      withCatalogTrace(
        { event: 'catalog_open', payloadVersion: 1 },
        {
          module: CATALOG_GRACE_MODULES.analytics,
          contract: 'catalog.analytics.event.v1',
          block: CATALOG_GRACE_BLOCKS.analytics.payloadBuild,
        },
      ),
    ).toEqual({
      event: 'catalog_open',
      payloadVersion: 1,
      module: 'M-CATALOG-ANALYTICS',
      contract: 'catalog.analytics.event.v1',
      block: 'PAYLOAD_BUILD',
      semantic_block: 'PAYLOAD_BUILD',
    });
  });

  it('preserves explicit semantic block and correlation id when present', () => {
    expect(
      withCatalogTrace(
        { event: 'catalog_resume' },
        {
          module: CATALOG_GRACE_MODULES.checkoutResume,
          contract: 'catalog.resume.event.v1',
          block: CATALOG_GRACE_BLOCKS.checkoutResume.ctaReady,
          semantic_block: 'READY_CTA',
          correlation_id: 'corr-123',
        },
      ),
    ).toEqual({
      event: 'catalog_resume',
      module: 'M-CATALOG-CHECKOUT-RESUME',
      contract: 'catalog.resume.event.v1',
      block: 'CTA_READY',
      semantic_block: 'READY_CTA',
      correlation_id: 'corr-123',
    });
  });

  it('omits correlation id when it is null', () => {
    const traced = withCatalogTrace(
      { event: 'catalog_view' },
      {
        module: CATALOG_GRACE_MODULES.reportsCatalog,
        contract: 'catalog.view.event.v1',
        block: CATALOG_GRACE_BLOCKS.catalog.catalogSection,
        correlation_id: null,
      },
    );

    expect(traced).toEqual({
      event: 'catalog_view',
      module: 'M-REPORTS-CATALOG',
      contract: 'catalog.view.event.v1',
      block: 'CATALOG_SECTION',
      semantic_block: 'CATALOG_SECTION',
    });
    expect(traced).not.toHaveProperty('correlation_id');
  });
});
