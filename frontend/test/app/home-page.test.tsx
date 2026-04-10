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

  it('renders explicit empty Today state for non-canonical payloads', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Legacy User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({ general_vibe: 'Legacy fallback headline' }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('Нет данных на сегодня')).toBeInTheDocument();
    expect(screen.getByTestId('today-render-path')).toHaveAttribute('data-render-path', 'empty');
    expect(screen.queryByTestId('today-verdict')).not.toBeInTheDocument();
    expect(screen.queryByTestId('today-scores')).not.toBeInTheDocument();
  });

  it('renders canonical Today sections only for strict canonical payloads', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Canonical User', subscription_active_until: '2026-05-01T00:00:00.000Z' }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_canon_v1',
            status: 'complete',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            hero: {
              title: 'Канонический день',
              subtitle: 'Работаем только через строгий day canon',
              day_type: 'balance',
            },
            domains: {
              energy: { key: 'energy', title: 'Энергия', score_status: 'complete', score: 71, status: 'green', description_status: 'complete', description: 'Есть рабочий ресурс на главное.', why_status: 'complete', why_astro_text: 'Твой Марс собран и не распыляется.', evidence_refs: [] },
              money: { key: 'money', title: 'Деньги', score_status: 'complete', score: 64, status: 'yellow', description_status: 'complete', description: 'Нужны точные цифры и один приоритет.', why_status: 'complete', why_astro_text: 'Твой 2-й дом денег сегодня требует внимательности.', evidence_refs: [] },
              love: { key: 'love', title: 'Любовь', score_status: 'complete', score: 59, status: 'yellow', description_status: 'complete', description: 'Контакт требует мягкого тона.', why_status: 'complete', why_astro_text: 'Твоя Венера просит бережной подачи.', evidence_refs: [] },
              focus: { key: 'focus', title: 'Фокус', score_status: 'complete', score: 77, status: 'green', description_status: 'complete', description: 'Один главный ход даёт лучший результат.', why_status: 'complete', why_astro_text: 'Твой Меркурий сегодня лучше работает в одной линии.', evidence_refs: [] },
            },
          },
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-verdict')).toBeInTheDocument();
    expect(screen.getByTestId('today-render-path')).toHaveAttribute('data-render-path', 'canonical');
    expect(screen.getByTestId('today-scores')).toBeInTheDocument();
    expect(screen.getByTestId('today-cta-panel')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByTestId('empty-state')).not.toBeInTheDocument();
    });
  });

  it('renders explicit no-data state for partial canonical payload without complete domains', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Compatibility User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_canon_v1',
            status: 'partial',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            hero: { title: 'День без полного слоя', subtitle: 'Часть полей отсутствует', day_type: 'balance' },
            domains: {
              energy: { key: 'energy', title: 'Энергия', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
              money: { key: 'money', title: 'Деньги', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
              love: { key: 'love', title: 'Любовь', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
              focus: { key: 'focus', title: 'Фокус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
            },
          },
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-no-data-state')).toBeInTheDocument();
    expect(screen.getByTestId('today-render-path')).toHaveAttribute('data-render-path', 'no_data');
  });
});
