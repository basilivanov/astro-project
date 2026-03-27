import { test, expect } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.use({ trace: "off" });

async function mockCreateFlow(page: import("@playwright/test").Page, options: {
  reportId: string;
  reportType: string;
  waitForWeek?: boolean;
}) {
  const { reportId, reportType, waitForWeek } = options;

  await page.route("**/api/analytics/**", async (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("**/api/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        full_name: "Debug User",
        can_ask_horary: true,
        can_access_premium: true,
        horary_balance: 1,
        birth_place: "Moscow",
        current_location: "Moscow",
        birth_timezone: "Europe/Moscow",
        current_timezone: "Europe/Moscow",
        report_access: {
          natal_master: { allowed: true },
          week_forecast: { allowed: true },
          solar_return: { allowed: true },
          synastry: { allowed: true },
        },
        feature_flags: {
          enable_one_off_entitlements_runtime: false,
          enable_persistent_checkout_sessions: false,
          legacy_premium_subscription_access: true,
        },
      }),
    });
  });
  await page.route("**/api/reports/create", async (route) => {
    const payload = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ report_id: reportId, status: "completed", payload }),
    });
  });
  await page.route(`**/api/reports/${reportId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        report: { id: reportId, report_type: reportType, status: "completed", client_name: "Debug User" },
        chunks: [{ id: "chunk-1", section: "summary", title: "Итог", content: JSON.stringify([{ type: "paragraph", text: "Тестовый блок" }]) }],
        chart_svg: null,
      }),
    });
  });
  if (waitForWeek) {
    await page.route("**/api/reports/my**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ id: reportId, report_type: "week_forecast", status: "completed", client_name: "Debug User" }]),
      });
    });
  }
}

test.describe("Critical Path", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test("should render horary flow inside semantic main and CTA section", async ({ page }) => {
    await mockCreateFlow(page, { reportId: "horary-report-id", reportType: "horary" });
    await page.goto("/create?type=horary&mock=1");

    await expect(page.getByTestId("create-page")).toBeVisible();
    await expect(page.locator("main").getByRole("heading", { level: 1, name: "Задать вопрос" })).toBeVisible();
    await expect(page.getByLabel("Horary question form")).toBeVisible();
    await expect(page.getByTestId("create-footer-cta")).toBeVisible();
    await page.getByTestId("create-horary-textarea").fill("Тестовый вопрос для E2E (Horary)");
    await expect(page.getByTestId("create-horary-submit")).toBeVisible();

    await page.goto("/read/horary-report-id?mock=1");
    await expect(page.getByTestId("read-sticky-panel")).toBeVisible();
    await expect(page.getByTestId("read-overview-panel")).toBeVisible();
    await expectNoCrash(page);
  });

  test("should render premium flow inside semantic main and header", async ({ page }) => {
    await mockCreateFlow(page, { reportId: "week-report-id", reportType: "week_forecast", waitForWeek: true });
    await page.goto("/create?type=week_forecast&mock=1");

    await expect(page.getByTestId("create-page")).toBeVisible();
    await expect(page.locator("main > header").getByRole("heading", { level: 1, name: "Сформировать разбор" })).toBeVisible();
    await expect(page.getByLabel("Premium offer summary")).toBeVisible();
    await expect(page.getByTestId("create-footer-cta")).toBeVisible();
    await expect(page.getByTestId("create-premium-generate")).toBeVisible();

    await page.goto("/week?mock=1");
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expectNoCrash(page);
  });

  test("should keep synastry semantic product input block consistent", async ({ page }) => {
    let capturedPayload: Record<string, unknown> | null = null;

    await page.route("**/api/analytics/**", async (route) => route.fulfill({ status: 204, body: "" }));
    await page.route("**/api/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          full_name: "Debug User",
          can_ask_horary: true,
          can_access_premium: true,
          horary_balance: 1,
          birth_place: "Moscow",
          current_location: "Moscow",
          birth_timezone: "Europe/Moscow",
          current_timezone: "Europe/Moscow",
          report_access: {
            natal_master: { allowed: true },
            week_forecast: { allowed: true },
            solar_return: { allowed: true },
            synastry: { allowed: true },
          },
          feature_flags: {
            enable_one_off_entitlements_runtime: false,
            enable_persistent_checkout_sessions: false,
            legacy_premium_subscription_access: true,
          },
        }),
      });
    });
    await page.route("**/api/reports/create", async (route) => {
      capturedPayload = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ report_id: "synastry-report-id" }) });
    });
    await page.route("**/api/reports/synastry-report-id", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report: { id: "synastry-report-id", report_type: "synastry", status: "completed", client_name: "Debug User" },
          chunks: [{ id: "chunk-1", section: "compatibility", title: "Совместимость", content: JSON.stringify([{ type: "paragraph", text: "Тестовый блок" }]) }],
          chart_svg: null,
        }),
      });
    });

    await page.goto("/create?type=synastry&mock=1");
    await expect(page.getByTestId("create-page")).toBeVisible();
    await expect(page.getByTestId("create-synastry-block")).toHaveAttribute("data-grace-block", "PRODUCT_INPUT_SYN");
    await expect(page.getByTestId("create-product-input-group-synastry")).toBeVisible();
    await page.getByTestId("create-synastry-partner-name").fill("Партнер");
    await page.getByTestId("create-synastry-partner-birth-date").fill("1992-02-02T06:30");
    await page.getByTestId("create-synastry-partner-birth-location").fill("London");
    await page.evaluate(async () => {
      await fetch("/api/reports/create", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Telegram-Auth": "123456789" },
        body: JSON.stringify({
          report_type: "synastry",
          partner_name: "Партнер",
          partner_birth_date: "1992-02-02T06:30",
          partner_birth_location: "London",
        }),
      });
    });
    await expect.poll(() => capturedPayload).not.toBeNull();
    await page.goto("/read/synastry-report-id?mock=1");
    expect(capturedPayload).toMatchObject({ report_type: "synastry", partner_name: "Партнер", partner_birth_date: "1992-02-02T06:30", partner_birth_location: "London" });
    await expectNoCrash(page);
  });

  test("should keep solar semantic product input block consistent", async ({ page }) => {
    let capturedPayload: Record<string, unknown> | null = null;

    await page.route("**/api/analytics/**", async (route) => route.fulfill({ status: 204, body: "" }));
    await page.route("**/api/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          full_name: "Debug User",
          can_ask_horary: true,
          can_access_premium: true,
          horary_balance: 1,
          birth_place: "Moscow",
          current_location: "Moscow",
          birth_timezone: "Europe/Moscow",
          current_timezone: "Europe/Moscow",
          report_access: {
            natal_master: { allowed: true },
            week_forecast: { allowed: true },
            solar_return: { allowed: true },
            synastry: { allowed: true },
          },
          feature_flags: {
            enable_one_off_entitlements_runtime: false,
            enable_persistent_checkout_sessions: false,
            legacy_premium_subscription_access: true,
          },
        }),
      });
    });
    await page.route("**/api/reports/create", async (route) => {
      capturedPayload = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ report_id: "solar-report-id" }) });
    });
    await page.route("**/api/reports/solar-report-id", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report: { id: "solar-report-id", report_type: "solar_return", status: "completed", client_name: "Debug User" },
          chunks: [{ id: "chunk-1", section: "solar_theme", title: "Главная тема года", content: JSON.stringify([{ type: "paragraph", text: "Тестовый соляр" }]) }],
          chart_svg: null,
        }),
      });
    });

    await page.goto("/create?type=solar_return&mock=1");
    await expect(page.getByTestId("create-page")).toBeVisible();
    await expect(page.getByTestId("create-solar-block")).toHaveAttribute("data-grace-block", "PRODUCT_INPUT_SYN");
    await expect(page.getByTestId("create-product-input-group-solar")).toBeVisible();
    await page.getByTestId("create-solar-current-location").fill("Tbilisi, Georgia");
    await page.evaluate(async () => {
      await fetch("/api/reports/create", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Telegram-Auth": "123456789" },
        body: JSON.stringify({
          report_type: "solar_return",
          solar_current_location: "Tbilisi, Georgia",
        }),
      });
    });
    await expect.poll(() => capturedPayload).not.toBeNull();
    await page.goto("/read/solar-report-id?mock=1");
    expect(capturedPayload).toMatchObject({ report_type: "solar_return", solar_current_location: "Tbilisi, Georgia" });
    await expectNoCrash(page);
  });
});
