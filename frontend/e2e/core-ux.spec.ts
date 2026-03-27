import { test, expect } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.describe("Core B2C UX", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test("guest should see landing page", async ({ page }) => {
    await bootstrapMockTelegram(page, { guest: true });
    await page.goto("/?guest=1");
    await expect(page.getByTestId("start-cta")).toBeVisible();
  });

  test("user auth flow shows Today brief", async ({ page }) => {
    await page.goto("/");
    await expectNoCrash(page);
    await expect(page.getByTestId("home-feed-page")).toBeVisible();
    await expect(page.getByTestId("consumer-page-shell-content")).toHaveAttribute("data-block", "SHELL_CONTENT");
    await expect(page.getByTestId("today-verdict")).toBeVisible();
    await expect(page.getByTestId("today-day-mode")).toBeVisible();
    await expect(page.getByTestId("traffic-lights")).toBeVisible();
    await expect(page.getByTestId("today-windows")).toBeVisible();
    await expect(page.getByTestId("today-actions")).toBeVisible();
    await expect(page.getByTestId("today-risks")).toBeVisible();
    await expect(page.getByTestId("today-explainability")).toBeVisible();
    await expect(page.getByTestId("today-cta-panel")).toBeVisible();
    await expect(page.getByTestId("today-cta-week")).toBeVisible();
    await expect(page.getByTestId("today-cta-premium")).toBeVisible();
    await expect(page.getByTestId("traffic-light-health-green")).toBeVisible();
    await expect(page.getByTestId("traffic-light-money-yellow")).toBeVisible();
    await expect(page.getByTestId("traffic-light-love-red")).toBeVisible();
  });

  test("daily feed falls back safely", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await bootstrapMockTelegram(page, { feedState: "fallback" });
    await page.goto("/");
    await expect(page.getByTestId("feed-fallback-banner")).toBeVisible();
    await expect(page.getByTestId("feed-fallback-banner")).toHaveAttribute("data-block", "FEED_LOAD_FALLBACK");
    await expect(page.getByTestId("moon-card")).toBeVisible();
    await expect(page.getByTestId("traffic-lights")).toBeVisible();
    await expect(page.getByRole("link", { name: "Каталог разборов" })).toBeVisible();
  });

  test("daily feed shows empty state in empty mode", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await bootstrapMockTelegram(page, { feedState: "empty" });
    await page.goto("/");
    await expect(page.getByTestId("feed-empty-state")).toBeVisible();
    await expect(page.getByText(/Сводка дня еще не готова/i)).toBeVisible();
  });

  test("daily feed shows retryable error state on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await bootstrapMockTelegram(page, { feedState: "error" });
    await page.goto("/");
    await expect(page.getByTestId("feed-error-state")).toBeVisible();
    await expect(page.getByRole("button", { name: /Попробовать снова/i })).toBeVisible();
  });

  test("profile page loads with trial status", async ({ page }) => {
    await page.goto("/profile");
    await expect(page.getByTestId("profile-content")).toBeVisible();
    await expect(page.locator("h1")).toContainText("Debug User");
  });

  test("week page loads new overview widgets", async ({ page }) => {
    await bootstrapMockTelegram(page);
    await page.addInitScript(() => {
      (window as Window & typeof globalThis & { MOCK_WEEK_REPORT_OVERRIDE?: unknown }).MOCK_WEEK_REPORT_OVERRIDE = {
        report: { id: "week-report-id", report_type: "week_forecast", status: "completed" },
        chunks: [
          {
            id: "week-chunk-1",
            section: "focus",
            title: "Главный фокус недели",
            content: JSON.stringify([{ type: "paragraph", text: "Неделя просит держать ритм и не форсировать красные зоны." }]),
          },
        ],
      };
    });
    await page.goto("/week?mock=1");
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expect(page.getByTestId("week-overview-panel")).toBeVisible();
  });
});
