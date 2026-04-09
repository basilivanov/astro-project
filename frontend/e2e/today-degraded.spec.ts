import { expect, test } from "@playwright/test";

import { attachConsoleAndPageErrors, bootstrapMockTelegram, expectNoCrash, expectNoRouteHygieneIssues } from "./utils";

test.describe("Today compatibility fallback", () => {
  test("shows an explicit degraded state instead of reconstructing premium Today from legacy payload", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    await bootstrapMockTelegram(page, {
      feedState: "ready",
      feedOverride: {
        general_vibe: "Legacy fallback headline",
        traffic_lights: { health: "green", money: "yellow" },
        fast_hits: [{ summary: "Утренний импульс" }],
      },
    });

    await page.goto("/?mock=1");
    await expectNoCrash(page);

    await expect(page.getByTestId("home-feed-page")).toBeVisible();
    await expect(page.getByTestId("today-degraded-state")).toBeVisible();
    await expect(page.getByTestId("today-degraded-note")).toContainText("day_brief_v1");
    await expect(page.getByTestId("today-degraded-cta")).toHaveAttribute("href", "/week");
    await expect(page.getByTestId("today-verdict")).toHaveCount(0);
    await expect(page.getByTestId("today-score-energy")).toHaveCount(0);
    await expect(page.getByTestId("today-windows")).toHaveCount(0);
    await expect(page.getByTestId("today-actions")).toHaveCount(0);
    await expect(page.getByTestId("today-risks")).toHaveCount(0);

    await expectNoRouteHygieneIssues("/?mock=1", hygiene);
    hygiene.dispose();
  });
});
