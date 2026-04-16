// START_MODULE_CONTRACT: M-WEEK-BRIEF-COMPATIBILITY
// purpose: Reconstruct legacy week_map plus report chunks into an explicit compatibility-only week surface model.
// owns:
//   - frontend/lib/week-brief-compat.ts
// inputs:
//   - legacy week_map payload and optional report chunks
// outputs:
//   - `WeekSurfaceModel` marked as `compatibility`
// dependencies:
//   - frontend/lib/week-brief.ts shared surface builder
//   - report block fallback text extraction
// invariants:
//   - compatibility helpers never re-enter the canonical /week product path
//   - legacy week_map/chunks stay explicit and bounded to secondary compatibility surfaces
// failure_policy:
//   - absent legacy payloads return an empty compatibility detector signal rather than widening the canonical route contract
// non_goals:
//   - canonical /week mapping or visible week route rewiring
// END_MODULE_CONTRACT: M-WEEK-BRIEF-COMPATIBILITY

import { extractReportFallbackText } from "../components/blocks/report-renderer";
import { dedupeSemanticTexts } from "./detail-layer";
import { buildWeekSurfaceModel, type LightStatus, type WeekBrief, type WeekSurfaceModel } from "./week-brief";

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

export type LegacyWeekChunk = {
  id?: string;
  section?: string;
  title?: string;
  content?: unknown;
};

export function hasExplicitWeekMigrationPayload(input: {
  legacyWeekMap?: LegacyWeekMapPayload | null;
  chunks?: LegacyWeekChunk[] | null;
}): boolean {
  return Boolean(input.legacyWeekMap) || Boolean(input.chunks?.length);
}

const LEGACY_DOMAIN_TITLES: Record<string, string> = {
  work: "Работа и деньги",
  work_money: "Работа и деньги",
  relationships: "Отношения",
  energy: "Энергия",
  focus: "Фокус",
};

const INTERNAL_VISIBLE_TOKEN_PATTERN = /\b(?:legacy|fallback|week_?map|weekbrief|compatibility|headline|markdown|weekly report)\b/i;
const RAW_SLUG_VISIBLE_PATTERN = /^[a-z0-9]+(?:[_:-][a-z0-9]+)+$/i;

const LEGACY_STATUS_BY_SCORE = (value: number): LightStatus => {
  if (value >= 70) return "green";
  if (value >= 45) return "yellow";
  return "red";
};

const normalizeList = (value: string[] | null | undefined): string[] =>
  Array.isArray(value) ? dedupeSemanticTexts(value) : [];

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

function normalizeLegacyStatus(value: string | null | undefined): LightStatus {
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

function normalizeChunkSections(chunks?: LegacyWeekChunk[] | null): NonNullable<WeekBrief["deep_sections"]> {
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

function normalizeLegacyTextItems(items: string[] | null | undefined, prefix: string) {
  return dedupeSemanticTexts(items ?? [])
    .map((text) => sanitizeVisibleWeekMetaValue(text))
    .filter((text): text is string => Boolean(text))
    .map((text, index) => ({ id: `${prefix}-${index + 1}`, text }));
}

function legacyWeekMapToCompatibilityBrief(
  legacyWeekMap?: LegacyWeekMapPayload | null,
  chunks?: LegacyWeekChunk[] | null,
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
      mode: normalizeLegacyStatus(item.mode),
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
    best_uses: normalizeLegacyTextItems(legacy?.actions, "action"),
    risks: normalizeLegacyTextItems(legacy?.risks, "risk"),
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

export function mapLegacyWeekMigrationToSurface(input: {
  legacyWeekMap?: LegacyWeekMapPayload | null;
  chunks?: LegacyWeekChunk[] | null;
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
