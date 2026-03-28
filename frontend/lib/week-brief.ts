import { extractReportFallbackText } from "../components/blocks/report-renderer";

export type WeekBriefStatus = "ready" | "in_progress" | "pending" | "error";
export type WeekType = "push" | "balance" | "caution" | "deep_work" | "recovery" | "transition";
export type LightStatus = "green" | "yellow" | "red";

export type ActionRiskItem = {
  id?: string | null;
  text?: string | null;
  factor_id?: string | null;
  impact?: string | null;
  timeframe?: string | null;
};

export type WeekBriefCtaLink = {
  type?: string | null;
  label?: string | null;
  href?: string | null;
};

export type WeekBrief = {
  version?: string | null;
  week_start?: string | null;
  week_end?: string | null;
  personalization_level?: string | null;
  fallback_mode?: boolean;
  status?: WeekBriefStatus | null;
  summary?: {
    headline?: string | null;
    subhead?: string | null;
    week_type?: WeekType | null;
    theme?: string | null;
  } | null;
  day_cards?: {
    date?: string | null;
    weekday?: string | null;
    mode?: LightStatus | null;
    score?: number | null;
    headline?: string | null;
    best_for?: string[] | null;
    avoid?: string[] | null;
    peak_window_label?: string | null;
  }[] | null;
  domains?: {
    key?: string | null;
    title?: string | null;
    status?: LightStatus | null;
    value?: number | null;
    headline?: string | null;
    advice?: string | null;
  }[] | null;
  best_uses?: ActionRiskItem[] | null;
  risks?: ActionRiskItem[] | null;
  major_factors?: {
    id?: string | null;
    label?: string | null;
    impact?: string | null;
    category?: string | null;
    explanation_human?: string | null;
    explanation_astro?: string | null;
    source_models?: string[] | null;
    weight?: number | null;
  }[] | null;
  deep_sections?: {
    id?: string | null;
    slug?: string | null;
    title?: string | null;
    summary?: string | null;
    body_markdown?: string | null;
    is_primary?: boolean;
    order?: number | null;
  }[] | null;
  explainability?: {
    confidence?: number | null;
    birth_time_used?: boolean;
    factor_count?: number | null;
    timing_precision?: string | null;
    top_signal_source?: string | null;
    explanation_depth?: string | null;
  } | null;
  premium?: {
    subscription_active?: boolean;
    show_upgrade_cta?: boolean;
    show_resume_banner?: boolean;
  } | null;
  cta?: {
    primary?: WeekBriefCtaLink | null;
    secondary?: WeekBriefCtaLink | null;
  } | null;
  report_ref?: {
    report_id?: string | null;
    report_type?: string | null;
    source_status?: string | null;
    generated_at?: string | null;
  } | null;
};

export type LegacyWeekMapPayload = {
  thesis?: string | null;
  theme?: string | null;
  day_cards?: {
    date?: string | null;
    weekday?: string | null;
    headline?: string | null;
    mode?: string | null;
    score?: number | null;
    best_for?: string[] | null;
    avoid?: string[] | null;
  }[] | null;
  domains?: Record<string, number> | null;
  major_factors?: {
    label?: string | null;
    category?: string | null;
    impact_pct?: number | null;
    impact?: number | null;
    explanation?: string | null;
    confidence?: number | null;
  }[] | null;
  actions?: string[] | null;
  risks?: string[] | null;
  deep_sections?: string[] | null;
  explainability?: {
    total_score?: number | null;
    confidence?: number | null;
    used_exact_birth_time?: boolean;
    pipeline?: { category?: string | null; weight_share?: number | null; impact?: number | null }[] | null;
  } | null;
  timezone?: string | null;
  location?: string | null;
  week_start?: string | null;
};

export type WeekSurfaceModel = {
  headline: string;
  subhead: string;
  theme: string;
  weekType: WeekType | "balance";
  status: WeekBriefStatus;
  weekStart: string | null;
  weekEnd: string | null;
  timezone: string | null;
  location: string | null;
  personalizationLevel: string | null;
  fallbackMode: boolean;
  reportId: string | null;
  dayCards: NonNullable<WeekBrief["day_cards"]>;
  domains: NonNullable<WeekBrief["domains"]>;
  actions: ActionRiskItem[];
  risks: ActionRiskItem[];
  factors: NonNullable<WeekBrief["major_factors"]>;
  deepSections: NonNullable<WeekBrief["deep_sections"]>;
  explainability: NonNullable<WeekBrief["explainability"]>;
  cta: NonNullable<WeekBrief["cta"]>;
  sectionsCount: number;
  waitMessage: string | null;
};

