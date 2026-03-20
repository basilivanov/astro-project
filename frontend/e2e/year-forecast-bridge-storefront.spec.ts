import { test, expect } from "@playwright/test";

// ############################################################################
// AI_HEADER: E2E_YEAR_FORECAST_BRIDGE_STOREFRONT
// ROLE: Verify year_forecast keeps subscription storefront when bridge flags are off.
// ############################################################################

test.describe("Year forecast storefront alignment", () => {
  test("catalog still presents year forecast as subscription", async ({
    page,
  }) => {
    await page.goto("/reports");

    await expect(
      page.locator('a[href="/create?type=year_forecast"]'),
    ).toContainText("299₽/мес");
  });

  test("create keeps year forecast on subscription paywall when runtime bridge flags are off", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem("mock_telegram_user", "1");
      Object.assign(window, {
        MOCK_INIT_DATA_OVERRIDE: "year-forecast-storefront",
        MOCK_USER_OVERRIDE: {
          id: 990102,
          first_name: "Year",
          last_name: "Storefront",
        },
      });
    });

    await page.route("**/api/users/me", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          full_name: "Year Storefront",
          can_ask_horary: false,
          can_access_premium: false,
          horary_balance: 0,
          report_unlocks: {
            natal_master: 0,
            month_forecast: 0,
            year_forecast: 0,
            solar_return: 0,
            synastry: 0,
          },
          feature_flags: {
            enable_one_off_entitlements_runtime: false,
            enable_persistent_checkout_sessions: false,
            legacy_premium_subscription_access: true,
          },
        }),
      });
    });

    await page.goto("/create?type=year_forecast&mock=1&runtime=1");

    await expect(page.getByTestId("create-subscription-note")).toContainText(
      "через подписку",
    );
    await expect(
      page.getByRole("button", { name: /Оформить подписку 299₽\/мес/i }),
    ).toBeVisible();
  });

  test("create prefers per-report access snapshot over legacy premium bool for one-off bridge", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem("mock_telegram_user", "1");
      Object.assign(window, {
        MOCK_INIT_DATA_OVERRIDE: "year-forecast-structured-access",
        MOCK_USER_OVERRIDE: {
          id: 990103,
          first_name: "Year",
          last_name: "Structured",
        },
      });
    });

    await page.route("**/api/users/me", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          full_name: "Year Structured",
          can_ask_horary: false,
          can_access_premium: true,
          horary_balance: 0,
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

    await page.goto("/create?type=year_forecast&mock=1&runtime=1");

    await expect(page.getByTestId("create-one-off-note")).toContainText(
      "один разовый unlock",
    );
    await expect(
      page.getByRole("button", { name: /Оплатить 499₽/i }),
    ).toBeVisible();
    await expect(page.getByTestId("create-premium-generate")).toHaveCount(0);
  });
});
