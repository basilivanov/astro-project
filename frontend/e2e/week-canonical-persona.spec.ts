import { expect, test, type ConsoleMessage } from "@playwright/test";

import { attachRuntimeErrorGuards, bootstrapMockTelegram, expectNoCrash, expectNoRuntimeErrors } from "./utils";
import { buildCanonicalTodayPersonaPack } from "./fixtures/canonical-personas";

const canonicalPersona = buildCanonicalTodayPersonaPack("CF-BE-001-baseline-exact-time");
const canonicalWeekReportId = "canonical-week-report";
const canonicalWeekBrief = canonicalPersona.week!.weekBrief;
const canonicalWeekMap = canonicalPersona.week!.weekMap;

function attachConsoleHygiene(page: Parameters<typeof test>[0]["page"], logs: string[]) {
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() === "error") {
      logs.push(`[console:error] ${msg.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    logs.push(`[pageerror] ${error.message}`);
  });
}

test.describe("Week surface canonical persona", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page, {
      profileOverride: canonicalPersona.profile,
      weekBriefOverride: canonicalWeekBrief,
      weekMapOverride: canonicalWeekMap,
    });

    await page.route("**/api/reports/my?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        json: [
          {
            id: canonicalWeekReportId,
            report_type: "week_forecast",
            status: "completed",
          },
        ],
      });
    });

    await page.route(`**/api/reports/${canonicalWeekReportId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        json: {
          report: {
            id: canonicalWeekReportId,
            report_type: "week_forecast",
            status: "completed",
          },
          week_brief: canonicalWeekBrief,
          week_brief_envelope: { status: "ready", data: canonicalWeekBrief, message: null },
          week_map: canonicalWeekMap,
          chunks: [
            {
              id: "strategy",
              section: "week_strategy",
              title: "Стратегия недели",
              content: "Держите опорный ритм и двигайте одно главное направление.",
            },
          ],
        },
      });
    });
  });

  test("renders truthful product-first Week path for canonical persona", async ({ page }) => {
    const hygiene = await attachRuntimeErrorGuards(page);
    await page.goto("/week");

    await expectNoCrash(page);
    await expect(page.getByTestId("week-map-surface")).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Неделя просит точной сборки и спокойного темпа");
    await expect(page.getByTestId("week-day-strip")).toBeVisible();
    await expect(page.getByTestId("week-day-strip")).toContainText("Соберите приоритеты");
    await expect(page.getByTestId("week-day-strip")).toContainText(/^[А-Я]{2},\s\d+\s[а-я]+/);
    await expect(page.getByTestId("week-day-drawer")).toContainText("Лучше для");
    await expect(page.getByTestId("week-domain-panel")).toContainText("Работа и деньги");
    await expect(page.getByTestId("week-domain-panel")).toContainText("78");
    await expect(page.getByTestId("week-domain-work_money")).toContainText("Работа и деньги");
    await expect(page.getByTestId("week-domain-work_money")).not.toContainText(/контакт/i);
    await expect(page.getByTestId("week-domain-work_money")).not.toContainText(/relationship|relationships/i);
    await expect(page.getByTestId("week-map-surface")).not.toContainText(/\ball_week\b/i);
    await expect(page.getByTestId("week-day-strip")).not.toContainText(/\bgreen\b|\byellow\b|\bred\b/i);
    await expect(page.getByTestId("week-day-strip")).not.toContainText(/светофор\s+money\s*:\s*green/i);
    await expect(page.getByTestId("week-day-strip")).not.toContainText(/explanation_astro|transit|natal|aspect/i);
    await expect(page.getByTestId("week-actions-list")).toContainText("Делайте один приоритетный ход за раз.");
    await expect(page.getByTestId("week-risks-list")).toContainText("Не пытайтесь закрыть то, что ещё не дозрело.");
    await expect(page.getByTestId("week-primary-cta")).toContainText("Открыть полный отчёт");
    await expect(page.getByTestId("week-fallback-note")).not.toBeVisible();
    await expectNoRuntimeErrors(hygiene, "week canonical persona render");
    hygiene.dispose();
  });

  test("opens explainability with visible persona-based factor details", async ({ page }) => {
    const logs: string[] = [];
    attachConsoleHygiene(page, logs);
    await page.goto("/week");

    const toggle = page.getByTestId("week-explainability-toggle");
    const details = page.getByTestId("week-explainability-details");

    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(details).toBeHidden();

    await toggle.click();

    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(details).toBeVisible();
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Почему неделя держится именно так");
    await expect(page.getByTestId("week-explainability-footnote")).toContainText("Ключевые причины уже встроены в домены недели");
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Учтено точное время рождения");
    await expect(page.getByTestId("week-explainability-panel")).not.toContainText("week_brief_v1");
    await expect(page.getByTestId("week-explainability-panel")).not.toContainText(/signal_only|structured_value|explanation_astro/i);

    await toggle.click();

    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(details).toBeHidden();
    expect(logs, `Found console or page errors on canonical /week persona path: ${logs.join(", ")}`).toHaveLength(0);
  });
});
