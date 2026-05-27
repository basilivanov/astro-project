import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import BillingCompletePageClient from '../../app/billing/complete/billing-complete-page-client';

const pushMock = jest.fn();
const replaceMock = jest.fn();
const useTelegramMock = jest.fn();

let searchParamsState = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
    replace: replaceMock,
  }),
  useSearchParams: () => searchParamsState,
}));

jest.mock('../../hooks/useTelegram', () => ({
  useTelegram: () => useTelegramMock(),
}));

describe('BillingCompletePageClient', () => {
  const fetchMock = jest.fn();
  const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    searchParamsState = new URLSearchParams();
    useTelegramMock.mockReturnValue({
      initData: 'telegram-auth',
      isReady: true,
      mode: 'live',
    });
    fetchMock.mockReset();
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  afterAll(() => {
    consoleErrorSpy.mockRestore();
  });

  it('uses runtime-aware fallback navigation when provider failure override is present', async () => {
    searchParamsState = new URLSearchParams('status=failed&reason=provider_return_failed&mock=1&runtime=1');

    render(<BillingCompletePageClient />);

    expect(await screen.findByText(/Checkout token не найден/i)).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button', { name: /назад/i })[0]);
    expect(pushMock).toHaveBeenCalledWith('/reports?mock=1&runtime=1');

    fireEvent.click(screen.getByTestId('billing-complete-swipe-back'));
    expect(pushMock).toHaveBeenLastCalledWith('/reports?mock=1&runtime=1');
    expect(screen.getByText('Жест назад обработан.')).toBeInTheDocument();

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('shows provider failure override when checkout resume is otherwise ready', async () => {
    searchParamsState = new URLSearchParams('checkout=session-42&status=failed&reason=provider_return_failed');
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'failed' }),
    });

    render(<BillingCompletePageClient />);

    expect(await screen.findByText(/ЮMoney вернул оплату с ошибкой/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it('shows checkout token error when telegram is ready but checkout is missing', async () => {
    render(<BillingCompletePageClient />);

    expect(await screen.findByText(/Checkout token не найден/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('shows telegram return error when initData is unavailable', async () => {
    searchParamsState = new URLSearchParams('checkout=session-42');
    useTelegramMock.mockReturnValue({
      initData: null,
      isReady: true,
      mode: 'live',
    });

    render(<BillingCompletePageClient />);

    expect(await screen.findByText(/Нужен возврат в Telegram WebApp/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('redirects to create preserving flags after successful resume', async () => {
    searchParamsState = new URLSearchParams('checkout=session-42&mock=1&runtime=1');
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'succeeded',
        return_path: '/create?foo=bar',
      }),
    });

    render(<BillingCompletePageClient />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/billing/sessions/session-42', {
        headers: { 'X-Telegram-Auth': 'telegram-auth' },
      });
    });

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith('/create?foo=bar&checkout=session-42&mock=1&runtime=1');
    });
  });

  it('redirects directly to read page for resumed reports in mock mode', async () => {
    searchParamsState = new URLSearchParams('checkout=session-42');
    useTelegramMock.mockReturnValue({
      initData: 'telegram-auth',
      isReady: true,
      mode: 'mock',
    });
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        resumed_report_id: 'report-7',
      }),
    });

    render(<BillingCompletePageClient />);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith('/read/report-7?mock=1');
    });
  });

  it('maps canceled and failed session responses to terminal errors', async () => {
    searchParamsState = new URLSearchParams('checkout=session-42');
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'canceled' }),
    });

    const { unmount } = render(<BillingCompletePageClient />);

    expect(await screen.findByText(/Оплата была отменена\./i)).toBeInTheDocument();
    unmount();

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'failed' }),
    });

    render(<BillingCompletePageClient />);

    expect(await screen.findByText(/Платежная сессия завершилась с ошибкой/i)).toBeInTheDocument();
  });

  it('falls back to a restore error when the resume request fails', async () => {
    searchParamsState = new URLSearchParams('checkout=session-42');
    fetchMock.mockResolvedValueOnce({
      ok: false,
      json: async () => ({}),
    });

    render(<BillingCompletePageClient />);

    expect(await screen.findByText(/Не удалось восстановить платежную сессию/i)).toBeInTheDocument();
    expect(consoleErrorSpy).toHaveBeenCalled();
  });

  it('handles swipe-back gesture and routes to the fallback path', async () => {
    searchParamsState = new URLSearchParams('status=canceled&runtime=1&checkout=session-42');

    render(<BillingCompletePageClient />);

    expect(await screen.findByText(/Оплата была отменена\./i)).toBeInTheDocument();

    act(() => {
      window.dispatchEvent(new TouchEvent('touchstart', { changedTouches: [{ clientX: 10 }] as unknown as TouchList }));
      window.dispatchEvent(new TouchEvent('touchend', { changedTouches: [{ clientX: 120 }] as unknown as TouchList }));
    });

    expect(pushMock).toHaveBeenLastCalledWith('/reports?runtime=1');
    expect(screen.getByText('Жест назад обработан.')).toBeInTheDocument();
  });
});
