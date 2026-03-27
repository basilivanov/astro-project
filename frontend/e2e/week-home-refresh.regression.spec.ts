import { expect, test } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.describe("Home and Week refreshed surfaces", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page, {
      feedState: "ready",
      profileOverride: {
        full_name: "Debug User",
        birth_date: "2000-01-01",
        subscription_active_until: "2026-04-15T00:00:00.000Z",
      },
      feedOverride: {
        date: "Сегодня",
        moon_sign: "Овен",
        moon_phase: "Растущая Луна",
        moon_emoji: "🌙",
        general_vibe: "Фокус на рутине и стабильных шагах.",
        traffic_lights: { health: "green", money: "yellow", love: "red" },
        moon: { sign: "Овен", phase: "Растущая Луна", emoji: "🌙" },
        fast_hits: [
          { transit: "Venus", natal: "Venus", type: "Соединение", summary: "Окно для мягких договорённостей" },
          { transit: "Moon", natal: "Mars", type: "Трин", summary: "Хорошо быстро закрывать бытовые задачи" },
        ],
        personalization_level: "personalized_v2",
      },
    });

    await page.addInitScript(() => {
      (window as Window & { MOCK_WEEK_REPORT_OVERRIDE?: unknown }).MOCK_WEEK_REPORT_OVERRIDE = {
        report: { id: "week-1", report_type: "week_forecast", status: "completed" },
        chunks: [
          {
            id: "week-strategy",
            section: "week_strategy",
            title: "Стратегия недели",
            content: JSON.stringify([
              { type: "paragraph", text: "Неделя требует спокойного темпа и аккуратной расстановки приоритетов." },
            ]),
          },
        ],
      };
    });
  });

  test("home shows Today brief layout", async ({ page }) => {
    await page.goto("/?mock=1");
    await expectNoCrash(page);

    await expect(page.getByTestId("today-verdict")).toBeVisible();
    await expect(page.getByTestId("today-day-mode")).toBeVisible();
    await expect(page.getByTestId("traffic-lights")).toBeVisible();
    await expect(page.getByTestId("today-windows")).toBeVisible();
    await expect(page.getByTestId("today-actions")).toBeVisible();
    await expect(page.getByTestId("today-risks")).toBeVisible();
    await expect(page.getByTestId("today-explainability")).toBeVisible();
    await expect(page.getByTestId("today-cta-panel")).toBeVisible();
  });

  test("week shows tabs, traffic panel and premium renewal actions", async ({ page }) => {
    await page.goto("/week?mock=1");
    await expectNoCrash(page);
    await expect(page.getByTestId("week-page")).toBeVisible();
    await expect(page.getByTestId("week-top-tabs")).toBeVisible();

    await expect(page.getByTestId("week-tab-feed")).toContainText("Лента");
    await expect(page.getByTestId("week-tab-week")).toContainText("Неделя");
    await expect(page.getByTestId("week-tab-catalog")).toContainText("Каталог");
    await expect(page.getByTestId("week-traffic-light-panel")).toContainText("Недельный светофор");
    await expect(page.getByTestId("week-premium-panel")).toContainText("Продлите доступ");
    await expect(page.getByTestId("week-premium-renew")).toBeVisible();
    await expect(page.getByTestId("week-overview-panel")).toBeVisible();
  });
});
