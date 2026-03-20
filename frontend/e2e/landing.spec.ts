import { test, expect } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.describe("Landing and start flow", () => {
  test("landing keeps CTA and product layout for guest", async ({ page }) => {
    await bootstrapMockTelegram(page, { guest: true });
    await page.goto("/?guest=1");
    await expectNoCrash(page);
    await expect(page.getByTestId("start-cta")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Твой личный астролог/i })).toBeVisible();
    await expect(page.getByText(/14 дней бесплатно/i)).toBeVisible();
  });

  test("start page redirects mock users into feed", async ({ page }) => {
    await bootstrapMockTelegram(page);
    await page.goto("/start");
    await page.waitForURL(/\/?mock=1$/, { timeout: 15000 });
    await expect(page.getByTestId("feed-page")).toBeVisible();
  });
});
