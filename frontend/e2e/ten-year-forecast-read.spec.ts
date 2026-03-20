import { test, expect } from '@playwright/test';

test.describe('Ten Year Forecast Read Path', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = {
        WebApp: {
          initData: '123456789',
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Ten', last_name: 'Year' } },
        },
      };
    });
  });

  test('should render ten_year_forecast sections on /read/[id] without runtime errors', async ({ page }) => {
    const reportId = 'ten-year-forecast-read-spec';
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
            report_type: 'ten_year_forecast',
            status: 'completed',
            client_name: 'Forecast Reader',
          },
          chunks: [
            {
              id: 'decade-overview',
              section: 'decade_overview',
              content: JSON.stringify([
                { type: 'paragraph', text: 'Главный тренд десятилетия строится вокруг медленной перестройки карьерного вектора.' },
                { type: 'callout', title: 'Фокус', text: 'Крупный разворот ожидается в начале периода и закрепляется к середине цикла.' },
              ]),
            },
            {
              id: 'decade-timeline',
              section: 'decade_timeline',
              content: JSON.stringify({
                blocks: [
                  { type: 'header', level: 4, text: '2028' },
                  { type: 'list', items: ['Смена долгосрочного приоритета', 'Рост ответственности и статуса'] },
                ],
              }),
            },
            {
              id: 'decade-storylines',
              section: 'decade_storylines',
              content: JSON.stringify([
                { type: 'paragraph', text: 'Линия отношений требует медленного созревания решений и отказа от случайных компромиссов.' },
              ]),
            },
          ],
        },
      });
    });

    await page.goto(`/read/${reportId}?mock=1`);

    await expect(page.getByRole('heading', { name: 'Прогноз на 10 лет' })).toHaveCount(2);
    await expect(page.getByTestId('read-overview-panel')).toBeVisible();
    await expect(page.getByText('Forecast Reader', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /Обзор 10 лет/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Хронология \(10 лет\)/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Сюжетные линии/ })).toBeVisible();
    await expect(page.locator('body')).toContainText('Главный тренд десятилетия строится вокруг медленной перестройки карьерного вектора.');
    await expect(page.locator('body')).toContainText('Смена долгосрочного приоритета');

    expect(logs, `Found console or page errors on ten_year_forecast read path: ${logs.join(', ')}`).toHaveLength(0);
  });
});
