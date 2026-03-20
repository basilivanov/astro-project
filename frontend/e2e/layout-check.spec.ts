import { test, expect } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.describe("Layout Integrity Check", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test("should not display raw markdown tables or artifacts", async ({ page }) => {
    const layoutReport = {
      id: "layout-report-id",
      report_type: "natal_master",
      status: "completed",
      paid: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      client_id: "layout-client",
      client_name: "Layout Fixture",
      chunk_count: 1,
    };

    let fixtureMode: "empty" | "full" = "empty";

    await page.route("**/api/admin/reports?**", async (route) => {
      const payload = fixtureMode === "empty" ? [] : [layoutReport];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(payload),
      });
    });

    await page.route(`**/api/admin/reports/${layoutReport.id}**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          report: layoutReport,
          chunks: [
            {
              id: "chunk-1",
              section: "summary",
              title: "Сводка",
              status: "completed",
              order_index: 1,
              content: JSON.stringify([{ type: "paragraph", text: "Тестовый чистый контент" }]),
              created_at: new Date().toISOString(),
            },
          ],
          runs: [],
        }),
      });
    });

    fixtureMode = "empty";
    await page.goto("/admin/reports?show_test=true");
    await expect(page.getByTestId("admin-reports-page")).toBeVisible();
    const emptyCards = page.locator('[data-testid="admin-report-empty-card"]');
    await expect(page.locator('[data-testid="admin-report-link"]').first()).toHaveCount(0, { timeout: 20000 });
    await expect(emptyCards.first()).toBeVisible({ timeout: 20000 });

    fixtureMode = "full";
    await page.goto("/admin/reports?show_test=true");
    await expect(page.getByTestId("admin-reports-page")).toBeVisible();

    const queue = page.getByTestId("admin-reports-queue").first();
    await expect(queue).not.toHaveText(/Загрузка/);

    const reportLink = page.locator('[data-testid="admin-report-link"]:visible').first();
    await expect(reportLink).toBeVisible({ timeout: 20000 });
    await reportLink.click();
    await expectNoCrash(page);
    await expect(page).toHaveURL(new RegExp(`/admin/reports/${layoutReport.id}`));

    const textElements = page.locator('[data-testid="read-overview-panel"], [data-testid="report-table"], .markdown-body, .report-content');
    const texts = await textElements.allInnerTexts();
    const combinedText = texts.length > 0 ? texts.join("\n") : await page.locator("body").innerText();
    expect(combinedText).not.toContain("| --- |");
    expect(combinedText).not.toMatch(/\|\s*[А-Яа-яA-Za-z]+\s*\|\s*[А-Яа-яA-Za-z]+\s*\|/);
  });

  test("should have styles loaded", async ({ page }) => {
    await page.goto("/");
    const fontFamily = await page.evaluate(() => getComputedStyle(document.body).fontFamily);
    expect(fontFamily).not.toBe("");
    expect(fontFamily).not.toContain("Times New Roman");
    const smoothing = await page.evaluate(() => (getComputedStyle(document.body) as CSSStyleDeclaration & { webkitFontSmoothing?: string }).webkitFontSmoothing);
    expect(smoothing).toBe("antialiased");
  });
});
