import { test, expect } from '@playwright/test';
import { bootstrapMockTelegram, expectNoCrash } from './utils';

type AnalyticsEvent = {
  event: string;
  payload: Record<string, unknown>;
};

const workflowReportId = 'workflow-report-id';
const checkoutToken = 'resume-workflow-token';

async function readAnalytics(page: Parameters<typeof test>[0]['page']) {
  return page.evaluate(() => (window as Window & typeof globalThis & { __analyticsEvents?: AnalyticsEvent[] }).__analyticsEvents ?? []);
}

test.describe('Report workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      (window as Window & typeof globalThis & { __analyticsEvents?: AnalyticsEvent[] }).__analyticsEvents = [];
      const originalFetch = window.fetch.bind(window);
      window.fetch = async (input, init) => {
        const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
        if (url.includes('/api/analytics')) {
          const bodyText = typeof init?.body === 'string' ? init.body : '';
          try {
            const parsed = JSON.parse(bodyText);
            const batch = Array.isArray(parsed?.events) ? parsed.events : parsed ? [parsed] : [];
            for (const item of batch) {
              const payload = typeof item?.properties === 'object' && item.properties
                ? item.properties
                : typeof item?.payload === 'object' && item.payload
                  ? item.payload
                  : {};
              (window as Window & typeof globalThis & { __analyticsEvents: AnalyticsEvent[] }).__analyticsEvents.push({
                event: typeof item?.event === 'string' ? item.event : typeof item?.event_name === 'string' ? item.event_name : 'unknown',
                payload: typeof payload?.payload === 'object' && payload.payload ? payload.payload as Record<string, unknown> : payload as Record<string, unknown>,
              });
            }
          } catch {}
        }
        return originalFetch(input, init);
      };
    });

    await bootstrapMockTelegram(page);

    await page.route('**/api/analytics/**', async (route) => {
      await route.fulfill({ status: 204, body: '' });
    });
  });

  test('async chunk lifecycle renders completion and safe fallback telemetry path', async ({ page }) => {
    let reportFetchCount = 0;

    await page.route(`**/api/reports/${workflowReportId}`, async (route) => {
      reportFetchCount += 1;
      const payload = reportFetchCount < 2
        ? {
            report: {
              id: workflowReportId,
              report_type: 'year_forecast',
              status: 'in_progress',
              client_name: 'Workflow Tester',
              access_source: 'one_off',
            },
            chart_svg: null,
            chunks: [],
          }
        : {
            report: {
              id: workflowReportId,
              report_type: 'year_forecast',
              status: 'completed',
              client_name: 'Workflow Tester',
              access_source: 'one_off',
            },
            chart_svg: null,
            chunks: [
              {
                id: 'chunk-overview',
                section: 'executive_summary',
                title: 'Executive summary',
                content: JSON.stringify([{ type: 'paragraph', text: 'Секция уже собрана и готова к чтению.' }]),
              },
              {
                id: 'chunk-fallback',
                section: 'timing_windows',
                title: 'Timing windows',
                content: 'Fallback copy keeps the section readable while telemetry captures the degraded path.',
              },
            ],
          };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(payload),
      });
    });

    await page.goto(`/read/${workflowReportId}?mock=1`);

    await expect(page.getByTestId('consumer-status-badge')).toContainText('В обработке');
    await expect(page.getByTestId('consumer-hero-meta')).toContainText('В работе');

    await expect.poll(async () => {
      const events = await readAnalytics(page);
      return events.filter((event) => event.event === 'catalog.read_opened').length;
    }, { timeout: 15000 }).toBeGreaterThan(0);

    const firstAnalytics = await readAnalytics(page);
    const openedPending = firstAnalytics.find((event) => event.event === 'catalog.read_opened');
    expect(openedPending?.event).toBe('catalog.read_opened');

    await page.reload();

    await expect(page.getByText('Секция уже собрана и готова к чтению.').first()).toBeVisible();
    await expect(page.getByTestId('report-fallback-card')).toContainText('Fallback copy keeps the section readable while telemetry captures the degraded path.');
    await expectNoCrash(page);

    const finalAnalytics = await readAnalytics(page);
    const readOpenedEvents = finalAnalytics.filter((event) => event.event === 'catalog.read_opened');
    expect(readOpenedEvents.length).toBeGreaterThanOrEqual(1);
  });

  test('resume banner reports pending-to-succeeded telemetry on catalog surface', async ({ page }) => {
    let billingFetchCount = 0;

    await page.route('**/api/reports/my*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(`**/api/billing/sessions/${checkoutToken}`, async (route) => {
      billingFetchCount += 1;
      const payload = billingFetchCount < 2
        ? {
            status: 'pending',
            report_type: 'year_forecast',
            return_path: '/create?type=year_forecast',
            resumed_report_id: null,
          }
        : {
            status: 'succeeded',
            report_type: 'year_forecast',
            return_path: '/create?type=year_forecast',
            resumed_report_id: workflowReportId,
          };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(payload),
      });
    });

    await page.goto(`/reports?mock=1&runtime=1&checkout=${checkoutToken}`);

    await expect(page.getByTestId('catalog-checkout-resume')).toBeVisible();
    await expect.poll(() => billingFetchCount, { timeout: 15000 }).toBeGreaterThanOrEqual(2);

    const resumeLink = page.getByRole('link', { name: 'Вернуться' }).first();
    await expect(resumeLink).toHaveAttribute('href', /\/create\?type=year_forecast&checkout=resume-workflow-token&mock=1&runtime=1/);

    await expect.poll(async () => {
      const analytics = await readAnalytics(page);
      return analytics.filter((event) => event.event.startsWith('catalog.checkout_resume')).length;
    }, { timeout: 15000 }).toBeGreaterThanOrEqual(3);

    const analytics = await readAnalytics(page);
    expect(analytics.some((event) => event.event === 'catalog.checkout_resume_ready')).toBeTruthy();
    expect(analytics.filter((event) => event.event === 'catalog.checkout_resume_status')).toHaveLength(2);
    expect(analytics.some((event) => event.event === 'catalog.checkout_resume_success')).toBeTruthy();
  });
});
