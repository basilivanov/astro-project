import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_PROFILE_REFERRAL
// ROLE: Verify Referral section on Profile page.
// ############################################################################

test.describe('Profile Referral', () => {
  
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
      
      // Mock Clipboard
      Object.assign(navigator, {
        clipboard: {
          writeText: async () => {}
        }
      });
    });
  });

  test('should show referral section and copy link', async ({ page }) => {
    await page.goto('/profile');
    await expect(page.getByTestId('profile-content')).toBeVisible({ timeout: 15000 });
    
    // Check if referral section text is present
    await expect(page.locator('text=Подарок за друга')).toBeVisible();
    await expect(page.locator('text=+14 дней бесплатно')).toBeVisible();
    
    // Check copy button
    const copyButton = page.locator('button:has-text("Копировать ссылку")');
    await expect(copyButton).toBeVisible();
    
    // Click copy button
    await copyButton.click();
    
    // Check if text changed to "Ссылка скопирована"
    await expect(page.locator('text=Ссылка скопирована')).toBeVisible();
  });
});
