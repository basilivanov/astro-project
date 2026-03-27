import { CorrelationManager, type CorrelationContext, withCorrelationHeaders } from "./correlation";

const SESSION_KEY = "astro.session_id";
const DEFAULT_FLOW_ID = "flow.analytics.default";
const ANALYTICS_MODULE_ID = "M-ANALYTICS-HELPER";

// START_MODULE_CONTRACT: M-ANALYTICS-HELPER
// purpose: Provide a strict GRACE analytics transport with correlation/flow propagation.
// owns:
//   - frontend/lib/analytics.ts
// inputs:
//   - event names, payload fragments, optional correlation/trace/flow metadata
// outputs:
//   - POST requests to /api/analytics/event and /api/analytics/batch with normalized metadata
// dependencies:
//   - ./correlation for correlation lifecycle + request header propagation
// side_effects:
//   - browser session storage reads for session ids
//   - network requests to analytics ingestion routes
// invariants:
//   - every dispatched event carries correlation-aware metadata
//   - every event has a stable flow_id fallback when caller omits one
//   - transport failures are block-aware and never throw to UI callers
// failure_policy:
//   - swallow transport/runtime failures after block-aware console warnings
// non_goals:
//   - business payload validation beyond transport normalization
// END_MODULE_CONTRACT: M-ANALYTICS-HELPER

// START_MODULE_MAP: M-ANALYTICS-HELPER
// public_entrypoints:
//   - getSessionId
//   - trackEvent
//   - trackEventBatch
// internal_helpers:
//   - isBrowser
//   - isMobileDevice
//   - resolveContext
//   - normalizeEventPayload
//   - dispatchAnalyticsRequest
// owned_tests:
//   - e2e/core-ux.spec.ts (analytics coverage when present)
// adjacent_modules:
//   - frontend/lib/correlation.ts
//   - frontend/components/catalog/catalog-analytics.ts
// END_MODULE_MAP: M-ANALYTICS-HELPER

const isBrowser = () => typeof window !== "undefined";

const isMobileDevice = () => {
  if (typeof navigator === "undefined") {
    return false;
  }
  return /Mobi|Android/i.test(navigator.userAgent);
};

// START_CONTRACT: FN-GET-SESSION-ID
// purpose: Return a stable browser session id for analytics events.
// inputs: none.
// returns: existing/generated session id or null outside browser/storage failures.
// side_effects: reads and may write browser sessionStorage.
// error_behavior: returns null on storage/runtime failures.
// END_CONTRACT: FN-GET-SESSION-ID
export const getSessionId = () => {
  if (!isBrowser()) {
    return null;
  }

  // START_BLOCK: SESSION_STORAGE_LOOKUP
  try {
    const storage = window.sessionStorage;
    let sid = storage.getItem(SESSION_KEY);
    if (!sid && typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      sid = crypto.randomUUID();
      storage.setItem(SESSION_KEY, sid);
    }
    return sid;
  } catch (_error) {
    return null;
  }
  // END_BLOCK: SESSION_STORAGE_LOOKUP
};

export type TrackEventOptions = {
  correlationId?: string | null;
  traceId?: string | null;
  flowId?: string | null;
  block?: string | null;
  semanticBlock?: string | null;
  keepalive?: boolean;
};

export type TrackEventInput = {
  eventName: string;
  params?: Record<string, unknown>;
  options?: TrackEventOptions;
};

type AnalyticsPayload = Record<string, unknown> & {
  event_name: string;
  session_id?: string;
  path?: string;
  device?: "mobile" | "desktop";
  correlation_id?: string;
  trace_id?: string;
  flow_id: string;
  block?: string;
  semantic_block?: string;
};

type ResolvedTrackContext = CorrelationContext & {
  block?: string;
  semanticBlock?: string;
};

const emitAnalyticsWarning = (
  fn: "trackEvent" | "trackEventBatch" | "resolveContext",
  block: string,
  error: unknown,
) => {
  console.warn("analytics.helper.error", {
    module: ANALYTICS_MODULE_ID,
    fn,
    block,
    error,
  });
};

// START_CONTRACT: FN-TRACK-EVENT
// purpose: Dispatch a single analytics event with normalized correlation/flow metadata.
// inputs: event name, payload fragment, TrackEventOptions.
// returns: Promise<void>.
// side_effects: POSTs to /api/analytics/event when browser runtime is available.
// emitted_logs: analytics.helper.error on block-aware failures.
// error_behavior: swallows transport/runtime failures after warning.
// END_CONTRACT: FN-TRACK-EVENT
export const trackEvent = async (
  eventName: string,
  params: Record<string, unknown> = {},
  options: TrackEventOptions = {},
) => {
  if (!isBrowser()) {
    return;
  }

  try {
    // START_BLOCK: SINGLE_EVENT_CONTEXT
    const context = resolveContext(options, params);
    // END_BLOCK: SINGLE_EVENT_CONTEXT

    // START_BLOCK: SINGLE_EVENT_DISPATCH
    const payload = normalizeEventPayload(eventName, params, context);
    await dispatchAnalyticsRequest("/api/analytics/event", payload, context);
    // END_BLOCK: SINGLE_EVENT_DISPATCH
  } catch (error) {
    emitAnalyticsWarning("trackEvent", "SINGLE_EVENT_DISPATCH", error);
  }
};

