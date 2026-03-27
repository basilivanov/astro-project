export const SUBSCRIPTION_PRICE_RUB = 299;
export const SUBSCRIPTION_PRICE_LABEL = "299₽/мес";
export const HORARY_PRICE_RUB = 199;
export const HORARY_PRICE_LABEL = "от 99₽";

const REPORT_UNLOCK_BRIDGE_PRODUCT_TYPES = new Set([
  "natal_master",
  "month_forecast",
  "year_forecast",
  "solar_return",
  "synastry",
]);

export type RuntimeFeatureFlags = {
  enable_one_off_entitlements_runtime?: boolean;
  enable_persistent_checkout_sessions?: boolean;
  legacy_premium_subscription_access?: boolean;
};

const REPORT_UNLOCK_PRICE_RUB: Record<string, number> = {
  natal_master: 199,
  month_forecast: 199,
  year_forecast: 499,
  solar_return: 199,
  synastry: 199,
};

const SUBSCRIPTION_PRODUCT_TYPES = new Set([
  "custom",
  "month_forecast",
  "natal_master",
  "solar_return",
  "synastry",
  "ten_year_forecast",
  "week_forecast",
  "year_forecast",
]);

const HORARY_PRODUCT_TYPES = new Set(["horary", "horary_answer"]);

export function isSubscriptionProductType(type?: string | null): boolean {
  return Boolean(type && SUBSCRIPTION_PRODUCT_TYPES.has(type));
}

export function isHoraryProductType(type?: string | null): boolean {
  return Boolean(type && HORARY_PRODUCT_TYPES.has(type));
}

export function getRuntimePriceLabel(type?: string | null): string {
  if (isSubscriptionProductType(type)) {
    return SUBSCRIPTION_PRICE_LABEL;
  }
  return HORARY_PRICE_LABEL;
}

export function getRuntimePriceValue(type?: string | null): number {
  if (isSubscriptionProductType(type)) {
    return SUBSCRIPTION_PRICE_RUB;
  }
  return HORARY_PRICE_RUB;
}

export function getRuntimeAccessBadge(type?: string | null): string {
  if (isSubscriptionProductType(type)) {
    return "По подписке";
  }
  if (isHoraryProductType(type)) {
    return "Разовый вопрос";
  }
  return "Каталог";
}

export function isReportUnlockBridgeEnabled(
  type?: string | null,
  flags?: RuntimeFeatureFlags | null,
): boolean {
  return Boolean(
    type &&
    REPORT_UNLOCK_BRIDGE_PRODUCT_TYPES.has(type) &&
    flags?.enable_one_off_entitlements_runtime &&
    flags?.enable_persistent_checkout_sessions,
  );
}

export function getReportUnlockPriceValue(type?: string | null): number {
  if (!type) {
    return HORARY_PRICE_RUB;
  }
  return REPORT_UNLOCK_PRICE_RUB[type] ?? HORARY_PRICE_RUB;
}

export function getReportUnlockPriceLabel(type?: string | null): string {
  return `${Math.round(getReportUnlockPriceValue(type))}₽`;
}
