import { test, expect } from "@playwright/test";

test.describe("Week Tab Live States", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem("mock_telegram_user", "1");
      (window as any).Telegram = {
        WebApp: {
          initData: "123456789",
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: "Debug", last_name: "User" } },
        },
      };
    });
  });

  test("renders hero map with CTA", async ({ page }) => {
    await page.goto("/week");
    const heroActions = page.getByTestId("week-hero-actions");

    await expect(page.getByTestId("week-map-surface")).toBeVisible({ timeout: 10000 });
    await expect(heroActions).toBeVisible();
    await expect(heroActions.getByTestId("week-primary-cta")).toBeVisible();
  });

  test("shows week panels", async ({ page }) => {
    await page.goto("/week");

    await expect(page.getByTestId("week-day-grid")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("week-domain-panel")).toBeVisible();
    await expect(page.getByTestId("week-actions-panel")).toBeVisible();
    await expect(page.getByTestId("week-explainability-panel")).toBeVisible();
    await expect(page.getByTestId("week-deep-sections")).toBeVisible();
  });

  test("opens and closes week explainability details from the visible toggle", async ({ page }) => {
    await page.goto("/week");

    const toggle = page.getByTestId("week-explainability-toggle");
    const details = page.getByTestId("week-explainability-details");

    await expect(toggle).toBeVisible({ timeout: 10000 });
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(details).toBeHidden();

    await toggle.click();

    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(details).toBeVisible();
    await expect(page.getByTestId("week-factor-1")).toBeVisible();

    await toggle.click();

    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(details).toBeHidden();
  });
});
