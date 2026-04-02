import { fireEvent, render, screen, waitFor, act } from '@testing-library/react';

import { CatalogCheckoutResumeBanner } from '../../../components/catalog/catalog-checkout-resume';

const mockReplace = jest.fn();
const mockTrackCatalogEvent = jest.fn(() => Promise.resolve());
const mockSetCatalogAnalyticsContext = jest.fn();
const mockSetCatalogCorrelationId = jest.fn();
const mockStartCatalogCorrelation = jest.fn(() => 'catalog-correlation-1');
const mockEnsureCorrelationId = jest.fn(() => 'global-correlation-1');

let mockPathname = '/reports';
let mockSearchParams = new URLSearchParams('checkout=token-123&foo=bar');

jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => mockPathname,
  useSearchParams: () => mockSearchParams,
}));

jest.mock('next/link', () => {
  const React = require('react');
  return function MockLink({ href, children, onClick, prefetch: _prefetch, ...props }: any) {
    return React.createElement(
      'a',
      {
        href,
        onClick: (event: any) => {
          event.preventDefault();
          onClick?.(event);
        },
        ...props,
      },
      children,
    );
  };
});

jest.mock('../../../components/catalog/catalog-analytics', () => ({
  startCatalogCorrelation: (...args: unknown[]) => mockStartCatalogCorrelation(...args),
  setCatalogAnalyticsContext: (...args: unknown[]) => mockSetCatalogAnalyticsContext(...args),
  setCatalogCorrelationId: (...args: unknown[]) => mockSetCatalogCorrelationId(...args),
  trackCatalogEvent: (...args: unknown[]) => mockTrackCatalogEvent(...args),
}));

jest.mock('../../../lib/correlation', () => ({
  CorrelationManager: {
    ensureCorrelationId: (...args: unknown[]) => mockEnsureCorrelationId(...args),
  },
}));

describe('CatalogCheckoutResumeBanner', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useRealTimers();
    mockPathname = '/reports';
    mockSearchParams = new URLSearchParams('checkout=token-123&foo=bar');
    global.fetch = jest.fn();
  });

  afterAll(() => {
    global.fetch = originalFetch;
  });

  function renderBanner(overrides: Partial<React.ComponentProps<typeof CatalogCheckoutResumeBanner>> = {}) {
    return render(
      <CatalogCheckoutResumeBanner
        surface="catalog"
        checkoutToken="token-123"
        initData="telegram-auth"
        isReady
        mode="live"
        {...overrides}
      />,
    );
  }

  it('renders nothing when checkout token is absent', () => {
    const { container } = renderBanner({ checkoutToken: null });

    expect(container.firstChild).toBeNull();
    expect(mockTrackCatalogEvent).not.toHaveBeenCalled();
  });

  it('shows unauthorized copy when init data is missing', async () => {
    renderBanner({ initData: '' });

    expect(await screen.findByText('Чтобы продолжить оформление, откройте экран из Telegram.')).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('uses fallback resume href with mock/runtime flags in mock mode', async () => {
    renderBanner({ mockEnabled: true, runtimeEnabled: true });

    const resumeLink = await screen.findByRole('link', { name: 'Вернуться' });
    expect(resumeLink).toHaveAttribute('href', '/create?checkout=token-123&mock=1&runtime=1');
    expect(await screen.findByText('Прогноз на неделю уже оплачен. Вернитесь, чтобы завершить запуск.')).toBeInTheDocument();
  });

  it('shows succeeded copy for resumed sessions and tracks success once', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'resumed',
        report_type: 'horary_answer',
      }),
    });

    renderBanner();

    expect(await screen.findByText('Вопрос уже оплачен. Вернитесь, чтобы завершить запуск.')).toBeInTheDocument();
    await waitFor(() => {
      expect(mockTrackCatalogEvent).toHaveBeenCalledWith(
        'catalog.checkout_resume_success',
        expect.objectContaining({
          report_type: 'horary_answer',
          semantic_block: 'CHECKOUT_RESUME_STATUS_SUCCEEDED',
        }),
      );
    });
  });

  it('tracks pending session status deterministically', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'pending', report_type: 'week_forecast' }),
    });

    renderBanner();

    expect(await screen.findByText('Продолжаем оформление Прогноз на неделю. Вернуться к оплате?')).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith('/api/billing/sessions/token-123', {
      headers: { 'X-Telegram-Auth': 'telegram-auth' },
    });
    expect(mockTrackCatalogEvent).toHaveBeenCalledWith(
      'catalog.checkout_resume_status',
      expect.objectContaining({
        report_type: 'week_forecast',
        block: 'CHECKOUT_RESUME_STATUS_PENDING',
      }),
    );
  });

  it('routes back to mock fallback resume href when back button is pressed', async () => {
    renderBanner({ mockEnabled: true });

    fireEvent.click(await screen.findByRole('button', { name: 'Назад' }));

    expect(mockReplace).toHaveBeenCalledWith('/create?checkout=token-123&mock=1&runtime=1');
  });

  it('removes checkout query param and clears analytics on cancel', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'failed', report_type: 'year_forecast' }),
    });

    renderBanner();

    fireEvent.click(await screen.findByRole('button', { name: 'Отменить' }));

    expect(mockSetCatalogAnalyticsContext).toHaveBeenCalledWith({ checkout_token: undefined });
    expect(mockReplace).toHaveBeenCalledWith('/reports?foo=bar');
    expect(mockTrackCatalogEvent).toHaveBeenCalledWith(
      'catalog.checkout_resume_cancel',
      expect.objectContaining({ semantic_block: 'CHECKOUT_RESUME_CTA_CANCEL' }),
    );
  });

  it('tracks resume click with current report type', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'canceled', report_type: 'synastry' }),
    });
    const onTrackAction = jest.fn();

    renderBanner({ onTrackAction, entryPoint: 'reports-grid' });

    fireEvent.click(await screen.findByRole('link', { name: 'Вернуться' }));

    expect(onTrackAction).toHaveBeenCalledWith('resume_click', 'reports-grid');
    expect(mockTrackCatalogEvent).toHaveBeenCalledWith(
      'catalog.checkout_resume_start',
      expect.objectContaining({
        entry_point: 'reports-grid',
        report_type: 'synastry',
        semantic_block: 'CHECKOUT_RESUME_CTA_PRIMARY',
      }),
    );
  });

  it('falls back to error copy when session fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('network'));

    renderBanner();

    expect(await screen.findByText('Не удалось проверить оплату. Повторите попытку.')).toBeInTheDocument();
  });
});
