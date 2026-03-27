import { CorrelationManager, correlatedFetch } from "./correlation";
import { trackEvent, type TrackEventOptions } from "./analytics";
import { withCatalogTrace } from "../components/catalog/create-shared";

// START_MODULE_CONTRACT: M-HOME-ANALYTICS
// purpose: Provide strict GRACE trace + correlation helpers for the home feed surface.
// owns:
//   - frontend/lib/home-analytics.ts
// inputs:
//   - home block names, event names, optional entry_point and correlation overrides
// outputs:
//   - normalized home analytics payloads and correlation-aware fetch wrappers
// dependencies:
//   - frontend/lib/correlation.ts
//   - frontend/lib/analytics.ts
//   - frontend/components/catalog/create-shared.ts
// invariants:
//   - home telemetry always includes surface=home and flow_id=FLOW-HOME-FEED
//   - semantic block defaults to block when omitted
// non_goals:
//   - UI rendering or feed business normalization
// END_MODULE_CONTRACT: M-HOME-ANALYTICS

// START_MODULE_MAP: M-HOME-ANALYTICS
// entrypoints:
//   - HOME_FLOW_ID
//   - HOME_MODULE_ID
//   - ensureHomeCorrelation
//   - makeHomeTrace
//   - trackHomeEvent
//   - homeFetch
// END_MODULE_MAP: M-HOME-ANALYTICS

export const HOME_FLOW_ID = "FLOW-HOME-FEED";
export const HOME_MODULE_ID = "M-HOME-FEED";

type HomeTraceInput = {
  contract: string;
  block: string;
  semantic_block?: string;
  correlation_id?: string | null;
};

type HomeEventMeta = Record<string, unknown> & {
  entry_point?: string;
  block?: string;
  semantic_block?: string;
  module?: string;
  contract?: string;
  correlation_id?: string | null;
};

export function ensureHomeCorrelation() {
  return CorrelationManager.ensureCorrelationId();
}

export function makeHomeTrace(input: HomeTraceInput) {
  return withCatalogTrace(
    {
      surface: "home",
      flow_id: HOME_FLOW_ID,
    },
    {
      module: HOME_MODULE_ID,
      contract: input.contract,
      block: input.block,
      semantic_block: input.semantic_block ?? input.block,
      correlation_id: input.correlation_id ?? ensureHomeCorrelation(),
    },
  );
}

export async function trackHomeEvent(
  eventName: string,
  meta: HomeEventMeta,
  options: TrackEventOptions = {},
) {
  const correlationId = options.correlationId ?? meta.correlation_id ?? ensureHomeCorrelation();
  const block = typeof meta.block === "string" ? meta.block : undefined;
  const payload = {
    ...makeHomeTrace({
      contract: typeof meta.contract === "string" ? meta.contract : "FN-HOME-EVENT",
      block: block ?? "HOME_EVENT",
      semantic_block: typeof meta.semantic_block === "string" ? meta.semantic_block : block,
      correlation_id: typeof correlationId === "string" ? correlationId : undefined,
    }),
    ...meta,
    surface: "home",
    flow_id: HOME_FLOW_ID,
  };

  await trackEvent(eventName, payload, {
    ...options,
    correlationId,
    flowId: HOME_FLOW_ID,
    block: block ?? options.block ?? null,
  });
}

export function homeFetch(input: Parameters<typeof fetch>[0], init?: RequestInit, block?: string) {
  return correlatedFetch(input, init, {
    correlationId: ensureHomeCorrelation(),
    flowId: HOME_FLOW_ID,
    block,
  });
}
