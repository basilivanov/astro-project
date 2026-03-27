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
    await page.waitForURL((url) => url.pathname === "/" && url.searchParams.get("mock") === "1", { timeout: 15000 });
    await expectNoCrash(page);
    await expect(page).toHaveURL(/\/?(?:\?mock=1)?$/);
    await expect(page.getByTestId("home-feed-page")).toBeVisible();
  });

  test("start page shows auth gate for guest mode", async ({ page }) => {
    await bootstrapMockTelegram(page, { guest: true });
    await page.goto("/start?guest=1");
    await page.waitForURL((url) => url.pathname === "/start" && url.searchParams.get("guest") === "1", { timeout: 15000 });
    await expectNoCrash(page);
    await expect(page.getByTestId("start-auth-gate")).toBeVisible();
    await expect(page.getByTestId("start-auth-gate-cta")).toBeVisible();
    await expect(page.getByTestId("start-auth-gate-hint")).toBeVisible();
  });
});
