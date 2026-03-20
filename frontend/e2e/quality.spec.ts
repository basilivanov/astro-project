import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_QUALITY
// ROLE: Verify absence of runtime errors and console errors on critical pages.
// VERIFIES: P0-DEV-ADMIN-AUDIT-01
// ############################################################################

test.describe('Quality & Stability Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      // Mock Telegram WebApp
      (window as any).Telegram = { 
        WebApp: { 
          initData: '123456789', 
          ready: () => {}, 
          expand: () => {}, 
          close: () => {},
          headerColor: '#ffffff',
          backgroundColor: '#ffffff',
          initDataUnsafe: { user: { id: 123456789, first_name: 'Debug', last_name: 'User' } }
        } 
      };
    });
  });

  test('should have no console errors on admin audit page', async ({ page }) => {
    const logs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });

    page.on('pageerror', err => {
        logs.push(err.message);
    });

    await page.goto('/admin/audit');
    
    // Wait for content to load to ensure JS execution
    await expect(page.locator('h1')).toContainText('Аудит');
    
    // Check if there are any recorded errors
    expect(logs, `Found console errors on /admin/audit: ${logs.join(', ')}`).toHaveLength(0);
  });

  test('should render report sections (report render)', async ({ page, request }) => {
    const response = await request.post('/api/reports/create', {
      headers: { 'X-Telegram-Auth': '123456789' },
      data: { report_type: 'natal_master' },
    });
    expect(response.ok()).toBeTruthy();
    const payload = await response.json();
    const reportId = payload.report_id;

    let isReportReady = false;
    for (let attempt = 0; attempt < 12; attempt += 1) {
      const reportResponse = await request.get(`/api/reports/${reportId}`, {
        headers: { 'X-Telegram-Auth': '123456789' },
      });

      if (reportResponse.ok()) {
        const reportPayload = await reportResponse.json();
        if (
          reportPayload?.report?.status === 'completed' &&
          Array.isArray(reportPayload?.chunks) &&
          reportPayload.chunks.length > 0
        ) {
          isReportReady = true;
          break;
        }
      }

      await page.waitForTimeout(1500);
    }

    expect(isReportReady).toBeTruthy();

    const readUrl = `/read/${reportId}?mock=1`;
    let renderError: unknown = null;

    // Cold direct opens can occasionally stall on the initial app shell in dev mode.
    // A bounded reload keeps the assertion focused on real rendering instead of startup jitter.
    for (let attempt = 0; attempt < 3; attempt += 1) {
      await page.goto(readUrl);

      try {
        await expect(page.locator('h2')).toContainText(/Наталь/i, { timeout: 6000 });
        await expect(page.locator('.report-content-blocks').first()).toBeVisible({ timeout: 6000 });
        renderError = null;
        break;
      } catch (error) {
        renderError = error;
      }
    }

    if (renderError) {
      throw renderError;
    }
  });

  test('should render chart SVG (chart render)', async ({ page, request }) => {
    const response = await request.post('/api/reports/create', {
      headers: { 'X-Telegram-Auth': '123456789' },
      data: { report_type: 'natal_master' },
    });
    expect(response.ok()).toBeTruthy();
    const payload = await response.json();
    const reportId = payload.report_id;

    let isReportReady = false;
    for (let attempt = 0; attempt < 12; attempt += 1) {
      const reportResponse = await request.get(`/api/reports/${reportId}`, {
        headers: { 'X-Telegram-Auth': '123456789' },
      });

      if (reportResponse.ok()) {
        const reportPayload = await reportResponse.json();
        if (
          reportPayload?.report?.status === 'completed' &&
          typeof reportPayload?.chart_svg === 'string' &&
          reportPayload.chart_svg.includes('<svg')
        ) {
          isReportReady = true;
          break;
        }
      }

      await page.waitForTimeout(1500);
    }

    expect(isReportReady).toBeTruthy();

    const readUrl = `/read/${reportId}?mock=1`;
    let renderError: unknown = null;
    for (let attempt = 0; attempt < 3; attempt += 1) {
      await page.goto(readUrl);

      try {
        const svg = page.locator('.chart-svg-container svg');
        await expect(svg).toBeVisible({ timeout: 6000 });
        renderError = null;
        break;
      } catch (error) {
        renderError = error;
      }
    }

    if (renderError) {
      throw renderError;
    }

    const svg = page.locator('.chart-svg-container svg');
    
    // Check it has dimensions
    const box = await svg.boundingBox();
    expect(box?.width).toBeGreaterThan(100);
    expect(box?.height).toBeGreaterThan(100);
    
    // Check for planets
    await expect(svg.locator('.planet-glyph').first()).toBeVisible();
  });

  test('should ignore invalid report blocks without crashing', async ({ page }) => {
    const logs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });

    page.on('pageerror', err => {
      logs.push(err.message);
    });

    const reportId = 'invalid-blocks-report';
    await page.route('**/api/reports/*', async route => {
      if (!route.request().url().includes(reportId)) {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          report: {
            id: reportId,
            report_type: 'natal_master',
            status: 'completed',
            client_name: 'Quality Client',
          },
          chunks: [
            {
              id: 'chunk-1',
              section: 'executive_summary',
              content: JSON.stringify([
                { type: 'paragraph', text: 'Валидный блок должен отрисоваться.' },
                { type: 'unknown', text: 'Этот блок надо пропустить.' },
                null,
                { type: 'callout' },
              ]),
            },
            {
              id: 'chunk-2',
              section: 'final_synthesis',
              content: 'not-json',
            },
            {
              id: 'chunk-3',
              section: 'money_realization',
              content: JSON.stringify([
                { type: 'list', items: ['Один рабочий пункт'] },
              ]),
            },
          ],
        }),
      });
    });

    await page.goto(`/read/${reportId}`);
    await page.waitForTimeout(2000);
    await expect(page.getByText('Quality Client')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('Валидный блок должен отрисоваться.')).toBeVisible();
    await expect(page.getByText('Один рабочий пункт')).toBeVisible();
    await expect(page.getByTestId('report-empty-state')).toHaveCount(0);
    expect(logs, `Found runtime errors on invalid block render: ${logs.join(', ')}`).toHaveLength(0);
  });

  test('should keep malformed report section visible via fallback card', async ({ page }) => {
    const reportId = 'fallback-blocks-report';
    await page.route('**/api/reports/*', async route => {
      if (!route.request().url().includes(reportId)) {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          report: {
            id: reportId,
            report_type: 'natal_master',
            status: 'completed',
            client_name: 'Empty Client',
          },
          chunks: [
            {
              id: 'chunk-1',
              section: 'executive_summary',
              content: 'Секция пришла как сырой текст без JSON-структуры, но пользователь все равно должен увидеть этот фрагмент в читаемом виде.',
            },
            {
              id: 'chunk-2',
              section: 'final_synthesis',
              content: JSON.stringify({ text: 'Даже одиночный текстовый объект должен попасть в fallback или безопасный paragraph.' }),
            },
          ],
        }),
      });
    });

    await page.goto(`/read/${reportId}`);
    await expect(page.getByTestId('report-fallback-card')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('Секция пришла как сырой текст без JSON-структуры')).toBeVisible();
    await expect(page.getByText('Даже одиночный текстовый объект')).toBeVisible();
    await expect(page.getByTestId('report-empty-state')).toHaveCount(0);
  });

  test('should show empty state for completed report without usable content', async ({ page }) => {
    const reportId = 'empty-blocks-report';
    await page.route('**/api/reports/*', async route => {
      if (!route.request().url().includes(reportId)) {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          report: {
            id: reportId,
            report_type: 'natal_master',
            status: 'completed',
            client_name: 'Empty Client',
          },
          chunks: [
            {
              id: 'chunk-1',
              section: 'executive_summary',
              content: '[]',
            },
            {
              id: 'chunk-2',
              section: 'final_synthesis',
              content: '{}',
            },
            {
              id: 'chunk-3',
              section: 'money_realization',
              content: '',
            },
          ],
        }),
      });
    });

    await page.goto(`/read/${reportId}`);
    await expect(page.getByTestId('report-empty-state')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('В отчете пока нет доступных блоков')).toBeVisible();
  });
});
