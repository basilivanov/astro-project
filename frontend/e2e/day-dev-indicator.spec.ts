import { expect, test, type Page } from "@playwright/test";

import { bootstrapMockTelegram, expectNoCrash } from "./utils";

const PROD_BASE_URL = process.env.E2E_PROD_BASE_URL || "http://astro-project-frontend-1:3000";

async function bootstrapDayHome(page: Page) {
  await page.setViewportSize({ width: 390, height: 844 });
  await bootstrapMockTelegram(page, {
    feedState: "ready",
  });
}

test.describe("day dev runtime indicator", () => {
  test("expands and collapses the local runtime disclosure on Day home in the active dev stack", async ({ page }) => {
    await bootstrapDayHome(page);

    await page.goto("/?mock=1", { waitUntil: "networkidle" });
    await expectNoCrash(page);

    const badge = page.getByTestId("runtime-environment-badge");
    await expect(badge).toBeVisible();
    await expect(badge).toHaveAttribute("data-route-eligible", "true");
    await expect(page.getByTestId("day-runtime-diagnostics-disclosure")).toHaveCount(0);

    await badge.click();

    const disclosure = page.getByTestId("day-runtime-diagnostics-disclosure");
    await expect(disclosure).toBeVisible();
    await expect(page.getByTestId("day-runtime-diagnostics-render-path")).toBeVisible();
    await expect(page.getByTestId("day-runtime-diagnostics-bootstrap")).toBeVisible();
    await expect(page.getByTestId("day-runtime-diagnostics-mode")).toBeVisible();
    await expect(disclosure.locator("dt")).toHaveCount(3);
    await expect(disclosure.locator("dd")).toHaveCount(3);

    await badge.click();
    await expect(disclosure).toHaveCount(0);
  });

  test("keeps the production runtime indicator inert and without disclosure output", async ({ page }) => {
    await bootstrapDayHome(page);

    await page.goto(`${PROD_BASE_URL}/?mock=1`, { waitUntil: "networkidle" });
    await expectNoCrash(page);

    const badge = page.locator('body > div.fixed.right-2.top-2').first();
    await expect(badge).toBeVisible();
    await expect(badge).toHaveText("PROD");
    await expect(page.locator('button[data-testid="runtime-environment-badge"]')).toHaveCount(0);
    await expect(page.getByTestId("day-runtime-diagnostics-disclosure")).toHaveCount(0);

    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent("astro:day-dev-indicator-toggle-request", {
        detail: { route: "/", source: "playwright-prod-proof" },
      }));
    });

    await expect(page.getByTestId("day-runtime-diagnostics-disclosure")).toHaveCount(0);
  });
});
