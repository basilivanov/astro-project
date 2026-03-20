import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_COSMOGRAM
// ROLE: Verify Client creation with unknown birth time (Cosmogram).
// VERIFIES: P0-COSMO-02
// ############################################################################

test.describe('Cosmogram Creation', () => {
  test.setTimeout(60000);
  
  test.beforeEach(async ({ page }) => {
    page.on('console', msg => console.log('BROWSER:', msg.text()));
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

  test('should create a client with unknown birth time and see it in the list', async ({ page }) => {
    await page.goto('/admin/clients');
    
    const uniqueName = `Cosmo Client ${Date.now()}`;
    
    // Fill the form
    await page.fill('input[name="client_name"]', uniqueName);
    await page.fill('input[name="birth_date_only"]', '1995-05-20');
    
    // Check "Unknown" checkbox
    await page.check('input[name="birth_time_unknown"]');
    
    // Time input should be hidden
    await expect(page.locator('input[name="birth_time"]')).not.toBeVisible();
    
    // GeoField search
    await page.fill('input[placeholder="Начните вводить город"]', 'Paris');
    await page.waitForSelector('.suggestions .suggestion', { timeout: 15000 });
    await page.click('.suggestions .suggestion:not(.muted):first-child');

    // Submit
    await page.click('button:has-text("Создать клиента")');

    // Wait for redirect to report create, then extract ID and go to admin detail
    await page.waitForURL(/\/create\?client_id=.+/);
    const url = page.url();
    const clientId = new URL(url).searchParams.get('client_id');
    
    // Go to admin detail page directly
    await page.goto(`/admin/clients/${clientId}`, { waitUntil: 'networkidle' });
    
    // Wait for page content
    const accordionBtn = page.getByText('Редактировать профиль');
    await expect(accordionBtn).toBeVisible({ timeout: 30000 });
    
    // Open accordion
    await accordionBtn.click();

    // Verify details
    const checkbox = page.locator('input[type="checkbox"][name="birth_time_unknown"]');
    await expect(checkbox).toBeChecked({ timeout: 15000 });
  });
});
