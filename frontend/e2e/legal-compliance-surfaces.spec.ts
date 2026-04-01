import { expect, test } from "@playwright/test";

import { bootstrapMockTelegram, expectNoCrash, mockCommonApis } from "./utils";

async function expectGlobalFooterLegal(page: import("@playwright/test").Page) {
  const footer = page.getByRole("contentinfo");

  await expect(
    footer.getByText(/ИП Иванов Василий Александрович/i),
  ).toBeVisible();
  await expect(footer.getByText(/ИНН 774300091472/i)).toBeVisible();
  await expect(footer.getByText(/ОГРНИП 313574924700061/i)).toBeVisible();
  await expect(footer.getByRole("link", { name: "Оферта" })).toHaveAttribute(
    "href",
    "/legal/terms",
  );
  await expect(
    footer.getByRole("link", { name: "Privacy / ПДн" }),
  ).toHaveAttribute("href", "/legal/privacy");
  await expect(footer.getByRole("link", { name: "Consent" })).toHaveAttribute(
    "href",
    "/legal/consent",
  );
  await expect(
    footer.getByRole("link", { name: "Оплата и возвраты" }),
  ).toHaveAttribute("href", "/legal/payments");
}

test.describe("Legal compliance surfaces", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
    await mockCommonApis(page);
  });

  test("onboarding consent block exposes legal links and blocks submit when unchecked", async ({
    page,
  }) => {
    await page.route("**/api/geo/autocomplete?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "moscow",
            name: "Moscow",
            admin1: "Moscow",
            country: "Russia",
            lat: 55.7558,
            lon: 37.6173,
            label: "Moscow, Russia",
          },
        ]),
      });
    });

    await page.route("**/api/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      });
    });

    await page.goto("/onboarding/profile");
    await expectNoCrash(page);

    await page.getByRole("button", { name: "Начать путешествие" }).click();
    await page.getByPlaceholder("Ваше имя").fill("Compliance User");
    await page.locator('input[type="date"]').fill("1994-04-12");
    await page.getByRole("button", { name: "Далее" }).click();
    await page.locator('input[type="time"]').fill("08:30");
    await page.getByRole("button", { name: "Далее" }).click();
    await page.getByPlaceholder("Начните вводить город...").fill("Moscow");
    await page.getByRole("button", { name: /Moscow, Russia/i }).click();

    await expect(
      page.getByText(/даю согласие на обработку данных/i),
    ).toBeVisible();
    await expect(
      page.getByText(/Актуальный публичный домен: app\.astrograce\.ru/i),
    ).toBeVisible();
    const legalSection = page.getByRole("main").getByText(/ИП Иванов Василий Александрович/i).first();
    await expect(legalSection).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Оферта" }).last(),
    ).toHaveAttribute("href", "/legal/terms");
    await expect(
      page.getByRole("link", { name: "Privacy / ПДн" }).last(),
    ).toHaveAttribute("href", "/legal/privacy");
    await expect(
      page.getByRole("link", { name: "Consent" }).last(),
    ).toHaveAttribute("href", "/legal/consent");
    await expect(
      page.getByRole("link", { name: "Payments & refunds" }),
    ).toHaveAttribute("href", "/legal/payments");

    const consentCheckbox = page.locator('input[type="checkbox"]').last();
    await consentCheckbox.uncheck();
    await expect(
      page.getByRole("button", { name: "Рассчитать карту" }),
    ).toBeDisabled();
    await consentCheckbox.check();
    await expect(
      page.getByRole("button", { name: "Рассчитать карту" }),
    ).toBeEnabled();
  });

  test("profile exposes legal block and global footer legal identity", async ({
    page,
  }) => {
    await page.goto("/profile?mock=1");
    await expectNoCrash(page);

    await expect(
      page.getByRole("region", { name: "Юридическая информация" }),
    ).toBeVisible();
    await expect(page.getByText(/^Legal$/)).toBeVisible();
    await expectGlobalFooterLegal(page);
  });

  test("create payment flow keeps visible legal context in global footer", async ({
    page,
  }) => {
    await page.goto("/create?type=year_forecast&mock=1&runtime=1");
    await expectNoCrash(page);

    await expect(page.getByTestId("create-page")).toBeVisible();
    await expect(page.getByTestId("create-footer-cta")).toBeVisible();
    await expectGlobalFooterLegal(page);
  });
});
