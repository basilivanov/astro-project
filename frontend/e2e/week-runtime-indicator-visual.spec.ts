import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

import { bootstrapTelegramWebApp, expectNoCrash } from "./utils";

const DEV_BYPASS_AUTH = "123456789";
const OUT_DIR = "/app/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator";
const PROD_BASE_URL = process.env.E2E_PROD_BASE_URL || "http://astro-project-frontend-1:3000";

async function ensureOutDir() {
  await fs.mkdir(OUT_DIR, { recursive: true });
}

async function writeShot(page: Parameters<typeof test>[0]["page"], name: string) {
  await page.screenshot({ path: path.join(OUT_DIR, name), fullPage: true });
}

async function mountWeekMock(page: Parameters<typeof test>[0]["page"]) {
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
  await page.setViewportSize({ width: 390, height: 844 });

  await page.route("**/api/analytics/**", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });
}

async function captureWeekObservabilityProof(page: Parameters<typeof test>[0]["page"]) {
  const reportsResponse = await page.request.get("/api/reports/my?limit=20", {
    headers: {
      "X-Telegram-Auth": DEV_BYPASS_AUTH,
    },
  });
  expect(reportsResponse.ok()).toBeTruthy();
  const reports = await reportsResponse.json() as Array<{ id?: string; report_type?: string; status?: string }>;
  const latestWeekReport = reports.find((item) => item.report_type === "week_forecast" && item.status === "completed");
  expect(latestWeekReport?.id).toBeTruthy();

  const detailResponse = await page.request.get(`/api/reports/${latestWeekReport!.id}`, {
    headers: {
      "X-Telegram-Auth": DEV_BYPASS_AUTH,
    },
  });
  expect(detailResponse.ok()).toBeTruthy();

  const detailPayload = await detailResponse.json() as {
    report?: { id?: string; report_type?: string };
    week_brief?: Record<string, unknown> | null;
    week_brief_envelope?: { status?: string } | null;
  };
  expect(detailPayload.report?.id).toBe(latestWeekReport!.id);
  expect(detailPayload.report?.report_type).toBe("week_forecast");
  expect(detailPayload.week_brief || detailPayload.week_brief_envelope?.status === "ready").toBeTruthy();

  const proof = {
    capturedAt: new Date().toISOString(),
    reportId: latestWeekReport!.id,
    requestId: detailResponse.headers()["x-request-id"] ?? null,
    traceId: detailResponse.headers()["x-trace-id"] ?? null,
    correlationId: detailResponse.headers()["x-correlation-id"] ?? null,
  };
  await fs.writeFile(path.join(OUT_DIR, "week-runtime-indicator-observability.json"), JSON.stringify(proof, null, 2), "utf8");
}

test.describe("week runtime indicator visual evidence", () => {
  test("captures dev collapsed and expanded Week runtime indicator states", async ({ page }) => {
    await ensureOutDir();
    await mountWeekMock(page);
    await captureWeekObservabilityProof(page);

    await page.goto("/week", { waitUntil: "networkidle" });
    await expectNoCrash(page);
    const badge = page.getByTestId("runtime-environment-badge");
    await expect(badge).toHaveText("DEV");
    await expect(badge).toHaveAttribute("data-route-eligible", "true");
    await expect(badge).toHaveAttribute("data-runtime-badge-event", "astro:week-dev-indicator-toggle-request");
    await expect(page.getByTestId("week-runtime-diagnostics-disclosure")).toHaveCount(0);

    await writeShot(page, "week-dev-indicator-collapsed.png");

    await badge.click();
    await expect(page.getByTestId("week-runtime-diagnostics-disclosure")).toBeVisible();
    await writeShot(page, "week-dev-indicator-expanded.png");
  });

  test("captures production Week runtime indicator unchanged state", async ({ page }) => {
    await ensureOutDir();
    await mountWeekMock(page);

    await page.goto(`${PROD_BASE_URL}/week`, { waitUntil: "networkidle" });
    await expectNoCrash(page);
    await expect(page.locator("body > div.fixed.right-2.top-2").first()).toHaveText("PROD");
    await expect(page.getByTestId("week-runtime-diagnostics-disclosure")).toHaveCount(0);
    await writeShot(page, "week-prod-indicator-inert.png");
  });
});
