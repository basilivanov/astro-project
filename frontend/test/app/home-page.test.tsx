import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

import FeedPage from '../../app/page';

const mockUseRouter = jest.fn();
const mockUseTelegram = jest.fn();
const ensureHomeCorrelationMock = jest.fn();
const homeFetchMock = jest.fn();
const makeHomeTraceMock = jest.fn();
const trackHomeEventMock = jest.fn().mockResolvedValue(undefined);

jest.mock('next/navigation', () => ({
  useRouter: () => mockUseRouter(),
}));

jest.mock('../../hooks/useTelegram', () => ({
  useTelegram: () => mockUseTelegram(),
}));

jest.mock('../../components/landing/LandingContent', () => ({
  LandingContent: () => <div data-testid="landing-content" />,
}));

jest.mock('../../components/TrialStatusWidget', () => ({
  TrialStatusWidget: () => <div data-testid="trial-status-widget" />,
}));

jest.mock('../../components/consumer-page-shell', () => ({
  ConsumerHero: ({ title }: { title?: string }) => <div data-testid="consumer-hero">{title}</div>,
  ConsumerMetaPill: ({ value }: { value?: string }) => <span data-testid="consumer-meta-pill">{value}</span>,
  ConsumerPageShell: ({ children, testId }: { children: React.ReactNode; testId?: string }) => <div data-testid={testId ?? 'consumer-page-shell'}>{children}</div>,
  ConsumerPanel: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
}));

jest.mock('../../components/ui-states', () => ({
  EmptyState: ({ title, message, actionHref, actionTestId }: { title: string; message: string; actionHref?: string; actionTestId?: string }) => (
    <div data-testid="empty-state">
      <h2>{title}</h2>
      <p>{message}</p>
      {actionHref ? <a href={actionHref} data-testid={actionTestId}>action</a> : null}
    </div>
  ),
  ErrorState: ({ error }: { error: string }) => <div data-testid="error-state">{error}</div>,
  LoadingState: ({ message }: { message: string }) => <div data-testid="loading-state">{message}</div>,
}));

jest.mock('../../components/today/daybrief-sections', () => ({
  TodayVerdict: () => <div data-testid="today-verdict">verdict</div>,
  TodayScores: () => <div data-testid="today-scores">scores</div>,
  TodayWindows: () => <div data-testid="today-windows">windows</div>,
  TodayActions: () => <div data-testid="today-actions">actions</div>,
  TodayRisks: () => <div data-testid="today-risks">risks</div>,
  TodayExplainability: () => <div data-testid="today-explainability">explainability</div>,
  TodayCtaPanel: () => <div data-testid="today-cta-panel">cta</div>,
}));

jest.mock('../../lib/home-analytics', () => ({
  HOME_FLOW_ID: 'flow.home',
  ensureHomeCorrelation: (...args: unknown[]) => ensureHomeCorrelationMock(...args),
  homeFetch: (...args: unknown[]) => homeFetchMock(...args),
  makeHomeTrace: (...args: unknown[]) => makeHomeTraceMock(...args),
  trackHomeEvent: (...args: unknown[]) => trackHomeEventMock(...args),
}));

describe('FeedPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue({ push: jest.fn() });
    mockUseTelegram.mockReturnValue({
      isReady: true,
      mode: 'telegram',
      initData: 'signed-init-data',
      user: { id: 42424242 },
    });
    ensureHomeCorrelationMock.mockReturnValue('corr-home');
    makeHomeTraceMock.mockReturnValue({ trace_id: 'trace-home' });
  });

  it('renders explicit degraded Today state for legacy payloads instead of premium sections', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Legacy User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          general_vibe: 'Legacy fallback headline',
          traffic_lights: { health: 'green', money: 'yellow' },
          fast_hits: [{ summary: 'Утренний импульс' }],
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-degraded-state')).toBeInTheDocument();
    expect(screen.getByTestId('today-render-path')).toHaveAttribute('data-render-path', 'degraded');
    expect(screen.getByText('Сегодня доступен только короткий обзор')).toBeInTheDocument();
    expect(screen.getByTestId('today-degraded-note')).toHaveTextContent('Полная персональная карта дня появится');
    expect(screen.getByTestId('today-degraded-cta')).toHaveAttribute('href', '/week');
    expect(screen.queryByTestId('today-verdict')).not.toBeInTheDocument();
    expect(screen.queryByTestId('today-scores')).not.toBeInTheDocument();
    expect(screen.queryByTestId('today-windows')).not.toBeInTheDocument();
    expect(screen.queryByTestId('today-actions')).not.toBeInTheDocument();
    expect(screen.queryByTestId('today-risks')).not.toBeInTheDocument();
  });

  it('renders canonical Today sections only for day_brief_v1 payloads', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Canonical User', subscription_active_until: '2026-05-01T00:00:00.000Z' }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_v1',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            fallback_mode: false,
            summary: {
              headline: 'Канонический день',
              subhead: 'Работаем только через day_brief_v1',
              day_type: 'balance',
            },
            context: {},
            scores: [],
            windows: [],
            best_uses: [],
            risks: [],
            personalized_factors: [],
            explainability: { confidence: 0.8, birth_time_used: true, factor_count: 2 },
          },
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-verdict')).toBeInTheDocument();
    expect(screen.getByTestId('today-render-path')).toHaveAttribute('data-render-path', 'canonical');
    expect(screen.getByTestId('today-scores')).toBeInTheDocument();
    expect(screen.getByTestId('today-windows')).toBeInTheDocument();
    expect(screen.getByTestId('today-actions')).toBeInTheDocument();
    expect(screen.getByTestId('today-risks')).toBeInTheDocument();
    expect(screen.getByTestId('today-explainability')).toBeInTheDocument();
    expect(screen.getByTestId('today-cta-panel')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByTestId('today-degraded-state')).not.toBeInTheDocument();
    });
  });

  it('marks canonical fallback_mode day_brief as compatibility for parity diagnostics', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Compatibility User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_v1',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            fallback_mode: true,
            summary: {
              headline: 'Совместимый день',
              subhead: 'Канонический transport, но fallback semantics',
              day_type: 'balance',
            },
            context: {},
            scores: [],
            windows: [],
            best_uses: [],
            risks: [],
            personalized_factors: [],
            explainability: { confidence: 0.4, birth_time_used: false, factor_count: 1 },
          },
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-verdict')).toBeInTheDocument();
    expect(screen.getByTestId('today-render-path')).toHaveAttribute('data-render-path', 'compatibility');
  });
});
