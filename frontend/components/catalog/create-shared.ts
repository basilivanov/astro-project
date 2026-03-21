import type { RuntimeFeatureFlags } from "../../lib/product-billing";

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