const LEGACY_DOMAIN_TITLES: Record<string, string> = {
  work: "Работа и деньги",
  work_money: "Работа и деньги",
  relationships: "Отношения",
  energy: "Энергия",
  focus: "Фокус",
};

const LEGACY_STATUS_BY_SCORE = (value: number): LightStatus => {
  if (value >= 70) return "green";
  if (value >= 45) return "yellow";
  return "red";
};

const normalizeList = (value: string[] | null | undefined): string[] =>
  Array.isArray(value) ? value.map((item) => item?.trim()).filter(Boolean) as string[] : [];

const normalizeActionItems = (items: ActionRiskItem[] | null | undefined, fallback: string[] | null | undefined, prefix: string) => {
  if (Array.isArray(items) && items.length > 0) {
    return items.filter((item) => item?.text?.trim()).map((item, index) => ({
      id: item.id ?? `${prefix}-${index + 1}`,
      text: item.text?.trim() ?? "",
      factor_id: item.factor_id ?? null,
      impact: item.impact ?? null,
      timeframe: item.timeframe ?? null,
    }));
  }
  return normalizeList(fallback).map((text, index) => ({ id: `${prefix}-${index + 1}`, text }));
};

export function mapWeekReportToWeekBrief(input: {
  weekBrief?: WeekBrief | null;
  legacyWeekMap?: LegacyWeekMapPayload | null;
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null;
  latestReportId?: string | null;
  sourceStatus?: string | null;
}): WeekSurfaceModel {
  const brief = input.weekBrief;
  const legacy = input.legacyWeekMap;
  const chunks = Array.isArray(input.chunks) ? input.chunks : [];

  const deepSections = (brief?.deep_sections?.length
    ? brief.deep_sections
    : chunks
        .filter((chunk) => typeof chunk?.content !== "undefined")
        .map((chunk, index) => ({
          id: chunk.id ?? `chunk-${index + 1}`,
          slug: chunk.section ?? chunk.id ?? `section-${index + 1}`,
          title: chunk.title ?? chunk.section ?? `Секция ${index + 1}`,
          summary: extractReportFallbackText(chunk.content) ?? null,
          body_markdown: typeof chunk.content === "string" ? chunk.content : JSON.stringify(chunk.content),
          is_primary: index === 0,
          order: index,
        }))) ?? [];

  const dayCards = brief?.day_cards?.length
    ? brief.day_cards
    : (legacy?.day_cards ?? []).map((item) => ({
        date: item.date ?? null,
        weekday: normalizeLegacyWeekday(item.weekday),
        mode: normalizeStatus(item.mode),
        score: normalizeLegacyScore(item.score),
        headline: item.headline ?? null,
        best_for: normalizeList(item.best_for),
        avoid: normalizeList(item.avoid),
        peak_window_label: null,
      }));

  const domains = brief?.domains?.length
    ? brief.domains
    : Object.entries(legacy?.domains ?? {}).map(([key, value]) => ({
        key,
        title: LEGACY_DOMAIN_TITLES[key] ?? key,
        status: LEGACY_STATUS_BY_SCORE(Number(value ?? 0)),
        value: Number(value ?? 0),
        headline: `${LEGACY_DOMAIN_TITLES[key] ?? key}: ${Number(value ?? 0)}/100`,
        advice: null,
      }));

  const actions = normalizeActionItems(brief?.best_uses, legacy?.actions, "action");
  const risks = normalizeActionItems(brief?.risks, legacy?.risks, "risk");
  const factors = brief?.major_factors ?? (legacy?.major_factors ?? []).map((item, index) => ({
    id: `factor-${index + 1}`,
    label: item.label ?? `Фактор ${index + 1}`,
    impact: item.impact_pct && item.impact_pct >= 35 ? "high" : item.impact_pct && item.impact_pct >= 18 ? "medium" : "low",
    category: item.category ?? null,
    explanation_human: item.explanation ?? null,
    explanation_astro: null,
    source_models: null,
    weight: typeof item.impact_pct === "number" ? Math.max(0, Math.min(1, item.impact_pct / 100)) : null,
  }));

  return {
    headline: brief?.summary?.headline?.trim() || legacy?.thesis?.trim() || "Неделя держится на спокойном темпе и точных решениях",
    subhead: brief?.summary?.subhead?.trim() || legacy?.theme?.trim() || "Двигайте главное в коротких циклах и оставляйте буфер для корректировок.",
    theme: brief?.summary?.theme?.trim() || legacy?.theme?.trim() || "Карта недели",
    weekType: brief?.summary?.week_type ?? "balance",
    status: brief?.status ?? (input.sourceStatus === "in_progress" ? "in_progress" : input.sourceStatus === "pending" ? "pending" : "ready"),
    weekStart: brief?.week_start ?? legacy?.week_start ?? null,
    weekEnd: brief?.week_end ?? null,
    timezone: legacy?.timezone ?? null,
    location: legacy?.location ?? null,
    personalizationLevel: brief?.personalization_level ?? null,
    fallbackMode: Boolean(brief?.fallback_mode),
    reportId: brief?.report_ref?.report_id ?? input.latestReportId ?? null,
    dayCards,
    domains,
    actions,
    risks,
    factors,
    deepSections,
    explainability: {
      confidence: brief?.explainability?.confidence ?? legacy?.explainability?.confidence ?? null,
      birth_time_used: brief?.explainability?.birth_time_used ?? legacy?.explainability?.used_exact_birth_time ?? false,
      factor_count: brief?.explainability?.factor_count ?? factors.length,
      timing_precision: brief?.explainability?.timing_precision ?? null,
      top_signal_source: brief?.explainability?.top_signal_source ?? null,
      explanation_depth: brief?.explainability?.explanation_depth ?? null,
    },
    cta: {
      primary: brief?.cta?.primary ?? null,
      secondary: brief?.cta?.secondary ?? null,
    },
    sectionsCount: deepSections.length,
    waitMessage:
      brief?.status === "in_progress" || brief?.status === "pending" || input.sourceStatus === "in_progress" || input.sourceStatus === "pending"
        ? legacy?.thesis?.trim() || "Неделя собирается, лог уже в работе"
        : null,
  };
}

