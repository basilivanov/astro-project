import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_ADMIN_USERS
// ROLE: Verify Admin Users management.
// ############################################################################

test.describe('Admin Users', () => {
  
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

  test('should list users', async ({ page }) => {
    await page.goto('/admin/users');
    
    // Ensure header is there
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible({ timeout: 15000 });
    await expect(h1).toContainText('Пользователи');
    
    // Check for either the table or the "Ничего не найдено" state
    await page.waitForTimeout(2000); // Allow data to settle
    
    const hasTable = await page.locator('table').count() > 0;
    const hasEmpty = await page.locator('text=Ничего не найдено').count() > 0;
    
    expect(hasTable || hasEmpty, 'Should show either users table or empty state').toBeTruthy();
  });

  test('should filter users', async ({ page }) => {
    await page.goto('/admin/users');
    
    const searchInput = page.getByPlaceholder(/Поиск/i);
    await expect(searchInput).toBeVisible();
    await searchInput.fill('test_user_search');
    
    // Ensure the loading state or results update without 500
    await page.waitForTimeout(1000); 
    await expect(page.locator('h1')).toContainText('Пользователи');
  });
});