import { test, expect } from '@playwright/test';

const exportMarkdownRoute = '**/api/admin/reports/*/export?format=md';
const reportsListRoute = '**/api/admin/reports?*';
const reportDetailRoute = '**/api/admin/reports/*?include_content=1';

const mockReportId = '11111111-1111-1111-1111-111111111111';

const queueResponse = [
    {
      id: mockReportId,
      report_type: 'natal_master',
      client_name: 'E2E Test Client',
      status: 'done',
      created_at: '2026-03-20T10:00:00Z',
      updated_at: '2026-03-20T10:05:00Z',
    },
];

const detailResponse = {
  report: {
    id: mockReportId,
    report_type: 'natal_master',
    client_name: 'E2E Test Client',
    status: 'done',
    created_at: '2026-03-20T10:00:00Z',
  },
  chunks: [
    {
      id: 'chunk-1',
      report_id: mockReportId,
      section: 'personality',
      title: 'Личность',
      status: 'done',
      content: 'Mock content',
      created_at: '2026-03-20T10:01:00Z',
      updated_at: '2026-03-20T10:02:00Z',
    },
  ],
  runs: [],
  chart_svg: null,
};

async function mockNatalMasterRoutes(page: Parameters<typeof test.beforeEach>[0]['page']) {
  await page.route(reportsListRoute, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(queueResponse) });
  });

  await page.route(reportDetailRoute, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(detailResponse) });
  });
}

test.describe('Админка natal_master', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = {
        WebApp: {
          initData: '123456789',
          ready: () => {},
          expand: () => {},
          close: () => {},
        },
      };
    });

    await mockNatalMasterRoutes(page);
  });

  test('happy-path: detail-route открывается и download-кнопки доступны', async ({ page }) => {
    await page.goto('/admin/reports');
    await expect(page.locator('h1')).toContainText('Отчеты');

    const firstVisibleCard = page.locator('[data-testid="admin-report-link"]:visible').first();
    await expect(firstVisibleCard).toBeVisible();
    await firstVisibleCard.click();

    await expect(page.locator('h1')).toContainText('Запуск, контроль и выгрузка natal_master');
    await expect(page.getByTestId('admin-generate-all')).toBeVisible();
    await expect(page.getByTestId('admin-download-markdown')).toBeVisible();
    await expect(page.getByTestId('admin-download-pdf')).toBeVisible();
  });

  test('error-path: toast появляется при mock-ошибке export', async ({ page }) => {
    await page.route(exportMarkdownRoute, async (route) => {
      await route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'export failed' }) });
    });

    await page.goto('/admin/reports');
    const firstVisibleCard = page.locator('[data-testid="admin-report-link"]:visible').first();
    await expect(firstVisibleCard).toBeVisible();
    await firstVisibleCard.click();

    await expect(page.getByTestId('admin-download-markdown')).toBeEnabled();
    await page.getByTestId('admin-download-markdown').click();
    await expect(page.getByTestId('admin-toast')).toContainText('Не удалось скачать Markdown.');
  });
});