function normalizeStatus(value: string | null | undefined): LightStatus {
  const normalized = value?.toLowerCase();
  if (normalized === "green") return "green";
  if (normalized === "yellow") return "yellow";
  return "red";
}

function normalizeLegacyScore(value: number | null | undefined): number {
  if (typeof value !== "number" || Number.isNaN(value)) return 50;
  if (value <= 1) return Math.round(value * 100);
  if (value <= 3) return Math.max(0, Math.min(100, Math.round(100 - value * 25)));
  return Math.max(0, Math.min(100, Math.round(value)));
}

function normalizeLegacyWeekday(value: string | null | undefined): string | null {
  if (!value) return null;
  const normalized = value.trim().toLowerCase();
  const map: Record<string, string> = {
    понедельник: "mon",
    вторник: "tue",
    среда: "wed",
    четверг: "thu",
    пятница: "fri",
    суббота: "sat",
    воскресенье: "sun",
    mon: "mon",
    tue: "tue",
    wed: "wed",
    thu: "thu",
    fri: "fri",
    sat: "sat",
    sun: "sun",
  };
  return map[normalized] ?? value;
}

export function formatWeekDateRange(start?: string | null, end?: string | null): string {
  if (!start && !end) return "Неделя без даты";
  const startDate = parseIsoDate(start);
  const endDate = parseIsoDate(end);
  if (startDate && endDate) {
    return `${formatShortDate(startDate)} — ${formatShortDate(endDate)}`;
  }
  if (startDate) return formatShortDate(startDate);
  if (endDate) return formatShortDate(endDate);
  return start ?? end ?? "Неделя без даты";
}

export function confidenceBucket(confidence?: number | null): "low" | "medium" | "high" | "unknown" {
  if (typeof confidence !== "number") return "unknown";
  if (confidence >= 0.75) return "high";
  if (confidence >= 0.45) return "medium";
  return "low";
}

function parseIsoDate(value?: string | null): Date | null {
  if (!value) return null;
  const parsed = new Date(`${value}T12:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatShortDate(date: Date): string {
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short" }).format(date);
}
