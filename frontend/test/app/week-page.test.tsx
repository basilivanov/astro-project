import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import WeekPage from '../../app/week/page';

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
  WeekHeroMap: ({ week, primaryHref, primaryLabel }: { week: { headline: string }; primaryHref: string; primaryLabel: string }) => (
    <div data-testid="week-hero-map">
      <span>{week.headline}</span>
      <span>{primaryHref}</span>
      <span>{primaryLabel}</span>
    </div>
  ),
}));

jest.mock('../../components/week/week-day-strip', () => ({
  WeekDayStrip: ({ week }: { week: { dayStrip: Array<{ weekday?: string | null }> } }) => (
    <div data-testid="week-day-strip">{week.dayStrip.map((day) => day.weekday).filter(Boolean).join(', ')}</div>
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
  beforeEach(() => {
    jest.clearAllMocks();
    mockUsePathname.mockReturnValue('/week');
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    mockUseTelegram.mockReturnValue({ isReady: true, initData: 'tg-auth', mode: 'user' });
    startCatalogCorrelationMock.mockReturnValue('corr-week');
    correlatedFetchMock.mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));
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

  it('renders safe fallback note and in-progress poller from fetched payload state', async () => {
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
                theme: 'Контролируемая неделя',
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
    expect(screen.getByTestId('week-fallback-note')).toHaveTextContent('weekly report ещё собирается');
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('Неделя собирается');
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('/read/week-42');
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('Открыть полный отчёт');
    expect(trackCatalogEventMock).toHaveBeenCalledWith(
      'week.brief_view',
      expect.objectContaining({ status: 'in_progress', sections_count: 1 }),
      expect.any(Object),
    );
  });

  it('renders honest signed fallback when report history is empty', async () => {
    correlatedFetchMock.mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    render(<WeekPage />);

    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    expect(screen.getByTestId('week-fallback-note')).toHaveTextContent('ещё нет сохранённого weekly report в истории');
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('/create?type=week_forecast');
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('Собрать персональную неделю');
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
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('/read/week-new');
  });

  it('uses mock runtime payload without fetching report details', async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams('mock=1'));
    correlatedFetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify([
          { id: 'week-99', report_type: 'week_forecast', status: 'completed' },
        ]),
        { status: 200 },
      ),
    );

    render(<WeekPage />);

    expect(await screen.findByTestId('week-map-surface')).toBeInTheDocument();
    await waitFor(() => expect(correlatedFetchMock).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId('week-hero-map')).toHaveTextContent('/read/week-99');
    expect(screen.getByTestId('week-day-strip')).toHaveTextContent('ПН, 23 мар');
  });

});
