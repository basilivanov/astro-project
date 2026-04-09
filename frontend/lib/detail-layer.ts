import type { DayBriefDto } from "/opt/astro-project/frontend/lib/day-brief";
import type { ActionRiskItem, WeekBrief } from "/opt/astro-project/frontend/lib/week-brief";

export type DetailLayerImpact = "high" | "medium" | "low" | null;

export type NormalizedDetailFactor = {
  id: string;
  label: string;
  explanationHuman: string;
  explanationAstro: string | null;
  value: string | null;
  impact: DetailLayerImpact;
  source: "today_personalized_factor" | "today_selected_factor" | "today_supporting_factor" | "week_major_factor" | "week_supporting_factor";
  relatedKey: string | null;
};

export type NormalizedDetailItem = {
  id: string;
  title: string;
  body: string | null;
  timeframe: string | null;
  impact: DetailLayerImpact;
  factors: NormalizedDetailFactor[];
  source: "today_score" | "today_window" | "today_best_use" | "today_risk" | "week_action" | "week_risk" | "week_domain" | "week_factor";
  relatedKey: string | null;
};

const trim = (value: string | null | undefined): string => String(value || "").trim();
const nullable = (value: string | null | undefined): string | null => {
  const normalized = trim(value);
  return normalized || null;
};
const impactOf = (value: string | null | undefined): DetailLayerImpact => value === "high" || value === "medium" || value === "low" ? value : null;

