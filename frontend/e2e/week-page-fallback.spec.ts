import { expect, test, type Page, type TestInfo } from "@playwright/test";

async function captureVisualEvidence(page: Page, testInfo: TestInfo, filename: string) {
  const screenshotPath = testInfo.outputPath(filename);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach(filename, { path: screenshotPath, contentType: "image/png" });
}

test.describe("Week Page Fallback Parsing", () => {
  test("should stay fail-closed when only legacy week chunks are available", async ({ browser }, testInfo) => {
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
        const text = msg.text();
        if (text.includes('data-runtime-badge-event')) {
          return;
        }
        logs.push(text);
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

    await expect(page.getByTestId('week-page')).toBeVisible();
    await expect(page.getByText('Персональной недели пока нет')).toBeVisible();
    await expect(page.getByText('Для этого Telegram-профиля пока нет сохранённой персональной недели. Чтобы увидеть её целиком, соберите новый недельный разбор.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Собрать персональную неделю' })).toHaveAttribute('href', '/create?type=week_forecast');
    await expect(page.getByTestId('week-map-surface')).toHaveCount(0);
    await expect(page.getByTestId('week-primary-cta')).toHaveCount(0);
    await expect(page.getByTestId('week-day-strip')).toHaveCount(0);
    await expect(page.getByTestId('week-deep-sections')).toHaveCount(0);
    await expect(page.getByTestId('report-fallback-card')).toHaveCount(0);
    await expect(page.locator('body')).not.toContainText(/legacy|fallback|week_map|weekbrief|headline|markdown|weekly report|compatibility/i);
    await captureVisualEvidence(page, testInfo, 'week-fail-closed-empty-state.png');

    expect(logs, `Found console or page errors on /week fallback path: ${logs.join(', ')}`).toHaveLength(0);
    await context.close();
  });

  test('should keep legacy raw slug fallback data out of the canonical week route', async ({ browser }) => {
    const reportId = 'week-raw-slug-report';

    const context = await browser.newContext();
    await context.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = {
        WebApp: {
          initData: '123456789',
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Week', last_name: 'Fallback' } },
        },
      };
    });

    const page = await context.newPage();

    await page.route('**/api/reports/**', async (route) => {
      const url = route.request().url();

      if (url.includes('/api/reports/my?')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          json: [{ id: reportId, report_type: 'week_forecast', status: 'completed' }],
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
          report: { id: reportId, report_type: 'week_forecast', status: 'completed' },
          chunks: [
            {
              id: 'week_strategy',
              section: 'week_strategy',
              title: 'week_strategy',
              content: 'week_strategy',
            },
          ],
        },
      });
    });

    await page.goto('/week');

    await expect(page.getByText('Персональной недели пока нет')).toBeVisible();
    await expect(page.getByText('Для этого Telegram-профиля пока нет сохранённой персональной недели. Чтобы увидеть её целиком, соберите новый недельный разбор.')).toBeVisible();
    await expect(page.getByTestId('week-map-surface')).toHaveCount(0);
    await expect(page.locator('body')).not.toContainText('week_strategy');
    await expect(page.locator('body')).not.toContainText(/accordion/i);
    await expect(page.getByTestId('report-fallback-card')).toHaveCount(0);

    await context.close();
  });
});
