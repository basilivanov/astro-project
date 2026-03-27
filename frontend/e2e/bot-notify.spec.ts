import { test, expect } from '@playwright/test';

type TelemetryEvent = {
  module?: string;
  contract?: string;
  block?: string;
  delivery_status?: string;
  non_fatal?: boolean;
  status_code?: number;
  [key: string]: unknown;
};

test.describe('VM-BOT-NOTIFY telemetry regression', () => {
  test('blocked chat remains non-fatal in telemetry evidence', async ({ page }) => {
    const telemetryEvents: TelemetryEvent[] = [];

    await page.route('**/api/analytics/**', async (route) => {
      const bodyText = route.request().postData() ?? '{}';
      let body: Record<string, unknown> = {};
      try {
        body = JSON.parse(bodyText);
      } catch {
        body = {};
      }
      if (Array.isArray(body.events)) {
        telemetryEvents.push(...(body.events as TelemetryEvent[]));
      } else {
        telemetryEvents.push(body as TelemetryEvent);
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ok: true }),
      });
    });

    await page.goto('/');

    await page.evaluate(async () => {
      await fetch('/api/analytics/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          module: 'M-NOTIFICATION-SERVICE',
          contract: 'send_bot_notification',
          block: 'POST_NOTIFY_REQUEST',
          delivery_status: 'blocked_chat',
          non_fatal: true,
          status_code: 403,
        }),
      });
    });

    await expect.poll(() => telemetryEvents.length).toBeGreaterThan(0);
    expect(
      telemetryEvents.some(
        (event) =>
          event.module === 'M-NOTIFICATION-SERVICE' &&
          event.contract === 'send_bot_notification' &&
          event.block === 'POST_NOTIFY_REQUEST' &&
          event.delivery_status === 'blocked_chat' &&
          event.non_fatal === true &&
          event.status_code === 403,
      ),
    ).toBeTruthy();
  });
});
