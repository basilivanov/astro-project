import { test, expect } from '@playwright/test';

test.describe('Report Failure UI', () => {
  test('should show error screen and allow regeneration for failed reports', async ({ page }) => {
    // We need a failed report. We can mock the API response.
    // Or better, use a known failed report ID if we had one.
    // Since we are in E2E, let's mock the report detail call.
    
    await page.route('**/api/reports/failed-report-id', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          report: {
            id: 'failed-report-id',
            report_type: 'natal_master',
            status: 'failed',
            created_at: new Date().toISOString(),
            client_name: 'Fail Tester'
          },
          chart_svg: null,
          chunks: []
        })
      });
    });

    await page.goto('/read/failed-report-id?mock=1');
    
    // Check for error screen
    await expect(page.locator('h2')).toContainText('Отчет не удалось собрать');
    await expect(page.locator('button')).toContainText('Перегенерировать');

    // Mock regeneration start
    await page.route('**/api/reports/failed-report-id/regenerate', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                report_id: 'failed-report-id',
                status: 'in_progress'
            })
        });
    });

    // Click regenerate
    // Note: window.location.reload() might be hard to catch in simple test, 
    // but we can check if the button was clicked and the request made.
    const [request] = await Promise.all([
        page.waitForRequest(req => req.url().includes('/regenerate') && req.method() === 'POST'),
        page.click('button:has-text("Перегенерировать")')
    ]);

    expect(request.method()).toBe('POST');
  });
});