// START_CONTRACT: FN-TRACK-EVENT-BATCH
// purpose: Dispatch a batch of analytics events under shared correlation context.
// inputs: array of TrackEventInput and optional shared TrackEventOptions.
// returns: Promise<void>.
// side_effects: POSTs to /api/analytics/batch when browser runtime is available.
// emitted_logs: analytics.helper.error on block-aware failures.
// error_behavior: swallows transport/runtime failures after warning.
// END_CONTRACT: FN-TRACK-EVENT-BATCH
export const trackEventBatch = async (
  events: TrackEventInput[],
  options: TrackEventOptions = {},
) => {
  if (!isBrowser() || events.length === 0) {
    return;
  }

  try {
    // START_BLOCK: BATCH_SHARED_CONTEXT
    const sharedContext = resolveContext(options);
    // END_BLOCK: BATCH_SHARED_CONTEXT

    // START_BLOCK: BATCH_EVENT_DISPATCH
    const payload = events.map((event) => {
      const mergedOptions = {
        ...options,
        ...(event.options ?? {}),
        correlationId: event.options?.correlationId ?? sharedContext.correlationId,
        traceId: event.options?.traceId ?? sharedContext.traceId,
        flowId: event.options?.flowId ?? sharedContext.flowId,
        block: event.options?.block ?? sharedContext.block,
        semanticBlock: event.options?.semanticBlock ?? sharedContext.semanticBlock,
      } satisfies TrackEventOptions;

      const eventContext = resolveContext(mergedOptions, event.params);
      return normalizeEventPayload(event.eventName, event.params ?? {}, eventContext);
    });
    await dispatchAnalyticsRequest("/api/analytics/batch", { events: payload }, sharedContext);
    // END_BLOCK: BATCH_EVENT_DISPATCH
  } catch (error) {
    emitAnalyticsWarning("trackEventBatch", "BATCH_EVENT_DISPATCH", error);
  }
};

// START_CONTRACT: FN-RESOLVE-CONTEXT
// purpose: Resolve correlation, trace, flow, and semantic block metadata for analytics events.
// inputs: TrackEventOptions and optional analytics params.
// returns: normalized ResolvedTrackContext.
// side_effects: may allocate correlation/trace ids through CorrelationManager.
// emitted_logs: analytics.helper.error on resolution failures.
// error_behavior: falls back to generated correlation context when resolution fails.
// END_CONTRACT: FN-RESOLVE-CONTEXT
function resolveContext(
  options: TrackEventOptions = {},
  params: Record<string, unknown> = {},
): ResolvedTrackContext {
  try {
    // START_BLOCK: CONTEXT_INPUT_NORMALIZATION
    const flowFromParams = typeof params.flow_id === "string" ? params.flow_id : null;
    const blockFromParams = typeof params.block === "string" ? params.block : null;
    const semanticBlockFromParams =
      typeof params.semantic_block === "string"
        ? params.semantic_block
        : typeof params.block === "string"
          ? params.block
          : null;
    // END_BLOCK: CONTEXT_INPUT_NORMALIZATION

    // START_BLOCK: CONTEXT_CORRELATION_RESOLUTION
    return CorrelationManager.resolveContext({
      correlationId: options.correlationId,
      traceId: options.traceId,
      flowId: options.flowId ?? flowFromParams ?? DEFAULT_FLOW_ID,
      block: options.block ?? blockFromParams,
      semanticBlock: options.semanticBlock ?? semanticBlockFromParams ?? blockFromParams,
    });
    // END_BLOCK: CONTEXT_CORRELATION_RESOLUTION
  } catch (error) {
    emitAnalyticsWarning("resolveContext", "CONTEXT_CORRELATION_RESOLUTION", error);
    return CorrelationManager.resolveContext({
      flowId: DEFAULT_FLOW_ID,
      block: options.block,
      semanticBlock: options.semanticBlock ?? options.block,
    });
  }
}

function normalizeEventPayload(
  eventName: string,
  params: Record<string, unknown>,
  context: ResolvedTrackContext,
): AnalyticsPayload {
  const sessionId = getSessionId();
  const semanticBlock =
    typeof params.semantic_block === "string"
      ? params.semantic_block
      : context.semanticBlock ?? context.block ?? undefined;

  return {
    event_name: eventName,
    session_id: sessionId ?? undefined,
    path: isBrowser() ? window.location.pathname : undefined,
    device: isMobileDevice() ? "mobile" : "desktop",
    correlation_id: context.correlationId,
    trace_id: context.traceId,
    flow_id: context.flowId,
    block: context.block ?? undefined,
    semantic_block: semanticBlock,
    ...params,
  };
}

async function dispatchAnalyticsRequest(
  endpoint: string,
  payload: Record<string, unknown>,
  context: ResolvedTrackContext,
) {
  const requestInit = withCorrelationHeaders(
    {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    {
      correlationId: context.correlationId,
      traceId: context.traceId,
      flowId: context.flowId,
      block: context.block,
      semanticBlock: context.semanticBlock,
    },
  );

  const response = await fetch(endpoint, requestInit);
  if (!response.ok) {
    throw new Error(`analytics request failed: ${response.status}`);
  }
}
