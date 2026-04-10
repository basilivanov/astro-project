// START_MODULE_CONTRACT: M-DAY-BRIEF-ADAPTER
// purpose: Normalize today/day brief payloads into stable frontend view models with fallback-safe defaults.
// owns:
//   - frontend/lib/day-brief.ts
// inputs:
//   - unknown API payloads, optional profile subscription context
// outputs:
//   - `TodayViewModel` and `DayBriefDto` structures with normalized defaults
// dependencies:
//   - local coercion helpers only
// invariants:
//   - adapter never throws on malformed payloads
//   - CTA, explainability, and premium branches always resolve to explicit defaults
// failure_policy:
//   - malformed values degrade into fallback-safe placeholder structures
// non_goals:
//   - rendering or analytics side effects
// END_MODULE_CONTRACT: M-DAY-BRIEF-ADAPTER

// START_MODULE_MAP: M-DAY-BRIEF-ADAPTER
// entrypoints:
//   - normalizeDayBriefPayload
// helpers:
//   - normalizeSupportingFactors
//   - normalizeDetails
//   - normalizeScores
//   - normalizeWindows
//   - normalizeActionItems
// owned_tests:
//   - frontend/test/lib/day-brief.test.ts
// adjacent_modules:
//   - frontend/app/page.tsx
//   - frontend/components/today/daybrief-sections.tsx
// END_MODULE_MAP: M-DAY-BRIEF-ADAPTER

export type DayBriefLight = "green" | "yellow" | "red";
export type DayBriefImpact = "high" | "medium" | "low";
export type DayBriefWindowMode = "best" | "soft" | "caution";
export type DayBriefScoreKey = "energy" | "money" | "love" | "focus";
export type DayBriefCtaType = "open_week" | "open_today" | "ask_question" | "open_premium" | "open_history" | "open_report" | "custom";

export type DayBriefDto = {
  version: "day_brief_v1";
  date: string;
  personalization_level: string;
  fallback_mode: boolean;
  summary: {
    headline: string;
    subhead: string;
    day_type: "push" | "balance" | "caution" | "deep_focus" | "recovery";
    tone?: string | null;
  };
  context: {
    moon_sign?: string | null;
    moon_phase?: string | null;
    moon_emoji?: string | null;
    aspects_count?: number | null;
    label?: string | null;
  };
  scores: Array<{
    key: DayBriefScoreKey;
    title: string;
    value: number;
    status: DayBriefLight;
    advice: string;
    details?: {
      why_title?: string | null;
      why_text: string;
      supporting_factors: Array<{
        id?: string | null;
        label: string;
        explanation_human: string;
        explanation_astro?: string | null;
        value?: string | null;
      }>;
      factor_ids?: string[];
    } | null;
  }>;
  windows: Array<{
    id: string;
    start: string;
    end: string;
    label: string;
    mode: DayBriefWindowMode;
    advice: string;
    details?: {
      why_text: string;
      supporting_factors: Array<{
        id?: string | null;
        label: string;
        explanation_human: string;
        explanation_astro?: string | null;
        value?: string | null;
      }>;
      factor_ids?: string[];
    } | null;
  }>;
  best_uses: Array<{
    id: string;
    text: string;
    factor_id?: string | null;
    factor_ids?: string[];
    impact?: DayBriefImpact | null;
    timeframe?: string | null;
  }>;
  risks: Array<{
    id: string;
    text: string;
    factor_id?: string | null;
    factor_ids?: string[];
    impact?: DayBriefImpact | null;
    timeframe?: string | null;
    why_text?: string | null;
    supporting_factors?: Array<{
      id?: string | null;
      label: string;
      explanation_human: string;
      explanation_astro?: string | null;
      value?: string | null;
    }>;
  }>;
  personalized_factors: Array<{
    id: string;
    label: string;
    impact: DayBriefImpact;
    category?: string | null;
    explanation_human: string;
    explanation_astro?: string | null;
    source_models?: string[];
    weight?: number | null;
  }>;
  explainability: {
    confidence: number;
    birth_time_used: boolean;
    factor_count: number;
    timing_precision?: "exact" | "approximate" | null;
    top_signal_source?: string | null;
    explanation_depth?: "minimal" | "standard" | "full" | null;
    selected_factors?: Array<{
      id: string;
      label: string;
      explanation_human: string;
      explanation_astro?: string | null;
      domain?: string | null;
      family?: string | null;
      signal?: number | null;
    }>;
  };
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
  legacy?: Record<string, unknown> | null;
};

