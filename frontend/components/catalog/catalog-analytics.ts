import { CorrelationManager } from "../../lib/correlation";
import { trackEvent, type TrackEventOptions } from "../../lib/analytics";
import { CATALOG_GRACE_BLOCKS, CATALOG_GRACE_MODULES, withCatalogTrace } from "./create-shared";

// START_MODULE_CONTRACT: M-CATALOG-ANALYTICS
// purpose: Provide a shared telemetry helper for catalog and profile-adjacent surfaces with enforced correlation IDs.
// owns:
//   - frontend/components/catalog/catalog-analytics.ts
// inputs:
//   - track event payload fragments from catalog/report/profile UIs
//   - optional correlation IDs or checkout tokens from surface hooks
// outputs:
//   - normalized analytics payloads with catalog entitlement flags
//   - hashed checkout tokens + correlation-aware `trackEvent` dispatches
// dependencies:
//   - ../../lib/correlation for correlation lifecycle
//   - ../../lib/analytics for the actual transport
// invariants:
//   - FLOW_FORECAST_CATALOG is stamped on every catalog payload
//   - checkout_token never leaves the client unhashed in telemetry
//   - correlation provenance is preserved for trace evidence
// non_goals:
//   - Rendering UI or mutating business state
// END_MODULE_CONTRACT: M-CATALOG-ANALYTICS

// START_MODULE_MAP: M-CATALOG-ANALYTICS
// entrypoints:
//   - setCatalogAnalyticsContext
//   - startCatalogCorrelation
//   - setCatalogCorrelationId
//   - trackCatalogEvent
// helpers:
//   - normalizeCatalogFlags
//   - resolveCatalogCorrelation
//   - resolveCheckoutMode
// owned_tests:
//   - tests/test_catalog_logging.py
// END_MODULE_MAP: M-CATALOG-ANALYTICS

export const FLOW_FORECAST_CATALOG = "FLOW-FORECAST-CATALOG";

export type CatalogSurface = "catalog" | "history" | "create" | "checkout" | "billing" | "read" | "week" | "profile" | "profile_edit";

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
  entry_semantic_block?: string | null;
  semantic_block?: string;
  block?: string;
  filter_id?: string;
  cta_id?: string;
  cta_href?: string;
  checkout_mode?: string;
  checkout_token?: string | null;
  checkout_token_hash?: string | null;
  correlation_id?: string | null;
  correlation_source?: string | null;
  status?: string;
  flow_id?: string;
  user_id?: number;
  [key: string]: unknown;
};

export type CatalogAnalyticsEvent = {
  event_name: string;
  payload?: CatalogEventPayload;
};

export type CatalogCorrelationMeta = {
  correlation_id?: string | null;
  correlation_source?: "options" | "context" | "manager";
};

type CatalogAnalyticsContext = {
  user_id?: number | null;
  checkout_token?: string | null;
  flags?: CatalogEntitlementFlags;
  correlation_id?: string | null;
  flow_id?: string | null;
  surface?: CatalogSurface | string | null;
  entry_point?: string | null;
  entry_semantic_block?: string | null;
  semantic_block?: string | null;
  block?: string | null;
};

let catalogContext: CatalogAnalyticsContext = {};

// START_CONTRACT: FN-SET-CATALOG-CONTEXT
// purpose: Merge caller-provided catalog analytics context (user, checkout, flags).
// inputs: partial context with optional flags/ids.
// side_effects: updates module-level catalogContext.
// END_CONTRACT: FN-SET-CATALOG-CONTEXT
export function setCatalogAnalyticsContext(context: CatalogAnalyticsContext) {
  // START_BLOCK: CONTEXT_MERGE
  catalogContext = {
    ...catalogContext,
    ...context,
    flags: {
      ...catalogContext.flags,
      ...(context.flags ?? {}),
    },
  };
  // END_BLOCK: CONTEXT_MERGE
}

