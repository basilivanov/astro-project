import { expect, type Page } from "@playwright/test";

type BootstrapOptions = {
  guest?: boolean;
  feedState?: "ready" | "fallback" | "empty" | "error";
  feedOverride?: Record<string, unknown>;
  profileOverride?: Record<string, unknown>;
  weekBriefOverride?: Record<string, unknown>;
  weekMapOverride?: Record<string, unknown>;
};

export type RouteHygiene = {
  logs: string[];
  dispose: () => void;
};

type TelegramSignedUser = {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
};

type SignedTelegramBootstrapOptions = {
  user?: TelegramSignedUser;
  authDate?: number;
  startParam?: string;
};

async function sha256Hex(message: string) {
  const crypto = await import("node:crypto");
  return crypto.createHash("sha256").update(message).digest("hex");
}

async function hmacSha256Hex(key: Buffer, message: string) {
  const crypto = await import("node:crypto");
  return crypto.createHmac("sha256", key).update(message).digest("hex");
}

async function hmacSha256Buffer(key: string | Buffer, message: string) {
  const crypto = await import("node:crypto");
  return crypto.createHmac("sha256", key).update(message).digest();
}

export async function buildSignedTelegramInitData(options?: SignedTelegramBootstrapOptions) {
  const user: TelegramSignedUser = options?.user ?? {
    id: 42424242,
    first_name: "Signed",
    last_name: "User",
    username: "signed_user",
    language_code: "ru",
  };

  const authDate = options?.authDate ?? Math.floor(Date.now() / 1000);
  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!botToken) {
    throw new Error("TELEGRAM_BOT_TOKEN is required for signed Telegram E2E lane");
  }

  const pairs = [
    ["auth_date", String(authDate)],
    ["query_id", await sha256Hex(`q:${user.id}:${authDate}`)],
    ["user", JSON.stringify(user)],
  ] as Array<[string, string]>;

  if (options?.startParam) {
    pairs.push(["start_param", options.startParam]);
  }

  const dataCheckString = [...pairs]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");

  const secretKey = await hmacSha256Buffer("WebAppData", botToken);
  const hash = await hmacSha256Hex(secretKey, dataCheckString);
  const searchParams = new URLSearchParams();
  for (const [key, value] of pairs) {
    searchParams.append(key, value);
  }
  searchParams.append("hash", hash);

  return {
    initData: searchParams.toString(),
    user,
  };
}

export async function bootstrapSignedTelegram(page: Page, options?: SignedTelegramBootstrapOptions) {
  const payload = await buildSignedTelegramInitData(options);
  await page.addInitScript((runtime) => {
    delete (window as Window & typeof globalThis & { MOCK_INIT_DATA_OVERRIDE?: unknown }).MOCK_INIT_DATA_OVERRIDE;
    delete (window as Window & typeof globalThis & { MOCK_USER_OVERRIDE?: unknown }).MOCK_USER_OVERRIDE;
    window.sessionStorage.removeItem("mock_telegram_user");
    (window as Window & typeof globalThis & { __TEST_TELEGRAM_RUNTIME__?: unknown }).__TEST_TELEGRAM_RUNTIME__ = runtime;
    (window as Window & typeof globalThis & { Telegram?: unknown }).Telegram = {
      WebApp: {
        initData: runtime.initData,
        ready: () => {},
        expand: () => {},
        close: () => {},
        headerColor: "#ffffff",
        backgroundColor: "#ffffff",
        initDataUnsafe: {
          user: runtime.user,
        },
      },
    };
  }, payload);

  return payload;
}

export async function bootstrapMockTelegram(page: Page, options?: BootstrapOptions) {
  await page.addInitScript((payload) => {
    const { guest, feedState, feedOverride, profileOverride, weekBriefOverride, weekMapOverride } = payload as BootstrapOptions;

    if (guest) {
      window.sessionStorage.removeItem("mock_telegram_user");
      delete (window as Window & typeof globalThis & { Telegram?: unknown }).Telegram;
      return;
    }

    window.sessionStorage.setItem("mock_telegram_user", "1");
    (window as Window & typeof globalThis & { Telegram?: unknown; MOCK_FEED_STATE?: unknown; MOCK_FEED_OVERRIDE?: unknown; MOCK_PROFILE_OVERRIDE?: unknown }).Telegram = {
      WebApp: {
        initData: "123456789",
        ready: () => {},
        expand: () => {},
        close: () => {},
        headerColor: "#ffffff",
        backgroundColor: "#ffffff",
        initDataUnsafe: {
          user: { id: 123456789, first_name: "Debug", last_name: "User" },
        },
      },
    };

    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => undefined,
      },
    });

    const w = window as Window & typeof globalThis & {
      MOCK_FEED_STATE?: unknown;
      MOCK_FEED_OVERRIDE?: unknown;
      MOCK_PROFILE_OVERRIDE?: unknown;
      MOCK_WEEK_BRIEF_OVERRIDE?: unknown;
      MOCK_WEEK_MAP_OVERRIDE?: unknown;
    };

    if (feedState) {
      w.MOCK_FEED_STATE = feedState;
    }
    if (feedOverride) {
      w.MOCK_FEED_OVERRIDE = feedOverride;
    }
    if (profileOverride) {
      w.MOCK_PROFILE_OVERRIDE = profileOverride;
    }
    if (weekBriefOverride) {
      w.MOCK_WEEK_BRIEF_OVERRIDE = weekBriefOverride;
    }
    if (weekMapOverride) {
      w.MOCK_WEEK_MAP_OVERRIDE = weekMapOverride;
    }
  }, options ?? {});
}

export function attachConsoleAndPageErrors(page: Page, options?: { includeWarnings?: boolean }): RouteHygiene {
  const logs: string[] = [];
  const includeWarnings = options?.includeWarnings ?? false;

  const onConsole = (msg: { type: () => string; text: () => string }) => {
    const type = msg.type();
    if (type === "error" || (includeWarnings && type === "warning")) {
      logs.push(`[console:${type}] ${msg.text()}`);
    }
  };

  const onPageError = (error: Error) => {
    logs.push(`[pageerror] ${error.message}`);
  };

  page.on("console", onConsole);
  page.on("pageerror", onPageError);

  return {
    logs,
    dispose: () => {
      page.off("console", onConsole);
      page.off("pageerror", onPageError);
    },
  };
}

export async function mockCommonApis(page: Page) {
  await page.route("**/api/analytics/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  await page.route("**/api/feedback/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });
}

export async function expectNoCrash(page: Page) {
  await expect(page.locator("body")).toBeVisible();
  await expect(page.locator("text=Application error")).toHaveCount(0);
  await expect(page.locator("text=Unhandled Runtime Error")).toHaveCount(0);
}

export async function expectNoRouteHygieneIssues(route: string, hygiene: RouteHygiene) {
  expect(hygiene.logs, `Found console or page errors on ${route}: ${hygiene.logs.join(", ")}`).toHaveLength(0);
}


export async function attachRuntimeErrorGuards(page: Page) {
  return attachConsoleAndPageErrors(page);
}

export async function expectNoRuntimeErrors(logs: string[] | RouteHygiene, label: string) {
  const entries = Array.isArray(logs) ? logs : logs.logs;
  expect(entries, `Found runtime errors on ${label}: ${entries.join(", ")}`).toHaveLength(0);
}
