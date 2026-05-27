import { expect, test, type Page } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.use({ trace: "off" });

type ConsoleIssue = {
  type: "console" | "pageerror";
  text: string;
};

async function attachRuntimeHygiene(page: Page) {
  const issues: ConsoleIssue[] = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      issues.push({ type: "console", text: msg.text() });
    }
  });

  page.on("pageerror", (error) => {
    issues.push({ type: "pageerror", text: error.message });
  });

  await page.route("**/api/analytics/**", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });

  return async () => {
    expect.soft(issues, issues.map((issue) => `${issue.type}: ${issue.text}`).join("\n")).toEqual([]);
  };
}

async function mockCatalogState(page: Page) {
  await page.route("**/api/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        full_name: "Slice User",
        can_ask_horary: true,
        can_access_premium: false,
        horary_balance: 0,
        birth_place: "Moscow",
        current_location: "Moscow",
        birth_timezone: "Europe/Moscow",
        current_timezone: "Europe/Moscow",
        report_unlocks: {
          natal_master: 0,
          month_forecast: 0,
          year_forecast: 0,
          solar_return: 0,
          synastry: 0,
        },
        report_access: {
          year_forecast: {
            allowed: false,
            granted_via: null,
            remaining_unlocks: 0,
            reason_code: "payment_required",
            legacy_subscription_applied: false,
          },
        },
        feature_flags: {
          enable_one_off_entitlements_runtime: true,
          enable_persistent_checkout_sessions: true,
          legacy_premium_subscription_access: false,
        },
      }),
    });
  });

  await page.route("**/api/reports/my*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
}

async function mockCreateHappyPath(page: Page, reportId: string) {
  await mockCatalogState(page);

  await page.route("**/api/reports/create", async (route) => {
    const payload = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        report_id: reportId,
        status: "completed",
        payload,
      }),
    });
  });

  await page.route(`**/api/reports/${reportId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        report: {
          id: reportId,
          report_type: "horary",
          status: "completed",
          client_name: "Slice User",
        },
        chunks: [
          {
            id: "chunk-1",
            section: "summary",
            title: "Итог",
            content: JSON.stringify([{ type: "paragraph", text: "Ваш ответ готов." }]),
          },
        ],
        chart_svg: null,
      }),
    });
  });
}

async function mockBillingReturn(page: Page, options: { checkout: string; status: string; resumedReportId: string | null; }) {
  const { checkout, status, resumedReportId } = options;

  await mockCatalogState(page);
  await page.route(`**/api/billing/sessions/${checkout}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        checkout_token: checkout,
        status,
        report_type: "year_forecast",
        return_path: "/create?type=year_forecast",
        resumed_report_id: resumedReportId,
      }),
    });
  });
}

test.describe("Catalog/Create/Billing P0 slice", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test("/reports loads cleanly and navigates CTA to /create", async ({ page }) => {
    const assertHygiene = await attachRuntimeHygiene(page);
    await mockCatalogState(page);

    await page.goto("/reports?mock=1&runtime=1");

    await expect(page.getByTestId("catalog-subscription-section")).toBeVisible();
    const cta = page.locator('a[href="/create?type=year_forecast"]').first();
    await expect(cta).toBeVisible();
    await cta.click();
    await page.waitForURL(/\/create\?type=year_forecast/);
    await expect(page.getByTestId("create-page")).toBeVisible();
    await expectNoCrash(page);
    await assertHygiene();
  });

  test("/create completes horary happy path without runtime errors", async ({ page }) => {
    const assertHygiene = await attachRuntimeHygiene(page);
    await mockCreateHappyPath(page, "slice-horary-report");

    await page.goto("/create?type=horary&mock=1&runtime=1");

    await expect(page.getByTestId("create-page")).toBeVisible();
    await expect(page.getByTestId("create-footer-cta")).toBeVisible();
    await page.getByTestId("create-horary-textarea").fill("Сработает ли этот guard?");
    await page.getByTestId("create-horary-submit").click();
    await page.waitForURL(/\/read\/slice-horary-report\?mock=1/);
    await expect(page.getByText("Ваш ответ готов.").last()).toBeVisible();
    await expectNoCrash(page);
    await assertHygiene();
  });

  test("/create empty state guards missing type and returns to catalog", async ({ page }) => {
    const assertHygiene = await attachRuntimeHygiene(page);
    await mockCatalogState(page);

    await page.goto("/create?mock=1&runtime=1");

    await expect(page.getByTestId("create-empty-state-actions")).toBeVisible();
    await page.getByTestId("create-empty-state-catalog").click();
    await page.waitForURL(/\/reports$/);
    await expect(page.getByTestId("catalog-subscription-section")).toBeVisible();
    await expectNoCrash(page);
    await assertHygiene();
  });

  test("/billing/complete success resumes the create flow cleanly", async ({ page }) => {
    const assertHygiene = await attachRuntimeHygiene(page);
    await mockBillingReturn(page, {
      checkout: "slice-success-checkout",
      status: "succeeded",
      resumedReportId: "slice-year-report",
    });

    await page.route("**/api/reports/slice-year-report", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report: {
            id: "slice-year-report",
            report_type: "year_forecast",
            status: "completed",
            client_name: "Slice User",
          },
          chunks: [
            {
              id: "year-chunk-1",
              section: "summary",
              title: "Итог",
              content: JSON.stringify([{ type: "paragraph", text: "Годовой разбор готов." }]),
            },
          ],
          chart_svg: null,
        }),
      });
    });

    await page.goto("/billing/complete?checkout=slice-success-checkout&mock=1&runtime=1");

    await page.waitForURL(/\/read\/slice-year-report\?mock=1/);
    await expect(page.getByText("Годовой разбор готов.").last()).toBeVisible();
    await expectNoCrash(page);
    await assertHygiene();
  });

  test("/billing/complete failure keeps recovery CTA and avoids crash", async ({ page }) => {
    const assertHygiene = await attachRuntimeHygiene(page);
    await mockBillingReturn(page, {
      checkout: "slice-failed-checkout",
      status: "failed",
      resumedReportId: null,
    });

    await page.goto("/billing/complete?checkout=slice-failed-checkout&status=failed&reason=provider_return_failed&mock=1&runtime=1");

    await expect(page.getByText(/ЮMoney вернул оплату с ошибкой/i)).toBeVisible();
    await expect(page.getByRole("button", { name: "Назад", exact: true })).toBeVisible();
    await expect(page.getByTestId("billing-complete-swipe-back")).toBeVisible();
    await expectNoCrash(page);
    await assertHygiene();
  });
});
