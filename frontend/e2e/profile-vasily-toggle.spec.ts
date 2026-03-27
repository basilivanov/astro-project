import { test, expect } from "@playwright/test";

import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.describe("Vasily profile mode switch", () => {
  test("shows client/admin switcher and updates CTA target", async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem("force_vasily_profile", "1");
    });
    await bootstrapMockTelegram(page);

    await page.route("**/api/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          full_name: "Василий",
          telegram_id: 123456789,
          days_left: 14,
          is_partner: false,
          referral_code: "VASILY14",
          subscription_active_until: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
        }),
      });
    });

    await page.goto("/profile?mock=1");
    await expectNoCrash(page);

    await expect(page.getByTestId("profile-audience-switcher")).toBeVisible();
    await expect(page.getByTestId("profile-audience-cta")).toContainText("магазин");
    await expect(page.getByTestId("profile-audience-cta").locator("a")).toHaveAttribute("href", "/reports");

    await page.getByRole("button", { name: /Админ/i }).click();
    await expect(page.getByTestId("profile-audience-cta")).toContainText("админ-выдачу");
    await expect(page.getByTestId("profile-audience-cta").locator("a")).toHaveAttribute("href", "/admin/reports");
  });
});
