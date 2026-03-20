import { test, expect } from '@playwright/test';

const ROUTES = [
  { path: '/', name: 'today' },
  { path: '/week', name: 'week' },
  { path: '/reports/history', name: 'history' },
  { path: '/admin/health', name: 'admin_health' },
  // /read/[id] requires a report, handling separately or mocking
];

test.describe('Route Console Smoke', () => {
  test.beforeEach(async ({ page }) => {
    // 1. Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        throw new Error(`Console Error: ${msg.text()}`);
      }
    });

    // 2. Capture page errors (runtime exceptions)
    page.on('pageerror', err => {
      throw new Error(`Page Error: ${err.message}`);
    });

    // 3. Mock Telegram Auth
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = { 
        WebApp: { 
          initData: '123456789', 
          ready: () => {}, 
          expand: () => {}, 
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Smoke', last_name: 'Test' } }
        } 
      };
    });
    // 4. Mock Analytics & Feedback
    await page.route('**/api/analytics/**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });
    await page.route('**/api/feedback/**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });
  });

  for (const route of ROUTES) {
    test(`should load ${route.path} without errors`, async ({ page }) => {
      // Mock API to ensure /week has data or /history works
      if (route.path === '/week') {
         await page.route('**/api/reports/my?*', async route => {
            await route.fulfill({ json: [{ id: 'mock-week', report_type: 'week_forecast', status: 'completed' }] });
         });
         await page.route('**/api/reports/mock-week', async route => {
            await route.fulfill({ json: { report: { id: 'mock-week', status: 'completed' }, chunks: [] } });
         });
      }

      await page.goto(route.path);
      await page.waitForLoadState('networkidle');
      
      // Basic visibility check to ensure render
      if (route.path === '/admin/health') {
          await expect(page.locator('h1')).toContainText('Система');
      } else {
          // For others, just ensure body is not empty
          await expect(page.locator('body')).toBeVisible();
      }
      
      // Take screenshot
      await page.screenshot({ path: `test-results/screens/smoke-${route.name}.png` });
    });
  }

  test('should load /read/[id] without errors', async ({ page }) => {
      const reportId = '123e4567-e89b-12d3-a456-426614174000';
      
      // Mock the report API - catch ANY report request
      await page.route('**/api/reports/*', async route => {
          // Check if it's our report
          if (route.request().url().includes(reportId)) {
              await route.fulfill({ 
                  status: 200,
                  contentType: 'application/json',
                  json: { 
                      report: { 
                          id: reportId, 
                          report_type: 'natal_master', 
                          status: 'completed', 
                          client_name: 'Smoke Client',
                          created_at: new Date().toISOString()
                      }, 
                      chunks: [
                          { 
                              id: 'c1', 
                              section: 'intro', 
                              content: JSON.stringify([{ type: 'paragraph', text: 'Smoke test content' }]) 
                          }
                      ] 
                  } 
              });
          } else {
              // Let others pass or mock them too
              await route.continue();
          }
      });

      await page.goto(`/read/${reportId}`);
      await page.waitForLoadState('networkidle');
      await expect(page.getByText('Smoke Client')).toBeVisible();
      await page.screenshot({ path: `test-results/screens/smoke-read-report.png` });
  });
});
