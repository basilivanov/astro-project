import { test, expect } from '@playwright/test';

test.describe('Year Forecast Read Path', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = {
        WebApp: {
          initData: '123456789',
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Year', last_name: 'Forecast' } },
        },
      };
    });
  });

  test('should render year_forecast sections on /read/[id] without runtime errors', async ({ page }) => {
    const reportId = 'year-forecast-read-spec';
    const logs: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });

    page.on('pageerror', (err) => {
      logs.push(err.message);
    });

    await page.route('**/api/reports/**', async (route) => {
      if (!route.request().url().includes(reportId)) {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        json: {
          report: {
            id: reportId,
            report_type: 'year_forecast',
            status: 'completed',
            client_name: 'Forecast Reader',
          },
          chunks: [
            {
              id: 'solar-theme',
              section: 'solar_theme',
              content: JSON.stringify([
                { type: 'paragraph', text: 'Главный вектор года строится вокруг обновления личных приоритетов.' },
                { type: 'callout', title: 'Фокус', text: 'Весной важно закрепить новую стратегию действий.' },
              ]),
            },
            {
              id: 'solar-strategy',
              section: 'solar_strategy',
              content: JSON.stringify({
                blocks: [
                  { type: 'list', items: ['Собрать цели по кварталам', 'Оставить запас времени на перестройку графика'] },
                ],
              }),
            },
          ],
        },
      });
    });

    await page.goto(`/read/${reportId}?mock=1`);

    await expect(page.getByRole('heading', { name: 'Альманах 2026' })).toHaveCount(2);
    await expect(page.getByTestId('read-overview-panel')).toBeVisible();
    await expect(page.getByText('Forecast Reader', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /Главная тема года/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Стратегия года/ })).toBeVisible();
    await expect(page.locator('body')).toContainText('Главный вектор года строится вокруг обновления личных приоритетов.');
    await expect(page.locator('body')).toContainText('Собрать цели по кварталам');

    expect(logs, `Found console or page errors on year_forecast read path: ${logs.join(', ')}`).toHaveLength(0);
  });
});
