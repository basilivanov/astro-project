import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_ADMIN_CLIENTS
// ROLE: Verify Client creation and listing in Admin.
// VERIFIES: P0-DEV-ADMIN-CLIENTS-01
// ############################################################################

test.describe('Admin Clients Management', () => {
  test.describe.configure({ mode: 'serial' });
  
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      // Mock Telegram WebApp
      (window as any).Telegram = { 
        WebApp: { 
          initData: '123456789', 
          ready: () => {}, 
          expand: () => {}, 
          close: () => {},
          headerColor: '#ffffff',
          backgroundColor: '#ffffff',
          initDataUnsafe: { user: { id: 123456789, first_name: 'Debug', last_name: 'User' } }
        } 
      };
    });
  });

  test('should create a new client and see it in the list', async ({ page }) => {
    await page.goto('/admin/clients');
    
    // Check header
    await expect(page.locator('h1')).toContainText('Клиенты');

    const uniqueName = `Test Client ${Date.now()}`;
    
    // Fill the form
    await page.fill('input[name="client_name"]', uniqueName);
    await page.fill('input[name="birth_date_only"]', '1990-01-01');
    await page.fill('input[name="birth_time"]', '15:30');
    
    // GeoField search
    await page.fill('input[placeholder="Начните вводить город"]', 'Moscow');
    await page.waitForSelector('.suggestions .suggestion', { timeout: 15000 });
    await page.click('.suggestions .suggestion:not(.muted):first-child');

    // Submit
    await page.click('button:has-text("Создать клиента")');

    // After creation, the app redirects to /reports/create?client_id=...
    // But we want to see it in the list. So we go back to /admin/clients
    await page.goto('/admin/clients');
    
    // Verify client exists in list
    await expect(page.locator(`text=${uniqueName}`)).toBeVisible({ timeout: 15000 });
  });
});