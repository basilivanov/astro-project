// START_MODULE_CONTRACT: M-WEEK-BRIEF-ADAPTER
// purpose: Normalize week report payloads into the stable week surface model consumed by route and presentation modules.
// owns:
//   - frontend/lib/week-brief.ts
// inputs:
//   - week brief DTO, legacy week map payload, deep-section chunks, report metadata
// outputs:
//   - `WeekSurfaceModel` with normalized dates, sections, CTA, and explainability labels
// dependencies:
//   - local date and text normalization helpers
// invariants:
//   - legacy and modern week sources reconcile into a single surface model
//   - degraded deep sections can be repaired from chunk payloads before rendering
// failure_policy:
//   - missing or partial payloads degrade into stable defaults rather than undefined state
// non_goals:
//   - network access or route-level telemetry
// END_MODULE_CONTRACT: M-WEEK-BRIEF-ADAPTER

// START_MODULE_MAP: M-WEEK-BRIEF-ADAPTER
// entrypoints:
//   - mapWeekReportToWeekBrief
//   - formatWeekDateRange
//   - confidenceBucket
// helpers:
//   - repairWeekBriefDeepSections
//   - normalizeStatus
//   - normalizeLegacyScore
//   - normalizeLegacyWeekday
// owned_tests:
//   - frontend/test/lib/week-brief.test.ts
// adjacent_modules:
//   - frontend/app/week/page.tsx
//   - frontend/components/week/week-hero-map.tsx
//   - frontend/lib/detail-layer.ts
// END_MODULE_MAP: M-WEEK-BRIEF-ADAPTER

import { extractReportFallbackText } from "../components/blocks/report-renderer";

export type WeekBriefStatus = "ready" | "in_progress" | "pending" | "error";
export type WeekType = "push" | "balance" | "caution" | "deep_work" | "recovery" | "transition";
export type LightStatus = "green" | "yellow" | "red";

export type ActionRiskItem = {
  id?: string | null;
  text?: string | null;
  tag?: string | null;
  factor_id?: string | null;
  impact?: string | null;
  timeframe?: string | null;
  why_text?: string | null;
  supporting_factors?: {
    label?: string | null;
    explanation_human?: string | null;
    explanation_astro?: string | null;
    value?: string | null;
  }[] | null;
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
    lead?: string | null;
    practical?: string[] | null;
    supporting_factors?: {
      label?: string | null;
      explanation_human?: string | null;
      explanation_astro?: string | null;
      value?: string | null;
    }[] | null;
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
    why_text?: string | null;
    supporting_factors?: {
      label?: string | null;
      explanation_human?: string | null;
      explanation_astro?: string | null;
      value?: string | null;
    }[] | null;
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
  dayStrip: NonNullable<WeekBrief["day_cards"]>;
  domains: NonNullable<WeekBrief["domains"]>;
  actions: ActionRiskItem[];
  risks: ActionRiskItem[];
  factors: NonNullable<WeekBrief["major_factors"]>;
  deepSections: NonNullable<WeekBrief["deep_sections"]>;
  explainabilitySummary: string;
  explainabilityDetailItems: {
    id: string;
    title: string;
    body: string | null;
    value: string | null;
  }[];
  explainability: NonNullable<WeekBrief["explainability"]>;
  confidenceLabel: string | null;
  confidenceShortLabel: string | null;
  birthTimeLabel: string;
  topSignalLabel: string | null;
  cta: NonNullable<WeekBrief["cta"]>;
  sectionsCount: number;
  waitMessage: string | null;
};

