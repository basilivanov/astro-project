import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_ADMIN_ENTITLEMENTS_V4
// ROLE: Verify Admin entitlement operations (Robust matching).
// VERIFIES: P0-ADMIN-ENTITLEMENTS-REPORT-01
// ############################################################################

test.describe('Admin Entitlements Operations', () => {
  test.describe.configure({ mode: 'serial' });
  test.setTimeout(120000);
  
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

  async function createTestClient(page) {
    await page.goto('/admin/clients');
    const uniqueName = `Entitlement Client ${Date.now()}`;
    await page.fill('input[name="client_name"]', uniqueName);
    await page.fill('input[name="birth_date_only"]', '1990-01-01');
    await page.fill('input[name="birth_time"]', '12:00');
    await page.fill('input[placeholder="Начните вводить город"]', 'London');
    await page.waitForSelector('.suggestions .suggestion', { timeout: 10000 });
    await page.click('.suggestions .suggestion:not(.muted):first-child');
    await page.click('button:has-text("Создать клиента")');
    await page.waitForURL(/\/create/);
    return uniqueName;
  }

  test('should add unlimited subscription and grant report', async ({ page }) => {
    await createTestClient(page);
    
    await page.goto('/admin/users');
    await page.fill('input[placeholder*="Поиск"]', 'Debug User');
    await page.waitForTimeout(1000); 
    await page.click(`text=Debug User`);

    // 1. Add Unlimited Subscription
    await page.click('button:has-text("∞ Безлимит")');
    await page.fill('input[placeholder="Причина..."]', 'E2E Test Unlimited');
    await page.click('button:has-text("Подтвердить")');
    await expect(page.locator('text=Успешно выполнено!')).toBeVisible({ timeout: 10000 });
    
    // 2. Grant Synastry Report
    await page.click('button:has-text("Синастрия")');
    await page.fill('input[placeholder="Причина..."]', 'E2E Test Grant');
    await page.click('button:has-text("Подтвердить")');
    await expect(page.locator('text=Успешно выполнено!')).toBeVisible({ timeout: 10000 });

    // 3. Verify canonical Synastry type in list
    await expect(page.locator('text=synastry').first()).toBeVisible({ timeout: 15000 });
  });

  test('should regenerate report with reason and see it in audit', async ({ page }) => {
    await page.goto('/admin/reports');
    await page.waitForSelector('button[title="Перегенерировать копию"]', { timeout: 15000 });
    
    const uniqueReason = `RegenReason${Date.now()}`;
    
    // Click button to show inline form
    await page.locator('button[title="Перегенерировать копию"]').first().click();
    
    // Fill reason and confirm
    await page.fill('input[placeholder="Причина..."]', uniqueReason);
    await page.click('button[title="Подтвердить"]');
    
    // Wait for success indicator
    await page.waitForSelector('button .lucide-check', { timeout: 15000 });
    
    // Check Audit Log
    // We navigate to audit and check for our reason. 
    // Playwright's goto will wait for load by default.
    await page.goto('/admin/audit');
    
    // Ensure "Пусто" is not showing if logs are expected
    await expect(page.locator('text=Пусто')).not.toBeVisible({ timeout: 10000 });
    
    // Find entry with regenerate_copy AND our uniqueReason
    const auditEntry = page.locator('.bg-white', { hasText: 'regenerate_copy' }).filter({ hasText: uniqueReason }).first();
    await expect(auditEntry).toBeVisible({ timeout: 20000 });
  });
});