export type TodayViewModel = {
  brief: DayBriefDto;
  premiumActiveUntil: string | null;
  state: "ready" | "fallback";
  usesCanonicalDayBrief: boolean;
};

const isRecord = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === "object");
const isLight = (value: unknown): value is DayBriefLight => value === "green" || value === "yellow" || value === "red";
const isWindowMode = (value: unknown): value is DayBriefWindowMode => value === "best" || value === "soft" || value === "caution";
const isImpact = (value: unknown): value is DayBriefImpact => value === "high" || value === "medium" || value === "low";
const text = (value: unknown, fallback = ""): string => typeof value === "string" ? value : fallback;
const bool = (value: unknown, fallback = false): boolean => typeof value === "boolean" ? value : fallback;
const num = (value: unknown, fallback = 0): number => typeof value === "number" && Number.isFinite(value) ? value : fallback;

function normalizeComparableText(value: string | null | undefined): string {
  return String(value ?? "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const INTERNAL_VISIBLE_TOKEN_PATTERN = /\b(?:legacy|fallback|headline|week_?map|weekbrief|compatibility|markdown|weekly report)\b/i;

function sanitizeLegacyDayHeadline(value: unknown): string {
  const raw = text(value).trim();
  if (!raw) {
    return "Сегодня: короткий обзор";
  }
  if (INTERNAL_VISIBLE_TOKEN_PATTERN.test(raw)) {
    return "Сегодня: короткий обзор";
  }
  if (/^[a-z][a-z\s-]{2,}$/i.test(raw) && !/[А-Яа-яЁё]/.test(raw)) {
    return "Сегодня: короткий обзор";
  }
  return raw;
}

// FN-CONTRACT: FN-DAY-NORMALIZE-SUPPORTING-FACTORS
// purpose: Coerce supporting-factor payloads into a stable array of human-readable factor records.
function normalizeSupportingFactors(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).map((item) => ({
    id: typeof item.id === "string" ? item.id : null,
    label: typeof item.label === "string" ? item.label : "",
    explanation_human: typeof item.explanation_human === "string" ? item.explanation_human : "",
    explanation_astro: typeof item.explanation_astro === "string" ? item.explanation_astro : null,
    value: typeof item.value === "string" || typeof item.value === "number" ? String(item.value) : null,
  })).filter((item) => {
    const label = item.label.trim().toLowerCase();
    const human = item.explanation_human.trim();
    const astro = String(item.explanation_astro || '').trim();
    const valueText = String(item.value || '').trim().toLowerCase();
    if (!label && !human && !astro && !valueText) return false;
    if (["factor", "supporting_factor", "why_text"].includes(label)) return false;
    if (["green", "yellow", "red", "high", "medium", "low", "all_day", "morning", "evening"].includes(valueText) && !label && !human && !astro) return false;
    return true;
  });
}

// FN-CONTRACT: FN-DAY-NORMALIZE-DETAILS
// purpose: Normalize optional score/window detail payloads with fallback-safe why-text and factors.
function normalizeDetails(value: unknown) {
  if (!isRecord(value)) return null;
  return {
    why_title: typeof value.why_title === "string" ? value.why_title : null,
    why_text: text(value.why_text, "Сегодня здесь лучше идти через спокойную точность, а не через голый напор."),
    supporting_factors: normalizeSupportingFactors(value.supporting_factors),
    factor_ids: Array.isArray(value.factor_ids) ? value.factor_ids.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [],
  };
}

function normalizeWindowLabelTaxonomy(input: {
  label?: string | null;
  mode?: DayBriefWindowMode | null;
  advice?: string | null;
  details?: { why_text?: string | null } | null;
}): string {
  const normalizedText = normalizeComparableText([
    input.label,
    input.advice,
    input.details?.why_text,
  ].filter(Boolean).join(" "));

  if (/(переговор|обсужд|созвон|договор|контакт)/.test(normalizedText)) {
    return "Окно переговоров";
  }
  if (/(провер|свер|редакт|уточн|контрол)/.test(normalizedText) || input.mode === "caution") {
    return "Окно проверки";
  }
  if (/(восстанов|отдых|передыш|сон|ресурс|пауза)/.test(normalizedText)) {
    return "Окно восстановления";
  }
  if (input.mode === "best") {
    return "Рабочий импульс";
  }
  return "Мягкое окно";
}

function dedupeSupportingFactors(
  factors: Array<{
    id?: string | null;
    label: string;
    explanation_human: string;
    explanation_astro?: string | null;
    value?: string | null;
  }>,
) {
  const seen = new Set<string>();
  return factors.filter((factor) => {
    const key = [
      normalizeComparableText(factor.label),
      normalizeComparableText(factor.explanation_human),
      normalizeComparableText(factor.explanation_astro),
      normalizeComparableText(factor.value),
    ].join("|");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function mergeAdjacentWindows(windows: DayBriefDto["windows"]): DayBriefDto["windows"] {
  return windows.reduce<DayBriefDto["windows"]>((result, currentWindow, index) => {
    const current = {
      ...currentWindow,
      label: normalizeWindowLabelTaxonomy(currentWindow),
    };
    const previous = result[result.length - 1];
    if (!previous) {
      result.push(current);
      return result;
    }

    const previousSignature = [
      normalizeComparableText(previous.label),
      previous.mode,
      normalizeComparableText(previous.advice),
      normalizeComparableText(previous.details?.why_text),
    ].join("|");
    const currentSignature = [
      normalizeComparableText(current.label),
      current.mode,
      normalizeComparableText(current.advice),
      normalizeComparableText(current.details?.why_text),
    ].join("|");

    if (previousSignature !== currentSignature) {
      result.push(current);
      return result;
    }

    const mergedFactors = dedupeSupportingFactors([
      ...(previous.details?.supporting_factors ?? []),
      ...(current.details?.supporting_factors ?? []),
    ]);
    const mergedFactorIds = Array.from(new Set([
      ...(previous.details?.factor_ids ?? []),
      ...(current.details?.factor_ids ?? []),
    ]));

    result[result.length - 1] = {
      ...previous,
      id: `${previous.id}-${index}`,
      end: current.end || previous.end,
      details: previous.details || current.details
        ? {
            why_title: previous.details?.why_title ?? current.details?.why_title ?? null,
            why_text: previous.details?.why_text ?? current.details?.why_text ?? "Сегодня здесь лучше идти через спокойную точность, а не через голый напор.",
            supporting_factors: mergedFactors,
            factor_ids: mergedFactorIds,
          }
        : null,
    };

    return result;
  }, []);
}

// FN-CONTRACT: FN-DAY-NORMALIZE-SCORES
// purpose: Convert raw score payloads into bounded `DayBriefDto` score entries.
function normalizeScores(value: unknown): DayBriefDto["scores"] {
  if (!Array.isArray(value)) return [];
  return value
    .filter(isRecord)
    .map((item) => ({
      key: (["energy", "money", "love", "focus"].includes(text(item.key)) ? text(item.key) : "energy") as DayBriefScoreKey,
      title: text(item.title, "Фокус"),
      value: Math.max(0, Math.min(100, num(item.value, 0))),
      status: isLight(item.status) ? item.status : "yellow",
      advice: text(item.advice, "Действуйте спокойно и без резких перегрузок."),
      details: normalizeDetails(item.details),
    }));
}

function normalizeItems(value: unknown): DayBriefDto["best_uses"] {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).map((item, index) => ({
    id: text(item.id, `item-${index}`),
    text: text(item.text, "Сфокусируйтесь на одном важном шаге."),
    factor_id: typeof item.factor_id === "string" ? item.factor_id : null,
    factor_ids: Array.isArray(item.factor_ids) ? item.factor_ids.filter((value): value is string => typeof value === "string" && value.trim().length > 0) : [],
    impact: isImpact(item.impact) ? item.impact : null,
    timeframe: typeof item.timeframe === "string" ? item.timeframe : null,
    why_text: typeof item.why_text === "string" ? item.why_text : null,
    supporting_factors: normalizeSupportingFactors(item.supporting_factors),
  }));
}

function dedupeRiskItems(items: DayBriefDto["risks"]): DayBriefDto["risks"] {
  const byText = new Map<string, DayBriefDto["risks"][number]>();

  for (const item of items) {
    const key = normalizeComparableText(item.text);
    if (!key) continue;
    const existing = byText.get(key);
    if (!existing) {
      byText.set(key, item);
      continue;
    }

    const existingScore = Number(Boolean(existing.why_text)) + (existing.supporting_factors?.length ?? 0);
    const candidateScore = Number(Boolean(item.why_text)) + (item.supporting_factors?.length ?? 0);
    if (candidateScore > existingScore) {
      byText.set(key, item);
    }
  }

  return Array.from(byText.values()).slice(0, 2);
}

// FN-CONTRACT: FN-DAY-NORMALIZE-WINDOWS
// purpose: Convert raw timing-window payloads into stable today window cards.
function normalizeWindows(value: unknown): DayBriefDto["windows"] {
  if (!Array.isArray(value)) return [];
  return mergeAdjacentWindows(value.filter(isRecord).map((item, index) => ({
    id: text(item.id, `window-${index}`),
    start: text(item.start, "09:00"),
    end: text(item.end, "11:00"),
    label: normalizeWindowLabelTaxonomy({
      label: text(item.label, "Рабочее окно"),
      mode: isWindowMode(item.mode) ? item.mode : "soft",
      advice: text(item.advice, "Держите спокойный темп и проверяйте детали."),
      details: normalizeDetails(item.details),
    }),
    mode: isWindowMode(item.mode) ? item.mode : "soft",
    advice: text(item.advice, "Держите спокойный темп и проверяйте детали."),
    details: normalizeDetails(item.details),
  }))).slice(0, 3);
}

function normalizeFactors(value: unknown): DayBriefDto["personalized_factors"] {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).map((item, index) => ({
    id: text(item.id, `factor-${index}`),
    label: text(item.label, `Фактор ${index + 1}`),
    impact: isImpact(item.impact) ? item.impact : "medium",
    category: typeof item.category === "string" ? item.category : null,
    explanation_human: text(item.explanation_human, "Фон дня поддерживает короткие точные действия."),
    explanation_astro: typeof item.explanation_astro === "string" ? item.explanation_astro : null,
    source_models: Array.isArray(item.source_models) ? item.source_models.filter((entry): entry is string => typeof entry === "string") : [],
    weight: typeof item.weight === "number" ? item.weight : null,
  }));
}

export function buildLegacyDayBrief(source: unknown, premiumActiveUntil?: string | null): DayBriefDto {
  const data = isRecord(source) ? source : {};
  const legacyTraffic = isRecord(data.traffic_lights) ? data.traffic_lights : {};
  const legacyMoon = isRecord(data.moon) ? data.moon : {};
  const generalVibe = text(data.general_vibe, "День лучше прожить в спокойном темпе.");
  const personalizationLevel = text(data.personalization_level, "fallback");
  const fastHits = Array.isArray(data.fast_hits) ? data.fast_hits.filter(isRecord) : [];
  const scores: DayBriefDto["scores"] = [
    { key: "energy", title: "Энергия", value: legacyTraffic.health === "green" ? 78 : legacyTraffic.health === "red" ? 28 : 55, status: isLight(legacyTraffic.health) ? legacyTraffic.health : "yellow", advice: "Соберите ритм тела и не перегружайте себя." },
    { key: "money", title: "Деньги", value: legacyTraffic.money === "green" ? 76 : legacyTraffic.money === "red" ? 32 : 57, status: isLight(legacyTraffic.money) ? legacyTraffic.money : "yellow", advice: "Перепроверьте цифры и договорённости." },
    { key: "love", title: "Отношения", value: legacyTraffic.love === "green" ? 74 : legacyTraffic.love === "red" ? 30 : 56, status: isLight(legacyTraffic.love) ? legacyTraffic.love : "yellow", advice: "Говорите мягче и уточняйте ожидания." },
    { key: "focus", title: "Фокус", value: personalizationLevel.includes("personal") ? 72 : 58, status: "yellow", advice: generalVibe },
  ];
  const windows: DayBriefDto["windows"] = fastHits.slice(0, 3).map((item, index) => ({
    id: text(item.summary, `window-${index}`),
    start: index === 0 ? "09:00" : index === 1 ? "13:00" : "18:00",
    end: index === 0 ? "11:00" : index === 1 ? "15:00" : "20:00",
    label: text(item.summary, "Окно дня"),
    mode: text(item.type).toLowerCase().includes("трин") ? "best" : text(item.type).toLowerCase().includes("квад") ? "caution" : "soft",
    advice: text(item.summary, "Действуйте в коротком понятном ритме."),
  }));
  const bestUses = scores.filter((item) => item.status === "green").map((item) => ({ id: `${item.key}-best`, text: item.advice, impact: "medium" as const, timeframe: "all_day" }));
  const risks = scores.filter((item) => item.status !== "green").slice(0, 3).map((item) => ({ id: `${item.key}-risk`, text: item.advice, impact: item.status === "red" ? "high" as const : "medium" as const, timeframe: "all_day" }));

  return {
    version: "day_brief_v1",
    date: text(data.date, new Date().toISOString().slice(0, 10)),
    personalization_level: personalizationLevel,
    fallback_mode: true,
    summary: {
      headline: sanitizeLegacyDayHeadline(data.general_vibe),
      subhead: "Сейчас показываем только спокойный короткий слой без полной персональной раскладки по сферам.",
      day_type: legacyTraffic.health === "red" ? "recovery" : legacyTraffic.love === "red" || legacyTraffic.money === "red" ? "caution" : legacyTraffic.health === "green" && legacyTraffic.money === "green" ? "push" : "balance",
      tone: null,
    },
    context: {
      moon_sign: text(data.moon_sign, text(legacyMoon.sign) || null),
      moon_phase: text(data.moon_phase, text(legacyMoon.phase) || null),
      moon_emoji: text(data.moon_emoji, text(legacyMoon.emoji, "🌙")),
      aspects_count: fastHits.length,
      label: text(data.moon_phase) || text(legacyMoon.phase) ? `${text(data.moon_sign, text(legacyMoon.sign, "Луна"))} · ${text(data.moon_phase, text(legacyMoon.phase, "фон дня"))}` : null,
    },
    scores,
    windows,
    best_uses: bestUses.length ? bestUses : [{ id: "legacy-best", text: generalVibe, impact: "medium", timeframe: "all_day" }],
    risks: risks.length ? risks : [{ id: "legacy-risk", text: "Не разгоняйте день быстрее контекста.", impact: "medium", timeframe: "all_day" }],
    personalized_factors: fastHits.slice(0, 3).map((item, index) => ({ id: `legacy-factor-${index}`, label: text(item.transit, `Фактор ${index + 1}`), impact: "medium", category: "legacy_fast_hit", explanation_human: text(item.summary, generalVibe), explanation_astro: [text(item.transit), text(item.type), text(item.natal)].filter(Boolean).join(" · ") || null, source_models: ["mixed"], weight: null })),
    explainability: {
      confidence: personalizationLevel.includes("personal") ? 0.72 : 0.48,
      birth_time_used: false,
      factor_count: fastHits.length,
      timing_precision: fastHits.length ? "approximate" : null,
      top_signal_source: fastHits.length ? "mixed" : null,
      explanation_depth: fastHits.length ? "standard" : "minimal",
    },
    premium: {
      subscription_active: Boolean(premiumActiveUntil),
      subscription_active_until: premiumActiveUntil ?? null,
      days_left: null,
      show_upgrade_cta: !premiumActiveUntil,
      show_resume_banner: false,
    },
    cta: {
      primary: { type: "open_week", label: "Открыть неделю", href: "/week" },
      secondary: { type: premiumActiveUntil ? "open_history" : "open_premium", label: premiumActiveUntil ? "История разборов" : "Открыть premium", href: premiumActiveUntil ? "/reports/history" : "/reports" },
    },
    legacy: data,
  };
}

// FN-CONTRACT: FN-DAY-NORMALIZE-PAYLOAD
// purpose: Produce a `TodayViewModel` from raw payloads and optional profile subscription context.
export function normalizeDayBriefPayload(payload: unknown, profile?: { subscription_active_until?: string | null } | null): TodayViewModel | null {
  if (!isRecord(payload)) return null;
  const premiumActiveUntil = profile?.subscription_active_until ?? null;
  const candidate = isRecord(payload.day_brief) ? payload.day_brief : payload;
  if (!isRecord(candidate) || text(candidate.version) !== "day_brief_v1") {
    return {
      brief: buildLegacyDayBrief(payload, premiumActiveUntil),
      premiumActiveUntil,
      state: "fallback",
      usesCanonicalDayBrief: false,
    };
  }

  const brief: DayBriefDto = {
    version: "day_brief_v1",
    date: text(candidate.date, new Date().toISOString().slice(0, 10)),
    personalization_level: text(candidate.personalization_level, "fallback"),
    fallback_mode: bool(candidate.fallback_mode, false),
    summary: {
      headline: text(isRecord(candidate.summary) ? candidate.summary.headline : undefined, "День просит собранного ритма и точности."),
      subhead: text(isRecord(candidate.summary) ? candidate.summary.subhead : undefined, "Сначала соберите контекст, затем двигайте главное."),
      day_type: (["push", "balance", "caution", "deep_focus", "recovery"].includes(text(isRecord(candidate.summary) ? candidate.summary.day_type : undefined)) ? text(isRecord(candidate.summary) ? candidate.summary.day_type : undefined) : "balance") as DayBriefDto["summary"]["day_type"],
      tone: isRecord(candidate.summary) && typeof candidate.summary.tone === "string" ? candidate.summary.tone : null,
    },
    context: {
      moon_sign: isRecord(candidate.context) ? text(candidate.context.moon_sign) || null : null,
      moon_phase: isRecord(candidate.context) ? text(candidate.context.moon_phase) || null : null,
      moon_emoji: isRecord(candidate.context) ? text(candidate.context.moon_emoji, "🌙") : "🌙",
      aspects_count: isRecord(candidate.context) ? (typeof candidate.context.aspects_count === "number" ? candidate.context.aspects_count : null) : null,
      label: isRecord(candidate.context) ? text(candidate.context.label) || null : null,
    },
    scores: normalizeScores(candidate.scores),
    windows: normalizeWindows(candidate.windows),
    best_uses: normalizeItems(candidate.best_uses),
    risks: dedupeRiskItems(normalizeItems(candidate.risks)),
    personalized_factors: normalizeFactors(candidate.personalized_factors),
    explainability: {
      confidence: isRecord(candidate.explainability) ? num(candidate.explainability.confidence, 0) : 0,
      birth_time_used: isRecord(candidate.explainability) ? bool(candidate.explainability.birth_time_used, false) : false,
      factor_count: isRecord(candidate.explainability) ? num(candidate.explainability.factor_count, 0) : 0,
      timing_precision: isRecord(candidate.explainability) && (candidate.explainability.timing_precision === "exact" || candidate.explainability.timing_precision === "approximate") ? candidate.explainability.timing_precision : null,
      top_signal_source: isRecord(candidate.explainability) ? text(candidate.explainability.top_signal_source) || null : null,
      explanation_depth: isRecord(candidate.explainability) && (["minimal", "standard", "full"].includes(text(candidate.explainability.explanation_depth))) ? candidate.explainability.explanation_depth as "minimal" | "standard" | "full" : null,
      selected_factors: isRecord(candidate.explainability) && Array.isArray(candidate.explainability.selected_factors)
        ? candidate.explainability.selected_factors
          .filter(isRecord)
          .map((factor, index) => ({
            id: text(factor.id, `selected-factor-${index}`),
            label: text(factor.label, `Фактор ${index + 1}`),
            explanation_human: text(factor.explanation_human, "Фактор поддерживает вывод дня."),
            explanation_astro: typeof factor.explanation_astro === "string" ? factor.explanation_astro : null,
            domain: typeof factor.domain === "string" ? factor.domain : null,
            family: typeof factor.family === "string" ? factor.family : null,
            signal: typeof factor.signal === "number" ? factor.signal : null,
          }))
        : [],
    },
    premium: isRecord(candidate.premium) ? {
      subscription_active: bool(candidate.premium.subscription_active, false),
      subscription_active_until: typeof candidate.premium.subscription_active_until === "string" ? candidate.premium.subscription_active_until : premiumActiveUntil,
      days_left: typeof candidate.premium.days_left === "number" ? candidate.premium.days_left : null,
      show_upgrade_cta: bool(candidate.premium.show_upgrade_cta, false),
      show_resume_banner: bool(candidate.premium.show_resume_banner, false),
    } : {
      subscription_active: Boolean(premiumActiveUntil),
      subscription_active_until: premiumActiveUntil,
      days_left: null,
      show_upgrade_cta: !premiumActiveUntil,
      show_resume_banner: false,
    },
    cta: isRecord(candidate.cta) ? {
      primary: isRecord(candidate.cta.primary) ? { type: (text(candidate.cta.primary.type, "custom") as DayBriefCtaType), label: text(candidate.cta.primary.label, "Открыть неделю"), href: text(candidate.cta.primary.href, "/week") } : null,
      secondary: isRecord(candidate.cta.secondary) ? { type: (text(candidate.cta.secondary.type, "custom") as DayBriefCtaType), label: text(candidate.cta.secondary.label, "Открыть premium"), href: text(candidate.cta.secondary.href, "/reports") } : null,
    } : {
      primary: { type: "open_week", label: "Открыть неделю", href: "/week" },
      secondary: { type: "open_premium", label: "Открыть premium", href: "/reports" },
    },
    legacy: isRecord(candidate.legacy) ? candidate.legacy : null,
  };

  return {
    brief,
    premiumActiveUntil: brief.premium?.subscription_active_until ?? premiumActiveUntil,
    state: brief.fallback_mode ? "fallback" : "ready",
    usesCanonicalDayBrief: true,
  };
}
