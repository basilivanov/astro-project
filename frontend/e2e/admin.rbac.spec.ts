import { test, expect, type Page, type Route } from '@playwright/test';
import { bootstrapMockTelegram, expectNoCrash } from './utils';

const adminUsers = [
  {
    id: 'u-1',
    full_name: 'Admin User',
    username: 'admin_user',
    subscription_active_until: '2026-04-10T00:00:00Z',
    balance: 1200,
    horary_credits: 2,
  },
];

const adminReports = [
  {
    id: 'r-1',
    report_type: 'natal_master',
    status: 'completed',
    paid: true,
    created_at: '2026-03-21T10:00:00Z',
    updated_at: '2026-03-21T11:00:00Z',
    client_id: 'c-1',
    client_name: 'Alice Example',
    chunk_count: 2,
  },
];

const adminReportDetail = {
  report: adminReports[0],
  chunks: [
    {
      id: 'chunk-1',
      section: 'executive_summary',
      title: 'Краткое резюме',
      status: 'completed',
      order_index: 0,
      content: JSON.stringify([{ type: 'paragraph', text: 'Summary text' }]),
      created_at: '2026-03-21T10:05:00Z',
    },
  ],
  runs: [
    {
      id: 'run-1',
      status: 'completed',
      started_at: '2026-03-21T10:01:00Z',
      finished_at: '2026-03-21T10:10:00Z',
      prompt_tokens: 100,
      completion_tokens: 200,
      total_tokens: 300,
      estimated_cost: 0.12,
      created_at: '2026-03-21T10:00:30Z',
    },
  ],
  chart_svg: null,
};

const adminDashboardStats = {
  clients: 12,
  reports_total: 40,
  reports_in_progress: 3,
  reports_completed: 31,
  reports_failed: 6,
  reports_by_type: { natal_chart: 10 },
  reports_daily: [{ date: '2026-03-21', count: 4 }],
  tasks_open: 2,
  tasks_total: 9,
  analytics_funnel: {
    landing_view: 100,
    login_completed: 80,
    report_generation_started: 20,
    checkout_started: 10,
  },
  window_days: 7,
  feedback_avg: 4.8,
  feedback_count: 5,
  entitlements: {
    total_balance_rub: 5000,
    active_subscriptions: 9,
    outstanding_credits: 3,
  },
};

const adminFeedback = [
  {
    id: 'fb-1',
    report_id: 'r-1',
    rating: 5,
    comment: 'Great',
    created_at: '2026-03-21T12:00:00Z',
    report_type: 'natal_master',
    client_name: 'Alice Example',
  },
];

type TelemetryEvent = {
  event_name?: string;
  path?: string;
  role?: string;
  target_path?: string;
  task_href?: string;
  block?: string;
  semantic_block?: string;
  flow_id?: string;
  surface?: string;
  [key: string]: unknown;
};

async function fulfillJson(route: Route, status: number, body: unknown) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

async function setupAdminRbacHarness(page: Page, role: 'admin' | 'analyst') {
  const telemetryEvents: TelemetryEvent[] = [];
  const deniedResponse = {
    detail: 'forbidden',
    role,
    allowed_roles: ['admin'],
    task_href: '/Task.md',
  };

  await bootstrapMockTelegram(page);

  await page.addInitScript(({ activeRole }) => {
    (window as Window & typeof globalThis & { __TEST_ADMIN_ROLE__?: string }).__TEST_ADMIN_ROLE__ = activeRole;
  }, { activeRole: role });

  await page.route('**/api/analytics/**', async (route) => {
    const request = route.request();
    const bodyText = request.postData() ?? '{}';
    let body: Record<string, unknown> = {};
    try {
      body = JSON.parse(bodyText);
    } catch {
      body = {};
    }

    if (Array.isArray(body.events)) {
      telemetryEvents.push(...(body.events as TelemetryEvent[]));
    } else {
      telemetryEvents.push(body as TelemetryEvent);
    }

    await fulfillJson(route, 200, { ok: true });
  });

  await page.route('**/api/admin/users**', async (route) => {
    if (role === 'analyst') {
      await fulfillJson(route, 403, deniedResponse);
      return;
    }
    await fulfillJson(route, 200, adminUsers);
  });

  await page.route('**/api/admin/stats**', async (route) => {
    await fulfillJson(route, 200, adminDashboardStats);
  });

  await page.route('**/api/admin/feedback**', async (route) => {
    await fulfillJson(route, 200, adminFeedback);
  });

  await page.route('**/api/admin/reports/*/generate-section', async (route) => {
    if (role === 'analyst') {
      await fulfillJson(route, 403, deniedResponse);
      return;
    }
    await fulfillJson(route, 200, { ok: true });
  });

  await page.route('**/api/admin/reports/*/regenerate', async (route) => {
    if (role === 'analyst') {
      await fulfillJson(route, 403, deniedResponse);
      return;
    }
    await fulfillJson(route, 200, { ok: true });
  });

  await page.route('**/api/admin/reports/*', async (route) => {
    if (role === 'analyst') {
      await fulfillJson(route, 403, deniedResponse);
      return;
    }
    await fulfillJson(route, 200, adminReportDetail);
  });

  await page.route('**/api/admin/reports**', async (route) => {
    await fulfillJson(route, 200, adminReports);
  });

  return { telemetryEvents, deniedResponse };
}

