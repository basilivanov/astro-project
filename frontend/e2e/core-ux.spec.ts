import { expect, test } from "@playwright/test";

import {
  attachConsoleAndPageErrors,
  bootstrapMockTelegram,
  expectNoCrash,
  expectNoRouteHygieneIssues,
} from "./utils";

test.describe("Core public and guest UX", () => {
  test("guest sees landing page without authenticated consumer surface", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

    await bootstrapMockTelegram(page, { guest: true });
    await page.goto("/?guest=1");
    await expectNoCrash(page);

    await expect(page.getByTestId("start-cta")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Твой личный астролог/i })).toBeVisible();
    await expect(page.getByText(/14 дней бесплатно/i)).toBeVisible();
    await expect(page.getByTestId("home-feed-page")).toHaveCount(0);

    await expectNoRouteHygieneIssues("/?guest=1", hygiene);
    hygiene.dispose();
  });

  test("guest start route keeps explicit auth gate", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

    await bootstrapMockTelegram(page, { guest: true });
    await page.goto("/start?guest=1");
    await expectNoCrash(page);

    await expect(page.getByTestId("start-auth-gate")).toBeVisible();
    await expect(page.getByTestId("start-auth-gate-cta")).toBeVisible();
    await expect(page.getByTestId("start-auth-gate-hint")).toBeVisible();

    await expectNoRouteHygieneIssues("/start?guest=1", hygiene);
    hygiene.dispose();
  });
});
