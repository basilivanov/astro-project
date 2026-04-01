import {
  READ_STATUS_META,
  buildExpandedSections,
  buildReadContinuityEvidence,
  buildReadContinuitySummary,
  buildReadDescription,
  buildReadFailureContext,
  buildSectionToggleState,
  extractReadContinuityFacts,
  formatAccessSource,
  prepareRenderableSections,
  toErrorMessage,
} from '../../app/read/[id]/page-helpers';

describe('read page helpers', () => {
  it('builds expanded state for the first two sections only', () => {
    const expanded = buildExpandedSections([
      { id: 'a', anchorId: 'a', section: 'one', title: 'One', blocks: [], fallbackText: 'x', preview: 'x', readingMinutes: 1 },
      { id: 'b', anchorId: 'b', section: 'two', title: 'Two', blocks: [], fallbackText: 'y', preview: 'y', readingMinutes: 1 },
      { id: 'c', anchorId: 'c', section: 'three', title: 'Three', blocks: [], fallbackText: 'z', preview: 'z', readingMinutes: 1 },
    ]);

    expect(expanded).toEqual({ a: true, b: true });
  });

  it('builds deterministic toggle state for all rendered sections', () => {
    const sections = [
      { id: 'a', anchorId: 'a', section: 'one', title: 'One', blocks: [], fallbackText: 'x', preview: 'x', readingMinutes: 1 },
      { id: 'b', anchorId: 'b', section: 'two', title: 'Two', blocks: [], fallbackText: 'y', preview: 'y', readingMinutes: 1 },
    ];

    expect(buildSectionToggleState(sections, true)).toEqual({ a: true, b: true });
    expect(buildSectionToggleState(sections, false)).toEqual({ a: false, b: false });
  });

  it('prepares structured and fallback sections deterministically', () => {
    const sections = prepareRenderableSections([
      {
        id: 'intro',
        section: 'summary',
        title: '  Мой заголовок  ',
        content: { blocks: [{ type: 'paragraph', text: 'Первый абзац секции для чтения.' }] },
      },
      {
        section: 'career_path',
        content: { foo: { bar: 'Неструктурированный, но полезный текст.' } },
      },
      {
        section: 'empty',
        content: null,
      },
    ]);

    expect(sections).toHaveLength(2);
    expect(sections[0]).toMatchObject({
      id: 'intro',
      section: 'summary',
      title: 'Мой заголовок',
      fallbackText: null,
    });
    expect(sections[0].blocks.length).toBeGreaterThan(0);
    expect(sections[0].anchorId).toContain('intro');

    expect(sections[1].id).toBe('career_path');
    expect(sections[1].title).toBeTruthy();
    expect(sections[1].blocks).toEqual([]);
    expect(sections[1].fallbackText).toContain('Неструктурированный');
  });

  it('returns no sections for unsupported or empty payloads', () => {
    expect(prepareRenderableSections(null)).toEqual([]);
    expect(prepareRenderableSections([{ section: 'empty', content: null }])).toEqual([]);
  });

  it('formats descriptions by status and empty fallback path', () => {
    expect(buildReadDescription('completed', 'Анна', 3)).toContain('Анна');
    expect(buildReadDescription('pending', 'Анна', 3)).toContain('еще в работе');
    expect(buildReadDescription('unknown', 'Анна', 0)).toContain('не содержит доступных блоков');
    expect(buildReadDescription('unknown', 'Анна', 2)).toContain('доступен в секциях');
  });

  it('maps access sources and preserves unknown values', () => {
    expect(formatAccessSource('report_entitlement')).toBe('Разовый unlock');
    expect(formatAccessSource('subscription')).toBe('Подписка');
    expect(formatAccessSource('credits')).toBe('Пакет вопросов');
    expect(formatAccessSource('trial')).toBe('Пробный доступ');
    expect(formatAccessSource('bypass')).toBe('Внутренний доступ');
    expect(formatAccessSource('manual')).toBe('manual');
  });

  it('builds failure telemetry context without leaking page decisions into tests', () => {
    expect(
      buildReadFailureContext({
        reportId: 'report-1',
        reportType: 'solar',
        status: 'failed',
        hasCheckoutToken: true,
        readEntryPoint: 'read_resume_banner',
        directEntryPoint: 'read_direct',
        failureSurface: 'failure',
        failureFlowId: 'flow-1',
      }),
    ).toEqual({
      report_id: 'report-1',
      report_type: 'solar',
      status: 'failed',
      entry_point: 'read_resume_banner',
      retry_cta_id: 'read-regenerate-button',
      support_cta_id: 'read-failure-history-link',
      surface: 'failure',
      flow_id: 'flow-1',
    });

    expect(
      buildReadFailureContext({
        reportId: 'report-2',
        hasCheckoutToken: false,
        readEntryPoint: 'read_resume_banner',
        directEntryPoint: 'read_direct',
        failureSurface: 'failure',
        failureFlowId: 'flow-2',
      }),
    ).toMatchObject({
      report_id: 'report-2',
      report_type: 'unknown',
      status: 'failed',
      entry_point: 'read_direct',
    });
  });

  it('exposes stable status labels and error fallback behavior', () => {
    expect(READ_STATUS_META.completed.metaValue).toBe('Готово');
    expect(READ_STATUS_META.failed.tone).toBe('rose');
    expect(toErrorMessage(new Error('boom'), 'fallback')).toBe('boom');
    expect(toErrorMessage(new Error('   '), 'fallback')).toBe('fallback');
    expect(toErrorMessage('bad', 'fallback')).toBe('fallback');
  });

  it('extracts canonical known-time continuity facts from read payloads', () => {
    const facts = extractReadContinuityFacts({
      report: {
        client_name: 'Ava Meridian',
        fixture_id: 'CF-BE-001-baseline-exact-time',
        fixture_manifest_id: 'canonical-astrology-fixtures-v1',
        birth_date_local: '1992-08-14T06:32:00',
        birth_timezone: 'Europe/London',
        birth_time_known: true,
      },
      persona_pack: {
        fixture_id: 'CF-BE-001-baseline-exact-time',
        manifest_id: 'canonical-astrology-fixtures-v1',
        scenario_label: 'baseline-exact-time',
      },
    });

    expect(facts).toEqual({
      fixtureId: 'CF-BE-001-baseline-exact-time',
      scenarioLabel: 'baseline-exact-time',
      manifestId: 'canonical-astrology-fixtures-v1',
      clientName: 'Ava Meridian',
      birthDateLocal: '1992-08-14T06:32:00',
      birthTimezone: 'Europe/London',
      birthTimeKnown: true,
    });
  });

  it('builds a read continuity summary only for majority-path known-time payloads', () => {
    expect(
      buildReadContinuitySummary({
        fixtureId: 'CF-BE-001-baseline-exact-time',
        scenarioLabel: 'baseline-exact-time',
        manifestId: 'canonical-astrology-fixtures-v1',
        clientName: 'Ava Meridian',
        birthDateLocal: '1992-08-14T06:32:00',
        birthTimezone: 'Europe/London',
        birthTimeKnown: true,
      }),
    ).toEqual({
      label: 'Точное время сохранено',
      value: '1992-08-14T06:32:00 • Europe/London',
    });

    expect(
      buildReadContinuitySummary({
        fixtureId: null,
        scenarioLabel: null,
        manifestId: null,
        clientName: 'Noon Vale',
        birthDateLocal: '1990-01-01T12:00:00',
        birthTimezone: 'Europe/Moscow',
        birthTimeKnown: false,
      }),
    ).toBeNull();
  });

  it('preserves visible whole-sign safe-mode continuity for the high-latitude canonical edge', () => {
    expect(
      buildReadContinuitySummary({
        fixtureId: 'CF-WS-002-whole-sign-edge',
        scenarioLabel: 'whole-sign-edge',
        manifestId: 'canonical-astrology-fixtures-v1',
        clientName: 'Mira North',
        birthDateLocal: '1980-10-30T19:50:00',
        birthTimezone: 'Europe/Moscow',
        birthTimeKnown: true,
      }),
    ).toEqual({
      label: 'Safe mode домов сохранён',
      value: '1980-10-30T19:50:00 • Europe/Moscow',
    });

    expect(
      buildReadContinuityEvidence({
        fixtureId: 'CF-WS-002-whole-sign-edge',
        scenarioLabel: 'whole-sign-edge',
        manifestId: 'canonical-astrology-fixtures-v1',
        clientName: 'Mira North',
        birthDateLocal: '1980-10-30T19:50:00',
        birthTimezone: 'Europe/Moscow',
        birthTimeKnown: true,
      }),
    ).toEqual([
      'Фикстура: CF-WS-002-whole-sign-edge',
      'Сценарий: whole-sign-edge',
      'Manifest: canonical-astrology-fixtures-v1',
      'Safe mode: Whole Sign',
    ]);
  });

  it('emits compact continuity evidence for the canonical majority path', () => {
    expect(
      buildReadContinuityEvidence({
        fixtureId: 'CF-BE-001-baseline-exact-time',
        scenarioLabel: 'baseline-exact-time',
        manifestId: 'canonical-astrology-fixtures-v1',
        clientName: 'Ava Meridian',
        birthDateLocal: '1992-08-14T06:32:00',
        birthTimezone: 'Europe/London',
        birthTimeKnown: true,
      }),
    ).toEqual([
      'Фикстура: CF-BE-001-baseline-exact-time',
      'Сценарий: baseline-exact-time',
      'Manifest: canonical-astrology-fixtures-v1',
    ]);
  });
});
