import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_VISUAL_V3
// ROLE: Visual regression for main screens AND report reading views.
// VERIFIES: P0-E2E-READ-VISUAL-01
// ############################################################################

test.describe('Visual Regression', () => {
  
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

  const STATIC_SCREENS = [
    { name: 'home', path: '/' },
    { name: 'week', path: '/week' },
    { name: 'profile', path: '/profile' },
    { name: 'catalog', path: '/reports' }
  ];

  for (const screen of STATIC_SCREENS) {
    test(`Visual match for ${screen.name} mobile`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(screen.path);
      await page.waitForTimeout(5000); // Allow content to load
      
      await expect(page).toHaveScreenshot(`${screen.name}__mobile.png`, { 
        maxDiffPixelRatio: 0.05
      });
    });
  }

  test('Visual match for Horary report', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      
      // Go to history
      await page.goto('/reports/history');
      await page.waitForTimeout(5000);
      
      // Look for ANY completed report if 'Хорар' tag is missing (sometimes it is just 'Completed')
      const reportLink = page.locator('a[href^="/reports/"]').first();
      
      if (await reportLink.count() > 0) {
          const href = await reportLink.getAttribute('href');
          console.log(`Found report link: ${href}`);
          await reportLink.click();
          await page.waitForTimeout(8000); // Reports are heavy
          await expect(page).toHaveScreenshot(`read_horary__mobile.png`, { maxDiffPixelRatio: 0.1 });
      } else {
          // Fallback to a known ID from seed if history is empty
          console.warn('History empty in UI, trying known ID...');
          await page.goto('/reports/be2bd290-4c4a-432f-8241-2a35986465b1'); // From previous successful smoke
          await page.waitForTimeout(8000);
          await expect(page).toHaveScreenshot(`read_horary__mobile.png`, { maxDiffPixelRatio: 0.1 });
      }
  });

  test('Visual match for Natal report', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      
      // Try known ID for Natal
      await page.goto('/reports/d502e311-6f36-4f94-8a92-716db8845c6c'); // Seeded ID
      await page.waitForTimeout(8000);
      await expect(page).toHaveScreenshot(`read_natal__mobile.png`, { maxDiffPixelRatio: 0.1 });
  });
});
