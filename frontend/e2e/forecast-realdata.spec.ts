import { test, expect } from '@playwright/test';

test.describe('Forecast Real Data', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = { 
        WebApp: { 
          initData: '123456789', 
          ready: () => {}, 
          expand: () => {}, 
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Forecast', last_name: 'Tester' } }
        } 
      };
    });
  });

  test('should generate week forecast with real data markers', async ({ page }) => {
    // 1. Trigger generation via API (faster than UI click)
    await page.goto('/');
    const response = await page.request.post('/api/reports/create', {
        headers: { 'X-Telegram-Auth': '123456789' },
        data: {
            report_type: 'week_forecast',
            client_name: 'Test User',
            birth_date: '1990-01-01T12:00:00',
            birth_location: 'Moscow',
            birth_lat: 55.75,
            birth_lon: 37.61,
            // Force OpenRouter/Stub based on env, but we expect structure
        }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    const reportId = data.report_id;

    // 2. Poll for completion
    await expect.poll(async () => {
        const res = await page.request.get(`/api/reports/${reportId}`, {
            headers: { 'X-Telegram-Auth': '123456789' }
        });
        const json = await res.json();
        return json.report.status;
    }, {
        timeout: 60000,
        intervals: [2000]
    }).toBe('completed');

    // 3. Verify content
    await page.goto(`/read/${reportId}`);
    
    // Check for traffic light emojis or text
    const content = page.locator('.report-content-blocks');
    await expect(content).toContainText(/🔴|🟡|🟢/); // Traffic light
    await expect(content).toContainText(/Луна:/); // Moon info
    await expect(content).toContainText(/Итоговое резюме/); // Footer
  });

  test('should generate month forecast with real data markers', async ({ page }) => {
    // 1. Trigger generation
    const response = await page.request.post('/api/reports/create', {
        headers: { 'X-Telegram-Auth': '123456789' },
        data: {
            report_type: 'month_forecast',
            client_name: 'Test User',
            birth_date: '1990-01-01T12:00:00',
            birth_location: 'Moscow',
            birth_lat: 55.75,
            birth_lon: 37.61,
        }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    const reportId = data.report_id;

    // 2. Poll
    await expect.poll(async () => {
        const res = await page.request.get(`/api/reports/${reportId}`, {
            headers: { 'X-Telegram-Auth': '123456789' }
        });
        const json = await res.json();
        return json.report.status;
    }, {
        timeout: 60000,
        intervals: [2000]
    }).toBe('completed');

    // 3. Verify
    await page.goto(`/read/${reportId}`);
    const content = page.locator('.report-content-blocks');
    await expect(content).toContainText(/СТАТУС МЕСЯЦА/); 
    await expect(content).toContainText(/Ключевые события/);
  });
});
