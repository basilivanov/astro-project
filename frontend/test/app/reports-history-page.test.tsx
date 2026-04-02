import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import HistoryPage from '../../app/reports/history/page';

const mockUseSearchParams = jest.fn();
const mockUseTelegram = jest.fn();
const setCatalogAnalyticsContextMock = jest.fn();
const startCatalogCorrelationMock = jest.fn();
const trackCatalogEventMock = jest.fn().mockResolvedValue(undefined);

jest.mock('next/navigation', () => ({
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock('../../hooks/useTelegram', () => ({
  useTelegram: () => mockUseTelegram(),
}));

jest.mock('next/link', () => {
  return function MockLink({ href, onClick, children, ...props }: React.PropsWithChildren<{ href: string; onClick?: () => void }>) {
    return (
      <a href={href} onClick={(event) => { event.preventDefault(); onClick?.(); }} {...props}>
        {children}
      </a>
    );
  };
});

jest.mock('../../components/catalog/catalog-checkout-resume', () => ({
  CatalogCheckoutResumeBanner: ({ checkoutToken }: { checkoutToken?: string | null }) => (
    <div data-testid="checkout-resume-banner">{checkoutToken ?? 'no-checkout'}</div>
  ),
}));

jest.mock('../../components/catalog/catalog-analytics', () => ({
  setCatalogAnalyticsContext: (...args: unknown[]) => setCatalogAnalyticsContextMock(...args),
  startCatalogCorrelation: (...args: unknown[]) => startCatalogCorrelationMock(...args),
  trackCatalogEvent: (...args: unknown[]) => trackCatalogEventMock(...args),
}));

describe('HistoryPage', () => {
  const fetchMock = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    mockUseTelegram.mockReturnValue({
      initData: 'tg-auth',
      isReady: true,
      mode: 'user',
      user: { id: 42 },
    });
    startCatalogCorrelationMock.mockReturnValue('corr-history');
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  it('renders guest empty state without requesting history', async () => {
    mockUseTelegram.mockReturnValue({
      initData: null,
      isReady: true,
      mode: 'guest',
      user: null,
    });

    render(<HistoryPage />);

    expect(await screen.findByText('История пока недоступна')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(startCatalogCorrelationMock).toHaveBeenCalledWith('history_view');
  });

  it('fetches reports with auth and runtime flags, then renders filtered content', async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams('checkout=session-42&runtime=1'));
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify([
          {
            id: 'report-natal',
            report_type: 'natal_master',
            status: 'completed',
            created_at: '2026-03-20T10:15:00.000Z',
            client_name: '  Алиса  ',
          },
          {
            id: 'report-forecast',
            report_type: 'year_forecast',
            status: 'pending',
            created_at: '2026-03-21T11:30:00.000Z',
            client_name: '',
          },
        ]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    render(<HistoryPage />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost/api/reports/my?runtime=1',
        expect.objectContaining({
          headers: {
            'X-Telegram-Auth': 'tg-auth',
          },
        }),
      );
    });

    expect(await screen.findByText('Натальная карта')).toBeInTheDocument();
    expect(screen.getAllByText('Алиса')).toHaveLength(2);
    expect(screen.getByText('Альманах 2026')).toBeInTheDocument();
    expect(screen.getAllByText('Личный профиль')).toHaveLength(2);
    expect(screen.getByTestId('checkout-resume-banner')).toHaveTextContent('session-42');
    expect(setCatalogAnalyticsContextMock).toHaveBeenCalledWith({
      user_id: 42,
      checkout_token: 'session-42',
      correlation_id: 'corr-history',
    });
    expect(startCatalogCorrelationMock).toHaveBeenCalledWith('history_checkout_resume');

    fireEvent.click(screen.getByRole('button', { name: 'Натал' }));

    expect(await screen.findByText('Создать новый Натал')).toBeInTheDocument();
    expect(screen.queryByText('Альманах 2026')).not.toBeInTheDocument();

    await waitFor(() => {
      expect(trackCatalogEventMock).toHaveBeenCalledWith(
        'catalog.history_filter',
        expect.objectContaining({ filter_id: 'natal', surface: 'history', entry_point: 'history-filter-chip' }),
      );
    });
  });

  it('tracks CTA clicks for filter and report open actions', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify([
          {
            id: 'report-horary',
            report_type: 'horary',
            status: 'completed',
            created_at: '2026-03-22T09:00:00.000Z',
            client_name: 'Игорь',
          },
        ]),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    render(<HistoryPage />);

    expect(await screen.findByText('Вопрос')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('history-filter-cta'));
    fireEvent.click(screen.getByRole('link', { name: 'Вопрос: Игорь' }));

    await waitFor(() => {
      expect(trackCatalogEventMock).toHaveBeenCalledWith(
        'catalog.history_cta',
        expect.objectContaining({ action: 'filter_cta', cta_href: '/reports', surface: 'history', filter_id: 'all' }),
      );
      expect(trackCatalogEventMock).toHaveBeenCalledWith(
        'catalog.history_open_report',
        expect.objectContaining({ report_id: 'report-horary', report_type: 'horary', surface: 'history', entry_point: 'history-report-card' }),
      );
    });
  });

  it('renders retryable error state when the history request fails', async () => {
    fetchMock.mockResolvedValueOnce(new Response('boom', { status: 500 }));

    render(<HistoryPage />);

    expect(await screen.findByText('Упс, ошибка')).toBeInTheDocument();
    expect(screen.getByText('Не удалось загрузить историю разборов')).toBeInTheDocument();

    await waitFor(() => {
      expect(trackCatalogEventMock).toHaveBeenCalledWith(
        'catalog.history_error',
        expect.objectContaining({ surface: 'history', entry_point: 'history-page-load' }),
      );
    });
  });
});
