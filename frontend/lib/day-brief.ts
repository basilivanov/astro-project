// START_MODULE_CONTRACT: M-DAY-BRIEF-ADAPTER
// purpose: Normalize strict canonical day payloads into the Today view model used by the home route.
// owns:
//   - frontend/lib/day-brief.ts
// inputs:
//   - unknown API payloads, optional profile subscription context
// outputs:
//   - `TodayViewModel` and strict `DayBriefDto`
// dependencies:
//   - local coercion helpers only
// invariants:
//   - only canonical day payloads render the Today premium surface
//   - missing or failed fields resolve into explicit status markers, never synthetic prose
// failure_policy:
//   - malformed or non-canonical payloads return `null`
// non_goals:
//   - rendering, telemetry, or compatibility adapters
// END_MODULE_CONTRACT: M-DAY-BRIEF-ADAPTER

export type DayBriefLight = "green" | "yellow" | "red";
export type DayBriefScoreKey = "energy" | "money" | "love" | "focus";
export type DayBriefCtaType = "open_week" | "open_today" | "ask_question" | "open_premium" | "open_history" | "open_report" | "custom";
export type DayFieldStatus = "complete" | "failed" | "missing";
export type TodaySurfaceState = "ready" | "no_data" | "error";

export type DayDomainCard = {
  key: DayBriefScoreKey;
  title: string;
  score_status: DayFieldStatus;
  score: number | null;
  status: DayBriefLight | null;
  description_status: DayFieldStatus;
  description: string | null;
  why_status: DayFieldStatus;
  why_astro_text: string | null;
  evidence_refs: Array<Record<string, unknown>>;
};

export type DayBriefDto = {
  version: "day_brief_canon_v1";
  status: "complete" | "partial" | "failed";
  date: string;
  personalization_level: string;
  hero: {
    title: string;
    subtitle: string;
    day_type: "push" | "balance" | "caution" | "deep_focus" | "recovery";
    tone?: string | null;
  };
  domains: Record<DayBriefScoreKey, DayDomainCard>;
  premium?: {
    subscription_active: boolean;
    subscription_active_until?: string | null;
    days_left?: number | null;
    show_upgrade_cta?: boolean;
    show_resume_banner?: boolean;
  } | null;
  cta?: {
    primary?: { type: DayBriefCtaType; label: string; href: string } | null;
    secondary?: { type: DayBriefCtaType; label: string; href: string } | null;
  } | null;
};

export type TodayViewModel = {
  brief: DayBriefDto;
  premiumActiveUntil: string | null;
  state: TodaySurfaceState;
  usesCanonicalDayBrief: true;
};

const DAY_KEYS: DayBriefScoreKey[] = ["energy", "money", "love", "focus"];

const DAY_TITLES: Record<DayBriefScoreKey, string> = {
  energy: "Тонус",
  money: "Работа и деньги",
  love: "Чувства",
  focus: "Фокус",
};

const isRecord = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === "object");
const text = (value: unknown, fallback = ""): string => typeof value === "string" ? value : fallback;
const bool = (value: unknown, fallback = false): boolean => typeof value === "boolean" ? value : fallback;
const num = (value: unknown, fallback = 0): number => typeof value === "number" && Number.isFinite(value) ? value : fallback;
const clampScore = (value: unknown): number | null => typeof value === "number" && Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value))) : null;

function normalizeFieldStatus(value: unknown): DayFieldStatus {
  return value === "complete" || value === "failed" || value === "missing" ? value : "missing";
}

function resolveSurfaceState(brief: DayBriefDto): TodaySurfaceState {
  if (brief.status === "failed") {
    return "error";
  }
  if (hasAnyCompleteDayDomain(brief)) {
    return "ready";
  }
  return "no_data";
}

function normalizeLight(value: unknown): DayBriefLight | null {
  return value === "green" || value === "yellow" || value === "red" ? value : null;
}

function normalizeTextField(value: unknown): string | null {
  const normalized = text(value).trim();
  return normalized || null;
}

function normalizeEvidenceRefs(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).slice(0, 4).map((item) => ({ ...item }));
}

function normalizeDomainCard(key: DayBriefScoreKey, value: unknown): DayDomainCard {
  const item = isRecord(value) ? value : {};
  const score = clampScore(item.score);
  const scoreStatus = normalizeFieldStatus(item.score_status);
  const description = normalizeTextField(item.description);
  const descriptionStatus = normalizeFieldStatus(item.description_status);
  const whyText = normalizeTextField(item.why_astro_text);
  const whyStatus = normalizeFieldStatus(item.why_status);

  return {
    key,
    title: text(item.title, DAY_TITLES[key]),
    score_status: scoreStatus,
    score,
    status: normalizeLight(item.status),
    description_status: descriptionStatus,
    description,
    why_status: whyStatus,
    why_astro_text: whyText,
    evidence_refs: normalizeEvidenceRefs(item.evidence_refs),
  };
}

