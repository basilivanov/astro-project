import { test, expect } from '@playwright/test';

test.describe('Localization Checks', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = { 
        WebApp: { 
          initData: '123456789', 
          initDataUnsafe: { user: { id: 123456789, first_name: 'Loc', last_name: 'Test' } } 
        } 
      };
    });
  });

  test('should render Russian section titles for Natal report', async ({ page }) => {
    // 1. Create Natal report via API
    const response = await page.request.post('/api/reports/create', {
        headers: { 'X-Telegram-Auth': '123456789' },
        data: {
            report_type: 'natal_master',
            client_name: 'Loc Test',
            birth_date: '1990-01-01T12:00:00',
            birth_location: 'Moscow',
            birth_lat: 55.75, 
            birth_lon: 37.61
        }
    });
    const data = await response.json();
    const reportId = data.report_id;

    // 2. Wait for completion
    await expect.poll(async () => {
        const res = await page.request.get(`/api/reports/${reportId}`, { headers: { 'X-Telegram-Auth': '123456789' } });
        return (await res.json()).report.status;
    }).toBe('completed');

    // 3. Open report
    await page.goto(`/read/${reportId}`);
    
    // 4. Check for Russian titles
    await expect(page.getByText('Синтез ядра')).toBeVisible();
    await expect(page.getByText('Баланс стихий')).toBeVisible();
    await expect(page.getByText('Личное ядро')).toBeVisible();
    await expect(page.getByText('Сферы жизни (Личность)')).toBeVisible();
    
    // 5. Check for absence of English keys
    await expect(page.getByText('synthesis')).not.toBeVisible();
    await expect(page.getByText('framework_elements_modes')).not.toBeVisible();
    await expect(page.getByText('balance_wheel_1_6')).not.toBeVisible();
  });
});
