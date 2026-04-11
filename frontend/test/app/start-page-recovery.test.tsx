import React from 'react';
import { render, screen } from '@testing-library/react';

import StartPage from '../../app/start/page';

const mockUseRouter = jest.fn();
const mockUseTelegram = jest.fn();
const ensureCorrelationIdMock = jest.fn();
const setCorrelationIdMock = jest.fn();
const trackCatalogEventMock = jest.fn().mockResolvedValue(undefined);

jest.mock('next/navigation', () => ({
  useRouter: () => mockUseRouter(),
}));

jest.mock('../../hooks/useTelegram', () => ({
  useTelegram: () => mockUseTelegram(),
}));

jest.mock('../../lib/correlation', () => ({
  CorrelationManager: {
    ensureCorrelationId: () => ensureCorrelationIdMock(),
    setCorrelationId: (...args: unknown[]) => setCorrelationIdMock(...args),
  },
  correlatedFetch: jest.fn(),
}));

jest.mock('../../components/catalog/catalog-analytics', () => ({
  trackCatalogEvent: (...args: unknown[]) => trackCatalogEventMock(...args),
}));

jest.mock('../../components/ui-states', () => ({
  LoadingState: ({ message }: { message: string }) => <div data-testid="loading-state">{message}</div>,
}));

describe('StartPage recovery', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue({ replace: jest.fn() });
    ensureCorrelationIdMock.mockReturnValue('corr-start');
    window.history.replaceState({}, '', '/start?recovery=runtime_missing');
    mockUseTelegram.mockReturnValue({
      user: null,
      initData: '',
      isReady: true,
      mode: 'none',
      correlationId: 'corr-start',
      flowId: 'FLOW-HOME-FEED',
      bootstrapOutcome: 'runtime_missing',
    });
  });

  it('shows explicit recovery copy and retry control', async () => {
    render(<StartPage />);

    expect(await screen.findByTestId('start-auth-gate')).toBeInTheDocument();
    expect(screen.getByTestId('start-recovery-copy')).toHaveTextContent('Mini App не получила Telegram runtime вовремя');
    expect(screen.getByTestId('start-recovery-retry')).toBeInTheDocument();
  });
});