// START_CONTRACT: FN-START-CATALOG-CORRELATION
// purpose: Allocate a correlation id for catalog flows.
// inputs: optional flow name.
// returns: correlation id string.
// END_CONTRACT: FN-START-CATALOG-CORRELATION
export function startCatalogCorrelation(flowName?: string) {
  const correlationId = CorrelationManager.newCorrelation(flowName);
  catalogContext.correlation_id = correlationId;
  catalogContext.flow_id = flowName ?? catalogContext.flow_id ?? FLOW_FORECAST_CATALOG;
  return correlationId;
}

// START_CONTRACT: FN-SET-CATALOG-CORRELATION-ID
// purpose: Force catalog correlation id (e.g., resume flows).
// inputs: correlation id or null.
// side_effects: updates context + CorrelationManager when id present.
// END_CONTRACT: FN-SET-CATALOG-CORRELATION-ID
export function setCatalogCorrelationId(id: string | null) {
  catalogContext.correlation_id = id;
  if (id) {
    CorrelationManager.setCorrelationId(id);
  }
}

// START_CONTRACT: FN-TRACK-CATALOG-EVENT
// purpose: Dispatch analytics event with normalized flags, hashed tokens, and correlation provenance.
// inputs: event name, payload, optional TrackEventOptions.
// returns: Promise<void>.
// side_effects: invokes trackEvent with enforced correlation id.
// emitted_logs: catalog.analytics.error on block-aware failures.
// error_behavior: swallows analytics enrichment/dispatch failures after warning.
// END_CONTRACT: FN-TRACK-CATALOG-EVENT
export async function trackCatalogEvent(
  eventName: string,
  payload: CatalogEventPayload = {},
  options: TrackEventOptions = {},
) {
  try {
    // START_BLOCK: PAYLOAD_BUILD
    const enrichedPayload = await buildCatalogPayload(payload);
    enrichedPayload.event = eventName;
    // END_BLOCK: PAYLOAD_BUILD

    // START_BLOCK: CORRELATION_RESOLUTION
    const correlationMeta = resolveCatalogCorrelation(options);
    const correlationId = correlationMeta.correlation_id;
    const flowId =
      options.flowId ??
      (typeof enrichedPayload.flow_id === "string" ? enrichedPayload.flow_id : null) ??
      catalogContext.flow_id ??
      FLOW_FORECAST_CATALOG;
    const blockName =
      options.block ??
      (typeof enrichedPayload.semantic_block === "string" ? enrichedPayload.semantic_block : null) ??
      (typeof enrichedPayload.block === "string" ? enrichedPayload.block : null) ??
      "catalog.analytics.track";

    if (correlationId) {
      enrichedPayload.correlation_id = correlationId;
      enrichedPayload.correlation_source = correlationMeta.correlation_source;
    }
    enrichedPayload.flow_id = flowId;
    // END_BLOCK: CORRELATION_RESOLUTION

    const semanticBlock =
      typeof enrichedPayload.semantic_block === "string" ? enrichedPayload.semantic_block : blockName;

    // START_BLOCK: CATALOG_EVENT_DISPATCH
    await trackEvent(
      eventName,
      withCatalogTrace(enrichedPayload, {
        module: CATALOG_GRACE_MODULES.analytics,
        contract: "FN-TRACK-CATALOG-EVENT",
        block: blockName,
        semantic_block: semanticBlock,
        correlation_id: correlationId,
      }),
      {
        ...options,
        correlationId,
        flowId,
        block: blockName,
        semanticBlock,
      },
    );
    // END_BLOCK: CATALOG_EVENT_DISPATCH
  } catch (error) {
    // eslint-disable-next-line no-console
    console.warn("catalog.analytics.error", {
      module: CATALOG_GRACE_MODULES.analytics,
      fn: "trackCatalogEvent",
      block: "CATALOG_EVENT_DISPATCH",
      error,
    });
  }
}

