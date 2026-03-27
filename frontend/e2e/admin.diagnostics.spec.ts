import { expect, test } from '@playwright/test';
import { bootstrapMockTelegram, expectNoCrash } from './utils';

type TelemetryEvent = {
  event?: string;
  stage?: string;
  status?: string;
  evidence?: string;
  flow_id?: string;
  block?: string;
  semantic_block?: string;
  surface?: string;
  telemetry_ready?: boolean;
  steps_count?: number;
  [key: string]: unknown;
};

const diagnosticsResponse = {
  status: 'ok',
  steps: [
    { name: 'natal', ok: true },
    { name: 'transit', ok: true },
    { name: 'month_data', ok: true },
    { name: 'synastry', ok: true },
    { name: 'llm', ok: true },
    { name: 'report', ok: true },
  ],
};

test.describe('Admin diagnostics runner', () => {
  test('runs diagnostics and records evidence + telemetry state', async ({ page }) => {
    const consoleEvents: TelemetryEvent[] = [];

    await bootstrapMockTelegram(page);

    page.on('console', async (message) => {
      if (message.type() !== 'info') return;
      const args = message.args();
      if (args.length < 2) return;
      const event = await args[0].jsonValue().catch(() => null);
      const payload = await args[1].jsonValue().catch(() => null);
      if (event === 'admin.diagnostics' && payload && typeof payload === 'object') {
        consoleEvents.push({ event, ...(payload as Record<string, unknown>) });
      }
    });

    await page.route('**/api/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok', db: 'connected' }),
      });
    });

    await page.route('**/api/diagnostics/run', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(diagnosticsResponse),
      });
    });

    await page.goto('/admin/health');
    await expectNoCrash(page);

    await expect(page.getByTestId('admin-health-page')).toBeVisible();
    await expect(page.getByTestId('admin-diagnostics-runner')).toBeVisible();
    await expect(page.getByTestId('admin-diagnostics-evidence')).toContainText('Task.md');
    await expect(page.getByTestId('admin-diagnostics-evidence')).toContainText('admin.diagnostics');

    await page.getByTestId('admin-diagnostics-run').click();

    await expect(page.getByTestId('admin-diagnostics-result')).toBeVisible();
    await expect(page.getByTestId('admin-diagnostics-status')).toContainText('ok');
    await expect(page.getByTestId('admin-diagnostics-step-natal')).toContainText('ok');
    await expect(page.getByTestId('admin-diagnostics-step-report')).toContainText('ok');

    await expect.poll(() => consoleEvents.length, { timeout: 15000 }).toBeGreaterThanOrEqual(2);

    expect(consoleEvents).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          event: 'admin.diagnostics',
          stage: 'request',
          evidence: 'Task.md',
          surface: 'admin_health',
          block: 'DIAGNOSTICS_RUNNER',
          semantic_block: 'DIAGNOSTICS_RUNNER',
          flow_id: 'FLOW-ADMIN-OPS',
        }),
        expect.objectContaining({
          event: 'admin.diagnostics',
          stage: 'success',
          status: 'ok',
          evidence: 'Task.md',
          telemetry_ready: true,
          steps_count: diagnosticsResponse.steps.length,
          surface: 'admin_health',
          block: 'DIAGNOSTICS_RUNNER',
          semantic_block: 'DIAGNOSTICS_RUNNER',
          flow_id: 'FLOW-ADMIN-OPS',
        }),
      ]),
    );
  });
});
