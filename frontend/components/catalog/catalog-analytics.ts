import { trackEvent } from "../../lib/analytics";

export const FLOW_FORECAST_CATALOG = "FLOW-FORECAST-CATALOG";

export type CatalogSurface = "catalog" | "history" | "create" | "checkout" | "billing" | "read" | "week";

export type CatalogEntitlementFlags = {
  has_subscription_access?: boolean;
  has_one_off_unlock?: boolean;
  report_unlock_bridge?: boolean;
  should_show_one_off_paywall?: boolean;
};

export type CatalogEventPayload = CatalogEntitlementFlags & {
  surface?: CatalogSurface | string;
  report_type?: string | null;
  action?: string;
  entry_point?: string | null;
  filter_id?: string;
  cta_id?: string;
  cta_href?: string;
  checkout_mode?: string;
  checkout_token?: string | null;
  status?: string;
  flow_id?: string;
  [key: string]: unknown;
};

export type CatalogAnalyticsEvent = {
  event_name: string;
  payload?: CatalogEventPayload;
};

export async function trackCatalogEvent(eventName: string, payload: CatalogEventPayload = {}) {
  try {
    await trackEvent(eventName, {
      flow_id: FLOW_FORECAST_CATALOG,
      ...payload,
    });
  } catch (error) {
    // eslint-disable-next-line no-console
    console.warn("catalog.analytics.error", error);
  }
}

export function normalizeCatalogFlags(flags?: CatalogEntitlementFlags): CatalogEntitlementFlags {
  if (!flags) {
    return {};
  }
  return {
    has_subscription_access: flags.has_subscription_access ?? false,
    has_one_off_unlock: flags.has_one_off_unlock ?? false,
    report_unlock_bridge: flags.report_unlock_bridge ?? false,
    should_show_one_off_paywall: flags.should_show_one_off_paywall ?? false,
  };
}

export function resolveCheckoutMode(options: {
  isReportUnlockCheckout: boolean;
  isHorary: boolean;
}): string {
  if (options.isReportUnlockCheckout) {
    return "report_unlock";
  }
  if (options.isHorary) {
    return "horary";
  }
  return "subscription";
}
