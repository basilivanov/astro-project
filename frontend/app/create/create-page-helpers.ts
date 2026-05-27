import {
  getReportUnlockPriceLabel,
  getRuntimePriceLabel,
  isReportUnlockBridgeEnabled,
} from "../../lib/product-billing";
import {
  normalizeCatalogFlags,
  resolveCheckoutMode,
} from "../../components/catalog/catalog-analytics";
import {
  type CheckoutSessionState,
  type CreateProfile,
} from "../../components/catalog/create-shared";

export type CreatePageDerivedStateArgs = {
  type: string | null;
  isHorary: boolean;
  isSubscriptionProduct: boolean;
  checkoutToken: string | null;
  mockQueryEnabled: boolean;
  profile: CreateProfile | null;
  shouldUseMockProfile: boolean;
  checkoutState: CheckoutSessionState;
};

export type CreatePageDerivedState = {
  effectiveProfile: CreateProfile | null;
  isReportUnlockBridge: boolean;
  availableUnlocks: number;
  hasOneOffUnlock: boolean;
  canAskFree: boolean;
  hasResolvedReportAccess: boolean;
  canGeneratePremium: boolean;
  shouldShowOneOffReportUnlockPaywall: boolean;
  runtimePriceLabel: string;
  checkoutBusy: boolean;
  checkoutMode: ReturnType<typeof resolveCheckoutMode>;
  analyticsFlags: ReturnType<typeof normalizeCatalogFlags>;
};

export function deriveCreatePageState({
  type,
  isHorary,
  isSubscriptionProduct,
  checkoutToken,
  mockQueryEnabled,
  profile,
  shouldUseMockProfile,
  checkoutState,
}: CreatePageDerivedStateArgs): CreatePageDerivedState {
  const effectiveProfile = profile || (shouldUseMockProfile ? buildMockProfileFallback() : null);
  const featureFlags = effectiveProfile?.feature_flags;
  const isReportUnlockBridge = isReportUnlockBridgeEnabled(type, featureFlags);
  const reportAccess = type ? effectiveProfile?.report_access?.[type] : undefined;
  const fallbackUnlocks = type ? effectiveProfile?.report_unlocks?.[type] ?? 0 : 0;
  const availableUnlocks = reportAccess?.remaining_unlocks ?? fallbackUnlocks;
  const hasResolvedReportAccess =
    (reportAccess ? reportAccess.allowed === true : effectiveProfile?.can_access_premium === true);
  const hasOneOffUnlock = isReportUnlockBridge && (reportAccess ? (reportAccess.remaining_unlocks ?? 0) > 0 : availableUnlocks > 0);
  const canAskFree = effectiveProfile?.can_ask_horary === true;
  const canGeneratePremium = !isHorary && (hasResolvedReportAccess || hasOneOffUnlock);
  const shouldShowOneOffReportUnlockPaywall =
    !isHorary && isReportUnlockBridge && !hasResolvedReportAccess && !hasOneOffUnlock;
  const runtimePriceLabel = shouldShowOneOffReportUnlockPaywall
    ? getReportUnlockPriceLabel(type)
    : getRuntimePriceLabel(type);
  const checkoutBusy = ["checking", "pending", "succeeded", "creating"].includes(checkoutState.status);
  const checkoutMode = resolveCheckoutMode({
    isReportUnlockCheckout: shouldShowOneOffReportUnlockPaywall,
    isHorary,
  });
  const analyticsFlags = normalizeCatalogFlags({
    has_subscription_access: hasResolvedReportAccess,
    has_one_off_unlock: hasOneOffUnlock,
    report_unlock_bridge: isReportUnlockBridge,
    should_show_one_off_paywall: shouldShowOneOffReportUnlockPaywall,
  });

  return {
    effectiveProfile,
    isReportUnlockBridge,
    availableUnlocks,
    hasOneOffUnlock,
    canAskFree,
    hasResolvedReportAccess,
    canGeneratePremium,
    shouldShowOneOffReportUnlockPaywall,
    runtimePriceLabel,
    checkoutBusy,
    checkoutMode,
    analyticsFlags,
  };
}

export function getSolarFallbackLabel(profile: CreateProfile | null): string {
  return profile?.current_location || profile?.birth_place || "текущую локацию из профиля";
}

export function getCheckoutStatusTone(status: CheckoutSessionState["status"]): string {
  return status === "failed" || status === "canceled"
    ? "border-rose-100 bg-rose-50 text-rose-700"
    : "border-emerald-100 bg-emerald-50 text-emerald-700";
}

function buildMockProfileFallback(): CreateProfile | null {
  return {
    id: 0,
    full_name: "Mock User",
    birth_date: "1990-01-01",
    birth_time: "12:00",
    birth_place: "Moscow",
    current_location: "Moscow",
    can_access_premium: true,
    can_ask_horary: true,
    feature_flags: {},
    report_access: {},
    report_unlocks: {},
  } as CreateProfile;
}
