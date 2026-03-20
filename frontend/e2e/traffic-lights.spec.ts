import { test, expect } from '@playwright/test';

test.describe('Traffic Lights UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = { 
        WebApp: { 
          initData: '123456789', 
          ready: () => {}, 
          expand: () => {}, 
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Traffic', last_name: 'Lights' } }
        } 
      };
    });
  });

  test('should show traffic lights on Daily Feed (Home)', async ({ page }) => {
    await page.goto('/');
    // Check for explicit labels
    await expect(page.getByText('Тонус')).toBeVisible();
    await expect(page.getByText('Деньги')).toBeVisible();
    await expect(page.getByText('Чувства')).toBeVisible();
    // Check for green/yellow/red classes or elements
    const grid = page.locator('.grid.grid-cols-3');
    await expect(grid).toBeVisible();
  });

  test('should show traffic lights in Week Report', async ({ page }) => {
    // Generate week forecast (stub mode returns traffic_lights block)
    const response = await page.request.post('/api/reports/create', {
        headers: { 'X-Telegram-Auth': '123456789' },
        data: {
            report_type: 'week_forecast',
            client_name: 'Test',
            birth_date: '1990-01-01T12:00:00',
            birth_location: 'Moscow',
            birth_lat: 55.75,
            birth_lon: 37.61,
        }
    });
    const data = await response.json();
    const reportId = data.report_id;

    await expect.poll(async () => {
        const res = await page.request.get(`/api/reports/${reportId}`, { headers: { 'X-Telegram-Auth': '123456789' } });
        return (await res.json()).report.status;
    }).toBe('completed');

    await page.goto(`/read/${reportId}`);
    
    // The ReportRenderer should render TrafficLights component
    await expect(page.getByText('Тонус')).toBeVisible();
    await expect(page.getByText('Деньги')).toBeVisible();
    await expect(page.getByText('Чувства')).toBeVisible();
  });

  test('should show traffic lights in Month Report', async ({ page }) => {
    const response = await page.request.post('/api/reports/create', {
        headers: { 'X-Telegram-Auth': '123456789' },
        data: {
            report_type: 'month_forecast',
            client_name: 'Test',
            birth_date: '1990-01-01T12:00:00',
            birth_location: 'Moscow',
            birth_lat: 55.75,
            birth_lon: 37.61,
        }
    });
    const data = await response.json();
    const reportId = data.report_id;

    await expect.poll(async () => {
        const res = await page.request.get(`/api/reports/${reportId}`, { headers: { 'X-Telegram-Auth': '123456789' } });
        return (await res.json()).report.status;
    }).toBe('completed');

    await page.goto(`/read/${reportId}`);
    await expect(page.getByText('Тонус')).toBeVisible();
    await expect(page.getByText('Деньги')).toBeVisible();
    await expect(page.getByText('Чувства')).toBeVisible();
  });
});
