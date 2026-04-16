import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import WeekPage from '../../app/week/page';

const originalNodeEnv = process.env.NODE_ENV;
const originalEnvironment = process.env.ENVIRONMENT;
const originalNextPublicEnvironment = process.env.NEXT_PUBLIC_ENVIRONMENT;
const originalVercelEnv = process.env.VERCEL_ENV;
const mockUsePathname = jest.fn();
const mockUseSearchParams = jest.fn();
const mockUseTelegram = jest.fn();
const correlatedFetchMock = jest.fn();
const setCatalogAnalyticsContextMock = jest.fn();
const startCatalogCorrelationMock = jest.fn();
const trackCatalogEventMock = jest.fn().mockResolvedValue(undefined);
const setCorrelationIdMock = jest.fn();

jest.mock('next/navigation', () => ({
  usePathname: () => mockUsePathname(),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock('../../hooks/useTelegram', () => ({
  useTelegram: () => mockUseTelegram(),
}));

jest.mock('next/script', () => ({
  __esModule: true,
  default: ({ children, id, src }: { children?: React.ReactNode; id?: string; src?: string }) => {
    const inlineScript = typeof children === 'string' ? children : Array.isArray(children) ? children.join('') : '';
    if (src) {
      return <script data-testid="mock-next-script" id={id} src={src} />;
    }
    return <script data-testid="mock-next-script" id={id} dangerouslySetInnerHTML={{ __html: inlineScript }} />;
  },
}));

jest.mock('../../components/BottomNav', () => ({
  __esModule: true,
  default: () => <div data-testid="bottom-nav" />,
}));

jest.mock('../../components/legal-links', () => ({
  LegalFooterBlock: ({ className, compact }: { className?: string; compact?: boolean }) => (
    <div data-testid="legal-footer-block" data-class-name={className ?? ''} data-compact={String(Boolean(compact))} />
  ),
}));

jest.mock('../../components/catalog/catalog-checkout-resume', () => ({
  CatalogCheckoutResumeBanner: () => <div data-testid="checkout-resume-banner" />,
}));

jest.mock('../../components/catalog/catalog-analytics', () => ({
  FLOW_FORECAST_CATALOG: 'flow.forecast.catalog',
  setCatalogAnalyticsContext: (...args: unknown[]) => setCatalogAnalyticsContextMock(...args),
  startCatalogCorrelation: (...args: unknown[]) => startCatalogCorrelationMock(...args),
  trackCatalogEvent: (...args: unknown[]) => trackCatalogEventMock(...args),
}));

jest.mock('../../lib/correlation', () => ({
  CorrelationManager: {
    setCorrelationId: (...args: unknown[]) => setCorrelationIdMock(...args),
  },
  correlatedFetch: (...args: unknown[]) => correlatedFetchMock(...args),
}));

jest.mock('../../components/week/week-hero-map', () => ({
  WeekHeroMap: ({ week, primaryHref, primaryLabel }: { week: { headline: string; subhead?: string; theme?: string; location?: string | null; timezone?: string | null; weekStart?: string | null; weekEnd?: string | null }; primaryHref: string; primaryLabel: string }) => (
    <div data-testid="week-hero-map" data-primary-href={primaryHref} data-primary-label={primaryLabel}>
      <span>{week.headline}</span>
      <span>{week.subhead ?? ''}</span>
      <span>{week.theme ?? ''}</span>
      <span>{week.location ?? ''}</span>
      <span>{week.timezone ?? ''}</span>
      <span>{week.weekStart ?? ''}</span>
      <span>{week.weekEnd ?? ''}</span>
    </div>
  ),
}));

jest.mock('../../components/week/week-day-strip', () => ({
  WeekDayStrip: ({ week, selectedDayKey }: { week: { dayStrip: Array<{ weekday?: string | null; date?: string | null }> }; selectedDayKey?: string | null }) => (
    <div data-testid="week-day-strip" data-selected-day={selectedDayKey ?? ''}>{week.dayStrip.map((day) => day.weekday).filter(Boolean).join(', ')}</div>
  ),
}));

jest.mock('../../components/week/week-day-drawer', () => ({
  WeekDayDrawer: ({ card, surfaceMode }: { card: { weekday?: string | null; headline?: string | null } | null; surfaceMode: string }) => (
    <div data-testid="week-day-drawer">{`${surfaceMode === 'compatibility' ? 'Короткий обзор дня' : 'Деталь дня'}:${card?.weekday ?? 'none'}:${card?.headline ?? 'none'}`}</div>
  ),
}));

jest.mock('../../components/week/week-domain-panel', () => ({
  WeekDomainPanel: ({ week }: { week: { domains: Array<{ title?: string | null }> } }) => (
    <div data-testid="week-domain-panel">{week.domains.map((domain) => domain.title).filter(Boolean).join(', ')}</div>
  ),
}));

jest.mock('../../components/week/week-actions-panel', () => ({
  WeekActionsPanel: ({ week }: { week: { actions: Array<{ text?: string | null }>; risks: Array<{ text?: string | null }> } }) => (
    <div data-testid="week-actions-panel">
      <span>{week.actions.map((action) => action.text).filter(Boolean).join(', ')}</span>
      <span>{week.risks.map((risk) => risk.text).filter(Boolean).join(', ')}</span>
    </div>
  ),
}));

jest.mock('../../components/week/week-explainability-panel', () => ({
  WeekExplainabilityPanel: ({ week }: { week: { explainabilitySummary: string; factors?: Array<{ label?: string | null }> } }) => (
    <div data-testid="week-explainability-panel">{week.explainabilitySummary}:{week.factors?.map((factor) => factor.label).join(',')}</div>
  ),
}));

jest.mock('../../components/week/week-deep-sections', () => ({
  WeekDeepSections: ({ week }: { week: { deepSections: Array<{ title?: string | null }> } }) => (
    <div data-testid="week-deep-sections">deep:{week.deepSections.map((section) => section.title).filter(Boolean).join(', ')}</div>
  ),
}));

jest.mock('../../components/report-status-poller', () => ({
  __esModule: true,
  default: ({ reportId, status }: { reportId?: string | null; status?: string | null }) => (
    <div data-testid="report-status-poller">{`${reportId ?? 'none'}:${status ?? 'none'}`}</div>
  ),
}));

describe('WeekPage', () => {
  const buildWeekBrief = (overrides: Record<string, unknown> = {}) => ({
    status: 'ready',
    fallback_mode: false,
    summary: {
      headline: 'Каноническая неделя',
      subhead: 'Только week_brief формирует экран',
      week_type: 'balance',
      theme: 'Canonical',
    },
    day_cards: [
      { weekday: 'fri', date: '2026-04-10', headline: 'Работать по главному приоритету' },
    ],
    best_uses: [],
    risks: [],
    domains: [],
    deep_sections: [],
    report_ref: { report_id: 'week-canonical', source_status: 'completed' },
    ...overrides,
  });

  const loadRootLayout = () => {
    let RootLayout: ((props: { children: React.ReactNode }) => React.ReactElement) | null = null;
    jest.isolateModules(() => {
      RootLayout = require('../../app/layout').default as (props: { children: React.ReactNode }) => React.ReactElement;
    });
    if (!RootLayout) {
      throw new Error('RootLayout failed to load');
    }
    return RootLayout;
  };

  const renderRootLayoutDocument = (node: React.ReactElement) => {
    const { renderToStaticMarkup } = require('react-dom/server') as typeof import('react-dom/server');
    const markup = renderToStaticMarkup(node);
    const parsed = new DOMParser().parseFromString(`<!doctype html>${markup}`, 'text/html');
    document.head.innerHTML = parsed.head.innerHTML;
    document.body.innerHTML = parsed.body.innerHTML;
  };

  const executeRuntimeBadgeRouteGate = () => {
    const script = document.getElementById('runtime-badge-route-gate');
    expect(script).not.toBeNull();
    const source = script?.textContent ?? '';
    expect(source).toContain('astro:week-dev-indicator-toggle-request');
    window.eval(source);
  };

  const toggleWeekRuntimeDiagnostics = async () => {
    await act(async () => {
      window.dispatchEvent(new CustomEvent('astro:week-dev-indicator-toggle-request', {
        detail: { route: '/week', source: 'test' },
      }));
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
    delete process.env.ENVIRONMENT;
    delete process.env.NEXT_PUBLIC_ENVIRONMENT;
    delete process.env.VERCEL_ENV;
    mockUsePathname.mockReturnValue('/week');
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    mockUseTelegram.mockReturnValue({ isReady: true, initData: 'tg-auth', mode: 'telegram', bootstrapOutcome: 'ready' });
    startCatalogCorrelationMock.mockReturnValue('corr-week');
    correlatedFetchMock.mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));
  });

  afterEach(() => {
    process.env.NODE_ENV = originalNodeEnv;
    if (typeof originalEnvironment === 'undefined') {
      delete process.env.ENVIRONMENT;
    } else {
      process.env.ENVIRONMENT = originalEnvironment;
    }
    if (typeof originalNextPublicEnvironment === 'undefined') {
      delete process.env.NEXT_PUBLIC_ENVIRONMENT;
    } else {
      process.env.NEXT_PUBLIC_ENVIRONMENT = originalNextPublicEnvironment;
    }
    if (typeof originalVercelEnv === 'undefined') {
      delete process.env.VERCEL_ENV;
    } else {
      process.env.VERCEL_ENV = originalVercelEnv;
    }
    window.history.replaceState({}, '', '/week');
  });

  afterAll(() => {
    process.env.NODE_ENV = originalNodeEnv;
    if (typeof originalEnvironment === 'undefined') {
      delete process.env.ENVIRONMENT;
    } else {
      process.env.ENVIRONMENT = originalEnvironment;
    }
    if (typeof originalNextPublicEnvironment === 'undefined') {
      delete process.env.NEXT_PUBLIC_ENVIRONMENT;
    } else {
      process.env.NEXT_PUBLIC_ENVIRONMENT = originalNextPublicEnvironment;
    }
    if (typeof originalVercelEnv === 'undefined') {
      delete process.env.VERCEL_ENV;
    } else {
      process.env.VERCEL_ENV = originalVercelEnv;
    }
  });

  it('renders guest empty state without requesting reports', async () => {
    mockUseTelegram.mockReturnValue({ isReady: true, initData: null, mode: 'guest' });

    render(<WeekPage />);

    expect(await screen.findByText('Неделя пока недоступна')).toBeInTheDocument();
    expect(screen.getByText('Авторизуйтесь через Telegram, чтобы увидеть персональную карту недели.')).toBeInTheDocument();
    expect(correlatedFetchMock).not.toHaveBeenCalled();
  });

  it('renders backend error state when report lookup fails', async () => {
    correlatedFetchMock.mockResolvedValueOnce(new Response('boom', { status: 500 }));

    render(<WeekPage />);

    expect(await screen.findByText('Упс, ошибка')).toBeInTheDocument();
    expect(screen.getByText('REPORT_LOOKUP_500')).toBeInTheDocument();
    await waitFor(() => {
      expect(trackCatalogEventMock).toHaveBeenCalledWith(
        'week.error',
        expect.objectContaining({ action: 'week_page_init', reason: 'REPORT_LOOKUP_500', block: 'WEEK_INIT' }),
        expect.any(Object),
      );
    });
  });

  it('keeps in-progress week on a calm top-layer state without the full content stack', async () => {
    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-42', report_type: 'week_forecast', status: 'in_progress' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-42', report_type: 'week_forecast', status: 'in_progress' },
            week_brief: {
              status: 'in_progress',
              fallback_mode: true,
              summary: {
                headline: 'Неделя собирается',
                subhead: 'Показываем устойчивый безопасный слой',
                week_type: 'balance',
                theme: 'weekly report',
              },
              report_ref: { report_id: 'week-42', source_status: 'in_progress' },
            },
            chunks: [{ id: 'deep-1', title: 'Фокус недели', content: 'Держите базовый ритм.' }],
          }),
          { status: 200 },
        ),
      );

    render(<WeekPage />);

    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    expect(screen.queryByTestId('week-fallback-note')).not.toBeInTheDocument();
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('Неделя собирается');
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('Тема уточняется');
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('Локация уточняется');
    expect(screen.getByTestId('week-hero-map')).not.toHaveTextContent(/legacy|fallback|week_map|weekbrief|headline|markdown|weekly report|compatibility/i);
    expect(screen.getByTestId('week-hero-map')).toHaveAttribute('data-primary-href', '/read/week-42');
    expect(screen.getByTestId('week-hero-map')).toHaveAttribute('data-primary-label', 'Открыть полный отчёт');
    expect(screen.getByTestId('week-in-progress-state')).toHaveTextContent('Показываем только спокойный верхний слой');
    expect(screen.queryByTestId('week-domain-panel')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-day-strip')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-day-drawer')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-actions-panel')).not.toBeInTheDocument();
    expect(trackCatalogEventMock).toHaveBeenCalledWith(
      'week.brief_view',
      expect.objectContaining({ status: 'in_progress', sections_count: 0 }),
      expect.any(Object),
    );
  });

  it('renders strict empty/create state when report history is empty', async () => {
    correlatedFetchMock.mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    render(<WeekPage />);

    expect(await screen.findByText('Персональной недели пока нет')).toBeInTheDocument();
    expect(screen.getByText('Для этого Telegram-профиля пока нет сохранённой персональной недели. Чтобы увидеть её целиком, соберите новый недельный разбор.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Собрать персональную неделю/i })).toHaveAttribute('href', '/create?type=week_forecast');
    expect(screen.queryByTestId('week-map-surface')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-fallback-note')).not.toBeInTheDocument();
  });

  it('prefers the freshest eligible week report before fetching details', async () => {
    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-old', report_type: 'week_forecast', status: 'completed', created_at: '2026-03-24T09:00:00+00:00' },
            { id: 'week-new', report_type: 'week_forecast', status: 'completed', created_at: '2026-04-02T08:00:00+00:00' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-new', report_type: 'week_forecast', status: 'completed' },
            week_brief: {
              status: 'ready',
              fallback_mode: false,
              summary: {
                headline: 'Свежая неделя',
                subhead: 'Берём newest completed report, а не первый в списке.',
                week_type: 'balance',
                theme: 'Fresh binding',
              },
              report_ref: { report_id: 'week-new', source_status: 'completed' },
            },
            chunks: [],
          }),
          { status: 200 },
        ),
      );

    render(<WeekPage />);

    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    await waitFor(() => {
      expect(correlatedFetchMock).toHaveBeenNthCalledWith(2, '/api/reports/week-new', expect.any(Object));
    });
    expect(screen.getByTestId('week-hero-map')).toHaveAttribute('data-primary-href', '/read/week-new');
  });

  it('keeps canonical week rendering independent from legacy week_map and chunks', async () => {
    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-canonical', report_type: 'week_forecast', status: 'completed', created_at: '2026-04-10T08:00:00+00:00' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-canonical', report_type: 'week_forecast', status: 'completed' },
            week_brief: {
              status: 'ready',
              fallback_mode: false,
              summary: {
                headline: 'Каноническая неделя',
                subhead: 'Только week_brief формирует экран',
                week_type: 'balance',
                theme: 'Canonical',
              },
              day_cards: [
                { weekday: 'fri', date: '2026-04-10', headline: 'Работать по главному приоритету' },
              ],
              best_uses: [],
              risks: [],
              domains: [],
              deep_sections: [],
              report_ref: { report_id: 'week-canonical', source_status: 'completed' },
            },
            week_map: {
              thesis: 'Legacy тезис не должен попасть в canonical render',
              actions: ['legacy action'],
              risks: ['legacy risk'],
            },
            chunks: [{ id: 'legacy', title: 'Legacy chunk', content: 'legacy content' }],
          }),
          { status: 200 },
        ),
      );

    render(<WeekPage />);

    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('Каноническая неделя');
    expect(screen.getByTestId('week-hero-map')).not.toHaveTextContent('Legacy тезис не должен попасть в canonical render');
    expect(screen.getByTestId('week-day-strip')).toHaveTextContent('ПН, 6 апр');
    expect(screen.getByTestId('week-day-strip')).toHaveTextContent('ПТ, 10 апр');
    expect(screen.getByTestId('week-day-strip')).toHaveTextContent('ВС, 12 апр');
    expect(screen.getByTestId('week-day-drawer')).toHaveTextContent('Деталь дня:ПТ, 10 апр:Работать по главному приоритету');
    expect(screen.queryByTestId('week-day-grid')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-fallback-note')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-secondary-reading')).not.toBeInTheDocument();
  });

  it('renders empty/create state instead of compatibility substitute when only legacy payload exists', async () => {
    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-legacy', report_type: 'week_forecast', status: 'completed', created_at: '2026-04-10T08:00:00+00:00' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-legacy', report_type: 'week_forecast', status: 'completed' },
            week_map: {
              thesis: 'Legacy fallback headline',
              theme: 'weekly report',
              day_cards: [{ weekday: 'Понедельник', date: '2026-03-23', headline: 'Legacy substitute' }],
            },
            chunks: [{ id: 'legacy-1', section: 'week_strategy', title: 'Стратегия недели', content: 'Legacy narrative' }],
          }),
          { status: 200 },
        ),
      );

    render(<WeekPage />);

    expect(await screen.findByText('Персональной недели пока нет')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Собрать персональную неделю/i })).toHaveAttribute('href', '/create?type=week_forecast');
    expect(screen.queryByTestId('week-map-surface')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-day-grid')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-compatibility-section')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-fallback-note')).not.toBeInTheDocument();
    expect(screen.queryByText(/Legacy|fallback|week_map|weekly report|compatibility/i)).not.toBeInTheDocument();
  });

  it('keeps mock runtime without explicit weekly payload on strict empty/create state', async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams('mock=1'));
    mockUseTelegram.mockReturnValue({ isReady: true, initData: '123456789', mode: 'mock', bootstrapOutcome: 'ready' });

    render(<WeekPage />);

    expect(await screen.findByText('Персональной недели пока нет')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Собрать персональную неделю/i })).toHaveAttribute('href', '/create?type=week_forecast');
    expect(screen.queryByTestId('week-map-surface')).not.toBeInTheDocument();
    expect(screen.queryByTestId('week-fallback-note')).not.toBeInTheDocument();
    expect(correlatedFetchMock).not.toHaveBeenCalled();
  });

  it('renders a deterministic /week route gate for the shared dev runtime badge', () => {
    process.env.NODE_ENV = 'development';
    window.history.replaceState({}, '', '/week');

    const RootLayout = loadRootLayout();
    renderRootLayoutDocument(
      <RootLayout>
        <div>week</div>
      </RootLayout>,
    );

    executeRuntimeBadgeRouteGate();

    const badge = document.querySelector('[data-testid="runtime-environment-badge"]');
    expect(badge).toBeInstanceOf(HTMLButtonElement);
    expect(badge).toHaveAttribute('data-runtime-badge-route-gate', 'day-home-only');
    expect(badge).toHaveAttribute('data-runtime-badge-event', 'astro:week-dev-indicator-toggle-request');
    expect(badge).toHaveAttribute('data-route-eligible', 'true');
    expect(badge).toHaveAttribute('aria-disabled', 'false');
    expect(badge).toHaveTextContent('DEV');

    const toggleListener = jest.fn();
    window.addEventListener('astro:week-dev-indicator-toggle-request', toggleListener);
    fireEvent.click(badge as Element);
    expect(toggleListener).toHaveBeenCalledTimes(1);
    window.removeEventListener('astro:week-dev-indicator-toggle-request', toggleListener);
  });

  it('exposes canonical render-path diagnostics and toggles the disclosure on Week in dev mode', async () => {
    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-canonical', report_type: 'week_forecast', status: 'completed', created_at: '2026-04-10T08:00:00+00:00' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-canonical', report_type: 'week_forecast', status: 'completed' },
            week_brief: buildWeekBrief(),
          }),
          { status: 200 },
        ),
      );

    render(<WeekPage />);

    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    expect(screen.getByTestId('week-render-path')).toHaveAttribute('data-render-path', 'canonical');
    expect(screen.queryByTestId('week-runtime-diagnostics-disclosure')).not.toBeInTheDocument();

    await toggleWeekRuntimeDiagnostics();

    expect(screen.getByTestId('week-runtime-diagnostics-disclosure')).toBeInTheDocument();
    expect(screen.getByTestId('week-runtime-diagnostics-render-path')).toHaveTextContent('canonical');
    expect(screen.getByTestId('week-runtime-diagnostics-bootstrap')).toHaveTextContent('ready');
    expect(screen.getByTestId('week-runtime-diagnostics-mode')).toHaveTextContent('telegram');

    await toggleWeekRuntimeDiagnostics();
    expect(screen.queryByTestId('week-runtime-diagnostics-disclosure')).not.toBeInTheDocument();
  });

  it('keeps stable render-path labels for loading, auth_gate, empty, in_progress, and error branches', async () => {
    mockUseTelegram.mockReturnValue({ isReady: false, initData: '', mode: 'none', bootstrapOutcome: 'runtime_missing' });
    const loadingView = render(<WeekPage />);
    expect(await screen.findByTestId('week-render-path')).toHaveAttribute('data-render-path', 'loading');
    loadingView.unmount();

    mockUseTelegram.mockReturnValue({ isReady: true, initData: '', mode: 'guest', bootstrapOutcome: 'initdata_missing' });
    const authGateView = render(<WeekPage />);
    expect(await screen.findByTestId('week-render-path')).toHaveAttribute('data-render-path', 'auth_gate');
    authGateView.unmount();

    correlatedFetchMock.mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    mockUseTelegram.mockReturnValue({ isReady: true, initData: 'tg-auth', mode: 'telegram', bootstrapOutcome: 'ready' });
    const emptyView = render(<WeekPage />);
    expect(await screen.findByTestId('week-render-path')).toHaveAttribute('data-render-path', 'empty');
    emptyView.unmount();

    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-progress', report_type: 'week_forecast', status: 'in_progress', created_at: '2026-04-12T08:00:00+00:00' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-progress', report_type: 'week_forecast', status: 'in_progress' },
            week_brief: buildWeekBrief({
              status: 'in_progress',
              report_ref: { report_id: 'week-progress', source_status: 'in_progress' },
            }),
          }),
          { status: 200 },
        ),
      );
    const inProgressView = render(<WeekPage />);
    await waitFor(() => {
      expect(screen.getByTestId('week-render-path')).toHaveAttribute('data-render-path', 'in_progress');
    });
    inProgressView.unmount();

    correlatedFetchMock.mockResolvedValueOnce(new Response('boom', { status: 500 }));
    const errorView = render(<WeekPage />);
    await waitFor(() => {
      expect(screen.getByTestId('week-render-path')).toHaveAttribute('data-render-path', 'error');
    });
    errorView.unmount();
  });

  it('uses stable fallback values and stays inert in production mode', async () => {
    process.env.NODE_ENV = 'production';
    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-canonical', report_type: 'week_forecast', status: 'completed', created_at: '2026-04-10T08:00:00+00:00' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-canonical', report_type: 'week_forecast', status: 'completed' },
            week_brief: buildWeekBrief(),
          }),
          { status: 200 },
        ),
      );
    mockUseTelegram.mockReturnValue({ isReady: true, initData: 'tg-auth', mode: 'telegram', bootstrapOutcome: null });

    render(<WeekPage />);

    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    expect(screen.queryByTestId('week-render-path')).not.toBeInTheDocument();

    await toggleWeekRuntimeDiagnostics();
    expect(screen.queryByTestId('week-runtime-diagnostics-disclosure')).not.toBeInTheDocument();

    process.env.NODE_ENV = 'development';
    mockUseTelegram.mockReturnValue({ isReady: true, initData: 'tg-auth', mode: '', bootstrapOutcome: '' });
    correlatedFetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { id: 'week-canonical', report_type: 'week_forecast', status: 'completed', created_at: '2026-04-10T08:00:00+00:00' },
          ]),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            report: { id: 'week-canonical', report_type: 'week_forecast', status: 'completed' },
            week_brief: buildWeekBrief(),
          }),
          { status: 200 },
        ),
      );

    const { unmount } = render(<WeekPage />);
    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    await toggleWeekRuntimeDiagnostics();
    expect(screen.getByTestId('week-runtime-diagnostics-bootstrap')).toHaveTextContent('unknown');
    expect(screen.getByTestId('week-runtime-diagnostics-mode')).toHaveTextContent('unavailable');
    unmount();
  });

});