test.describe('Admin RBAC telemetry', () => {
  test('admin can access users list without Task.md blocker link', async ({ page }) => {
    const { telemetryEvents } = await setupAdminRbacHarness(page, 'admin');

    await page.goto('/admin/users');
    await expectNoCrash(page);
    await expect(page.getByRole('heading', { name: 'Пользователи' })).toBeVisible();
    await expect(page.getByText('Admin User')).toBeVisible();
    await expect(page.getByRole('link', { name: /Task\.md/i })).toHaveCount(0);

    await expect.poll(() => telemetryEvents.length).toBeGreaterThan(0);
    expect(
      telemetryEvents.some(
        (event) => event.event_name === 'admin.users_view' && event.target_path === '/admin/users' && event.flow_id === 'FLOW-ADMIN-OPS',
      ),
    ).toBeTruthy();
    expect(telemetryEvents.some((event) => event.task_href === '/Task.md')).toBeFalsy();
  });

  test('admin sees dashboard and report actions without denial telemetry', async ({ page }) => {
    const { telemetryEvents } = await setupAdminRbacHarness(page, 'admin');

    await page.goto('/admin/dashboard');
    await expectNoCrash(page);
    await expect(page.getByTestId('admin-dashboard-page')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Дашборд/i })).toBeVisible();
    await expect(page.getByTestId('admin-dashboard-page').locator('text=В работе')).toBeVisible();

    await page.goto('/admin/reports');
    await expectNoCrash(page);
    await expect(page.getByTestId('admin-reports-page')).toBeVisible();
    await expect(page.getByTestId('admin-reports-queue-mobile')).toBeAttached();

    await page.goto('/admin/reports/r-1');
    await expectNoCrash(page);
    await expect(page.getByText(/Запуск, контроль и выгрузка natal_master/i)).toBeVisible();
    await expect(page.getByTestId('admin-generate-all')).toBeVisible();
    await expect(page.getByTestId('admin-download-markdown')).toBeVisible();

    expect(telemetryEvents.filter((event) => event.event_name === 'admin.rbac_denied')).toHaveLength(0);
  });

  test('analyst sees RBAC denial, Task.md link and denial telemetry on users path', async ({ page }) => {
    const { telemetryEvents, deniedResponse } = await setupAdminRbacHarness(page, 'analyst');

    await page.goto('/admin/users');
    await expectNoCrash(page);
    await expect(page.getByRole('heading', { name: 'Пользователи' })).toBeVisible();
    await expect(page.getByTestId('admin-users-rbac-denied')).toBeVisible();

    const denialLink = page.getByRole('link', { name: /Task\.md/i });
    await expect(denialLink).toBeVisible();
    await expect(denialLink).toHaveAttribute('href', deniedResponse.task_href);

    await expect.poll(() => telemetryEvents.length).toBeGreaterThan(0);
    expect(
      telemetryEvents.some(
        (event) =>
          event.event_name === 'admin.rbac_denied' &&
          event.role === 'analyst' &&
          event.target_path === '/admin/users' &&
          event.task_href === '/Task.md' &&
          event.surface === 'admin_users' &&
          event.block === 'RBAC_DENIED' &&
          event.semantic_block === 'RBAC_DENIED' &&
          event.flow_id === 'FLOW-ADMIN-OPS',
      ),
    ).toBeTruthy();
  });

  test('analyst denied paths keep dashboard readable and block report detail actions', async ({ page }) => {
    const { telemetryEvents } = await setupAdminRbacHarness(page, 'analyst');

    await page.goto('/admin/dashboard');
    await expectNoCrash(page);
    await expect(page.getByTestId('admin-dashboard-page')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Дашборд/i })).toBeVisible();
    await expect(page.getByTestId('admin-dashboard-page').locator('text=В работе')).toBeVisible();

    await page.goto('/admin/reports');
    await expectNoCrash(page);
    await expect(page.getByTestId('admin-reports-page')).toBeVisible();
    await expect(page.getByTestId('admin-reports-queue-mobile')).toBeAttached();

    await page.goto('/admin/reports/r-1');
    await expectNoCrash(page);
    await expect(page.getByTestId('admin-report-detail-denied')).toBeVisible();
    const denialLink = page.getByRole('link', { name: /Task\.md/i });
    await expect(denialLink).toBeVisible();
    await expect(denialLink).toHaveAttribute('href', '/Task.md');

    await expect.poll(() => telemetryEvents.length).toBeGreaterThan(0);
    expect(
      telemetryEvents.some(
        (event) =>
          event.event_name === 'admin.report_detail_rbac_denied' &&
          event.role === 'analyst' &&
          event.target_path === '/admin/reports/r-1' &&
          event.task_href === '/Task.md' &&
          event.block === 'REPORT_DETAIL_RBAC_DENIED' &&
          event.semantic_block === 'REPORT_DETAIL_RBAC_DENIED' &&
          event.flow_id === 'FLOW-ADMIN-OPS',
      ),
    ).toBeTruthy();
  });
});
