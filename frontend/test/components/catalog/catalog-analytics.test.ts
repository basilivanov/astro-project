import { trackEvent } from "../../../lib/analytics";
import {
  FLOW_FORECAST_CATALOG,
  normalizeCatalogFlags,
  resolveCatalogCorrelation,
  resolveCheckoutMode,
  setCatalogAnalyticsContext,
  setCatalogCorrelationId,
  startCatalogCorrelation,
  trackCatalogEvent,
} from "../../../components/catalog/catalog-analytics";

jest.mock("../../../lib/analytics", () => ({
  trackEvent: jest.fn().mockResolvedValue(undefined),
}));

describe("catalog-analytics", () => {
  const trackEventMock = trackEvent as jest.MockedFunction<typeof trackEvent>;
  const originalCrypto = global.window?.crypto;

  beforeEach(() => {
    jest.clearAllMocks();
    setCatalogAnalyticsContext({
      user_id: null,
      checkout_token: null,
      correlation_id: null,
      flow_id: null,
      surface: null,
      entry_point: null,
      entry_semantic_block: null,
      semantic_block: null,
      block: null,
      flags: {
        has_subscription_access: undefined,
        has_one_off_unlock: undefined,
        report_unlock_bridge: undefined,
        should_show_one_off_paywall: undefined,
      },
    });
    setCatalogCorrelationId(null);
    if (global.window) {
      Object.defineProperty(global.window, "crypto", {
        value: originalCrypto,
        configurable: true,
      });
    }
  });

  it("normalizes partial entitlement flags to explicit booleans", () => {
    expect(normalizeCatalogFlags({ has_subscription_access: true })).toEqual({
      has_subscription_access: true,
      has_one_off_unlock: false,
      report_unlock_bridge: false,
      should_show_one_off_paywall: false,
    });
    expect(normalizeCatalogFlags()).toEqual({});
  });

  it("prefers explicit correlation id over context and manager", () => {
    setCatalogCorrelationId("ctx-correlation");

    expect(resolveCatalogCorrelation({ correlationId: "opt-correlation" })).toEqual({
      correlation_id: "opt-correlation",
      correlation_source: "options",
    });
  });

  it("uses shared context correlation id when options omit one", () => {
    setCatalogCorrelationId("ctx-correlation");

    expect(resolveCatalogCorrelation({})).toEqual({
      correlation_id: "ctx-correlation",
      correlation_source: "context",
    });
  });

  it("creates and stores manager correlation id as fallback", () => {
    const correlationId = resolveCatalogCorrelation({}).correlation_id;

    expect(correlationId).toBeTruthy();
    expect(resolveCatalogCorrelation({})).toEqual({
      correlation_id: correlationId,
      correlation_source: "context",
    });
  });

  it("starts catalog correlation with provided flow name", () => {
    const correlationId = startCatalogCorrelation("catalog.checkout");

    expect(correlationId).toBeTruthy();
    expect(resolveCatalogCorrelation({})).toEqual({
      correlation_id: correlationId,
      correlation_source: "context",
    });
  });

  it("maps checkout modes to canonical names", () => {
    expect(resolveCheckoutMode({ isReportUnlockCheckout: true, isHorary: false })).toBe("report_unlock");
    expect(resolveCheckoutMode({ isReportUnlockCheckout: false, isHorary: true })).toBe("horary");
    expect(resolveCheckoutMode({ isReportUnlockCheckout: false, isHorary: false })).toBe("subscription");
  });

  it("tracks events with hashed checkout tokens and merged context", async () => {
    const digestMock = jest.fn().mockResolvedValue(new Uint8Array([0xab, 0xcd]).buffer);
    Object.defineProperty(global.window, "crypto", {
      value: { subtle: { digest: digestMock } },
      configurable: true,
    });

    setCatalogAnalyticsContext({
      user_id: 77,
      checkout_token: "context-token",
      flow_id: "catalog.flow",
      entry_point: "catalog_card",
      entry_semantic_block: "catalog.card.entry",
      flags: {
        has_subscription_access: true,
      },
    });
    setCatalogCorrelationId("ctx-correlation");

    await trackCatalogEvent(
      "catalog.clicked",
      {
        block: "catalog.card.click",
        report_unlock_bridge: true,
      },
      { block: "catalog.analytics.block" },
    );

    expect(digestMock).toHaveBeenCalled();
    expect(trackEventMock).toHaveBeenCalledTimes(1);

    const [eventName, payload, options] = trackEventMock.mock.calls[0];
    expect(eventName).toBe("catalog.clicked");
    expect(payload).toMatchObject({
      event: "catalog.clicked",
      flow_id: "catalog.flow",
      correlation_id: "ctx-correlation",
      correlation_source: "context",
      user_id: 77,
      entry_point: "catalog_card",
      entry_semantic_block: "catalog.card.entry",
      semantic_block: "catalog.card.click",
      block: "catalog.analytics.block",
      has_subscription_access: true,
      has_one_off_unlock: false,
      report_unlock_bridge: true,
      should_show_one_off_paywall: false,
      checkout_token_hash: "abcd",
    });
    expect(payload).not.toHaveProperty("checkout_token");
    expect(options).toMatchObject({
      correlationId: "ctx-correlation",
      flowId: "catalog.flow",
      block: "catalog.analytics.block",
      semanticBlock: "catalog.card.click",
    });
  });

  it("falls back to deterministic hash when crypto digest fails", async () => {
    const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => undefined);
    Object.defineProperty(global.window, "crypto", {
      value: { subtle: { digest: jest.fn().mockRejectedValue(new Error("boom")) } },
      configurable: true,
    });

    await trackCatalogEvent("catalog.hash_fallback", { checkout_token: "abc" });

    const [, payload] = trackEventMock.mock.calls[0];
    expect(payload).toMatchObject({
      flow_id: FLOW_FORECAST_CATALOG,
      checkout_token_hash: "h96354",
    });
    expect(warnSpy).toHaveBeenCalledWith("catalog.analytics.hash_error", expect.any(Error));
    warnSpy.mockRestore();
  });

  it("swallows analytics transport failures after warning", async () => {
    const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => undefined);
    trackEventMock.mockRejectedValueOnce(new Error("transport down"));
    setCatalogCorrelationId("ctx-correlation");

    await expect(trackCatalogEvent("catalog.failure", { block: "catalog.failure.block" })).resolves.toBeUndefined();
    expect(warnSpy).toHaveBeenCalledWith(
      "catalog.analytics.error",
      expect.objectContaining({
        fn: "trackCatalogEvent",
        block: "CATALOG_EVENT_DISPATCH",
      }),
    );
    warnSpy.mockRestore();
  });
});
