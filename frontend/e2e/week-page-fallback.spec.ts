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

    await expect(page.getByTestId('week-map-surface')).toBeVisible();
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Неделя просит точного темпа: двигайте главное и сразу фиксируйте результат.');
    await expect(page.getByTestId('week-map-surface')).not.toContainText('Europe/Moscow');
    await expect(page.getByTestId('week-primary-cta')).toBeVisible();
    await expect(page.getByTestId('week-day-strip')).toBeVisible();
    await expect(page.getByTestId('week-day-strip-card-1')).toContainText(/^[А-Я]{2},\s\d+\s[а-я]+/);
    await expect(page.getByTestId('week-day-strip').locator('article[data-testid^="week-day-strip-card-"]')).toHaveCount(7);
    await expect(page.getByTestId('week-day-strip-card-1')).not.toContainText(/\bgreen\b/i);
    await expect(page.getByTestId('week-day-strip-card-2')).not.toContainText(/\byellow\b/i);
    await expect(page.getByTestId('week-day-strip-card-3')).not.toContainText(/\bred\b/i);
    await expect(page.getByTestId('week-day-strip')).not.toContainText(/светофор\s+money\s*:\s*green/i);
    await expect(page.getByTestId('week-day-strip')).not.toContainText(/\ball_week\b/i);
    await expect(page.getByTestId('week-day-strip')).not.toContainText(/explanation_astro|transit|natal|aspect/i);
    await expect(page.getByTestId('week-deep-sections')).toBeVisible();
    await expect(page.getByTestId('week-deep-sections')).toContainText('Неделя требует спокойного темпа и аккуратной расстановки приоритетов.');
    await expect(page.getByTestId('week-deep-sections-summary')).toContainText('длинного чтения');
    await expect(page.getByText('Короткая версия раздела')).toBeVisible();
    await expect(page.getByTestId('week-deep-sections')).not.toContainText('{"text"');
    await expect(page.getByTestId('week-fallback-note')).toBeVisible();
    await expect(page.getByTestId('week-fallback-note')).toContainText('сокращённая версия недели');
    await expect(page.getByTestId('week-fallback-note')).not.toContainText(/fallback|weekbrief|legacy|week_map/i);

    expect(logs, `Found console or page errors on /week fallback path: ${logs.join(', ')}`).toHaveLength(0);
    await context.close();
  });

  test('should not leak raw slug-like deep fallback values into week UI', async ({ browser }) => {
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

    await expect(page.getByTestId('week-deep-sections')).toBeVisible();
    await expect(page.getByTestId('week-deep-sections')).toContainText('Раздел 1');
    await expect(page.getByTestId('week-deep-sections')).not.toContainText('week_strategy');
    await expect(page.getByTestId('week-deep-sections')).not.toContainText(/accordion/i);
    await expect(page.getByTestId('report-fallback-card')).toHaveCount(0);

    await context.close();
  });
});
