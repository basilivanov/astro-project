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
//   - canonical `week_brief` and compatibility `week_map/chunks` stay on separate mapping paths
//   - degraded deep sections are rendered only inside the explicit compatibility branch
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
//   - legacyWeekMapToCompatibilityBrief
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
import { dedupeSemanticTexts, normalizeWeekDetailItems, type DetailLayer } from "./detail-layer";

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
    id?: string | null;
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
    details?: {
      why_text?: string | null;
      why_title?: string | null;
      supporting_factors?: {
        label?: string | null;
        explanation_human?: string | null;
        explanation_astro?: string | null;
        value?: string | null;
      }[] | null;
    } | null;
    factor_ids?: string[] | null;
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

export function hasExplicitWeekCompatibilityPayload(input: {
  legacyWeekMap?: LegacyWeekMapPayload | null;
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null;
}): boolean {
  return Boolean(input.legacyWeekMap) || Boolean(input.chunks?.length);
}

export type WeekSurfaceModel = {
  surfaceMode: "canonical" | "compatibility";
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
  usesCanonicalWeekBrief: boolean;
  reportId: string | null;
  dayCards: NonNullable<WeekBrief["day_cards"]>;
  dayStrip: NonNullable<WeekBrief["day_cards"]>;
  domains: NonNullable<WeekBrief["domains"]>;
  actions: ActionRiskItem[];
  risks: ActionRiskItem[];
  factors: NonNullable<WeekBrief["major_factors"]>;
  detailLayers: DetailLayer[];
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

const WEEKDAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;
const WEEKDAY_INDEX = WEEKDAY_ORDER.reduce<Record<string, number>>((acc, day, index) => {
  acc[day] = index;
  return acc;
}, {});

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
  Array.isArray(value) ? dedupeSemanticTexts(value) : [];

function normalizeComparableText(value: string | null | undefined): string {
  return String(value ?? "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const INTERNAL_VISIBLE_TOKEN_PATTERN = /\b(?:legacy|fallback|week_?map|weekbrief|compatibility|headline|markdown|weekly report)\b/i;
const RAW_SLUG_VISIBLE_PATTERN = /^[a-z0-9]+(?:[_:-][a-z0-9]+)+$/i;

function sanitizeVisibleWeekText(
  value: string | null | undefined,
  fallback: string,
  options?: { allowAscii?: boolean },
): string {
  const raw = String(value || "").trim();
  if (!raw) return fallback;
  if (INTERNAL_VISIBLE_TOKEN_PATTERN.test(raw)) return fallback;
  if (RAW_SLUG_VISIBLE_PATTERN.test(raw)) return fallback;
  if (!options?.allowAscii && /^[a-z][a-z0-9\s-]{2,}$/i.test(raw) && !/[А-Яа-яЁё]/.test(raw)) {
    return fallback;
  }
  return raw;
}

function sanitizeVisibleWeekMetaValue(value: string | null | undefined): string | null {
  const raw = String(value || "").trim();
  if (!raw) return null;
  if (INTERNAL_VISIBLE_TOKEN_PATTERN.test(raw)) return null;
  if (RAW_SLUG_VISIBLE_PATTERN.test(raw)) return null;
  if (/^[a-z][a-z0-9\s._-]{2,}$/i.test(raw) && !/[А-Яа-яЁё]/.test(raw) && !raw.includes("/")) {
    return null;
  }
  return raw;
}

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function addUtcDays(date: Date, days: number): Date {
  const next = new Date(date.getTime());
  next.setUTCDate(next.getUTCDate() + days);
  return next;
}

function startOfCalendarWeek(date: Date): Date {
  const offset = (date.getUTCDay() + 6) % 7;
  return addUtcDays(date, -offset);
}

function endOfCalendarWeek(date: Date): Date {
  return addUtcDays(startOfCalendarWeek(date), 6);
}

function sortDayCardsMondayToSunday(dayCards: NonNullable<WeekBrief["day_cards"]>) {
  return [...dayCards].sort((left, right) => {
    const leftDate = parseIsoDate(left.date);
    const rightDate = parseIsoDate(right.date);
    if (leftDate && rightDate) {
      return leftDate.getTime() - rightDate.getTime();
    }
    if (leftDate) return -1;
    if (rightDate) return 1;
    const leftWeekday = WEEKDAY_INDEX[normalizeLegacyWeekday(left.weekday) ?? ""] ?? Number.MAX_SAFE_INTEGER;
    const rightWeekday = WEEKDAY_INDEX[normalizeLegacyWeekday(right.weekday) ?? ""] ?? Number.MAX_SAFE_INTEGER;
    return leftWeekday - rightWeekday;
  });
}

function resolveCalendarWeekBounds(brief: WeekBrief, dayCards: NonNullable<WeekBrief["day_cards"]>) {
  const anchor =
    parseIsoDate(brief.week_start)
    ?? parseIsoDate(brief.week_end)
    ?? sortDayCardsMondayToSunday(dayCards).map((card) => parseIsoDate(card.date)).find((value): value is Date => Boolean(value))
    ?? null;

  if (!anchor) {
    return {
      weekStart: brief.week_start ?? null,
      weekEnd: brief.week_end ?? null,
    };
  }

  const weekStart = startOfCalendarWeek(anchor);
  const weekEnd = endOfCalendarWeek(anchor);
  return {
    weekStart: toIsoDate(weekStart),
    weekEnd: toIsoDate(weekEnd),
  };
}

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

function compactRhythmFallbackHeadline(card: NonNullable<WeekBrief["day_cards"]>[number], index: number): string {
  const best = normalizeList(card.best_for)[0] ?? null;
  const avoid = normalizeList(card.avoid)[0] ?? null;
  if (best) return `Фокус: ${best}`;
  if (avoid) return `Без ${avoid.toLowerCase()}`;
  if (card.mode === "red") return "Сбавьте нажим";
  if (card.mode === "yellow") return "Проверьте ход";
  if (card.mode === "green") return index === 0 ? "Соберите старт" : "Держите главное";
  return "Спокойный ритм";
}

function dedupeRhythmCards(cards: NonNullable<WeekBrief["day_cards"]>) {
  const seen = new Map<string, number>();

  return cards.map((card, index) => {
    const normalizedHeadline = normalizeComparableText(card.headline);
    if (!normalizedHeadline) return card;

    const seenCount = seen.get(normalizedHeadline) ?? 0;
    seen.set(normalizedHeadline, seenCount + 1);

    if (seenCount === 0) return card;

    return {
      ...card,
      headline: compactRhythmFallbackHeadline(card, index),
    };
  });
}

const normalizeActionItems = (items: ActionRiskItem[] | null | undefined, fallback: string[] | null | undefined, prefix: string) => {
  if (Array.isArray(items) && items.length > 0) {
    return items
      .filter((item) => sanitizeVisibleWeekMetaValue(item?.text) || item?.why_text?.trim())
      .map((item, index) => ({
      id: item.id ?? `${prefix}-${index + 1}`,
      text: sanitizeVisibleWeekMetaValue(item.text) ?? "Короткий ориентир",
      tag: item.tag?.trim() ?? null,
      factor_id: item.factor_id ?? null,
      impact: item.impact ?? null,
      timeframe: item.timeframe ?? null,
      why_text: sanitizeVisibleWeekMetaValue(item.why_text) ?? null,
      supporting_factors: Array.isArray(item.supporting_factors)
        ? item.supporting_factors.filter(Boolean).map((factor) => ({
            label: sanitizeVisibleWeekMetaValue(factor?.label) ?? null,
            explanation_human: sanitizeVisibleWeekMetaValue(factor?.explanation_human) ?? null,
            explanation_astro: sanitizeVisibleWeekMetaValue(factor?.explanation_astro) ?? null,
            value: sanitizeVisibleWeekMetaValue(factor?.value) ?? null,
          }))
        : [],
      }))
      .filter((item) => item.tag !== "all_week");
  }
  return dedupeSemanticTexts(fallback ?? [])
    .map((text) => sanitizeVisibleWeekMetaValue(text))
    .filter((text): text is string => Boolean(text))
    .map((text, index) => ({ id: `${prefix}-${index + 1}`, text }));
};

function normalizeChunkSections(
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null,
): NonNullable<WeekBrief["deep_sections"]> {
  return (Array.isArray(chunks) ? chunks : [])
    .filter((chunk) => typeof chunk?.content !== "undefined")
    .map((chunk, index) => ({
      id: chunk.id ?? `chunk-${index + 1}`,
      slug: chunk.section ?? chunk.id ?? `section-${index + 1}`,
      title: sanitizeVisibleWeekText(chunk.title ?? chunk.section ?? null, `Раздел ${index + 1}`),
      summary: sanitizeVisibleWeekMetaValue(extractReportFallbackText(chunk.content)) ?? null,
      body_markdown: typeof chunk.content === "string" ? chunk.content : JSON.stringify(chunk.content),
      is_primary: index === 0,
      order: index,
    }));
}

function legacyWeekMapToCompatibilityBrief(
  legacyWeekMap?: LegacyWeekMapPayload | null,
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null,
): WeekBrief {
  const legacy = legacyWeekMap ?? null;
  const chunkSections = normalizeChunkSections(chunks);

  return {
    version: "week_brief_v1",
    fallback_mode: true,
    week_start: legacy?.week_start ?? null,
    summary: {
      headline: sanitizeVisibleWeekText(legacy?.thesis, "Неделя в коротком обзоре"),
      subhead: sanitizeVisibleWeekText(legacy?.theme, "Сейчас доступна спокойная короткая карта по дням и главным акцентам."),
      week_type: "balance",
      theme: sanitizeVisibleWeekText(legacy?.theme, "Короткий ориентир"),
    },
    day_cards: (legacy?.day_cards ?? []).map((item, index) => ({
      id: item.date ? `week-day-${item.date}` : `week-day-${index + 1}`,
      date: item.date ?? null,
      weekday: normalizeLegacyWeekday(item.weekday),
      mode: normalizeStatus(item.mode),
      score: normalizeLegacyScore(item.score),
      headline: sanitizeVisibleWeekMetaValue(item.headline) ?? null,
      lead: null,
      practical: [],
      supporting_factors: [],
      details: {
        why_text: null,
        why_title: null,
        supporting_factors: [],
      },
      factor_ids: [],
      best_for: normalizeList(item.best_for),
      avoid: normalizeList(item.avoid),
      peak_window_label: null,
    })),
    domains: Object.entries(legacy?.domains ?? {}).map(([key, value]) => ({
      key,
      title: LEGACY_DOMAIN_TITLES[key] ?? "Общий фокус",
      status: LEGACY_STATUS_BY_SCORE(Number(value ?? 0)),
      value: Number(value ?? 0),
      headline: `${LEGACY_DOMAIN_TITLES[key] ?? "Общий фокус"}: ${Number(value ?? 0)}/100`,
      advice: null,
      why_text: null,
      supporting_factors: [],
    })),
    best_uses: normalizeActionItems(null, legacy?.actions, "action"),
    risks: normalizeActionItems(null, legacy?.risks, "risk"),
    major_factors: (legacy?.major_factors ?? []).map((item, index) => ({
      id: `factor-${index + 1}`,
      label: item.label ?? `Фактор ${index + 1}`,
      impact: item.impact_pct && item.impact_pct >= 35 ? "high" : item.impact_pct && item.impact_pct >= 18 ? "medium" : "low",
      category: item.category ?? null,
      explanation_human: item.explanation ?? null,
      explanation_astro: null,
      source_models: null,
      weight: typeof item.impact_pct === "number" ? Math.max(0, Math.min(1, item.impact_pct / 100)) : null,
    })),
    deep_sections: chunkSections,
    explainability: {
      confidence: legacy?.explainability?.confidence ?? null,
      birth_time_used: legacy?.explainability?.used_exact_birth_time ?? false,
      factor_count: null,
      timing_precision: null,
      top_signal_source: null,
      explanation_depth: null,
    },
    cta: {
      primary: null,
      secondary: null,
    },
  };
}

function buildWeekSurfaceModel(input: {
  brief: WeekBrief;
  latestReportId?: string | null;
  sourceStatus?: string | null;
  surfaceMode: WeekSurfaceModel["surfaceMode"];
  usesCanonicalWeekBrief: boolean;
  timezone?: string | null;
  location?: string | null;
  waitMessageFallback?: string | null;
}): WeekSurfaceModel {
  const brief = input.brief;
  const rawDayCards = brief.day_cards ?? [];
  const calendarBounds = resolveCalendarWeekBounds(brief, rawDayCards);
  const dayCards = sortDayCardsMondayToSunday(rawDayCards);
  const actions = normalizeActionItems(brief.best_uses, null, "action");
  const risks = normalizeActionItems(brief.risks, null, "risk");
  const factors = brief.major_factors ?? [];
  const detailLayers = normalizeWeekDetailItems({
    ...brief,
    best_uses: actions,
    risks,
    major_factors: factors,
  });
  const confidence = brief.explainability?.confidence ?? null;
  const birthTimeUsed = brief.explainability?.birth_time_used ?? false;
  const topSignalLabel = humanizeTopSignalSource(brief.explainability?.top_signal_source ?? null);
  const explainabilitySummaryParts = [
    humanizeConfidence(confidence),
    birthTimeUsed ? "Учтено точное время рождения" : "Без точного времени рождения",
    topSignalLabel ? `Главный слой влияния: ${topSignalLabel}` : null,
  ].filter(Boolean);

  const stripByDate = new Map(dayCards.filter((card) => Boolean(card.date)).map((card) => [card.date as string, card]));
  const stripByWeekday = new Map(dayCards.map((card) => [normalizeLegacyWeekday(card.weekday), card] as const).filter((entry): entry is [string, NonNullable<WeekBrief["day_cards"]>[number]] => Boolean(entry[0])));
  const dayStripBase: NonNullable<WeekBrief["day_cards"]> = calendarBounds.weekStart
    ? WEEKDAY_ORDER.map((weekday, index) => {
        const date = toIsoDate(addUtcDays(parseIsoDate(calendarBounds.weekStart)!, index));
        const card = stripByDate.get(date) ?? stripByWeekday.get(weekday) ?? null;
        return {
          id: card?.id ?? `week-day-shell-${date}`,
          date,
          weekday: compactDateLabel(date, weekday),
          mode: card?.mode ?? null,
          score: card?.score ?? null,
          headline: card ? normalizeStripHeadline(card.headline, card.best_for, card.avoid) : null,
          lead: null,
          practical: [],
          supporting_factors: [],
          details: { why_text: null, why_title: null, supporting_factors: [] },
          factor_ids: Array.isArray(card?.factor_ids) ? card?.factor_ids : [],
          best_for: normalizeList(card?.best_for).slice(0, 1),
          avoid: normalizeList(card?.avoid).slice(0, 1),
          peak_window_label: card?.peak_window_label ?? null,
        };
      })
    : dayCards.map((card) => ({
        id: card.id ?? null,
        date: card.date ?? null,
        weekday: compactDateLabel(card.date ?? null, card.weekday ?? null),
        mode: card.mode ?? null,
        score: card.score ?? null,
        headline: normalizeStripHeadline(card.headline, card.best_for, card.avoid),
        lead: null,
        practical: [],
        supporting_factors: [],
        details: { why_text: null, why_title: null, supporting_factors: [] },
        factor_ids: Array.isArray(card.factor_ids) ? card.factor_ids : [],
        best_for: normalizeList(card.best_for).slice(0, 1),
        avoid: normalizeList(card.avoid).slice(0, 1),
        peak_window_label: card.peak_window_label ?? null,
      }));
  const dayStrip = dedupeRhythmCards(dayStripBase);

  return {
    surfaceMode: input.surfaceMode,
    headline: sanitizeVisibleWeekText(
      brief.summary?.headline,
      input.surfaceMode === "compatibility" ? "Неделя в коротком обзоре" : "Неделя держится на спокойном темпе и точных решениях",
    ),
    subhead: sanitizeVisibleWeekText(
      brief.summary?.subhead,
      input.surfaceMode === "compatibility"
        ? "Сейчас доступна спокойная короткая карта по дням и главным акцентам."
        : "Двигайте главное в коротких циклах и оставляйте буфер для корректировок.",
    ),
    theme: sanitizeVisibleWeekText(
      brief.summary?.theme,
      brief.status === "in_progress" || brief.status === "pending" || input.sourceStatus === "in_progress" || input.sourceStatus === "pending"
        ? "Тема уточняется"
        : input.surfaceMode === "compatibility"
          ? "Короткий ориентир"
          : "Карта недели",
    ),
    weekType: brief.summary?.week_type ?? "balance",
    status: brief.status ?? (input.sourceStatus === "in_progress" ? "in_progress" : input.sourceStatus === "pending" ? "pending" : "ready"),
    weekStart: calendarBounds.weekStart,
    weekEnd: calendarBounds.weekEnd,
    timezone: sanitizeVisibleWeekMetaValue(input.timezone) ?? null,
    location: sanitizeVisibleWeekMetaValue(input.location) ?? null,
    personalizationLevel: brief.personalization_level ?? null,
    fallbackMode: input.surfaceMode === "compatibility" || Boolean(brief.fallback_mode),
    usesCanonicalWeekBrief: input.usesCanonicalWeekBrief,
    reportId: brief.report_ref?.report_id ?? input.latestReportId ?? null,
    dayCards,
    dayStrip,
    domains: brief.domains ?? [],
    actions,
    risks,
    factors,
    detailLayers,
    deepSections: brief.deep_sections ?? [],
    explainabilitySummary: explainabilitySummaryParts.length ? `${explainabilitySummaryParts.join(". ")}.` : "Опора недели собрана в краткий сводный слой.",
    explainabilityDetailItems: [
      {
        id: "week-explainability-confidence",
        title: "Надёжность сигнала",
        body: humanizeConfidence(confidence),
        value: typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : null,
      },
      {
        id: "week-explainability-birth-time",
        title: "Контекст рождения",
        body: birthTimeUsed
          ? "Точная карта рождения добавляет больше персональной опоры в недельную интерпретацию."
          : "Интерпретация собрана без точного времени рождения, поэтому часть нюансов остаётся более общей.",
        value: birthTimeUsed ? "Точное время учтено" : "Точное время не указано",
      },
      {
        id: "week-explainability-top-signal",
        title: "Главный слой влияния",
        body: topSignalLabel
          ? "Именно этот слой сильнее всего формирует краткий недельный вывод и рекомендации."
          : "Сигнал распределён между несколькими факторами без одного доминирующего слоя.",
        value: topSignalLabel,
      },
    ].filter((item) => item.body || item.value),
    explainability: {
      confidence,
      birth_time_used: birthTimeUsed,
      factor_count: brief.explainability?.factor_count ?? factors.length,
      timing_precision: brief.explainability?.timing_precision ?? null,
      top_signal_source: brief.explainability?.top_signal_source ?? null,
      explanation_depth: brief.explainability?.explanation_depth ?? null,
    },
    confidenceLabel: humanizeConfidence(confidence),
    confidenceShortLabel: humanizeConfidenceShort(confidence),
    birthTimeLabel: birthTimeUsed ? "учтено точное время рождения" : "без точного времени рождения",
    topSignalLabel,
    cta: {
      primary: brief.cta?.primary ?? null,
      secondary: brief.cta?.secondary ?? null,
    },
    sectionsCount: (brief.deep_sections ?? []).length,
    waitMessage:
      brief.status === "in_progress" || brief.status === "pending" || input.sourceStatus === "in_progress" || input.sourceStatus === "pending"
        ? sanitizeVisibleWeekText(input.waitMessageFallback, "Персональная неделя собирается и скоро станет доступна целиком.")
        : null,
  };
}

export function mapCanonicalWeekBriefToSurface(input: {
  weekBrief: WeekBrief;
  latestReportId?: string | null;
  sourceStatus?: string | null;
}): WeekSurfaceModel {
  return buildWeekSurfaceModel({
    brief: input.weekBrief,
    latestReportId: input.latestReportId,
    sourceStatus: input.sourceStatus,
    surfaceMode: "canonical",
    usesCanonicalWeekBrief: true,
  });
}

export function mapLegacyWeekFallbackToSurface(input: {
  legacyWeekMap?: LegacyWeekMapPayload | null;
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null;
  latestReportId?: string | null;
  sourceStatus?: string | null;
}): WeekSurfaceModel {
  const compatibilityBrief = legacyWeekMapToCompatibilityBrief(input.legacyWeekMap, input.chunks);
  return buildWeekSurfaceModel({
    brief: compatibilityBrief,
    latestReportId: input.latestReportId,
    sourceStatus: input.sourceStatus,
    surfaceMode: "compatibility",
    usesCanonicalWeekBrief: false,
    timezone: input.legacyWeekMap?.timezone ?? null,
    location: input.legacyWeekMap?.location ?? null,
    waitMessageFallback: sanitizeVisibleWeekText(input.legacyWeekMap?.thesis, "Персональная неделя собирается и скоро станет доступна целиком."),
  });
}

// FN-CONTRACT: FN-WEEK-MAP-REPORT-TO-BRIEF
// purpose: Preserve a bounded compatibility wrapper while canonical and degraded week paths stay split.
export function mapWeekReportToWeekBrief(input: {
  weekBrief?: WeekBrief | null;
  legacyWeekMap?: LegacyWeekMapPayload | null;
  chunks?: { id?: string; section?: string; title?: string; content?: unknown }[] | null;
  latestReportId?: string | null;
  sourceStatus?: string | null;
}): WeekSurfaceModel {
  if (input.weekBrief) {
    return mapCanonicalWeekBriefToSurface({
      weekBrief: input.weekBrief,
      latestReportId: input.latestReportId,
      sourceStatus: input.sourceStatus,
    });
  }

  return mapLegacyWeekFallbackToSurface({
    legacyWeekMap: input.legacyWeekMap,
    chunks: input.chunks,
    latestReportId: input.latestReportId,
    sourceStatus: input.sourceStatus,
  });
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
  if (!start && !end) return "Диапазон уточняется";
  const startDate = parseIsoDate(start);
  const endDate = parseIsoDate(end);
  if (startDate && endDate) {
    return `${formatShortDate(startDate)} — ${formatShortDate(endDate)}`;
  }
  if (startDate) return formatShortDate(startDate);
  if (endDate) return formatShortDate(endDate);
  return start ?? end ?? "Диапазон уточняется";
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
