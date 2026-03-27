import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_HISTORY_CTA
// ROLE: Verify that history page CTA buttons lead to correct creation flows.
// VERIFIES: P0-REPORT-HISTORY-CTA-01
// ############################################################################

test.describe('History CTA Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      (window as Window & typeof globalThis & { __analyticsEvents?: Array<{ event: string; payload: Record<string, unknown> }> }).__analyticsEvents = [];
      const originalFetch = window.fetch.bind(window);
      window.fetch = async (input, init) => {
        const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
        if (url.includes('/api/analytics')) {
          const bodyText = typeof init?.body === 'string' ? init.body : '';
          try {
            const parsed = JSON.parse(bodyText);
            const batch = Array.isArray(parsed?.events) ? parsed.events : parsed ? [parsed] : [];
            for (const item of batch) {
              const payload = typeof item?.properties === 'object' && item.properties
                ? item.properties
                : typeof item?.payload === 'object' && item.payload
                  ? item.payload
                  : {};
              (window as Window & typeof globalThis & { __analyticsEvents: Array<{ event: string; payload: Record<string, unknown> }> }).__analyticsEvents.push({
                event: typeof item?.event === 'string' ? item.event : typeof item?.event_name === 'string' ? item.event_name : 'unknown',
                payload: typeof payload?.payload === 'object' && payload.payload ? payload.payload as Record<string, unknown> : payload as Record<string, unknown>,
              });
            }
          } catch {}
        }
        return originalFetch(input, init);
      };
    });

    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = {
        WebApp: {
          initData: '123456789',
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Debug', last_name: 'User' } }
        }
      };
    });

    await page.route('**/api/reports/my*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'natal-report-id',
            report_type: 'natal_master',
            status: 'completed',
            created_at: '2026-03-18T10:30:00.000Z',
            client_name: 'Debug User'
          },
          {
            id: 'forecast-report-id',
            report_type: 'year_forecast',
            status: 'completed',
            created_at: '2026-03-17T09:15:00.000Z',
            client_name: 'Debug User'
          }
        ])
      });
    });
  });

  test('should navigate to natal creation from history filter', async ({ page }) => {
    await page.goto('/reports/history');

    await expect(page.getByTestId('reports-history-page')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('reports-history-page')).toHaveAttribute('data-block', 'SHELL_RENDER');
    await page.getByRole('button', { name: 'Натал' }).click();

    const createBtn = page.getByTestId('history-filter-cta');
    await expect(createBtn).toContainText('Создать новый Натал');
    await createBtn.click();

    const analytics = await page.evaluate(() => (window as Window & typeof globalThis & { __analyticsEvents?: Array<{ event: string; payload: Record<string, unknown> }> }).__analyticsEvents ?? []);
    const historyView = analytics.find((item) => item.event === 'catalog.history_view');
    const historyFilter = analytics.find((item) => item.event === 'catalog.history_filter');
    const historyCta = analytics.find((item) => item.event === 'catalog.history_cta');

    expect(historyView?.event).toBe('catalog.history_view');
    expect(historyFilter?.event).toBe('catalog.history_filter');
    expect(historyCta?.event).toBe('catalog.history_cta');
    await expect(page.getByTestId('reports-history-page')).toHaveAttribute('data-block', 'SHELL_RENDER');
    await expect(page.getByTestId('history-filter-cta')).toHaveAttribute('data-block', 'CTA_TRACKING');

    await expect(page).toHaveURL(/\/create\?type=natal_master/);
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('text=Натал (базовый)')).toBeVisible();
  });
});
