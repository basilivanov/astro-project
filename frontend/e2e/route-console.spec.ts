import { test, expect, type Page } from "@playwright/test";

import {
  attachConsoleAndPageErrors,
  bootstrapMockTelegram,
  expectNoCrash,
  expectNoRouteHygieneIssues,
  mockCommonApis,
} from "./utils";

type SmokeRoute = {
  path: string;
  name: string;
  beforeGoto?: (page: Page) => Promise<void>;
  ready: (page: Page) => Promise<void>;
};

const ROUTES: SmokeRoute[] = [
  {
    path: "/",
    name: "today",
    ready: async (page) => {
      await expect(page.locator("body")).toBeVisible();
    },
  },
  {
    path: "/week",
    name: "week",
    beforeGoto: async (page) => {
      await page.route("**/api/reports/my?*", async (route) => {
        await route.fulfill({ json: [{ id: "mock-week", report_type: "week_forecast", status: "completed" }] });
      });
      await page.route("**/api/reports/mock-week", async (route) => {
        await route.fulfill({ json: { report: { id: "mock-week", status: "completed" }, chunks: [] } });
      });
    },
    ready: async (page) => {
      await expect(page.locator("body")).toBeVisible();
    },
  },
  {
    path: "/reports/history",
    name: "history",
    ready: async (page) => {
      await expect(page.locator("body")).toBeVisible();
    },
  },
  {
    path: "/admin/health",
    name: "admin_health",
    ready: async (page) => {
      await expect(page.locator("h1")).toContainText("Система");
    },
  },
  {
    path: "/profile?mock=1",
    name: "profile",
    ready: async (page) => {
      await expect(page.getByTestId("profile-content")).toBeVisible();
    },
  },
  {
    path: "/profile/edit",
    name: "profile_edit",
    beforeGoto: async (page) => {
      await page.route("**/api/users/me", async (route) => {
        const request = route.request();
        if (request.method() === "GET") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              full_name: "Smoke User",
              birth_date: "1990-05-20",
              birth_time: "08:45",
              birth_time_known: true,
              birth_place: "Moscow, Russia",
              birth_lat: 55.7558,
              birth_lon: 37.6173,
              birth_timezone: "Europe/Moscow",
              sun_sign: "Taurus",
            }),
          });
          return;
        }
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
      });
      await page.route("**/api/geo/autocomplete?**", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
      });
      await page.route("**/api/geo/timezone?**", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ timezone_id: "Europe/Moscow" }) });
      });
    },
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "Настройки профиля" })).toBeVisible();
    },
  },
  {
    path: "/onboarding/profile",
    name: "onboarding_profile",
    beforeGoto: async (page) => {
      await page.route("**/api/users/me", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
      });
      await page.route("**/api/geo/autocomplete?**", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
      });
      await page.route("**/api/geo/timezone?**", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ timezone_id: "Europe/Moscow" }) });
      });
    },
    ready: async (page) => {
      await expect(page.getByRole("button", { name: "Начать путешествие" })).toBeVisible();
    },
  },
];

test.describe("Route Console Smoke", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
    await mockCommonApis(page);
  });

  for (const route of ROUTES) {
    test(`should load ${route.path} without errors`, async ({ page }) => {
      const hygiene = attachConsoleAndPageErrors(page);
      await route.beforeGoto?.(page);

      await page.goto(route.path);
      await page.waitForLoadState("networkidle");
      await expectNoCrash(page);
      await route.ready(page);

      await page.screenshot({ path: `test-results/screens/smoke-${route.name}.png` });
      await expectNoRouteHygieneIssues(route.path, hygiene);
      hygiene.dispose();
    });
  }

  test("should load /read/[id] without errors", async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);
    const reportId = "123e4567-e89b-12d3-a456-426614174000";

    await page.route("**/api/reports/*", async (route) => {
      if (route.request().url().includes(reportId)) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          json: {
            report: {
              id: reportId,
              report_type: "natal_master",
              status: "completed",
              client_name: "Smoke Client",
              created_at: new Date().toISOString(),
            },
            chunks: [
              {
                id: "c1",
                section: "intro",
                content: JSON.stringify([{ type: "paragraph", text: "Smoke test content" }]),
              },
            ],
          },
        });
        return;
      }
      await route.continue();
    });

    await page.goto(`/read/${reportId}`);
    await page.waitForLoadState("networkidle");
    await expectNoCrash(page);
    await expect(page.getByText("Smoke Client", { exact: true }).filter({ visible: true }).first()).toBeVisible();
    await page.screenshot({ path: "test-results/screens/smoke-read-report.png" });

    await expectNoRouteHygieneIssues(`/read/${reportId}`, hygiene);
    hygiene.dispose();
  });
});