const RU_DAY_SHORT: Record<string, string> = {
  mon: "ПН",
  tue: "ВТ",
  wed: "СР",
  thu: "ЧТ",
  fri: "ПТ",
  sat: "СБ",
  sun: "ВС",
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

const compactDateLabel = (dateValue?: string | null, weekdayValue?: string | null) => {
  const normalizedWeekday = normalizeLegacyWeekday(weekdayValue);
  if (!dateValue) {
    return normalizedWeekday ? RU_DAY_SHORT[normalizedWeekday] ?? null : null;
  }

  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) {
    return normalizedWeekday ? RU_DAY_SHORT[normalizedWeekday] ?? null : null;
  }

  const dayLabel = normalizedWeekday ? RU_DAY_SHORT[normalizedWeekday] : null;
  const dateLabel = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short" })
    .format(date)
    .replace('.', '')
    .trim();

  return dayLabel ? `${dayLabel}, ${dateLabel}` : dateLabel;
};

const normalizeStripHeadline = (headline?: string | null, bestFor?: string[] | null, avoid?: string[] | null) => {
  const cleanHeadline = headline?.trim();
  if (cleanHeadline) return cleanHeadline;

  const primaryBest = normalizeList(bestFor)[0] ?? null;
  if (primaryBest) return `Фокус на ${primaryBest.toLowerCase()}`;

  const primaryRisk = normalizeList(avoid)[0] ?? null;
  if (primaryRisk) return `Держите темп без ${primaryRisk.toLowerCase()}`;

  return "Спокойный обзор дня";
};

const normalizeActionItems = (items: ActionRiskItem[] | null | undefined, fallback: string[] | null | undefined, prefix: string) => {
  if (Array.isArray(items) && items.length > 0) {
    return items
      .filter((item) => item?.text?.trim())
      .map((item, index) => ({
      id: item.id ?? `${prefix}-${index + 1}`,
      text: item.text?.trim() ?? "",
      tag: item.tag?.trim() ?? null,
      factor_id: item.factor_id ?? null,
      impact: item.impact ?? null,
      timeframe: item.timeframe ?? null,
      why_text: item.why_text?.trim() ?? null,
      supporting_factors: Array.isArray(item.supporting_factors)
        ? item.supporting_factors.filter(Boolean).map((factor) => ({
            label: factor?.label?.trim() ?? null,
            explanation_human: factor?.explanation_human?.trim() ?? null,
            explanation_astro: factor?.explanation_astro?.trim() ?? null,
            value: factor?.value?.trim() ?? null,
          }))
        : [],
      }))
      .filter((item) => item.tag !== "all_week");
  }
  return normalizeList(fallback).map((text, index) => ({ id: `${prefix}-${index + 1}`, text }));
};

