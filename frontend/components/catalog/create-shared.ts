import type { RuntimeFeatureFlags } from "../../lib/product-billing";

// START_MODULE_CONTRACT: M-CATALOG-CREATE-SHARED
// purpose: Keep shared catalog/create semantic labels and lightweight helper constants aligned across checkout/resume/read surfaces.
// inputs:
//   - report types, block ids, telemetry metadata fragments
// outputs:
//   - canonical GRACE labels and payload helper fragments for catalog flows
// invariants:
//   - module/block labels stay stable across catalog, checkout, history, and read pages
// END_MODULE_CONTRACT: M-CATALOG-CREATE-SHARED

// START_MODULE_MAP: M-CATALOG-CREATE-SHARED
// entrypoints:
//   - CATALOG_GRACE_MODULES
//   - CATALOG_GRACE_BLOCKS
//   - withCatalogTrace
// END_MODULE_MAP: M-CATALOG-CREATE-SHARED

export type ProductInputDraft = {
  partnerName: string;
  partnerBirthDate: string;
  partnerBirthLocation: string;
  solarCurrentLocation: string;
};

export type CheckoutSessionState = {
  status: string;
  message: string | null;
};

export type CreateReportAccess = {
  allowed?: boolean;
  granted_via?: string | null;
  remaining_unlocks?: number;
  reason_code?: string;
  legacy_subscription_applied?: boolean;
};

export type CreateProfile = {
  full_name?: string | null;
  can_ask_horary?: boolean;
  can_access_premium?: boolean;
  horary_balance?: number;
  birth_place?: string | null;
  current_location?: string | null;
  birth_timezone?: string | null;
  current_timezone?: string | null;
  report_unlocks?: Record<string, number>;
  report_access?: Record<string, CreateReportAccess>;
  feature_flags?: RuntimeFeatureFlags;
};

export const PRODUCT_META: Record<string, { label: string }> = {
  natal_master: { label: "Натал (базовый)" },
  week_forecast: { label: "Прогноз на неделю" },
  month_forecast: { label: "Прогноз на месяц" },
  year_forecast: { label: "Альманах 2026" },
  ten_year_forecast: { label: "Прогноз на 10 лет" },
  solar_return: { label: "Соляр (Личный год)" },
  synastry: { label: "Совместимость" },
  horary: { label: "Вопрос (Хорар)" },
  horary_answer: { label: "Вопрос (Хорар)" },
  custom: { label: "Индивидуальный разбор" },
};

export const MOCK_INIT_DATA = "123456789";

export const EMPTY_PRODUCT_INPUT_DRAFT: ProductInputDraft = {
  partnerName: "",
  partnerBirthDate: "",
  partnerBirthLocation: "",
  solarCurrentLocation: "",
};

export const getDraftStorageKey = (type: string) => `create:draft:${type}`;

export const buildMockProfile = (): CreateProfile => ({
  full_name: "Debug User",
  can_ask_horary: true,
  can_access_premium: true,
  horary_balance: 1,
  birth_place: "Moscow",
  current_location: "Moscow",
  birth_timezone: "Europe/Moscow",
  current_timezone: "Europe/Moscow",
  report_unlocks: {
    natal_master: 0,
    month_forecast: 0,
    year_forecast: 0,
    solar_return: 0,
    synastry: 0,
  },
  report_access: {
    natal_master: {
      allowed: true,
      granted_via: "subscription",
      remaining_unlocks: 0,
      reason_code: "ok",
      legacy_subscription_applied: true,
    },
    month_forecast: {
      allowed: true,
      granted_via: "subscription",
      remaining_unlocks: 0,
      reason_code: "ok",
      legacy_subscription_applied: true,
    },
    year_forecast: {
      allowed: true,
      granted_via: "subscription",
      remaining_unlocks: 0,
      reason_code: "ok",
      legacy_subscription_applied: true,
    },
    solar_return: {
      allowed: true,
      granted_via: "subscription",
      remaining_unlocks: 0,
      reason_code: "ok",
      legacy_subscription_applied: true,
    },
    synastry: {
      allowed: true,
      granted_via: "subscription",
      remaining_unlocks: 0,
      reason_code: "ok",
      legacy_subscription_applied: true,
    },
  },
  feature_flags: {
    enable_one_off_entitlements_runtime: false,
    enable_persistent_checkout_sessions: false,
    legacy_premium_subscription_access: true,
  },
});

