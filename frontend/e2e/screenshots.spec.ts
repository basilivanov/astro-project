import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_SCREENSHOTS
// ROLE: Capture baseline screenshots for the review pack.
// ############################################################################

const ROUTES = [
  { path: '/', name: 'home' },
  { path: '/reports/history', name: 'history' },
  { path: '/profile', name: 'profile' },
  { path: '/create', name: 'create' },
  { path: '/admin/dashboard', name: 'admin_dashboard' },
  { path: '/admin/users', name: 'admin_users' },
  { path: '/admin/reports', name: 'admin_reports' }
];

test.describe('Baseline Screenshots', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
    });
  });

  for (const route of ROUTES) {
    test(`Screenshot ${route.name} mobile`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      const response = await page.goto(route.path);
      
      // DoD: HTTP < 400
      expect(response?.status() ?? 0).toBeLessThan(400);
      
      await page.waitForTimeout(3000); 
      await page.screenshot({ path: `test-results/screens/${route.name}__mobile.png` });
    });

    if (route.path.startsWith('/admin')) {
      test(`Screenshot ${route.name} desktop`, async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 720 });
        const response = await page.goto(route.path);
        
        expect(response?.status() ?? 0).toBeLessThan(400);
        
        await page.waitForTimeout(3000);
        await page.screenshot({ path: `test-results/screens/${route.name}__desktop.png` });
      });
    }
  }
});