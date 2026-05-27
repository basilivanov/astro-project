import { expect, test, type Page } from "@playwright/test";

import { bootstrapTelegramWebApp, expectNoCrash } from "./utils";

const DEV_BYPASS_AUTH = "123456789";
const PROD_BASE_URL = process.env.E2E_PROD_BASE_URL || "http://astro-project-frontend-1:3000";

async function bootstrapWeekHome(page: Page) {
  await page.setViewportSize({ width: 390, height: 844 });
  await bootstrapTelegramWebApp(page, {
    initData: DEV_BYPASS_AUTH,
    initDataUnsafe: {
      user: {
        id: 123456789,
        first_name: "Week",
        last_name: "Runtime",
        username: "week_runtime",
        language_code: "ru",
      },
    },
    sessionMockUser: true,
  });

  await page.route("**/api/analytics/**", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });
}

async function getLatestCompletedWeekReportId(page: Page) {
  const reportsResponse = await page.request.get("/api/reports/my?limit=20", {
    headers: {
      "X-Telegram-Auth": DEV_BYPASS_AUTH,
    },
  });
  expect(reportsResponse.ok()).toBeTruthy();
  const reports = await reportsResponse.json() as Array<{ id?: string; report_type?: string; status?: string }>;
  const latestWeekReport = reports.find((item) => item.report_type === "week_forecast" && item.status === "completed");
  expect(latestWeekReport?.id).toBeTruthy();
  return latestWeekReport!.id!;
}

async function primeWeekCanonicalEvidence(page: Page) {
  const reportId = await getLatestCompletedWeekReportId(page);
  const reportResponse = await page.request.get(`/api/reports/${reportId}`, {
    headers: {
      "X-Telegram-Auth": DEV_BYPASS_AUTH,
    },
  });
  expect(reportResponse.ok()).toBeTruthy();
  const reportPayload = await reportResponse.json() as {
    report?: { id?: string; report_type?: string; status?: string };
    week_brief?: Record<string, unknown> | null;
    week_brief_envelope?: { status?: string } | null;
  };
  expect(reportPayload.report?.id).toBe(reportId);
  expect(reportPayload.report?.report_type).toBe("week_forecast");
  expect(reportPayload.week_brief || reportPayload.week_brief_envelope?.status === "ready").toBeTruthy();

  return {
    reportId,
    requestId: reportResponse.headers()["x-request-id"] ?? null,
    traceId: reportResponse.headers()["x-trace-id"] ?? null,
    correlationId: reportResponse.headers()["x-correlation-id"] ?? null,
  };
}

test.describe("week dev runtime indicator", () => {
  test("expands and collapses the local runtime disclosure on /week in the active dev stack", async ({ page }) => {
    await bootstrapWeekHome(page);
    const evidence = await primeWeekCanonicalEvidence(page);
    expect(evidence.reportId).toBeTruthy();

    await page.goto("/week", { waitUntil: "networkidle" });
    await expectNoCrash(page);

    const badge = page.getByTestId("runtime-environment-badge");
    await expect(badge).toBeVisible();
    await expect(badge).toHaveAttribute("data-route-eligible", "true");
    await expect(badge).toHaveAttribute("data-runtime-badge-event", "astro:week-dev-indicator-toggle-request");
    await expect(page.getByTestId("week-render-path")).toHaveAttribute("data-render-path", "canonical");
    await expect(page.getByTestId("week-runtime-diagnostics-disclosure")).toHaveCount(0);

    await badge.click();

    const disclosure = page.getByTestId("week-runtime-diagnostics-disclosure");
    await expect(disclosure).toBeVisible();
    await expect(page.getByTestId("week-runtime-diagnostics-render-path")).toHaveText("canonical");
    await expect(page.getByTestId("week-runtime-diagnostics-bootstrap")).toHaveText("unknown");
    await expect(page.getByTestId("week-runtime-diagnostics-mode")).toHaveText("mock");
    await expect(disclosure.locator("dt")).toHaveCount(3);
    await expect(disclosure.locator("dd")).toHaveCount(3);

    await badge.click();
    await expect(disclosure).toHaveCount(0);
  });

  test("keeps the production runtime indicator inert on /week and never renders disclosure output", async ({ page }) => {
    await bootstrapWeekHome(page);

    await page.goto(`${PROD_BASE_URL}/week`, { waitUntil: "networkidle" });
    await expectNoCrash(page);

    const badge = page.locator("body > div.fixed.right-2.top-2").first();
    await expect(badge).toBeVisible();
    await expect(badge).toHaveText("PROD");
    await expect(page.locator('button[data-testid="runtime-environment-badge"]')).toHaveCount(0);
    await expect(page.getByTestId("week-runtime-diagnostics-disclosure")).toHaveCount(0);
    await expect(page.getByTestId("week-render-path")).toHaveCount(0);

    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent("astro:week-dev-indicator-toggle-request", {
        detail: { route: "/week", source: "playwright-prod-proof" },
      }));
    });

    await expect(page.getByTestId("week-runtime-diagnostics-disclosure")).toHaveCount(0);
  });
});
