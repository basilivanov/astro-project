import { test, expect } from "@playwright/test";
import { bootstrapMockTelegram, expectNoCrash } from "./utils";

test.describe("Admin Smoke Tests", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test("should load admin dashboard and queue", async ({ page }) => {
    await page.goto("/admin/dashboard");
    await expectNoCrash(page);
    await expect(page.getByTestId("admin-dashboard-page")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Дашборд/i })).toBeVisible();
    await expect(page.getByTestId("admin-dashboard-page").locator("text=В работе")).toBeVisible();
  });

  test("should load admin audit logs", async ({ page }) => {
    await page.goto("/admin/audit");
    await expect(page.getByRole("heading", { name: /Аудит/i })).toBeVisible();
    await expect(page.locator(".max-w-7xl").first()).toBeVisible();
  });

  test("should load admin health status", async ({ page }) => {
    await page.goto("/admin/health");
    await expect(page.getByTestId("admin-health-page")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Система/i })).toBeVisible();
  });

  test("should load admin clients list", async ({ page }) => {
    await page.goto("/admin/clients");
    await expect(page.getByRole("heading", { name: /Клиенты/i })).toBeVisible();
  });

  test("should load reports queue page", async ({ page }) => {
    await page.goto("/admin/reports");
    await expect(page.getByTestId("admin-reports-page")).toBeVisible();
    await expect(page.getByTestId("admin-reports-queue")).toBeVisible();
  });
});
