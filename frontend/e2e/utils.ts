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

type TelegramWebAppHarnessOptions = {
  initData?: string;
  initDataUnsafe?: Record<string, unknown>;
  platform?: string;
  colorScheme?: "light" | "dark";
  viewportHeight?: number;
  viewportStableHeight?: number;
  themeParams?: Record<string, string>;
  sessionMockUser?: boolean;
};

type TelegramWebAppHarnessPayload = {
  initData: string;
  initDataUnsafe: Record<string, unknown>;
  platform: string;
  colorScheme: "light" | "dark";
  viewportHeight: number;
  viewportStableHeight: number;
  themeParams: Record<string, string>;
  sessionMockUser: boolean;
};

const DEFAULT_TELEGRAM_USER: TelegramSignedUser = {
  id: 123456789,
  first_name: "Debug",
  last_name: "User",
  username: "dev_user",
  language_code: "ru",
};

const DEFAULT_THEME_PARAMS = {
  bg_color: "#ffffff",
  secondary_bg_color: "#f4f4f5",
  text_color: "#111827",
  hint_color: "#6b7280",
  link_color: "#2563eb",
  button_color: "#2563eb",
  button_text_color: "#ffffff",
  header_bg_color: "#ffffff",
  accent_text_color: "#2563eb",
  section_bg_color: "#ffffff",
  section_header_text_color: "#111827",
  subtitle_text_color: "#6b7280",
  destructive_text_color: "#dc2626",
};

function buildTelegramWebAppHarnessPayload(options?: TelegramWebAppHarnessOptions): TelegramWebAppHarnessPayload {
  const initData = options?.initData ?? "123456789";
  const initDataUnsafe = {
    query_id: "debug-query-id",
    user: DEFAULT_TELEGRAM_USER,
    auth_date: Math.floor(Date.now() / 1000),
    ...(options?.initDataUnsafe ?? {}),
  };

  return {
    initData,
    initDataUnsafe,
    platform: options?.platform ?? "android",
    colorScheme: options?.colorScheme ?? "light",
    viewportHeight: options?.viewportHeight ?? 844,
    viewportStableHeight: options?.viewportStableHeight ?? options?.viewportHeight ?? 844,
    themeParams: {
      ...DEFAULT_THEME_PARAMS,
      ...(options?.themeParams ?? {}),
    },
    sessionMockUser: options?.sessionMockUser ?? initData === "123456789",
  };
}

export async function bootstrapTelegramWebApp(page: Page, options?: TelegramWebAppHarnessOptions) {
  const payload = buildTelegramWebAppHarnessPayload(options);

  await page.addInitScript((runtime) => {
    const telegramWindow = window as Window & typeof globalThis & {
      Telegram?: unknown;
      __TEST_TELEGRAM_RUNTIME__?: unknown;
      MOCK_INIT_DATA_OVERRIDE?: unknown;
      MOCK_USER_OVERRIDE?: unknown;
    };

    delete telegramWindow.MOCK_INIT_DATA_OVERRIDE;
    delete telegramWindow.MOCK_USER_OVERRIDE;

    if (runtime.sessionMockUser) {
      window.sessionStorage.setItem("mock_telegram_user", "1");
    } else {
      window.sessionStorage.removeItem("mock_telegram_user");
    }

    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => undefined,
      },
    });

    const webApp = {
      initData: runtime.initData,
      initDataUnsafe: runtime.initDataUnsafe,
      platform: runtime.platform,
      colorScheme: runtime.colorScheme,
      version: "7.7",
      isExpanded: false,
      viewportHeight: runtime.viewportHeight,
      viewportStableHeight: runtime.viewportStableHeight,
      headerColor: runtime.themeParams.header_bg_color,
      backgroundColor: runtime.themeParams.bg_color,
      themeParams: runtime.themeParams,
      ready: () => {},
      expand: () => {
        webApp.isExpanded = true;
      },
      close: () => {},
      sendData: () => {},
      enableClosingConfirmation: () => {},
      disableClosingConfirmation: () => {},
      onEvent: () => {},
      offEvent: () => {},
      setHeaderColor: (color: string) => {
        webApp.headerColor = color;
      },
      setBackgroundColor: (color: string) => {
        webApp.backgroundColor = color;
      },
      HapticFeedback: {
        impactOccurred: () => {},
        notificationOccurred: () => {},
        selectionChanged: () => {},
      },
      MainButton: {
        text: "",
        color: runtime.themeParams.button_color,
        textColor: runtime.themeParams.button_text_color,
        isVisible: false,
        isEnabled: true,
        show: () => {
          webApp.MainButton.isVisible = true;
        },
        hide: () => {
          webApp.MainButton.isVisible = false;
        },
        enable: () => {
          webApp.MainButton.isEnabled = true;
        },
        disable: () => {
          webApp.MainButton.isEnabled = false;
        },
        setText: (text: string) => {
          webApp.MainButton.text = text;
        },
        onClick: () => {},
        offClick: () => {},
      },
      BackButton: {
        isVisible: false,
        show: () => {
          webApp.BackButton.isVisible = true;
        },
        hide: () => {
          webApp.BackButton.isVisible = false;
        },
        onClick: () => {},
        offClick: () => {},
      },
    };

    telegramWindow.__TEST_TELEGRAM_RUNTIME__ = {
      initData: runtime.initData,
      user: runtime.initDataUnsafe.user,
    };
    telegramWindow.Telegram = { WebApp: webApp };
  }, payload);

  return payload;
}

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
  await bootstrapTelegramWebApp(page, {
    initData: payload.initData,
    initDataUnsafe: {
      user: payload.user,
    },
    sessionMockUser: false,
  });

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


