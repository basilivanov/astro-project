import { expect, test, type Page } from "@playwright/test";

import {
  attachConsoleAndPageErrors,
  bootstrapMockTelegram,
  expectNoCrash,
  expectNoRouteHygieneIssues,
  mockCommonApis,
} from "./utils";

type StaticRouteCase = {
  path: string;
  name: string;
  ready: (page: Page) => Promise<void>;
  interact?: (page: Page) => Promise<void>;
  beforeGoto?: (page: Page) => Promise<void>;
};

const FATAL_TEXT_PATTERNS = [
  /application error/i,
  /unhandled runtime error/i,
  /failed to load/i,
  /something went wrong/i,
  /ошибка загрузки/i,
  /что-то пошло не так/i,
];

async function expectNoFatalState(page: Page) {
  await expectNoCrash(page);
  for (const pattern of FATAL_TEXT_PATTERNS) {
    await expect(page.getByText(pattern)).toHaveCount(0);
  }
}

async function mockProfileApis(page: Page, overrides?: Record<string, unknown>) {
  await page.route("**/api/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        full_name: "Route Smoke User",
        referral_code: "ROUTE123",
        balance: 2400,
        referrals_count: 7,
        is_partner: true,
        ...overrides,
      }),
    });
  });
}

const ROUTES: StaticRouteCase[] = [
  {
    path: "/support?mock=1&runtime=1",
    name: "support",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: /поддержка/i })).toBeVisible();
      await expect(page.getByPlaceholder(/опишите ситуацию подробнее/i)).toBeVisible();
    },
    interact: async (page) => {
      await page.getByRole("combobox").selectOption("billing");
      const message = page.getByPlaceholder(/опишите ситуацию подробнее/i);
      await message.fill("Нужна помощь с оплатой по Lane 1 route integrity.");
      await expect(message).toHaveValue(/Lane 1 route integrity/);
      await expect(page.getByRole("button", { name: /отправить/i })).toBeEnabled();
    },
    beforeGoto: async (page) => {
      await page.route("**/api/support/tickets", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
      });
    },
  },
  {
    path: "/prices",
    name: "prices",
    ready: async (page) => {
      await expect(page.getByRole("link", { name: /назад/i })).toBeVisible();
      await expect(page.getByText(/натальная карта/i).first()).toBeVisible();
    },
    interact: async (page) => {
      await page.getByRole("link", { name: /назад/i }).click();
      await page.waitForURL(/\/$/);
      await expect(page.locator("body")).toBeVisible();
    },
  },
  {
    path: "/share?mock=1&runtime=1",
    name: "share",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: /дари и получай/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /копировать ссылку/i })).toBeVisible();
    },
    interact: async (page) => {
      const openCalls: string[] = [];
      await page.evaluate(() => {
        (window as Window & typeof globalThis & { __shareCalls?: string[] }).__shareCalls = [];
        const originalOpen = window.open.bind(window);
        window.open = ((...args: Parameters<typeof window.open>) => {
          const calls = (window as Window & typeof globalThis & { __shareCalls?: string[] }).__shareCalls;
          calls?.push(String(args[0] ?? ""));
          return originalOpen("about:blank", "_blank");
        }) as typeof window.open;
      });
      await page.getByRole("button", { name: /копировать ссылку/i }).click();
      await expect(page.getByRole("button", { name: /скопировано/i })).toBeVisible();
      await page.getByRole("button", { name: /отправить в telegram/i }).click();
      openCalls.push(...(await page.evaluate(() => (window as Window & typeof globalThis & { __shareCalls?: string[] }).__shareCalls ?? [])));
      expect(openCalls.some((url) => url.includes("https://t.me/share/url?url="))).toBeTruthy();
    },
    beforeGoto: async (page) => {
      await mockProfileApis(page);
    },
  },
  {
    path: "/partner?mock=1&runtime=1",
    name: "partner",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: /кабинет партнера/i })).toBeVisible();
      await expect(page.getByText("2400")).toBeVisible();
    },
    interact: async (page) => {
      const payoutCta = page.getByRole("link", { name: /вывести средства/i });
      await expect(payoutCta).toHaveAttribute("href", "/support?topic=payout");
      await payoutCta.click();
      await page.waitForURL(/\/support\?topic=payout/);
      await expect(page.getByRole("combobox")).toHaveValue("payout");
    },
    beforeGoto: async (page) => {
      await mockProfileApis(page);
      await page.route("**/api/support/tickets", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
      });
    },
  },
  {
    path: "/legal/privacy",
    name: "legal_privacy",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: /политика обработки персональных данных/i })).toBeVisible();
      await expect(page.getByText(/оператором персональных данных является/i)).toBeVisible();
    },
    interact: async (page) => {
      await page.mouse.wheel(0, 1600);
      await expect(page.getByText(/трансграничная передача данных/i)).toBeVisible();
    },
  },
  {
    path: "/legal/terms",
    name: "legal_terms",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: /публичная оферта/i })).toBeVisible();
      await expect(page.getByText(/договором присоединения/i)).toBeVisible();
    },
    interact: async (page) => {
      await page.mouse.wheel(0, 1600);
      await expect(page.getByText(/разовые цифровые продукты/i)).toBeVisible();
    },
  },
  {
    path: "/legal/payments",
    name: "legal_payments",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: /оплата, отмена и возвраты/i })).toBeVisible();
      await expect(page.getByText(/условий оплаты, отмены и возвратов/i)).toBeVisible();
    },
    interact: async (page) => {
      await page.mouse.wheel(0, 1800);
      await expect(page.getByText(/платёжный провайдер/i)).toBeVisible();
    },
  },
  {
    path: "/legal/consent",
    name: "legal_consent",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: /согласие на обработку персональных данных/i })).toBeVisible();
      await expect(page.getByText(/кто запрашивает согласие/i)).toBeVisible();
    },
    interact: async (page) => {
      await page.mouse.wheel(0, 1800);
      await expect(page.getByText(/логируемый чекбокс/i)).toBeVisible();
    },
  },
];

test.describe("Consumer static route integrity", () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
    await mockCommonApis(page);
  });

  for (const route of ROUTES) {
    test(`${route.path} loads cleanly and preserves bounded interaction`, async ({ page }) => {
      const hygiene = attachConsoleAndPageErrors(page);
      await route.beforeGoto?.(page);

      await page.goto(route.path);
      await page.waitForLoadState("networkidle");
      await route.ready(page);
      await expectNoFatalState(page);
      await route.interact?.(page);
      await expectNoFatalState(page);
      await expectNoRouteHygieneIssues(route.path, hygiene);
      hygiene.dispose();
    });
  }
});
