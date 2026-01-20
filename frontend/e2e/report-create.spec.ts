import { expect, test, type Page } from "@playwright/test";

const baseUrl = process.env.E2E_BASE_URL || "http://localhost:3000";
const baseOrigin = new URL(baseUrl).origin;

type ErrorLog = string[];

const attachGuards = (page: Page): ErrorLog => {
  const errors: ErrorLog = [];

  page.on("pageerror", (error) => {
    if (error.message.includes("Invalid or unexpected token")) return;
    errors.push(`pageerror: ${error.message}`);
  });

  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (text.includes("Extra attributes from the server")) return;
    if (text.includes("Failed to fetch RSC payload")) return;
    errors.push(`console: ${text}`);
  });

  page.on("response", (response) => {
    const url = response.url();
    if (!url.startsWith(baseOrigin)) return;
    if (url.includes("/_next/static/webpack/") && url.includes("hot-update")) {
      return;
    }
    const type = response.request().resourceType();
    if (!["document", "xhr", "fetch"].includes(type)) return;
    const status = response.status();
    if (status >= 400) {
      errors.push(`http ${status} ${type} ${url}`);
    }
  });

  return errors;
};

const failIfErrors = (errors: ErrorLog) => {
  if (errors.length === 0) return;
  throw new Error(errors.join("\n"));
};

test("create report without UI lock", async ({ page }) => {
  const errors = attachGuards(page);

  const createResponse = await page.request.post(
    `${baseOrigin}/api/admin/clients`,
    {
      data: {
        client_name: "Playwright Client",
        birth_date: "2000-01-01T12:00:00",
        birth_location: "Sochi, Russia",
      },
    }
  );
  if (!createResponse.ok()) {
    throw new Error(`Client create failed: ${createResponse.status()}`);
  }
  const client = await createResponse.json();
  const clientId = client.id;

  await page.goto(`/clients/${clientId}`);
  await page.waitForLoadState("domcontentloaded");

  const reportForm = page.locator("form", {
    has: page.getByRole("button", { name: "Сгенерировать отчет" }),
  });
  await reportForm.getByRole("button", { name: "Сгенерировать отчет" }).waitFor();

  const reportResponse = await page.request.post(
    `${baseOrigin}/api/workflows/report`,
    {
      data: {
        client_id: clientId,
        client_name: "Playwright Client",
        birth_date: "2000-01-01T12:00:00",
        birth_location: "Sochi, Russia",
        report_type: "horary_answer",
        question: "Will this test pass?",
        include_fixed_stars: false,
        llm_mode: "fallback",
      },
    }
  );
  if (!reportResponse.ok()) {
    throw new Error(`Report create failed: ${reportResponse.status()}`);
  }
  const report = await reportResponse.json();
  const reportId = report.report_id;

  await page.goto(`/reports/${reportId}`);
  await page.waitForLoadState("domcontentloaded");
  await expect(page).toHaveURL(/\/reports\//);
  await expect(
    page.getByRole("button", { name: "Сгенерировать все" })
  ).toBeVisible();

  failIfErrors(errors);
});
