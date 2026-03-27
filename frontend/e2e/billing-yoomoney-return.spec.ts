import { expect, test } from "@playwright/test";

const bootstrap = async (page: Parameters<typeof test>[0]["page"]) => {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("mock_telegram_user", "1");
    Object.assign(window, {
      MOCK_INIT_DATA_OVERRIDE: "billing-yoomoney-user",
      MOCK_USER_OVERRIDE: { id: 777001, first_name: "Billing", last_name: "Yoo" },
    });
  });
};

test.describe("Billing YooMoney return", () => {
  test("shows provider failure state and supports back button", async ({ page }) => {
    await bootstrap(page);
    await page.goto("/billing/complete?checkout=resume-yoo-1&status=failed&reason=provider_return_failed&mock=1&runtime=1");
    await expect(page.getByText(/ЮMoney вернул оплату с ошибкой/i)).toBeVisible();
    await page.getByRole("button", { name: /Назад/i }).click();
    await page.waitForURL(/\/reports\?mock=1&runtime=1/);
  });

  test("supports swipe-back affordance on provider failure state", async ({ page }) => {
    await bootstrap(page);
    await page.goto("/billing/complete?checkout=resume-yoo-2&status=failed&reason=provider_return_failed&mock=1&runtime=1");
    await expect(page.getByText(/ЮMoney вернул оплату с ошибкой/i)).toBeVisible();
    await page.getByTestId("billing-complete-swipe-back").click();
    await page.waitForURL(/\/reports\?mock=1&runtime=1/);
  });
});
