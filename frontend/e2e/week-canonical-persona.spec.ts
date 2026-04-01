import { expect, test, type ConsoleMessage } from "@playwright/test";

import { attachRuntimeErrorGuards, bootstrapMockTelegram, expectNoCrash, expectNoRuntimeErrors } from "./utils";
import { buildCanonicalTodayPersonaPack } from "./fixtures/canonical-personas";

const canonicalPersona = buildCanonicalTodayPersonaPack("CF-BE-001-baseline-exact-time");
const canonicalWeekReportId = "canonical-week-report";
const canonicalWeekBrief = canonicalPersona.weekBrief!;
const canonicalWeekMap = {
  thesis: "Неделя держит курс на одно главное направление.",
  theme: "Соберите опорный ритм и не распыляйтесь на параллельные обещания.",
  day_cards: [
    {
      weekday: "Понедельник",
      date: "2026-03-23",
      mode: "GREEN",
      headline: "Стартуйте с одной ключевой задачи.",
      best_for: ["План недели", "Главный рабочий блок"],
      avoid: ["Лишние согласования"],
      score: 0.22,
    },
    {
      weekday: "Вторник",
      date: "2026-03-24",
      mode: "YELLOW",
      headline: "Проверяйте формулировки и стыки.",
      best_for: ["Редактура", "Короткие встречи"],
      avoid: ["Импульсивные ответы"],
      score: 0.95,
    },
  ],
  domains: { work: 74, relationships: 59 },
  major_factors: [
    { label: "Опорный ритм", category: "timing", impact_pct: 42, explanation: "Неделя лучше складывается, когда вы повторяете один рабочий ритм вместо резких переключений.", confidence: 0.84 },
  ],
  actions: ["Закрыть один глубокий рабочий цикл до середины недели", "Свести договорённости к коротким и проверяемым пунктам"],
  risks: ["Не обещайте больше, чем реально удержать в темпе недели"],
  deep_sections: ["strategy"],
  explainability: { confidence: 0.84, used_exact_birth_time: true },
  timezone: "Europe/London",
  location: "London, UK",
  week_start: "2026-03-23",
};

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
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Неделя держит курс на одно главное направление.");
    await expect(page.getByTestId("week-day-grid")).toContainText("Стартуйте с одной ключевой задачи.");
    await expect(page.getByTestId("week-domain-panel")).toContainText("Работа и деньги");
    await expect(page.getByTestId("week-domain-panel")).toContainText("74");
    await expect(page.getByTestId("week-actions-list")).toContainText("Закрыть один глубокий рабочий цикл до середины недели");
    await expect(page.getByTestId("week-risks-list")).toContainText("Не обещайте больше, чем реально удержать в темпе недели");
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
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Почему карта именно такая");
    await expect(page.getByTestId("week-factor-1")).toContainText("Опорный ритм");
    await expect(page.getByTestId("week-factor-1")).toContainText("Неделя лучше складывается, когда вы повторяете один рабочий ритм вместо резких переключений.");
    await expect(page.getByTestId("week-explainability-panel")).toContainText("Учтено точное время рождения");
    await expect(page.getByTestId("week-explainability-panel")).not.toContainText("week_brief_v1");

    await toggle.click();

    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(details).toBeHidden();
    expect(logs, `Found console or page errors on canonical /week persona path: ${logs.join(", ")}`).toHaveLength(0);
  });
});
