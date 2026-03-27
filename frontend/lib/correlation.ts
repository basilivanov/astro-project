const STORAGE_KEY = "astro.correlation_id";
let memoryCorrelationId: string | null = null;

type CorrelationSetOptions = {
  reason?: string;
  flowId?: string | null;
};

export type CorrelationContext = {
  correlationId: string;
  traceId: string;
  flowId: string;
  block?: string | null;
  semanticBlock?: string | null;
};

type HeaderOverrides = {
  correlationId?: string | null;
  traceId?: string | null;
  flowId?: string | null;
  block?: string | null;
  semanticBlock?: string | null;
};

// START_MODULE_CONTRACT: M-CORRELATION
// purpose: Manage correlation/trace/flow identifiers for frontend request and analytics helpers.
// owns:
//   - frontend/lib/correlation.ts
// inputs:
//   - optional caller-supplied correlation, trace, flow, and block metadata
// outputs:
//   - stable correlation ids in storage/memory and normalized request headers
// invariants:
//   - ensureCorrelationId always returns a non-empty id
//   - resolveContext always returns correlation + trace + flow ids
// END_MODULE_CONTRACT: M-CORRELATION

// START_MODULE_MAP: M-CORRELATION
// entrypoints:
//   - CorrelationManager.getCorrelationId
//   - CorrelationManager.setCorrelationId
//   - CorrelationManager.newCorrelation
//   - CorrelationManager.ensureCorrelationId
//   - CorrelationManager.generateTraceId
//   - CorrelationManager.resolveContext
//   - withCorrelationHeaders
//   - correlatedFetch
// END_MODULE_MAP: M-CORRELATION

const isBrowser = () => typeof window !== "undefined";

const getSessionStorage = () => {
  if (!isBrowser()) {
    return null;
  }
  try {
    return window.sessionStorage;
  } catch (_error) {
    return null;
  }
};

const generateId = () => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `corr_${Date.now().toString(16)}_${Math.random().toString(16).slice(2, 10)}`;
};

function generateFlowId(seed?: string | null) {
  if (seed && seed.trim()) {
    return seed.trim();
  }
  return "flow.default";
}

const persistCorrelationId = (id: string) => {
  memoryCorrelationId = id;
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  try {
    storage.setItem(STORAGE_KEY, id);
  } catch (error) {
    // eslint-disable-next-line no-console
    console.warn("correlation.persist_failed", error);
  }
};

const readStoredId = () => {
  const storage = getSessionStorage();
  if (!storage) {
    return memoryCorrelationId;
  }
  try {
    const stored = storage.getItem(STORAGE_KEY);
    if (stored) {
      memoryCorrelationId = stored;
    }
    return stored ?? memoryCorrelationId;
  } catch (_error) {
    return memoryCorrelationId;
  }
};

const normalizeHeaders = (headers?: HeadersInit): Record<string, string> => {
  if (!headers) {
    return {};
  }
  if (headers instanceof Headers) {
    const pairs: Record<string, string> = {};
    headers.forEach((value, key) => {
      pairs[key] = value;
    });
    return pairs;
  }
  if (Array.isArray(headers)) {
    return headers.reduce<Record<string, string>>((acc, [key, value]) => {
      acc[key] = value;
      return acc;
    }, {});
  }
  return { ...headers } as Record<string, string>;
};

const toHeadersInit = (entries: Record<string, string>) => {
  if (typeof Headers === "function") {
    const next = new Headers();
    Object.entries(entries).forEach(([key, value]) => {
      next.set(key, value);
    });
    return next;
  }
  return entries;
};

export const CorrelationManager = {
  getCorrelationId(): string | null {
    return readStoredId() ?? null;
  },
  setCorrelationId(id: string, _options?: CorrelationSetOptions) {
    if (!id) {
      return;
    }
    persistCorrelationId(id);
  },
  newCorrelation(_flow?: string) {
    const nextId = generateId();
    persistCorrelationId(nextId);
    return nextId;
  },
  ensureCorrelationId() {
    return this.getCorrelationId() ?? this.newCorrelation();
  },
  generateTraceId() {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
    return `trace_${Date.now().toString(16)}_${Math.random().toString(16).slice(2, 10)}`;
  },
  resolveContext(overrides: HeaderOverrides = {}): CorrelationContext {
    return {
      correlationId: overrides.correlationId ?? this.ensureCorrelationId(),
      traceId: overrides.traceId ?? this.generateTraceId(),
      flowId: generateFlowId(overrides.flowId),
      block: overrides.block ?? undefined,
      semanticBlock: overrides.semanticBlock ?? overrides.block ?? undefined,
    };
  },
};

export const withCorrelationHeaders = (
  init: RequestInit = {},
  overrides?: HeaderOverrides,
): RequestInit => {
  const context = CorrelationManager.resolveContext(overrides);
  const headers = normalizeHeaders(init.headers);

  headers["X-Correlation-Id"] = context.correlationId;
  headers["X-Trace-Id"] = context.traceId;
  headers["X-Flow-Id"] = context.flowId;
  if (context.block) {
    headers["X-Flow-Block"] = context.block;
  }
  if (context.semanticBlock) {
    headers["X-Semantic-Block"] = context.semanticBlock;
  }

  return {
    ...init,
    headers: toHeadersInit(headers),
  };
};

type FetchInput = Parameters<typeof fetch>[0];

export const correlatedFetch = (
  input: FetchInput,
  init?: RequestInit,
  overrides?: HeaderOverrides,
) => {
  return fetch(input, withCorrelationHeaders(init ?? {}, overrides));
};