function normalizeDomains(value: unknown): Record<DayBriefScoreKey, DayDomainCard> {
  const source = isRecord(value) ? value : {};
  return {
    energy: normalizeDomainCard("energy", source.energy),
    money: normalizeDomainCard("money", source.money),
    love: normalizeDomainCard("love", source.love),
    focus: normalizeDomainCard("focus", source.focus),
  };
}

export function normalizeDayBriefPayload(payload: unknown, profile?: { subscription_active_until?: string | null } | null): TodayViewModel | null {
  const source = isRecord(payload) && isRecord(payload.day_brief) ? payload.day_brief : payload;
  if (!isRecord(source)) return null;

  const version = text(source.version);
  if (version !== "day_brief_canon_v1") {
    return null;
  }

  const premiumActiveUntil = typeof profile?.subscription_active_until === "string" ? profile.subscription_active_until : null;
  const domains = normalizeDomains(source.domains);
  const brief: DayBriefDto = {
    version,
    status: source.status === "complete" || source.status === "partial" || source.status === "failed" ? source.status : "failed",
    date: text(source.date),
    personalization_level: text(source.personalization_level, "personalized_v2"),
    hero: {
      title: text(isRecord(source.hero) ? source.hero.title : undefined, "Сегодня"),
      subtitle: text(isRecord(source.hero) ? source.hero.subtitle : undefined, "Четыре ключевые сферы на сегодня."),
      day_type: (["push", "balance", "caution", "deep_focus", "recovery"].includes(text(isRecord(source.hero) ? source.hero.day_type : undefined))
        ? text(isRecord(source.hero) ? source.hero.day_type : undefined)
        : "balance") as DayBriefDto["hero"]["day_type"],
      tone: isRecord(source.hero) && typeof source.hero.tone === "string" ? source.hero.tone : null,
    },
    domains,
    premium: isRecord(source.premium) ? {
      subscription_active: bool(source.premium.subscription_active, false),
      subscription_active_until: typeof source.premium.subscription_active_until === "string" ? source.premium.subscription_active_until : premiumActiveUntil,
      days_left: typeof source.premium.days_left === "number" ? source.premium.days_left : null,
      show_upgrade_cta: bool(source.premium.show_upgrade_cta, false),
      show_resume_banner: bool(source.premium.show_resume_banner, false),
    } : {
      subscription_active: Boolean(premiumActiveUntil),
      subscription_active_until: premiumActiveUntil,
      days_left: null,
      show_upgrade_cta: !premiumActiveUntil,
      show_resume_banner: false,
    },
    cta: isRecord(source.cta) ? {
      primary: isRecord(source.cta.primary) ? { type: (text(source.cta.primary.type, "open_week") as DayBriefCtaType), label: text(source.cta.primary.label, "Открыть неделю"), href: text(source.cta.primary.href, "/week") } : null,
      secondary: isRecord(source.cta.secondary) ? { type: (text(source.cta.secondary.type, "open_premium") as DayBriefCtaType), label: text(source.cta.secondary.label, "История разборов"), href: text(source.cta.secondary.href, "/reports/history") } : null,
    } : {
      primary: { type: "open_week", label: "Открыть неделю", href: "/week" },
      secondary: { type: premiumActiveUntil ? "open_history" : "open_premium", label: premiumActiveUntil ? "История разборов" : "Открыть premium", href: premiumActiveUntil ? "/reports/history" : "/reports" },
    },
  };

  return {
    brief,
    premiumActiveUntil: brief.premium?.subscription_active_until ?? premiumActiveUntil,
    state: resolveSurfaceState(brief),
    usesCanonicalDayBrief: true,
  };
}

export function hasCompleteDayDomain(brief: DayBriefDto, key: DayBriefScoreKey): boolean {
  const domain = brief.domains[key];
  return Boolean(domain && domain.score_status === "complete" && domain.description_status === "complete" && domain.why_status === "complete" && domain.score !== null && domain.description && domain.why_astro_text);
}

export function hasAnyCompleteDayDomain(brief: DayBriefDto): boolean {
  return DAY_KEYS.some((key) => hasCompleteDayDomain(brief, key));
}
