// ############################################################################
// AI_HEADER: MODULE_FE_ANALYTICS
// ROLE: Frontend analytics client.
// ############################################################################

export type AnalyticsEventName = string;

type AnalyticsEventOptions = {
  telegramId?: number;
  source?: string;
  metadata?: Record<string, unknown>;
  sessionId?: string;
  path?: string;
};

export async function trackEvent(
  eventName: AnalyticsEventName,
  options: AnalyticsEventOptions = {}
) {
  try {
    const payload: any = {
      event_name: eventName,
      telegram_id: options.telegramId,
      source: options.source || "webapp",
      metadata: options.metadata,
    };
    
    if (typeof window !== "undefined") {
        payload.path = window.location.pathname;
        payload.session_id = sessionStorage.getItem("session_id") || undefined;
    }

    await fetch("/api/analytics/event", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(options.telegramId ? { "X-Telegram-Auth": options.telegramId.toString() } : {}), // Header might need fix if using initData
      },
      body: JSON.stringify(payload),
      keepalive: true,
    });
  } catch (error) {
    console.warn("analytics.track.failed", error);
  }
}