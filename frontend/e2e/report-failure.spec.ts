import { test, expect } from '@playwright/test';

import { bootstrapMockTelegram } from './utils';

test.describe('Report Failure UI', () => {
  test('should show failure CTA with resume telemetry and allow regeneration for failed reports', async ({ page }) => {
    const analyticsEvents: Array<{ name: string; payload: Record<string, unknown> }> = [];
    await bootstrapMockTelegram(page);

    await page.route('**/api/analytics/event', async (route) => {
      const body = route.request().postDataJSON() as { event_name?: string } & Record<string, unknown>;
      analyticsEvents.push({
        name: body.event_name ?? 'unknown',
        payload: body,
      });
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ok: true }),
      });
    });

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
            client_name: 'Fail Tester',
          },
          chart_svg: null,
          chunks: [],
        }),
      });
    });

    await page.route('**/api/reports/failed-report-id/regenerate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          report_id: 'failed-report-id',
          status: 'in_progress',
        }),
      });
    });

    await page.route('**/api/billing/sessions/checkout-secret-token', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'pending',
          report_type: 'natal_master',
          resumed_report_id: 'failed-report-id',
          return_path: '/create?report=natal',
        }),
      });
    });

    await page.goto('/read/failed-report-id?mock=1&checkout=checkout-secret-token');

    await expect(page.getByTestId('report-failure-surface')).toBeVisible();
    await expect(page.getByTestId('report-failure-context')).toBeVisible();
    await expect(page.getByTestId('report-failure-retry-block')).toBeVisible();
    await expect(page.getByTestId('report-failure-support-block')).toBeVisible();
    await expect(page.getByTestId('read-resume-entry')).toBeVisible();
    await expect(page.getByTestId('catalog-checkout-resume')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Отчет не удалось собрать');
    await expect(page.getByTestId('read-regenerate-button')).toContainText('Перегенерировать');

    await page.getByTestId('catalog-checkout-resume').getByRole('link', { name: 'Вернуться' }).click();

    await expect.poll(() => analyticsEvents.some((event) => event.name === 'catalog.read_resume_click')).toBeTruthy();

    const resumeClick = analyticsEvents.find((event) => event.name === 'catalog.read_resume_click');
    expect(resumeClick?.payload.surface).toBe('read');
    expect(resumeClick?.payload.block).toBe('RESUME_ENTRY');
    expect(resumeClick?.payload.semantic_block).toBe('RESUME_ENTRY');
    expect(resumeClick?.payload.entry_point).toBe('read_resume_banner');
    expect(resumeClick?.payload.action).toBe('resume_click');

    const resumeStatus = analyticsEvents.find((event) => event.name === 'catalog.checkout_resume_status');
    expect(resumeStatus?.payload.surface).toBe('read');
    expect(resumeStatus?.payload.entry_point).toBe('read_resume_banner');

    const [request] = await Promise.all([
      page.waitForRequest((req) => req.url().includes('/regenerate') && req.method() === 'POST'),
      page.getByTestId('read-regenerate-button').click(),
    ]);

    expect(request.method()).toBe('POST');

    await expect.poll(() => analyticsEvents.length).toBeGreaterThan(0);

    const readOpened = analyticsEvents.find((event) => event.name === 'catalog.read_opened');
    expect(readOpened?.payload.surface).toBe('read');
    expect(readOpened?.payload.flow_id).toBe('FLOW-FORECAST-CATALOG');
    expect(readOpened?.payload.block).toBe('CTA_TRACKING');
    expect(readOpened?.payload.semantic_block).toBe('CTA_TRACKING');
    expect(readOpened?.payload.entry_point).toBe('read_resume_banner');

    const regenerateClick = analyticsEvents.find((event) => event.name === 'catalog.read_regenerate_click');
    expect(regenerateClick?.payload.surface).toBe('failure');
    expect(regenerateClick?.payload.block).toBe('FAILURE_RETRY');
    expect(regenerateClick?.payload.flow_id).toBe('FLOW-FORECAST-CATALOG');
    expect(regenerateClick?.payload.module).toBe('M-CATALOG-ANALYTICS');
    expect(regenerateClick?.payload.semantic_block).toBe('FAILURE_RETRY');
    expect(regenerateClick?.payload.retry_cta_id).toBe('read-regenerate-button');

    await page.getByTestId('read-failure-history-link').click();

    await expect.poll(() => analyticsEvents.some((event) => event.name === 'catalog.read_support_click')).toBeTruthy();

    const supportClick = analyticsEvents.find((event) => event.name === 'catalog.read_support_click');
    expect(supportClick?.payload.surface).toBe('failure');
    expect(supportClick?.payload.block).toBe('FAILURE_SUPPORT');
    expect(supportClick?.payload.module).toBe('M-CATALOG-ANALYTICS');
    expect(supportClick?.payload.semantic_block).toBe('FAILURE_SUPPORT');
    expect(supportClick?.payload.support_cta_id).toBe('read-failure-history-link');

    for (const event of analyticsEvents) {
      const serialized = JSON.stringify(event.payload);
      expect(serialized).not.toContain('checkout-secret-token');
    }
  });
});