export function formatCreateAccessError(isOneOffFlow: boolean): string {
  if (isOneOffFlow) {
    return "Разовый доступ к этому разбору пока недоступен. Проверьте оплату или попробуйте снова через пару секунд.";
  }
  return "У вас нет активной подписки или закончились лимиты. Пожалуйста, оплатите доступ.";
}


export const CATALOG_GRACE_MODULES = {
  analytics: "M-CATALOG-ANALYTICS",
  checkoutResume: "M-CATALOG-CHECKOUT-RESUME",
  reportsCatalog: "M-REPORTS-CATALOG",
  reportsHistory: "M-REPORTS-HISTORY",
  readReport: "M-READ-REPORT-PAGE",
  createCheckout: "M-CREATE-CHECKOUT",
  homeFeed: "M-HOME-FEED",
} as const;

export const CATALOG_GRACE_BLOCKS = {
  analytics: {
    contextMerge: "CONTEXT_MERGE",
    payloadBuild: "PAYLOAD_BUILD",
    correlationResolution: "CORRELATION_RESOLUTION",
  },
  catalog: {
    analyticsBootstrap: "ANALYTICS_CONTEXT_BOOTSTRAP",
    ctaTracking: "CTA_TRACKING",
    catalogSection: "CATALOG_SECTION",
    billingNote: "BILLING_NOTE",
  },
  history: {
    analyticsBootstrap: "ANALYTICS_CONTEXT_BOOTSTRAP",
    dataFetch: "DATA_FETCH",
    ctaTracking: "CTA_TRACKING",
    resumeState: "RESUME_STATE",
  },
  checkoutResume: {
    tokenResolution: "TOKEN_RESOLUTION",
    resumeLinkState: "RESUME_LINK_STATE",
    analyticsBootstrap: "ANALYTICS_CONTEXT_BOOTSTRAP",
    ctaReady: "CTA_READY",
    resumeState: "RESUME_STATE",
    ctaPrimary: "CTA_PRIMARY",
    ctaCancel: "CTA_CANCEL",
  },
  read: {
    loading: "LOADING_STATE",
    share: "SHARE_SECTION",
    ctaTracking: "CTA_TRACKING",
    resumeEntry: "RESUME_ENTRY",
    analyticsBootstrap: "ANALYTICS_CONTEXT_BOOTSTRAP",
  },
  create: {
    checkoutInit: "CHECKOUT_INIT",
    checkoutPayload: "CHECKOUT_PAYLOAD",
    checkoutRedirect: "CHECKOUT_RESULT_REDIRECT",
    checkoutProvider: "CHECKOUT_RESULT_PROVIDER",
    checkoutResume: "CHECKOUT_RESULT_RESUME",
    checkoutError: "CHECKOUT_ERROR",
  },
} as const;

export function withCatalogTrace<T extends Record<string, unknown>>(
  meta: T,
  trace: {
    module: string;
    contract: string;
    block: string;
    semantic_block?: string;
    correlation_id?: string | null;
  },
): T & {
  module: string;
  contract: string;
  block: string;
  semantic_block: string;
  correlation_id?: string | null;
} {
  return {
    ...meta,
    module: trace.module,
    contract: trace.contract,
    block: trace.block,
    semantic_block: trace.semantic_block ?? trace.block,
    ...(trace.correlation_id ? { correlation_id: trace.correlation_id } : {}),
  };
}
