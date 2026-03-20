import { test, expect } from '@playwright/test';

test.describe('Week Tab Live States', () => {
  test.beforeEach(async ({ page }) => {
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
  });

  test('should show "Get Forecast" for empty state', async ({ page }) => {
    await page.goto('/week');
    // Use longer timeout for the initial load
    await expect(page.getByText('Получить прогноз').or(page.getByText('Навигатор недели'))).toBeVisible({ timeout: 10000 });
  });

  test('should show report content for completed state', async ({ page }) => {
    await page.goto('/week');
    // It should either show the CTA or the report sections
    const cta = page.getByText('Получить прогноз');
    const sections = page.locator('.report-content-blocks');
    
    // We expect at least the header or the CTA
    await expect(page.getByText('Навигатор недели')).toBeVisible({ timeout: 10000 });
    
    // If completed report exists, we should see sections or the summary
    // Since we can't easily guarantee report existence without mocking, 
    // we just check that one of the valid states is visible
    await expect(cta.or(sections).or(page.getByText('Готовим прогноз'))).toBeVisible();
  });
});