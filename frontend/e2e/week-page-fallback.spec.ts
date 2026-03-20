import { expect, test } from "@playwright/test";

test.describe("Week Page Fallback Parsing", () => {
  test("should render safe text fallback when week chunk content is not JSON blocks", async ({ browser }) => {
    const reportId = 'week-fallback-report';
    const logs: string[] = [];

    const context = await browser.newContext();
    await context.addInitScript(() => {
      window.sessionStorage.setItem("mock_telegram_user", "1");
      (window as any).Telegram = {
        WebApp: {
          initData: "123456789",
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: "Week", last_name: "Fallback" } },
        },
      };
    });

    const page = await context.newPage();

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });

    page.on('pageerror', (err) => {
      logs.push(err.message);
    });

    await page.route('**/api/reports/**', async (route) => {
      const url = route.request().url();

      if (url.includes('/api/reports/my?')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          json: [
            {
              id: reportId,
              report_type: 'week_forecast',
              status: 'completed',
            },
          ],
        });
        return;
      }

      if (!url.includes(reportId)) {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        json: {
          report: {
            id: reportId,
            report_type: 'week_forecast',
            status: 'completed',
          },
          chunks: [
            {
              id: 'week-strategy',
              section: 'week_strategy',
              content: 'Неделя требует спокойного темпа и аккуратной расстановки приоритетов.',
            },
          ],
        },
      });
    });

    await page.goto('/week');

    await expect(page.locator('h1').filter({ hasText: 'Навигатор недели' })).toBeVisible();
    await expect(page.getByTestId('week-overview-panel')).toBeVisible();
    await expect(page.getByTestId('report-fallback-card')).toBeVisible();
    await expect(
      page.getByTestId('report-fallback-card').getByText('Неделя требует спокойного темпа и аккуратной расстановки приоритетов.')
    ).toBeVisible();

    expect(logs, `Found console or page errors on /week fallback path: ${logs.join(', ')}`).toHaveLength(0);
    await context.close();
  });
});
