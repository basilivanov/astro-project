import { HOME_FLOW_ID, HOME_MODULE_ID, ensureHomeCorrelation, homeFetch, makeHomeTrace, trackHomeEvent } from "../../lib/home-analytics";
import { CorrelationManager } from "../../lib/correlation";
import { trackEvent } from "../../lib/analytics";

jest.mock("../../lib/analytics", () => ({
  trackEvent: jest.fn().mockResolvedValue(undefined),
}));

describe("home analytics helpers", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    jest.restoreAllMocks();
    (trackEvent as jest.Mock).mockResolvedValue(undefined);
  });

  it("ensures and reuses the session correlation id", () => {
    const ensureSpy = jest.spyOn(CorrelationManager, "ensureCorrelationId");

    const first = ensureHomeCorrelation();
    const second = ensureHomeCorrelation();

    expect(first).toBeTruthy();
    expect(second).toBe(first);
    expect(ensureSpy).toHaveBeenCalledTimes(2);
    expect(window.sessionStorage.getItem("astro.correlation_id")).toBe(first);
  });

  it("builds a home trace with defaults and explicit correlation", () => {
    const trace = makeHomeTrace({
      contract: "FN-HOME-BLOCK",
      block: "HERO",
      correlation_id: "corr-explicit",
    });

    expect(trace).toEqual(expect.objectContaining({
      surface: "home",
      flow_id: HOME_FLOW_ID,
      module: HOME_MODULE_ID,
      contract: "FN-HOME-BLOCK",
      block: "HERO",
      semantic_block: "HERO",
      correlation_id: "corr-explicit",
    }));
  });

  it("falls back semantic_block to block and generated correlation", () => {
    jest.spyOn(CorrelationManager, "ensureCorrelationId").mockReturnValue("corr-generated");

    const trace = makeHomeTrace({
      contract: "FN-HOME-SECONDARY",
      block: "SECONDARY",
    });

    expect(trace.semantic_block).toBe("SECONDARY");
    expect(trace.correlation_id).toBe("corr-generated");
  });

  it("tracks home events with normalized payload and option precedence", async () => {
    jest.spyOn(CorrelationManager, "ensureCorrelationId").mockReturnValue("corr-fallback");

    await trackHomeEvent(
      "home_block_click",
      {
        entry_point: "feed",
        block: "HERO",
        semantic_block: "FEATURED_HERO",
        contract: "FN-HOME-CLICK",
        correlation_id: "corr-meta",
        extra_flag: true,
      },
      {
        correlationId: "corr-option",
        block: "OPTION_BLOCK",
      },
    );

    expect(trackEvent).toHaveBeenCalledWith(
      "home_block_click",
      expect.objectContaining({
        entry_point: "feed",
        block: "HERO",
        semantic_block: "FEATURED_HERO",
        contract: "FN-HOME-CLICK",
        correlation_id: "corr-meta",
        module: HOME_MODULE_ID,
        surface: "home",
        flow_id: HOME_FLOW_ID,
        extra_flag: true,
      }),
      expect.objectContaining({
        correlationId: "corr-option",
        flowId: HOME_FLOW_ID,
        block: "HERO",
      }),
    );
  });

  it("tracks home events with helper defaults when meta is partial", async () => {
    jest.spyOn(CorrelationManager, "ensureCorrelationId").mockReturnValue("corr-generated");

    await trackHomeEvent("home_impression", { entry_point: "home_screen" });

    expect(trackEvent).toHaveBeenCalledWith(
      "home_impression",
      expect.objectContaining({
        entry_point: "home_screen",
        contract: "FN-HOME-EVENT",
        block: "HOME_EVENT",
        semantic_block: "HOME_EVENT",
        correlation_id: "corr-generated",
        module: HOME_MODULE_ID,
        surface: "home",
        flow_id: HOME_FLOW_ID,
      }),
      expect.objectContaining({
        correlationId: "corr-generated",
        flowId: HOME_FLOW_ID,
        block: null,
      }),
    );
  });

  it("wraps fetch with home flow correlation metadata", async () => {
    jest.spyOn(CorrelationManager, "ensureCorrelationId").mockReturnValue("corr-fetch");
    const fetchMock = jest.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    global.fetch = fetchMock as typeof fetch;

    await homeFetch("/api/home", { method: "POST", headers: { Existing: "value" } }, "HOME_FEED");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0] as [RequestInfo | URL, RequestInit];
    const headers = Object.fromEntries(new Headers(init.headers).entries());
    expect(headers["existing"]).toBe("value");
    expect(headers["x-correlation-id"]).toBe("corr-fetch");
    expect(headers["x-flow-id"]).toBe(HOME_FLOW_ID);
    expect(headers["x-flow-block"]).toBe("HOME_FEED");
  });
});