type RenderedGateSummaryOptions = {
  flowId: string;
  surface: string;
  scenarioId: string;
  passMode: string;
  status: string;
  assertionClass: string;
  artifactRefs?: string[];
  details?: Record<string, unknown>;
};

type RenderedParityDetailsOptions = {
  counterpartPassMode: string;
  parityStatus: string;
  notes?: string[];
  sharedArtifactRefs?: string[];
  invariantGroups?: string[];
};

type StablePassMode = {
  key: string;
  channel: string;
  path: string;
};

function stableRenderedPassMode(value: string): StablePassMode {
  const normalized = value.trim().toLowerCase();
  if (["both", "both_pass_modes", "site_and_telegram", "site_web+telegram_webapp"].includes(normalized)) {
    return { key: "both", channel: "multi", path: "site_web+telegram_webapp" };
  }
  if (["site", "web", "site_web", "site/web"].includes(normalized)) {
    return { key: "site_web", channel: "web", path: "/" };
  }
  if (["telegram", "telegram_web", "telegram_webapp", "telegram/webapp"].includes(normalized)) {
    return { key: "telegram_webapp", channel: "telegram", path: "webapp" };
  }
  return { key: normalized || "site_web", channel: normalized || "web", path: normalized || "site_web" };
}

export function buildRenderedParityDetails(options: RenderedParityDetailsOptions) {
  return {
    counterpart_pass_mode: stableRenderedPassMode(options.counterpartPassMode),
    parity_status: options.parityStatus,
    notes: options.notes ?? [],
    shared_artifact_refs: options.sharedArtifactRefs ?? [],
    invariant_groups: options.invariantGroups ?? [],
  };
}

export async function writeRenderedGateSummary(options: RenderedGateSummaryOptions) {
  const artifactDir = process.env.RENDERED_GATE_ARTIFACT_DIR || "test-results/rendered-gate";
  const safeName = [options.flowId, options.surface, options.scenarioId]
    .map((part) => part.replace(/[\/\s]+/g, "-"))
    .join("__");
  const payload = {
    flow_id: options.flowId,
    surface: options.surface,
    scenario_id: options.scenarioId,
    pass_mode: stableRenderedPassMode(options.passMode),
    status: options.status,
    assertion_class: options.assertionClass,
    artifact_refs: options.artifactRefs ?? [],
    details: options.details ?? {},
    recorded_at: new Date().toISOString(),
  };

  await expect
    .poll(async () => {
      const fs = await import("node:fs/promises");
      await fs.mkdir(artifactDir, { recursive: true });
      const target = `${artifactDir}/${safeName}.json`;
      await fs.writeFile(target, `${JSON.stringify(payload, null, 2)}\n`, "utf-8");
      return target;
    })
    .toContain(`${safeName}.json`);
}
