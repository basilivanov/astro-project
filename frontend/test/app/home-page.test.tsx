import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import FeedPage from '../../app/page';

const originalNodeEnv = process.env.NODE_ENV;
const mockUseRouter = jest.fn();
const mockUsePathname = jest.fn();
const mockUseTelegram = jest.fn();
const ensureHomeCorrelationMock = jest.fn();
const homeFetchMock = jest.fn();
const makeHomeTraceMock = jest.fn();
const trackHomeEventMock = jest.fn().mockResolvedValue(undefined);

jest.mock('next/navigation', () => ({
  useRouter: () => mockUseRouter(),
  usePathname: () => mockUsePathname(),
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

jest.mock('../../components/landing/LandingContent', () => ({
  LandingContent: () => <div data-testid="landing-content" />,
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

jest.mock('../../components/today/daybrief-sections', () => {
  const actual = jest.requireActual('../../components/today/daybrief-sections') as typeof import('../../components/today/daybrief-sections');
  return {
    ...actual,
    TodayVerdict: () => <div data-testid="today-verdict">verdict</div>,
    TodayScores: () => <div data-testid="today-scores">scores</div>,
    TodayCtaPanel: () => <div data-testid="today-cta-panel">cta</div>,
  };
});

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
    mockUsePathname.mockReturnValue('/');
    mockUseRouter.mockReturnValue({ push: jest.fn() });
    mockUseTelegram.mockReturnValue({
      isReady: true,
      mode: 'telegram',
      initData: 'signed-init-data',
      user: { id: 42424242 },
      bootstrapOutcome: 'ready',
      bootstrapDiagnostics: null,
    });
    ensureHomeCorrelationMock.mockReturnValue('corr-home');
    makeHomeTraceMock.mockReturnValue({ trace_id: 'trace-home' });
  });

  afterEach(() => {
    process.env.NODE_ENV = originalNodeEnv;
    window.history.replaceState({}, '', '/');
  });

  afterAll(() => {
    process.env.NODE_ENV = originalNodeEnv;
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
    expect(source).toContain('astro:day-dev-indicator-toggle-request');
    window.eval(source);
  };

  const toggleDayRuntimeDiagnostics = async () => {
    await act(async () => {
      window.dispatchEvent(new CustomEvent('astro:day-dev-indicator-toggle-request', {
        detail: { route: '/', source: 'test' },
      }));
    });
  };

  it('shows bootstrap recovery state instead of infinite shell after timeout', async () => {
    jest.useFakeTimers();
    mockUseTelegram.mockReturnValue({
      isReady: false,
      mode: 'none',
      initData: '',
      user: null,
      bootstrapOutcome: 'runtime_missing',
      bootstrapDiagnostics: { href: 'https://dev.astro.vasiliy-ivanov.ru/', hash: '', outcome: 'runtime_missing' },
    });

    render(<FeedPage />);
    await act(async () => {
      jest.advanceTimersByTime(4500);
    });

    expect(await screen.findByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('Telegram runtime не инициализировался')).toBeInTheDocument();
    expect(screen.getByTestId('home-bootstrap-recover-cta')).toHaveAttribute('href', '/start?recovery=runtime_missing');
    jest.useRealTimers();
  });

  it('uses recovery query on home bootstrap CTA for initdata_missing', async () => {
    jest.useFakeTimers();
    mockUseTelegram.mockReturnValue({
      isReady: false,
      mode: 'none',
      initData: '',
      user: null,
      bootstrapOutcome: 'initdata_missing',
      bootstrapDiagnostics: { href: '/?foo=1', hash: '#tg', outcome: 'initdata_missing' },
    });

    render(<FeedPage />);
    await act(async () => {
      jest.advanceTimersByTime(4500);
    });

    const cta = await screen.findByTestId('home-bootstrap-recover-cta');
    expect(cta).toHaveAttribute('href', '/start?recovery=initdata_missing');
    expect(screen.getByText('Telegram не передал initData')).toBeInTheDocument();
    jest.useRealTimers();
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
              energy: { key: 'energy', title: 'Тонус', score_status: 'complete', score: 71, status: 'green', description_status: 'complete', description: 'Есть рабочий ресурс на главное.', why_status: 'complete', why_astro_text: 'Твой Марс собран и не распыляется.', evidence_refs: [] },
              money: { key: 'money', title: 'Работа и деньги', score_status: 'complete', score: 64, status: 'yellow', description_status: 'complete', description: 'Нужны точные цифры и один приоритет.', why_status: 'complete', why_astro_text: 'Твой 2-й дом денег сегодня требует внимательности.', evidence_refs: [] },
              love: { key: 'love', title: 'Чувства', score_status: 'complete', score: 59, status: 'yellow', description_status: 'complete', description: 'Контакт требует мягкого тона.', why_status: 'complete', why_astro_text: 'Твоя Венера просит бережной подачи.', evidence_refs: [] },
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
    expect(screen.queryByTestId('consumer-hero')).not.toBeInTheDocument();
    expect(screen.getByTestId('today-scores')).toBeInTheDocument();
    expect(screen.getByTestId('today-cta-panel')).toBeInTheDocument();
    expect(screen.queryByTestId('today-premium-block')).not.toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByTestId('empty-state')).not.toBeInTheDocument();
    });
  });

  it('does not render duplicate top hero shell in canonical ready path', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Canonical User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_canon_v1',
            status: 'complete',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            hero: { title: 'Один герой дня', subtitle: 'Без второго верхнего блока', day_type: 'balance' },
            domains: {
              energy: { key: 'energy', title: 'Тонус', score_status: 'complete', score: 71, status: 'green', description_status: 'complete', description: 'Есть рабочий ресурс на главное.', why_status: 'complete', why_astro_text: 'Твой Марс собран и не распыляется.', evidence_refs: [] },
              money: { key: 'money', title: 'Работа и деньги', score_status: 'complete', score: 64, status: 'yellow', description_status: 'complete', description: 'Сверяй условия, сроки и цифры.', why_status: 'complete', why_astro_text: 'Второй дом просит точности.', evidence_refs: [] },
              love: { key: 'love', title: 'Чувства', score_status: 'complete', score: 59, status: 'yellow', description_status: 'complete', description: 'Контакт требует мягкого тона.', why_status: 'complete', why_astro_text: 'Твоя Венера просит бережной подачи.', evidence_refs: [] },
              focus: { key: 'focus', title: 'Фокус', score_status: 'complete', score: 77, status: 'green', description_status: 'complete', description: 'Держи один главный приоритет и не дроби внимание.', why_status: 'complete', why_astro_text: 'Меркурий лучше работает в одной линии.', evidence_refs: [] },
            },
          },
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-verdict')).toBeInTheDocument();
    expect(screen.queryByTestId('consumer-hero')).not.toBeInTheDocument();
    expect(screen.getByTestId('today-render-path')).toHaveAttribute('data-render-path', 'canonical');
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
              energy: { key: 'energy', title: 'Тонус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
              money: { key: 'money', title: 'Работа и деньги', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
              love: { key: 'love', title: 'Чувства', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
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

  it('keeps partial-ready canonical state when at least one domain is complete and another failed', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Partial User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_canon_v1',
            status: 'partial',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            hero: { title: 'Частичный день', subtitle: 'Одна сфера собрана честно.', day_type: 'balance' },
            domains: {
              energy: { key: 'energy', title: 'Тонус', score_status: 'complete', score: 80, status: 'green', description_status: 'complete', description: 'Есть ресурс.', why_status: 'complete', why_astro_text: 'Твой Марс собран и держит темп.', evidence_refs: [] },
              money: { key: 'money', title: 'Работа и деньги', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
              love: { key: 'love', title: 'Чувства', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
              focus: { key: 'focus', title: 'Фокус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
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
    expect(screen.queryByTestId('today-no-data-state')).not.toBeInTheDocument();
  });

  it('expands and collapses the Day runtime disclosure with only the approved visible fields', async () => {
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Canonical User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_canon_v1',
            status: 'complete',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            hero: { title: 'День проверки disclosure', subtitle: 'Показываем только локальные runtime поля.', day_type: 'balance' },
            domains: {
              energy: { key: 'energy', title: 'Тонус', score_status: 'complete', score: 71, status: 'green', description_status: 'complete', description: 'Есть рабочий ресурс.', why_status: 'complete', why_astro_text: 'Марс держит темп.', evidence_refs: [] },
              money: { key: 'money', title: 'Работа и деньги', score_status: 'complete', score: 64, status: 'yellow', description_status: 'complete', description: 'Смотри на цифры.', why_status: 'complete', why_astro_text: 'Второй дом просит точности.', evidence_refs: [] },
              love: { key: 'love', title: 'Чувства', score_status: 'complete', score: 59, status: 'yellow', description_status: 'complete', description: 'Контакт требует мягкости.', why_status: 'complete', why_astro_text: 'Венера просит бережности.', evidence_refs: [] },
              focus: { key: 'focus', title: 'Фокус', score_status: 'complete', score: 77, status: 'green', description_status: 'complete', description: 'Один главный приоритет.', why_status: 'complete', why_astro_text: 'Меркурий держит одну линию.', evidence_refs: [] },
            },
          },
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-verdict')).toBeInTheDocument();
    expect(screen.queryByTestId('day-runtime-diagnostics-disclosure')).not.toBeInTheDocument();

    await toggleDayRuntimeDiagnostics();

    expect(await screen.findByTestId('day-runtime-diagnostics-disclosure')).toBeInTheDocument();
    expect(screen.getByTestId('day-runtime-diagnostics-render-path')).toHaveTextContent('canonical');
    expect(screen.getByTestId('day-runtime-diagnostics-bootstrap')).toHaveTextContent('ready');
    expect(screen.getByTestId('day-runtime-diagnostics-mode')).toHaveTextContent('telegram');
    expect(screen.getByText('Render path')).toBeInTheDocument();
    expect(screen.getByText('Bootstrap')).toBeInTheDocument();
    expect(screen.getByText('Mode')).toBeInTheDocument();
    expect(screen.queryByText(/initData/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/trace/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/correlation/i)).not.toBeInTheDocument();

    await toggleDayRuntimeDiagnostics();

    await waitFor(() => {
      expect(screen.queryByTestId('day-runtime-diagnostics-disclosure')).not.toBeInTheDocument();
    });
  });

  it('uses stable fallback values when runtime diagnostics sources are absent', async () => {
    mockUseTelegram.mockReturnValue({
      isReady: false,
      mode: undefined,
      initData: '',
      user: null,
      bootstrapOutcome: null,
      bootstrapDiagnostics: null,
    });

    render(<FeedPage />);

    await toggleDayRuntimeDiagnostics();

    expect(await screen.findByTestId('day-runtime-diagnostics-disclosure')).toBeInTheDocument();
    expect(screen.getByTestId('day-runtime-diagnostics-render-path')).toHaveTextContent('empty');
    expect(screen.getByTestId('day-runtime-diagnostics-bootstrap')).toHaveTextContent('unknown');
    expect(screen.getByTestId('day-runtime-diagnostics-mode')).toHaveTextContent('unavailable');
  });

  it('keeps the Day runtime disclosure inert in production even if the toggle event is dispatched', async () => {
    process.env.NODE_ENV = 'production';
    homeFetchMock.mockImplementation(async (url: string) => {
      if (url === '/api/users/me') {
        return new Response(JSON.stringify({ full_name: 'Canonical User', subscription_active_until: null }), { status: 200 });
      }

      if (url === '/api/feed/today') {
        return new Response(JSON.stringify({
          day_brief: {
            version: 'day_brief_canon_v1',
            status: 'complete',
            date: '2026-04-10',
            personalization_level: 'personalized_v2',
            hero: { title: 'Prod day', subtitle: 'Disclosure must stay inert.', day_type: 'balance' },
            domains: {
              energy: { key: 'energy', title: 'Тонус', score_status: 'complete', score: 71, status: 'green', description_status: 'complete', description: 'Есть рабочий ресурс.', why_status: 'complete', why_astro_text: 'Марс держит темп.', evidence_refs: [] },
              money: { key: 'money', title: 'Работа и деньги', score_status: 'complete', score: 64, status: 'yellow', description_status: 'complete', description: 'Смотри на цифры.', why_status: 'complete', why_astro_text: 'Второй дом просит точности.', evidence_refs: [] },
              love: { key: 'love', title: 'Чувства', score_status: 'complete', score: 59, status: 'yellow', description_status: 'complete', description: 'Контакт требует мягкости.', why_status: 'complete', why_astro_text: 'Венера просит бережности.', evidence_refs: [] },
              focus: { key: 'focus', title: 'Фокус', score_status: 'complete', score: 77, status: 'green', description_status: 'complete', description: 'Один главный приоритет.', why_status: 'complete', why_astro_text: 'Меркурий держит одну линию.', evidence_refs: [] },
            },
          },
        }), { status: 200 });
      }

      throw new Error(`Unexpected url ${url}`);
    });

    render(<FeedPage />);

    expect(await screen.findByTestId('today-verdict')).toBeInTheDocument();

    await toggleDayRuntimeDiagnostics();

    expect(screen.queryByTestId('day-runtime-diagnostics-disclosure')).not.toBeInTheDocument();
    expect(screen.queryByTestId('today-render-path')).not.toBeInTheDocument();
  });

  it('exposes a deterministic home-only route gate for the dev runtime badge', () => {
    process.env.NODE_ENV = 'development';
    window.history.replaceState({}, '', '/');

    const RootLayout = loadRootLayout();
    renderRootLayoutDocument(
      <RootLayout>
        <div>home</div>
      </RootLayout>,
    );

    executeRuntimeBadgeRouteGate();

    const badge = document.querySelector('[data-testid="runtime-environment-badge"]');
    expect(badge).toBeInstanceOf(HTMLButtonElement);
    expect(badge).toHaveAttribute('data-runtime-badge-route-gate', 'day-home-only');
    expect(badge).toHaveAttribute('data-runtime-badge-event', 'astro:day-dev-indicator-toggle-request');
    expect(badge).toHaveAttribute('data-route-eligible', 'true');
    expect(badge).toHaveAttribute('aria-disabled', 'false');
    expect(badge).toHaveTextContent('DEV');

    const toggleListener = jest.fn();
    window.addEventListener('astro:day-dev-indicator-toggle-request', toggleListener);
    fireEvent.click(badge as Element);
    expect(toggleListener).toHaveBeenCalledTimes(1);
    window.removeEventListener('astro:day-dev-indicator-toggle-request', toggleListener);
  });

  it('keeps the dev runtime badge inert outside the Day route', () => {
    process.env.NODE_ENV = 'development';
    window.history.replaceState({}, '', '/reports');

    const RootLayout = loadRootLayout();
    renderRootLayoutDocument(
      <RootLayout>
        <div>reports</div>
      </RootLayout>,
    );

    executeRuntimeBadgeRouteGate();

    const badge = document.querySelector('[data-testid="runtime-environment-badge"]');
    expect(badge).toBeInstanceOf(HTMLButtonElement);
    expect(badge).toHaveAttribute('data-route-eligible', 'false');
    expect(badge).toHaveAttribute('aria-disabled', 'true');
    expect(badge).toHaveAttribute('tabindex', '-1');

    const toggleListener = jest.fn();
    window.addEventListener('astro:day-dev-indicator-toggle-request', toggleListener);
    fireEvent.click(badge as Element);
    expect(toggleListener).not.toHaveBeenCalled();
    window.removeEventListener('astro:day-dev-indicator-toggle-request', toggleListener);
  });

  it('keeps the production badge inert and without route-gated disclosure hooks', () => {
    process.env.NODE_ENV = 'production';
    window.history.replaceState({}, '', '/');

    const RootLayout = loadRootLayout();
    renderRootLayoutDocument(
      <RootLayout>
        <div>home</div>
      </RootLayout>,
    );

    const badge = document.querySelector('[data-testid="runtime-environment-badge"]');
    expect(badge).toBeInstanceOf(HTMLDivElement);
    expect(badge).toHaveTextContent('PROD');
    expect(badge).not.toHaveAttribute('data-runtime-badge-route-gate');
    expect(badge).not.toHaveAttribute('data-runtime-badge-event');
    expect(document.getElementById('runtime-badge-route-gate')).toBeNull();
  });
});