function normalizeComparableText(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[\s.,!?;:()[\]{}\"'«»—–-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function isSemanticallyDuplicateText(primary: string | null | undefined, secondary: string | null | undefined): boolean {
  const normalizedPrimary = normalizeComparableText(primary);
  const normalizedSecondary = normalizeComparableText(secondary);
  if (!normalizedPrimary || !normalizedSecondary) return false;
  return normalizedPrimary === normalizedSecondary
    || normalizedPrimary.includes(normalizedSecondary)
    || normalizedSecondary.includes(normalizedPrimary);
}

function isLikelyRawSemanticKey(value: string | null | undefined): boolean {
  const raw = String(value || "").trim();
  if (!raw) return true;
  if (/[А-Яа-яЁё]/.test(raw)) return false;
  const normalized = raw.toLowerCase();
  if (/^[a-z]+:[a-z0-9_-]+$/.test(normalized)) {
    return true;
  }
  if (/^[a-z0-9_./:-]+$/.test(normalized) && (normalized.includes("_") || normalized.includes(".") || normalized.includes("/"))) {
    return true;
  }
  return ["factor", "signal", "astro_factor", "human_thesis", "why_text", "supporting_factor"].includes(normalized);
}

function isLikelyRawStatusValue(value: string | null | undefined): boolean {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return false;
  return ["green", "yellow", "red", "high", "medium", "low", "background", "week:green", "week:yellow", "week:red", "all_day", "morning", "evening", "week_start", "week_end"].includes(normalized);
}

function sanitizeDetailText(value: string | null | undefined): string | null {
  const normalized = nullable(value);
  if (!normalized) return null;
  if (/^\d{2}:\d{2}[–-]\d{2}:\d{2}$/.test(normalized)) return normalized;
  if (/^[a-z_]+$/.test(normalized.toLowerCase()) && ["morning", "evening", "all_day", "week_start", "week_end"].includes(normalized.toLowerCase())) return normalized;
  if (isLikelyRawSemanticKey(normalized) || isLikelyRawStatusValue(normalized)) return null;
  return normalized;
}

function sanitizeFactorValue(value: string | null | undefined, label: string | null | undefined, explanationHuman: string | null | undefined): string | null {
  const normalized = sanitizeDetailText(value);
  if (!normalized) return null;
  if (isSemanticallyDuplicateText(normalized, label) || isSemanticallyDuplicateText(normalized, explanationHuman)) {
    return null;
  }
  return normalized;
}

export function sanitizeDetailLayer<T extends { body: string | null; timeframe: string | null; factors: NormalizedDetailFactor[] }>(item: T): T {
  const body = sanitizeDetailText(item.body);
  const timeframe = sanitizeDetailText(item.timeframe);
  const seen = new Set<string>();
  const factors = item.factors.filter((factor) => {
    const label = sanitizeDetailText(factor.label);
    const explanationHuman = sanitizeDetailText(factor.explanationHuman);
    const explanationAstro = sanitizeDetailText(factor.explanationAstro);
    const value = sanitizeFactorValue(factor.value, label, explanationHuman);
    if (!label && !explanationHuman && !explanationAstro && !value) return false;
    if ((label && body && isSemanticallyDuplicateText(label, body)) || (explanationHuman && body && isSemanticallyDuplicateText(explanationHuman, body))) {
      return false;
    }
    const dedupKey = [normalizeComparableText(label), normalizeComparableText(explanationHuman), normalizeComparableText(value)].filter(Boolean).join('|');
    if (dedupKey && seen.has(dedupKey)) return false;
    if (dedupKey) seen.add(dedupKey);
    factor.label = label || "";
    factor.explanationHuman = explanationHuman || "";
    factor.explanationAstro = explanationAstro;
    factor.value = value;
    return Boolean(factor.label || factor.explanationHuman || factor.explanationAstro || factor.value);
  });

  return { ...item, body, timeframe, factors };
}

function supportingFactorsToNormalized(
  factors:
    | Array<{ label?: string | null; explanation_human?: string | null; explanation_astro?: string | null; value?: string | null }>
    | null
    | undefined,
  source: NormalizedDetailFactor["source"],
  relatedKey: string,
  fallbackPrefix: string,
): NormalizedDetailFactor[] {
  if (!Array.isArray(factors)) return [];
  return factors
    .map((factor, index) => {
      const label = trim(factor?.label);
      const explanationHuman = trim(factor?.explanation_human);
      const explanationAstro = nullable(factor?.explanation_astro);
      if ((!label && !explanationHuman) || isLikelyRawSemanticKey(label)) return null;
      if (explanationHuman && isSemanticallyDuplicateText(label, explanationHuman)) return null;
      return {
        id: `${fallbackPrefix}-factor-${index + 1}`,
        label: label || `Фактор ${index + 1}`,
        explanationHuman,
        explanationAstro: explanationAstro && !isLikelyRawSemanticKey(explanationAstro) && !isSemanticallyDuplicateText(explanationAstro, explanationHuman)
          ? explanationAstro
          : null,
        value: sanitizeFactorValue(factor?.value, label, explanationHuman),
        impact: null,
        source,
        relatedKey,
      } satisfies NormalizedDetailFactor;
    })
    .filter((item): item is NormalizedDetailFactor => Boolean(item));
}

function mapActionRiskItem(item: ActionRiskItem, index: number, source: NormalizedDetailItem["source"]): NormalizedDetailItem | null {
  const title = trim(item.text);
  if (!title) return null;
  const relatedKey = nullable(item.factor_id) ?? `${source}-${index + 1}`;
  return {
    id: item.id?.trim() || `${source}-${index + 1}`,
    title,
    body: nullable(item.why_text),
    timeframe: nullable(item.timeframe),
    impact: impactOf(item.impact),
    factors: supportingFactorsToNormalized(item.supporting_factors, "week_supporting_factor", relatedKey, `${source}-${index + 1}`),
    source,
    relatedKey,
  };
}

export function normalizeTodayDetailItems(brief: DayBriefDto): NormalizedDetailItem[] {
  const scoreItems = brief.scores.map((score) => ({
    id: `today-score-${score.key}`,
    title: trim(score.title) || trim(score.key),
    body: nullable(score.details?.why_text) ?? nullable(score.advice),
    timeframe: null,
    impact: null,
    factors: supportingFactorsToNormalized(score.details?.supporting_factors, "today_supporting_factor", score.key, `today-score-${score.key}`),
    source: "today_score" as const,
    relatedKey: score.key,
  }));

  const windowItems = brief.windows.map((window) => ({
    id: window.id || `today-window-${window.start}-${window.end}`,
    title: trim(window.label) || "Окно дня",
    body: nullable(window.details?.why_text) ?? nullable(window.advice),
    timeframe: [trim(window.start), trim(window.end)].filter(Boolean).join("–") || null,
    impact: null,
    factors: supportingFactorsToNormalized(window.details?.supporting_factors, "today_supporting_factor", window.id, window.id || `today-window-${window.start}-${window.end}`),
    source: "today_window" as const,
    relatedKey: window.id || null,
  }));

  const bestUseItems = brief.best_uses.map((item, index) => ({
    id: item.id || `today-best-use-${index + 1}`,
    title: trim(item.text),
    body: null,
    timeframe: nullable(item.timeframe),
    impact: impactOf(item.impact),
    factors: [],
    source: "today_best_use" as const,
    relatedKey: nullable(item.factor_id) ?? (Array.isArray(item.factor_ids) && item.factor_ids.length ? item.factor_ids[0] : null),
  })).filter((item) => item.title);

  const riskItems = brief.risks.map((item, index) => ({
    id: item.id || `today-risk-${index + 1}`,
    title: trim(item.text),
    body: nullable(item.why_text),
    timeframe: nullable(item.timeframe),
    impact: impactOf(item.impact),
    factors: supportingFactorsToNormalized(item.supporting_factors, "today_supporting_factor", item.factor_id || (Array.isArray(item.factor_ids) && item.factor_ids.length ? item.factor_ids[0] : null) || `today-risk-${index + 1}`, item.id || `today-risk-${index + 1}`),
    source: "today_risk" as const,
    relatedKey: nullable(item.factor_id) ?? (Array.isArray(item.factor_ids) && item.factor_ids.length ? item.factor_ids[0] : null),
  })).filter((item) => item.title);

  return [...scoreItems, ...windowItems, ...bestUseItems, ...riskItems].map((item) => sanitizeDetailLayer(item));
}

export function normalizeWeekDetailItems(brief: WeekBrief): NormalizedDetailItem[] {
  const dayItems = (brief.day_cards || []).map((card, index) => ({
    id: trim(card?.id) || `week-day-${index + 1}`,
    title: trim(card?.details?.why_title) || trim(card?.headline) || `День ${index + 1}`,
    body: nullable(card?.details?.why_text) ?? nullable(card?.lead),
    timeframe: nullable(card?.peak_window_label),
    impact: impactOf(card?.mode === 'green' ? 'high' : card?.mode === 'yellow' ? 'medium' : 'low'),
    factors: supportingFactorsToNormalized(card?.details?.supporting_factors, 'week_supporting_factor', Array.isArray(card?.factor_ids) && card.factor_ids.length ? card.factor_ids[0] : trim(card?.id) || `week-day-${index + 1}`, trim(card?.id) || `week-day-${index + 1}`),
    source: 'week_day' as const,
    relatedKey: Array.isArray(card?.factor_ids) && card.factor_ids.length ? card.factor_ids[0] : nullable(card?.id),
  })).filter((item) => item.body || item.factors.length);
  const actionItems = (brief.best_uses || []).map((item, index) => mapActionRiskItem(item, index, "week_action")).filter((item): item is NormalizedDetailItem => Boolean(item));
  const riskItems = (brief.risks || []).map((item, index) => mapActionRiskItem(item, index, "week_risk")).filter((item): item is NormalizedDetailItem => Boolean(item));
  const domainItems = (brief.domains || []).map((domain, index) => {
    const title = trim(domain?.title) || trim(domain?.key) || `domain-${index + 1}`;
    return {
      id: trim(domain?.key) || `week-domain-${index + 1}`,
      title,
      body: nullable(domain?.why_text) ?? nullable(domain?.advice) ?? nullable(domain?.headline),
      timeframe: null,
      impact: null,
      factors: supportingFactorsToNormalized(domain?.supporting_factors, "week_supporting_factor", trim(domain?.key) || `week-domain-${index + 1}`, trim(domain?.key) || `week-domain-${index + 1}`),
      source: "week_domain" as const,
      relatedKey: nullable(domain?.key),
    };
  });
  const factorItems = (brief.major_factors || []).map((factor, index) => {
    const label = trim(factor?.label);
    if (!label) return null;
    const normalizedFactor: NormalizedDetailFactor = {
      id: trim(factor?.id) || `week-factor-${index + 1}`,
      label,
      explanationHuman: trim(factor?.explanation_human),
      explanationAstro: nullable(factor?.explanation_astro),
      value: null,
      impact: impactOf(factor?.impact),
      source: "week_major_factor",
      relatedKey: nullable(factor?.id),
    };
    return {
      id: normalizedFactor.id,
      title: normalizedFactor.label,
      body: normalizedFactor.explanationHuman || normalizedFactor.explanationAstro,
      timeframe: null,
      impact: normalizedFactor.impact,
      factors: [normalizedFactor],
      source: "week_factor" as const,
      relatedKey: normalizedFactor.relatedKey,
    };
  }).filter((item): item is NormalizedDetailItem => Boolean(item));

  return [...dayItems, ...domainItems, ...actionItems, ...riskItems, ...factorItems].map((item) => item.source === 'week_factor' ? item : sanitizeDetailLayer(item));
}
