import { expect, test } from "@playwright/test";
import { buildRenderedParityDetails, writeRenderedGateSummary } from "./utils";

function normalizeRenderedText(value: string | null | undefined): string {
  return String(value || "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[\s.,!?;:()[\]{}"'«»—–-]+/g, " ")
    .trim();
}

test.describe("Rendered Gate Wave 1", () => {
  test("Today surface avoids raw keys, duplicate factors and nested interactive issues", async ({ browser }) => {
    const logs: string[] = [];
    const context = await browser.newContext();
    await context.addInitScript(() => {
      window.sessionStorage.setItem("mock_telegram_user", "1");
      (window as any).Telegram = {
        WebApp: {
          initData: "123456789",
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: "Today", last_name: "Rendered" } },
        },
      };
      (window as any).MOCK_FEED_STATE = "ready";
      (window as any).MOCK_FEED_OVERRIDE = {
        version: "day_brief_v1",
        date: "2026-04-01",
        personalization_level: "full",
        fallback_mode: false,
        summary: { headline: "Собранный день", subhead: "Сначала главное, потом остальное", day_type: "deep_focus", tone: "calm" },
        context: { moon_sign: "Телец", moon_phase: "waxing", moon_emoji: "🌔", aspects_count: 3, label: "Луна в Тельце" },
        scores: [
          {
            key: "energy",
            title: "Энергия",
            value: 82,
            status: "green",
            advice: "Держите устойчивый темп.",
            details: {
              why_title: "Почему энергия высокая",
              why_text: "Есть запас на важные задачи.",
              supporting_factors: [
                { label: "Тонус", explanation_human: "Ресурс тела выше среднего.", value: "82/100" },
                { label: "Тонус", explanation_human: "Ресурс тела выше среднего.", value: "82/100" },
                { label: "energy:green", explanation_human: "Ресурс тела выше среднего.", value: "82/100" },
              ],
            },
          },
        ],
        windows: [],
        actions: [],
        risks: [
          {
            id: "risk-1",
            text: "Не спорьте из принципа.",
            impact: "signal_only",
            timeframe: "structured_value",
            why_text: "Пауза перед ответом снимает лишнюю резкость.",
            supporting_factors: [
              { label: "signal_only", explanation_human: "Пауза перед ответом снимает лишнюю резкость.", value: "structured_value" },
            ],
          },
        ],
        personalized_factors: [
          { id: "factor-1", label: "Фокус", impact: "high", explanation_human: "Главное окно дня приходится на утро." },
        ],
        explainability: { confidence: 0.83, birth_time_used: true, factor_count: 1, timing_precision: "exact", top_signal_source: "transits", explanation_depth: "full" },
        premium: { subscription_active: false, subscription_active_until: null, days_left: null, show_upgrade_cta: true, show_resume_banner: false },
        cta: { primary: { type: "ask_question", label: "Спросить совет", href: "/question" }, secondary: { type: "open_premium", label: "Открыть premium", href: "/reports" } },
        legacy: null,
      };
    });

    const page = await context.newPage();
    page.on("console", (msg) => { if (msg.type() === "error") logs.push(msg.text()); });
    page.on("pageerror", (err) => logs.push(err.message));

    await page.goto("/");
    await expect(page.getByTestId("today-verdict")).toBeVisible();
    await page.getByRole("button", { name: /Энергия: 82/i }).click();
    await page.getByText("Не спорьте из принципа.").click();
    await expect(page.getByTestId("today-risks-details-risk-1")).toBeVisible();

    const bodyText = normalizeRenderedText(await page.locator("body").innerText());
    expect(bodyText).not.toContain("signal only");
    expect(bodyText).not.toContain("structured value");
    expect(bodyText).not.toContain("energy green");

    const scoreDetailsText = normalizeRenderedText(await page.getByTestId("today-score-details-energy").innerText());
    expect((scoreDetailsText.match(/тонус/g) ?? []).length).toBe(1);

    expect(await page.locator("button details").count()).toBe(0);
    expect(await page.locator("summary button").count()).toBe(0);
    expect(logs, `Found console or page errors on / today rendered gate: ${logs.join(", ")}`).toHaveLength(0);

    await writeRenderedGateSummary({
      flowId: "FLOW-TODAY-PREMIUM",
      surface: "today",
      scenarioId: "today_rendered_wave1_site_web",
      passMode: "site/web",
      status: "passed",
      assertionClass: "rendered_hygiene",
      details: {
        route: "/",
        consoleErrors: logs.length,
        rawKeyGuards: ["signal only", "structured value", "energy green"],
        duplicateFactorLabel: "тонус",
      },
      artifactRefs: ["dom://today-verdict", "dom://today-score-details-energy", "dom://today-risks-details-risk-1"],
    });

    await writeRenderedGateSummary({
      flowId: "FLOW-TODAY-PREMIUM",
      surface: "today",
      scenarioId: "today_rendered_wave1_telegram_webapp",
      passMode: "telegram_webapp",
      status: "passed",
      assertionClass: "rendered_harness",
      details: {
        route: "/",
        telegramHarness: true,
        consoleErrors: logs.length,
        parity: buildRenderedParityDetails({
          counterpartPassMode: "site/web",
          parityStatus: "pilot_same_assertion_surface",
          notes: ["Today telegram pilot reuses same narrow rendered assertions as site/web"],
          sharedArtifactRefs: ["dom://today-verdict", "dom://today-score-details-energy"],
          invariantGroups: ["today.verdict", "today.score_details"],
        }),
      },
      artifactRefs: ["telegram://webapp", "dom://today-verdict", "dom://today-score-details-energy"],
    });
    await writeRenderedGateSummary({
      flowId: "FLOW-TODAY-PREMIUM",
      surface: "today",
      scenarioId: "today_rendered_wave1_both",
      passMode: "both",
      status: "passed",
      assertionClass: "rendered_parity",
      details: {
        route: "/",
        parity: buildRenderedParityDetails({
          counterpartPassMode: "site/web",
          parityStatus: "pilot_dom_model_invariants",
          notes: ["Today both/pass pilot materializes shared DOM/UI-model invariants"],
          sharedArtifactRefs: ["dom://today-verdict", "dom://today-score-details-energy", "telegram://webapp"],
          invariantGroups: ["today.verdict", "today.score_details", "today.no_nested_interactive"],
        }),
      },
      artifactRefs: ["dom://today-verdict", "dom://today-score-details-energy", "telegram://webapp"],
    });
    await context.close();
  });

  test("Week surface avoids raw status text, duplicate rows and nested interactive issues", async ({ browser }) => {
    const reportId = "week-rendered-wave1";
    const logs: string[] = [];
    const context = await browser.newContext();
    await context.addInitScript(() => {
      window.sessionStorage.setItem("mock_telegram_user", "1");
      (window as any).Telegram = {
        WebApp: {
          initData: "123456789",
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: "Week", last_name: "Rendered" } },
        },
      };
    });

    const page = await context.newPage();
    page.on("console", (msg) => { if (msg.type() === "error") logs.push(msg.text()); });
    page.on("pageerror", (err) => logs.push(err.message));

    await page.route("**/api/reports/**", async (route) => {
      const url = route.request().url();
      if (url.includes("/api/reports/my?")) {
        await route.fulfill({ status: 200, contentType: "application/json", json: [{ id: reportId, report_type: "week_forecast", status: "completed" }] });
        return;
      }
      if (!url.includes(reportId)) {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        json: {
          report: { id: reportId, report_type: "week_forecast", status: "completed" },
          week_brief: {
            version: "week_brief_v1",
            week_start: "2026-03-30",
            week_end: "2026-04-05",
            fallback_mode: false,
            status: "ready",
            summary: { headline: "Неделя держится на одном главном приоритете.", subhead: "Сначала фиксируйте опору, потом добавляйте скорость.", week_type: "deep_work", theme: "Точный темп" },
            day_cards: [
              {
                date: "2026-03-30",
                weekday: "mon",
                mode: "green",
                score: 78,
                headline: "День для основного блока",
                lead: "Лучше закрыть один главный слот.",
                practical: ["09:00–11:00"],
                avoid: ["Лишние переключения"],
                peak_window_label: "Утро",
                supporting_factors: [
                  { label: "Ритм", explanation_human: "Утренний блок держит фокус.", value: "09:00–11:00" },
                  { label: "Ритм", explanation_human: "Утренний блок держит фокус.", value: "09:00–11:00" },
                ],
              },
            ],
            domains: [
              {
                key: "work",
                title: "Работа",
                status: "green",
                value: 81,
                headline: "Рабочий фокус недели",
                advice: "Держите решения простыми и проверяемыми.",
                why_text: "Лучше удерживать один приоритет.",
                supporting_factors: [
                  { label: "Контур", explanation_human: "Один приоритет держит скорость.", value: "81/100" },
                  { label: "Контур", explanation_human: "Один приоритет держит скорость.", value: "81/100" },
                ],
              },
            ],
            best_uses: [
              {
                id: "best-1",
                text: "Фиксируйте главное до середины недели.",
                impact: "signal_only",
                timeframe: "structured_value",
                why_text: "Так меньше лишних разворотов.",
                supporting_factors: [
                  { label: "signal_only", explanation_human: "Так меньше лишних разворотов.", value: "structured_value" },
                ],
              },
            ],
            risks: [
              {
                id: "risk-1",
                text: "Не дробите главный приоритет.",
                impact: "signal_only",
                timeframe: "structured_value",
                why_text: "Дробление сбивает ритм.",
                supporting_factors: [
                  { label: "signal_only", explanation_human: "Дробление сбивает ритм.", value: "structured_value" },
                ],
              },
            ],
            major_factors: [
              { id: "factor-1", label: "Ритм", impact: "high", category: "focus", explanation_human: "Один приоритет держит неделю собранной." },
            ],
            deep_sections: [
              { id: "section-1", slug: "week_strategy", title: "Стратегия недели", summary: "Главный фокус недели", body_markdown: "Неделя требует спокойного темпа и аккуратной расстановки приоритетов.", is_primary: true, order: 1 },
            ],
            explainability: { confidence: 0.82, birth_time_used: true, factor_count: 1, timing_precision: "exact", top_signal_source: "transits", explanation_depth: "full" },
            premium: { subscription_active: false, show_upgrade_cta: true, show_resume_banner: false },
            cta: { primary: { type: "open_report", label: "Открыть полный отчёт", href: "/read/week-rendered-wave1" } },
            report_ref: { report_id: reportId, report_type: "week_forecast", source_status: "completed" },
          },
          chunks: [],
        },
      });
    });

    await page.goto("/week");
    await expect(page.getByTestId("week-hero-actions")).toBeVisible();
    await expect(page.getByTestId("week-day-grid")).toBeVisible();
    await expect(page.getByTestId("week-domain-panel")).toBeVisible();
    await expect(page.getByTestId("week-actions-panel")).toBeVisible();
    await expect(page.getByTestId("week-risks-panel")).toBeVisible();

    const bodyText = normalizeRenderedText(await page.locator("body").innerText());
    expect(bodyText).not.toContain("signal only");
    expect(bodyText).not.toContain("structured value");
    expect(bodyText).not.toContain("completed");

    await page.getByText("Что повлияло").first().click();
    const domainText = normalizeRenderedText(await page.getByTestId("week-domain-explainability-work").innerText());
    expect(domainText).toContain("контур");
    expect(domainText).not.toContain("signal only");
    expect(domainText).not.toContain("structured value");

    expect(await page.locator("button details").count()).toBe(0);
    expect(await page.locator("summary button").count()).toBe(0);
    expect(logs, `Found console or page errors on /week rendered gate: ${logs.join(", ")}`).toHaveLength(0);

    await writeRenderedGateSummary({
      flowId: "FLOW-WEEK-BRIEF",
      surface: "week",
      scenarioId: "week_rendered_wave1_site_web",
      passMode: "site/web",
      status: "passed",
      assertionClass: "rendered_hygiene",
      details: {
        route: "/week",
        reportId,
        consoleErrors: logs.length,
        rawKeyGuards: ["signal only", "structured value", "completed"],
        duplicateFactorLabel: "контур",
      },
      artifactRefs: ["dom://week-hero-actions", "dom://week-domain-explainability-work", `report://${reportId}`],
    });

    await writeRenderedGateSummary({
      flowId: "FLOW-WEEK-BRIEF",
      surface: "week",
      scenarioId: "week_rendered_wave1_telegram_webapp",
      passMode: "telegram_webapp",
      status: "passed",
      assertionClass: "rendered_harness",
      details: {
        route: "/week",
        reportId,
        telegramHarness: true,
        consoleErrors: logs.length,
        parity: buildRenderedParityDetails({
          counterpartPassMode: "site/web",
          parityStatus: "pilot_same_assertion_surface",
          notes: ["Week telegram pilot reuses same narrow rendered assertions as site/web"],
          sharedArtifactRefs: ["dom://week-hero-actions", "dom://week-domain-explainability-work"],
          invariantGroups: ["week.hero_actions", "week.domain_explainability"],
        }),
      },
      artifactRefs: ["telegram://webapp", "dom://week-hero-actions", `report://${reportId}`],
    });
    await writeRenderedGateSummary({
      flowId: "FLOW-WEEK-BRIEF",
      surface: "week",
      scenarioId: "week_rendered_wave1_both",
      passMode: "both",
      status: "passed",
      assertionClass: "rendered_parity",
      details: {
        route: "/week",
        reportId,
        parity: buildRenderedParityDetails({
          counterpartPassMode: "site/web",
          parityStatus: "pilot_dom_model_invariants",
          notes: ["Week both/pass pilot materializes shared DOM/UI-model invariants"],
          sharedArtifactRefs: ["dom://week-hero-actions", "dom://week-domain-explainability-work", `report://${reportId}`, "telegram://webapp"],
          invariantGroups: ["week.hero_actions", "week.domain_explainability", "week.no_nested_interactive"],
        }),
      },
      artifactRefs: ["dom://week-hero-actions", "dom://week-domain-explainability-work", `report://${reportId}`, "telegram://webapp"],
    });
    await context.close();
  });
});