// FN-CONTRACT: FN-WEEK-MAP-REPORT-TO-BRIEF
// purpose: Merge modern week brief and legacy week map payloads into one render-ready surface model.
export function mapWeekReportToWeekBrief(input: {
  weekBrief?: WeekBrief | null;
  legacyWeekMap?: LegacyWeekMapPayload | null;
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null;
  latestReportId?: string | null;
  sourceStatus?: string | null;
}): WeekSurfaceModel {
  // START_BLOCK: WEEK_BRIEF_SURFACE_MAPPING
  const brief = input.weekBrief;
  const legacy = input.legacyWeekMap;
  const chunks = Array.isArray(input.chunks) ? input.chunks : [];

  const chunkSections = chunks
    .filter((chunk) => typeof chunk?.content !== "undefined")
    .map((chunk, index) => ({
      id: chunk.id ?? `chunk-${index + 1}`,
      slug: chunk.section ?? chunk.id ?? `section-${index + 1}`,
      title: chunk.title ?? chunk.section ?? `Секция ${index + 1}`,
      summary: extractReportFallbackText(chunk.content) ?? null,
      body_markdown: typeof chunk.content === "string" ? chunk.content : JSON.stringify(chunk.content),
      is_primary: index === 0,
      order: index,
    }));

  const deepSections = brief?.deep_sections?.length
    ? repairWeekBriefDeepSections(brief.deep_sections, chunkSections)
    : chunkSections;

  const dayCards = brief?.day_cards?.length
    ? brief.day_cards
    : (legacy?.day_cards ?? []).map((item) => ({
        date: item.date ?? null,
        weekday: normalizeLegacyWeekday(item.weekday),
        mode: normalizeStatus(item.mode),
        score: normalizeLegacyScore(item.score),
        headline: item.headline ?? null,
        lead: item.headline ?? null,
        practical: normalizeList(item.best_for).slice(0, 2),
        supporting_factors: [],
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
        why_text: null,
        supporting_factors: [],
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
    dayStrip: dayCards.map((card) => ({
      date: card.date ?? null,
      weekday: compactDateLabel(card.date ?? null, card.weekday ?? null),
      mode: card.mode ?? null,
      score: card.score ?? null,
      headline: normalizeStripHeadline(card.headline, card.best_for, card.avoid),
      lead: null,
      practical: [],
      supporting_factors: [],
      best_for: normalizeList(card.best_for).slice(0, 1),
      avoid: normalizeList(card.avoid).slice(0, 1),
      peak_window_label: card.peak_window_label ?? null,
    })),
    domains,
    actions,
    risks,
    factors,
    deepSections,
    explainabilitySummary: [
      humanizeConfidence(brief?.explainability?.confidence ?? legacy?.explainability?.confidence ?? null),
      (brief?.explainability?.birth_time_used ?? legacy?.explainability?.used_exact_birth_time ?? false)
        ? "Учтено точное время рождения"
        : "Без точного времени рождения",
      humanizeTopSignalSource(brief?.explainability?.top_signal_source ?? null)
        ? `Главный слой влияния: ${humanizeTopSignalSource(brief?.explainability?.top_signal_source ?? null)}`
        : null,
    ].filter(Boolean).join('. ') + '.',
    explainabilityDetailItems: [
      {
        id: "week-explainability-confidence",
        title: "Надёжность сигнала",
        body: humanizeConfidence(brief?.explainability?.confidence ?? legacy?.explainability?.confidence ?? null),
        value: typeof (brief?.explainability?.confidence ?? legacy?.explainability?.confidence) === "number"
          ? `${Math.round((brief?.explainability?.confidence ?? legacy?.explainability?.confidence ?? 0) * 100)}%`
          : null,
      },
      {
        id: "week-explainability-birth-time",
        title: "Контекст рождения",
        body: (brief?.explainability?.birth_time_used ?? legacy?.explainability?.used_exact_birth_time ?? false)
          ? "Точная карта рождения добавляет больше персональной опоры в недельную интерпретацию."
          : "Интерпретация собрана без точного времени рождения, поэтому часть нюансов остаётся более общей.",
        value: (brief?.explainability?.birth_time_used ?? legacy?.explainability?.used_exact_birth_time ?? false)
          ? "Точное время учтено"
          : "Точное время не указано",
      },
      {
        id: "week-explainability-top-signal",
        title: "Главный слой влияния",
        body: humanizeTopSignalSource(brief?.explainability?.top_signal_source ?? null)
          ? "Именно этот слой сильнее всего формирует краткую weekly summary и рекомендации."
          : "Сигнал распределён между несколькими факторами без одного доминирующего слоя.",
        value: humanizeTopSignalSource(brief?.explainability?.top_signal_source ?? null),
      },
    ].filter((item) => item.body || item.value),
    explainability: {
      confidence: brief?.explainability?.confidence ?? legacy?.explainability?.confidence ?? null,
      birth_time_used: brief?.explainability?.birth_time_used ?? legacy?.explainability?.used_exact_birth_time ?? false,
      factor_count: brief?.explainability?.factor_count ?? factors.length,
      timing_precision: brief?.explainability?.timing_precision ?? null,
      top_signal_source: brief?.explainability?.top_signal_source ?? null,
      explanation_depth: brief?.explainability?.explanation_depth ?? null,
    },
    confidenceLabel: humanizeConfidence(brief?.explainability?.confidence ?? legacy?.explainability?.confidence ?? null),
    confidenceShortLabel: humanizeConfidenceShort(brief?.explainability?.confidence ?? legacy?.explainability?.confidence ?? null),
    birthTimeLabel: (brief?.explainability?.birth_time_used ?? legacy?.explainability?.used_exact_birth_time ?? false)
      ? "учтено точное время рождения"
      : "без точного времени рождения",
    topSignalLabel: humanizeTopSignalSource(brief?.explainability?.top_signal_source ?? null),
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
  // END_BLOCK: WEEK_BRIEF_SURFACE_MAPPING
}

// FN-CONTRACT: FN-WEEK-REPAIR-DEEP-SECTIONS
// purpose: Repair degraded deep sections by backfilling summaries and markdown from chunk payloads.
function repairWeekBriefDeepSections(
  sections: NonNullable<WeekBrief["deep_sections"]>,
  chunkSections: NonNullable<WeekBrief["deep_sections"]>,
): NonNullable<WeekBrief["deep_sections"]> {
  const hasDegradedSection = sections.some((section) => !section.body_markdown?.trim() || !section.summary?.trim());
  const chunkBySlug = new Map(chunkSections.map((section) => [section.slug ?? section.id ?? "", section]));
  const repaired = sections.map((section) => {
    const slug = section.slug ?? section.id ?? "";
    const chunkMatch = chunkBySlug.get(slug);
    const hasBody = Boolean(section.body_markdown?.trim());
    const hasSummary = Boolean(section.summary?.trim());

    if (!chunkMatch || (hasBody && hasSummary)) {
      return section;
    }

    return {
      ...section,
      summary: hasSummary ? section.summary : chunkMatch.summary,
      body_markdown: hasBody ? section.body_markdown : chunkMatch.body_markdown,
    };
  });

  if (!hasDegradedSection) {
    return repaired;
  }

  const existingSlugs = new Set(repaired.map((section) => section.slug ?? section.id ?? ""));
  const appended = chunkSections
    .filter((section) => !existingSlugs.has(section.slug ?? section.id ?? ""))
    .map((section, index) => ({
      ...section,
      is_primary: false,
      order: repaired.length + index,
    }));

  return [...repaired, ...appended];
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

// FN-CONTRACT: FN-WEEK-FORMAT-DATE-RANGE
// purpose: Format normalized week date boundaries into compact Russian UI copy.
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

// FN-CONTRACT: FN-WEEK-CONFIDENCE-BUCKET
// purpose: Collapse numeric explainability confidence into stable analytics and UI buckets.
export function confidenceBucket(confidence?: number | null): "low" | "medium" | "high" | "unknown" {
  if (typeof confidence !== "number") return "unknown";
  if (confidence >= 0.75) return "high";
  if (confidence >= 0.45) return "medium";
  return "low";
}

function humanizeConfidence(confidence?: number | null): string | null {
  const bucket = confidenceBucket(confidence);
  if (bucket === "high") return "Высокая опора на текущие данные";
  if (bucket === "medium") return "Хорошая опора на текущие данные";
  if (bucket === "low") return "Ориентир предварительный";
  return null;
}

function humanizeConfidenceShort(confidence?: number | null): string | null {
  const bucket = confidenceBucket(confidence);
  if (bucket === "high") return "высокая";
  if (bucket === "medium") return "хорошая";
  if (bucket === "low") return "предварительная";
  return null;
}

function humanizeTopSignalSource(value?: string | null): string | null {
  if (!value) return null;
  const normalized = value.trim().toLowerCase();
  const labels: Record<string, string> = {
    transit_natal: "личная натальная опора и текущие транзиты",
    natal_transit: "личная натальная опора и текущие транзиты",
    transits: "текущие транзиты",
    natal: "натальная карта",
    timing: "тайминг недели",
  };
  return labels[normalized] ?? null;
}

function parseIsoDate(value?: string | null): Date | null {
  if (!value) return null;
  const parsed = new Date(`${value}T12:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatShortDate(date: Date): string {
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short" }).format(date);
}