// START_CONTRACT: FN-RESOLVE-CATALOG-CORRELATION
// purpose: Resolve correlation id from explicit options, shared context, or manager fallback.
// inputs: optional TrackEventOptions.
// returns: correlation metadata with source label for telemetry.
// side_effects: stores fallback correlation id into shared catalog context.
// END_CONTRACT: FN-RESOLVE-CATALOG-CORRELATION
export function resolveCatalogCorrelation(options: TrackEventOptions = {}): CatalogCorrelationMeta {
  // START_BLOCK: CORRELATION_SOURCE_RESOLUTION
  if (options.correlationId) {
    return {
      correlation_id: options.correlationId,
      correlation_source: "options",
    };
  }

  if (catalogContext.correlation_id) {
    return {
      correlation_id: catalogContext.correlation_id,
      correlation_source: "context",
    };
  }

  const correlationId = CorrelationManager.ensureCorrelationId();
  catalogContext.correlation_id = correlationId;
  return {
    correlation_id: correlationId,
    correlation_source: "manager",
  };
  // END_BLOCK: CORRELATION_SOURCE_RESOLUTION
}

// START_CONTRACT: FN-BUILD-CATALOG-PAYLOAD
// purpose: Merge context + flags + hashed checkout token into analytics payload.
// inputs: raw payload fragment.
// returns: analytics-safe payload with FLOW tag.
// END_CONTRACT: FN-BUILD-CATALOG-PAYLOAD
async function buildCatalogPayload(payload: CatalogEventPayload): Promise<Record<string, unknown>> {
  const merged: CatalogEventPayload = { ...payload };
  const normalizedFlags = normalizeCatalogFlags({
    ...catalogContext.flags,
    ...payload,
  });

  Object.assign(merged, normalizedFlags);

  if (merged.user_id == null && catalogContext.user_id != null) {
    merged.user_id = catalogContext.user_id;
  }

  const checkoutToken = payload.checkout_token ?? catalogContext.checkout_token;
  if (checkoutToken) {
    merged.checkout_token_hash = await hashCheckoutToken(checkoutToken);
  }

  if (!merged.semantic_block && merged.block) {
    merged.semantic_block = merged.block;
  }

  if (merged.entry_point == null && catalogContext.entry_point != null) {
    merged.entry_point = catalogContext.entry_point;
  }

  if (merged.entry_semantic_block == null && catalogContext.entry_semantic_block != null) {
    merged.entry_semantic_block = catalogContext.entry_semantic_block;
  }

  delete merged.checkout_token;

  return {
    flow_id: payload.flow_id ?? catalogContext.flow_id ?? FLOW_FORECAST_CATALOG,
    ...merged,
  };
}

// START_CONTRACT: FN-HASH-CHECKOUT-TOKEN
// purpose: Hash checkout tokens before logging analytics.
// inputs: plaintext token string.
// returns: SHA-256 hash (or fallback) string.
// END_CONTRACT: FN-HASH-CHECKOUT-TOKEN
async function hashCheckoutToken(token: string): Promise<string> {
  try {
    if (typeof window !== "undefined" && window.crypto?.subtle) {
      const encoder = new TextEncoder();
      const data = encoder.encode(token);
      const digest = await window.crypto.subtle.digest("SHA-256", data);
      return Array.from(new Uint8Array(digest))
        .map((byte) => byte.toString(16).padStart(2, "0"))
        .join("");
    }
  } catch (error) {
    console.warn("catalog.analytics.hash_error", error);
  }
  return fallbackHash(token);
}

function fallbackHash(value: string): string {
  let hash = 0;
  for (let idx = 0; idx < value.length; idx += 1) {
    const char = value.charCodeAt(idx);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return `h${Math.abs(hash)}`;
}

// START_CONTRACT: FN-NORMALIZE-CATALOG-FLAGS
// purpose: Ensure analytics flags are explicit booleans.
// inputs: optional flag object (possibly partial).
// returns: CatalogEntitlementFlags with defaults.
// END_CONTRACT: FN-NORMALIZE-CATALOG-FLAGS
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

// START_CONTRACT: FN-RESOLVE-CHECKOUT-MODE
// purpose: Map runtime checkout booleans to canonical mode string.
// inputs: object describing report unlock/horary state.
// returns: "report_unlock" | "horary" | "subscription".
// END_CONTRACT: FN-RESOLVE-CHECKOUT-MODE
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
