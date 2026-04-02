// START_MODULE_CONTRACT: M-TODAY-SECTIONS
// purpose: Render today detail sections and explainability disclosures from normalized day brief DTOs.
// owns:
//   - frontend/components/today/daybrief-sections.tsx
// inputs:
//   - normalized `DayBriefDto`, detail-layer normalized factors/items, optional CTA handlers
// outputs:
//   - presentational Today panels with disclosure-ready copy and evidence chips
// dependencies:
//   - consumer page shell primitives, detail helpers, TrafficLights
// invariants:
//   - section components stay render-only and derive content from normalized DTOs
//   - explainability suppression removes duplicate or semantically raw phrases
// failure_policy:
//   - sparse payload branches collapse to compact UI without throwing
// non_goals:
//   - fetching today payloads or emitting analytics
// END_MODULE_CONTRACT: M-TODAY-SECTIONS

// START_MODULE_MAP: M-TODAY-SECTIONS
// entrypoints:
//   - TodayVerdict
//   - TodayScores
//   - TodayWindows
//   - TodayActions
//   - TodayRisks
//   - TodayExplainability
//   - TodayCtaPanel
// helpers:
//   - buildTodayExplainabilityCards
//   - buildScoreDisclosureContent
//   - buildWindowDisclosureContent
// owned_tests:
//   - frontend/test/components/today/daybrief-sections.test.tsx
// adjacent_modules:
//   - frontend/app/page.tsx
//   - frontend/lib/day-brief.ts
//   - frontend/lib/detail-layer.ts
// END_MODULE_MAP: M-TODAY-SECTIONS

"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, Clock3, Sparkles } from "lucide-react";
import { ConsumerPanel, ConsumerStatusBadge } from "../consumer-page-shell";
import { TrafficLights } from "../TrafficLights";
import type { DayBriefDto } from "../../lib/day-brief";
import { normalizeTodayDetailItems, type NormalizedDetailFactor, type NormalizedDetailItem } from "../../lib/detail-layer";
import { DetailDisclosureCard } from "../detail/detail-disclosure-card";
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";

const DAY_MODE_COPY: Record<DayBriefDto["summary"]["day_type"], { label: string; badgeClass: string }> = {
  push: { label: "День для рывка", badgeClass: "border border-emerald-200 bg-emerald-50 text-emerald-900" },
  balance: { label: "День в балансе", badgeClass: "border border-amber-200 bg-amber-50 text-amber-900" },
  caution: { label: "Осторожный день", badgeClass: "border border-rose-200 bg-rose-50 text-rose-900" },
  deep_focus: { label: "Глубокий фокус", badgeClass: "border border-indigo-200 bg-indigo-50 text-indigo-900" },
  recovery: { label: "День на восстановление", badgeClass: "border border-slate-200 bg-slate-50 text-slate-800" },
};

const WINDOW_MODE_COPY = {
  best: { label: "Лучшее окно", className: "border-emerald-100 bg-emerald-50" },
  soft: { label: "Мягкое окно", className: "border-amber-100 bg-amber-50" },
  caution: { label: "С осторожностью", className: "border-rose-100 bg-rose-50" },
} as const;

// FN-CONTRACT: FN-TODAY-FORMAT-TIMEFRAME
// purpose: Convert raw timeframe labels into concise human-facing copy.
function formatItemTimeframe(value: string | null | undefined): string | null {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return null;
  const map: Record<string, string | null> = {
    morning: "Утро",
    afternoon: "День",
    day: "День",
    evening: "Вечер",
    all_day: null,
    allday: null,
    all: null,
    high: null,
    medium: null,
    low: null,
  };
  if (normalized in map) return map[normalized] ?? null;
  return /^[a-z0-9_-]+$/.test(normalized) ? null : String(value).trim();
}

// FN-CONTRACT: FN-TODAY-FORMAT-IMPACT
// purpose: Hide generic impact keys and preserve only user-meaningful impact labels.
function formatImpact(value: string | null | undefined): string | null {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return null;
  const map: Record<string, string | null> = {
    high: null,
    medium: null,
    low: null,
    green: null,
    yellow: null,
    red: null,
    background: null,
  };
  if (normalized in map) return map[normalized] ?? null;
  if (/^[a-z]+:[a-z0-9_-]+$/.test(normalized)) return null;
  return /^[a-z0-9_-]+$/.test(normalized) ? null : String(value).trim();
}

function looksLikeDomainScopedFactor(factor: { domain?: string | null; category?: string | null; label?: string | null }, scoreKey: string): boolean {
  const normalizedScoreKey = String(scoreKey || "").trim().toLowerCase();
  const candidates = [factor.domain, factor.category, factor.label]
    .map((value) => String(value || "").trim().toLowerCase())
    .filter(Boolean);
  if (!candidates.length) return false;
  const aliases: Record<string, string[]> = {
    energy: ["energy", "health", "tone", "ресурс", "энерг"],
    money: ["money", "work_money", "work", "career", "работ", "деньг", "финанс"],
    work_money: ["work_money", "money", "work", "career", "работ", "деньг", "финанс"],
    love: ["love", "relationships", "relationship", "relation", "отнош", "чувств", "контакт"],
    relationships: ["relationships", "love", "relationship", "relation", "отнош", "чувств", "контакт"],
    focus: ["focus", "mind", "focus_time", "фокус", "ритм", "вниман"],
  };
  const needles = aliases[normalizedScoreKey] ?? [normalizedScoreKey];
  return candidates.some((candidate) => needles.some((needle) => candidate.includes(needle)));
}

function isGenericDomainFactor(
  factor: { label?: string | null; explanation_human?: string | null; explanation_astro?: string | null },
  brief: DayBriefDto,
): boolean {
  const human = String(factor.explanation_human || "").trim();
  const astro = String(factor.explanation_astro || "").trim();
  const label = String(factor.label || "").trim();
  const anchors = collectTodayCompositionAnchors(brief);

  if (isGenericExplainabilityPhrase(label) || isGenericExplainabilityPhrase(human) || isGenericExplainabilityPhrase(astro)) {
    return true;
  }

  return [human, astro, label].some((value) => value && shouldSuppressByComposition(value, anchors));
}

function normalizeComparableText(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[\s.,!?;:()[\]{}"'«»—–-]+/g, " ")
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

function isGenericExplainabilityPhrase(value: string | null | undefined): boolean {
  const normalized = normalizeComparableText(value);
  if (!normalized) return true;
  return [
    "ключевые сигналы дня собраны в короткий персональный вывод",
    "короткий персональный вывод",
    "персональный контекст дня",
    "что повлияло",
    "почему такой день",
    "фактор дня",
    "рабочий контекст",
    "контакт и тон",
    "ресурс и темп",
  ].includes(normalized);
}

function isLikelyRawSemanticKey(value: string | null | undefined): boolean {
  const raw = String(value || "").trim();
  if (!raw) return true;
  if (/[А-Яа-яЁё]/.test(raw)) return false;
  const normalized = raw.toLowerCase();
  if (/^[a-z0-9_-]+:[a-z0-9_-]+(?:[:/][a-z0-9_-]+)*$/.test(normalized)) {
    return true;
  }
  if (/^[a-z0-9_./:-]+$/.test(normalized) && (normalized.includes("_") || normalized.includes(".") || normalized.includes("/"))) {
    return true;
  }
  return [
    "factor",
    "signal",
    "astro_factor",
    "human_thesis",
    "why_text",
    "supporting_factor",
  ].includes(normalized);
}

function sanitizeHumanFacingText(value: string | null | undefined): string | null {
  const raw = String(value || "").trim();
  if (!raw) return null;
  if (isLikelyRawSemanticKey(raw)) return null;

  const normalized = raw.toLowerCase();
  const cleaned = raw
    .replace(/\b(?:светофор|traffic\s*light)\s+[a-z0-9_./-]+\s*:\s*[a-z0-9_./-]+\b/gi, "")
    .replace(/\b(?:светофор|traffic\s*light)\b/gi, "")
    .replace(/\b[a-z0-9_./-]+\s*:\s*(?:green|yellow|red|high|medium|low|background|signal_only|structured_value)\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .replace(/^[,;:–—\-\s]+|[,;:–—\-\s]+$/g, "")
    .trim();

  if (!cleaned) return null;
  if (isLikelyRawSemanticKey(cleaned)) return null;
  if (/^(?:светофор|traffic\s*light)$/i.test(cleaned)) return null;
  if (/\b(?:светофор|traffic\s*light)\b/i.test(raw) && normalizeComparableText(cleaned).length < 3) return null;
  if (/^(?:green|yellow|red|high|medium|low|background|signal only|structured value)$/i.test(cleaned)) return null;
  if (normalized !== cleaned.toLowerCase() && isGenericExplainabilityPhrase(cleaned)) return null;
  return cleaned;
}

function dedupeNormalizedFactors(factors: NormalizedDetailFactor[] | undefined): NormalizedDetailFactor[] {
  const deduped = new Map<string, NormalizedDetailFactor>();
  const seenHumanAstro = new Set<string>();
  const seenLabels = new Set<string>();
  const seenHuman = new Set<string>();

  for (const factor of factors ?? []) {
    const label = sanitizeHumanFacingText(factor.label);
    const human = sanitizeHumanFacingText(factor.explanationHuman);
    const astro = sanitizeHumanFacingText(factor.explanationAstro);
    if (!label && !human && !astro) continue;

    const normalizedLabel = normalizeComparableText(label);
    const normalizedHuman = normalizeComparableText(human);
    const normalizedAstro = normalizeComparableText(astro);

    if (normalizedLabel && seenLabels.has(normalizedLabel)) {
      continue;
    }

    if (normalizedHuman && seenHuman.has(normalizedHuman)) {
      if (!normalizedLabel || seenLabels.has(normalizedLabel)) {
        continue;
      }
    }

    const dedupeKey = [normalizedLabel, normalizedHuman, normalizedAstro].join("|");
    if (!dedupeKey.replace(/\|/g, "")) continue;

    const humanAstroKey = [normalizedHuman, normalizedAstro].join("|");
    if (humanAstroKey !== "|" && seenHumanAstro.has(humanAstroKey)) {
      continue;
    }

    const existing = deduped.get(dedupeKey);
    if (!existing) {
      deduped.set(dedupeKey, {
        ...factor,
        label,
        explanationHuman: human,
        explanationAstro: astro,
      });
      if (humanAstroKey !== "|") {
        seenHumanAstro.add(humanAstroKey);
      }
      if (normalizedLabel) seenLabels.add(normalizedLabel);
      if (normalizedHuman) seenHuman.add(normalizedHuman);
      continue;
    }

    const existingScore = Number(Boolean(existing.value)) + Number(Boolean(existing.explanationAstro)) + Number(Boolean(existing.explanationHuman));
    const candidateScore = Number(Boolean(factor.value)) + Number(Boolean(factor.explanationAstro)) + Number(Boolean(factor.explanationHuman));
    if (candidateScore > existingScore) {
      deduped.set(dedupeKey, {
        ...factor,
        label,
        explanationHuman: human,
        explanationAstro: astro,
      });
    }
  }

  return Array.from(deduped.values());
}

function preferAstroExplanationWhenHumanDuplicatesLabel(factor: NormalizedDetailFactor): NormalizedDetailFactor {
  const label = sanitizeHumanFacingText(factor.label);
  const human = sanitizeHumanFacingText(factor.explanationHuman);
  const astro = sanitizeHumanFacingText(factor.explanationAstro);

  if (!isSemanticallyDuplicateText(human, label)) {
    return {
      ...factor,
      label: label || factor.label,
      explanationHuman: human || factor.explanationHuman,
      explanationAstro: astro,
    };
  }

  if (astro && !isSemanticallyDuplicateText(astro, label)) {
    return {
      ...factor,
      label: label || factor.label,
      explanationHuman: astro,
      explanationAstro: null,
    };
  }

  return {
    ...factor,
    label: label || factor.label,
    explanationHuman: "",
    explanationAstro: astro,
  };
}

function normalizeExplainabilityCard<T extends { label: string; explanation_human: string; explanation_astro?: string | null }>(item: T): T {
  const label = sanitizeHumanFacingText(item.label) || "";
  const human = sanitizeHumanFacingText(item.explanation_human) || "";
  const astro = sanitizeHumanFacingText(item.explanation_astro);

  if (isSemanticallyDuplicateText(human, label)) {
    if (astro && !isSemanticallyDuplicateText(astro, label)) {
      return {
        ...item,
        label,
        explanation_human: astro,
        explanation_astro: null,
      };
    }

    return {
      ...item,
      label,
      explanation_human: "",
      explanation_astro: astro,
    };
  }

  return {
    ...item,
    label,
    explanation_human: human,
    explanation_astro: astro,
  };
}

function textLooksDomainScoped(value: string | null | undefined, scoreKey: string): boolean {
  const normalizedValue = normalizeComparableText(value);
  if (!normalizedValue) return false;
  const aliases: Record<string, string[]> = {
    energy: ['energy', 'health', 'tone', 'ресурс', 'энерг', 'тел', 'тонус'],
    money: ['money', 'work_money', 'work', 'career', 'работ', 'деньг', 'финанс', 'цен', 'срок', 'обязательств'],
    love: ['love', 'relationships', 'relationship', 'relation', 'отнош', 'чувств', 'контакт', 'партнер', 'близост', 'мотив'],
    focus: ['focus', 'mind', 'focus_time', 'фокус', 'ритм', 'вниман'],
  };
  return (aliases[String(scoreKey || '').trim().toLowerCase()] ?? [String(scoreKey || '').trim().toLowerCase()])
    .some((needle) => normalizedValue.includes(needle));
}

function factorMatchesScoreKey(label: string | null | undefined, relatedKey: string): boolean {
  const normalizedLabel = normalizeComparableText(label);
  const normalizedKey = normalizeComparableText(relatedKey);
  if (!normalizedLabel || !normalizedKey) return false;

  const aliases: Record<string, string[]> = {
    energy: ["energy", "энерг", "тонус", "ресурс", "сил", "драйв", "ритм"],
    focus: ["focus", "фокус", "вниман", "концентрац", "ясност", "структур"],
    money: ["money", "деньг", "финанс", "доход", "бюджет", "cash"],
    love: ["love", "отношен", "любов", "romance", "партнер", "сердц"],
  };

  return (aliases[normalizedKey] ?? [normalizedKey]).some((alias) => normalizedLabel.includes(alias));
}

function buildScoreFallbackFactors(score: DayBriefDto["scores"][number], brief: DayBriefDto) {
  const scoped = (brief.explainability.selected_factors ?? [])
    .filter((factor) => {
      if (!(factor?.label || factor?.explanation_human)) return false;
      const factorRecord = factor as { related_key?: string | null; domain?: string | null; key?: string | null };
      const relatedKey = String(factorRecord.related_key || factorRecord.domain || factorRecord.key || "").trim();
      if (relatedKey) {
        return normalizeComparableText(relatedKey) === normalizeComparableText(score.key);
      }
      return factorMatchesScoreKey(factor.label, score.key)
        || textLooksDomainScoped(factor.explanation_human, score.key)
        || textLooksDomainScoped(factor.explanation_astro, score.key);
    })
    .map((factor) => ({
      label: factor.label,
      explanation_human: factor.explanation_human,
      explanation_astro: factor.explanation_astro,
      value: factor.signal != null && factor.signal >= 0.35 ? "Сильный сигнал" : factor.signal != null && factor.signal >= 0.15 ? "Умеренный сигнал" : factor.signal != null ? "Фоновый сигнал" : null,
    }));

  return scoped.slice(0, 3);
}

function shouldSuppressAstroText(
  astro: string | null | undefined,
  itemText: string | null | undefined,
  whyText?: string | null,
  humanText?: string | null,
): boolean {
  const trimmed = String(astro || "").trim();
  if (!trimmed) return true;
  if (isLikelyRawSemanticKey(trimmed)) return true;
  if (isSemanticallyDuplicateText(trimmed, itemText) || isSemanticallyDuplicateText(trimmed, whyText) || isSemanticallyDuplicateText(trimmed, humanText)) {
    return true;
  }
  return false;
}

function collectTodayCompositionAnchors(brief: DayBriefDto): string[] {
  return [
    brief.summary.headline,
    brief.summary.subhead,
    ...brief.best_uses.map((item) => item.text),
    ...brief.risks.map((item) => item.text),
    ...brief.scores.flatMap((score) => [score.advice, score.details?.why_text ?? null]),
    ...brief.windows.flatMap((window) => [window.advice, window.details?.why_text ?? null]),
  ]
    .map((item) => String(item || "").trim())
    .filter(Boolean);
}

function shouldSuppressByComposition(value: string | null | undefined, anchors: string[]): boolean {
  const normalizedValue = normalizeComparableText(value);
  if (!normalizedValue) return true;
  return anchors.some((anchor) => isSemanticallyDuplicateText(normalizedValue, anchor));
}

function isScopedScoreWhyText(
  whyText: string | null | undefined,
  score: DayBriefDto["scores"][number],
  brief: DayBriefDto,
): boolean {
  const normalizedWhyText = normalizeComparableText(whyText);
  if (!normalizedWhyText) return false;
  if (isGenericExplainabilityPhrase(whyText)) return false;
  if (isSemanticallyDuplicateText(whyText, score.advice) && !textLooksDomainScoped(whyText, score.key)) return false;

  const occurrences = brief.scores.reduce((count, candidate) => {
    const candidateWhyText = candidate.details?.why_text;
    return isSemanticallyDuplicateText(candidateWhyText, whyText) ? count + 1 : count;
  }, 0);

  if (occurrences > 1) return false;

  const reusedSelectedFactor = (brief.explainability.selected_factors ?? []).some((factor) => {
    if (!isSemanticallyDuplicateText(factor.explanation_human, whyText)) return false;
    return !looksLikeDomainScopedFactor(factor, score.key);
  });

  if (reusedSelectedFactor) return false;

  const reusedPersonalizedFactor = (brief.personalized_factors ?? []).some((factor) => {
    if (!isSemanticallyDuplicateText(factor.explanation_human, whyText)) return false;
    return !factorMatchesScoreKey(factor.label, score.key);
  });

  return !reusedPersonalizedFactor;
}

function pickExplainabilityLead(cards: Array<{ explanation_human: string }>): string {
  const lead = cards.find((card) => !isGenericExplainabilityPhrase(card.explanation_human));
  if (!lead) {
    return "Ключевые сигналы дня собраны в короткий персональный вывод.";
  }
  return lead.explanation_human;
}

// FN-CONTRACT: FN-TODAY-BUILD-EXPLAINABILITY-CARDS
// purpose: Build de-duplicated explainability cards from personalized and selected factors.
function buildTodayExplainabilityCards(brief: DayBriefDto) {
  // START_BLOCK: TODAY_EXPLAINABILITY_CARD_SELECTION
  const compositionAnchors = collectTodayCompositionAnchors(brief);
  const personalized = brief.personalized_factors.map((factor, index) => normalizeExplainabilityCard({
    id: factor.id || `personalized-${index}`,
    label: sanitizeHumanFacingText(factor.label) || "",
    explanation_human: sanitizeHumanFacingText(factor.explanation_human) || "",
    explanation_astro: sanitizeHumanFacingText(factor.explanation_astro),
    priority: typeof factor.weight === "number"
      ? factor.weight
      : factor.impact === "high"
        ? 3
        : factor.impact === "medium"
          ? 2
          : 1,
    source: "personalized" as const,
  }));

  const selected = (brief.explainability.selected_factors ?? []).map((factor, index) => normalizeExplainabilityCard({
    id: factor.id || `selected-${index}`,
    label: sanitizeHumanFacingText(factor.label) || "",
    explanation_human: sanitizeHumanFacingText(factor.explanation_human) || "",
    explanation_astro: sanitizeHumanFacingText(factor.explanation_astro),
    priority: typeof factor.signal === "number" ? factor.signal : 0,
    source: "selected" as const,
  }));

  const deduped = new Map<string, (typeof personalized)[number]>();
  const seenExplanationKeys = new Set<string>();

  for (const item of [...personalized, ...selected]) {
    const normalizedLabel = normalizeComparableText(item.label);
    const normalizedExplanation = normalizeComparableText(item.explanation_human);
    if ((!normalizedLabel && !normalizedExplanation) || isGenericExplainabilityPhrase(item.explanation_human)) {
      continue;
    }

    if (shouldSuppressByComposition(item.explanation_human, compositionAnchors)) {
      continue;
    }

    if (normalizedExplanation && seenExplanationKeys.has(normalizedExplanation)) {
      continue;
    }

    const dedupKey = [normalizedExplanation, normalizedLabel].filter(Boolean).join('|');
    const existing = deduped.get(dedupKey);
    if (!existing) {
      deduped.set(dedupKey, item);
      if (normalizedExplanation) seenExplanationKeys.add(normalizedExplanation);
      continue;
    }

    const existingScore = existing.priority + (existing.source === "personalized" ? 0.25 : 0);
    const candidateScore = item.priority + (item.source === "personalized" ? 0.25 : 0);
    if (candidateScore > existingScore) {
      deduped.set(dedupKey, item);
      if (normalizedExplanation) seenExplanationKeys.add(normalizedExplanation);
    }
  }

  return Array.from(deduped.values())
    .sort((left, right) => {
      const byPriority = right.priority - left.priority;
      if (byPriority !== 0) return byPriority;
      if (left.source !== right.source) return left.source === "personalized" ? -1 : 1;
      return left.label.localeCompare(right.label, "ru");
    })
    .slice(0, 3);
  // END_BLOCK: TODAY_EXPLAINABILITY_CARD_SELECTION
}

// FN-CONTRACT: FN-TODAY-BUILD-SCORE-DISCLOSURE
// purpose: Prepare score disclosure copy and evidence factors from brief detail branches.
function buildScoreDisclosureContent(score: DayBriefDto["scores"][number], brief: DayBriefDto) {
  const ownFactors = Array.isArray(score.details?.supporting_factors)
    ? score.details.supporting_factors.filter((item) => item?.label || item?.explanation_human)
    : [];
  const normalizedOwnFactors = mapLegacyFactorsToNormalized(ownFactors, score.key);
  const hasScopedOwnFactors = normalizedOwnFactors.length > 0;
  const domainScopedSelected = (brief.explainability.selected_factors ?? [])
    .filter((factor) => looksLikeDomainScopedFactor(factor, score.key))
    .filter((factor) => !isGenericDomainFactor(factor, brief))
    .map((factor) => ({
      label: factor.label,
      explanation_human: factor.explanation_human,
      explanation_astro: factor.explanation_astro,
      value: null,
    }));
  const normalizedFallbackFactors = mapLegacyFactorsToNormalized(domainScopedSelected, score.key);
  const hasMeaningfulFallback = normalizedFallbackFactors.some((factor) => factor.label || factor.explanationHuman || factor.explanationAstro || factor.value);

  return {
    title: hasScopedOwnFactors || hasMeaningfulFallback ? "Что повлияло" : null,
    body: null,
    factors: hasScopedOwnFactors ? normalizedOwnFactors : (hasMeaningfulFallback ? normalizedFallbackFactors : []),
  };
}

function mapLegacyFactorsToNormalized(
  factors: Array<{ label?: string | null; explanation_human?: string | null; explanation_astro?: string | null; value?: string | null }> | undefined,
  relatedKey: string,
): NormalizedDetailFactor[] {
  return dedupeNormalizedFactors((factors ?? [])
    .filter((factor) => factor?.label || factor?.explanation_human)
    .flatMap((factor, index) => {
      const label = sanitizeHumanFacingText(factor.label);
      const human = sanitizeHumanFacingText(factor.explanation_human);
      const astro = sanitizeHumanFacingText(factor.explanation_astro);
      if (!label && !human && !astro) {
        return [];
      }
      const sanitizedLabel = label && !isGenericExplainabilityPhrase(label) ? label : null;
      const keepLabel = label && (
        factorMatchesScoreKey(label, relatedKey)
        || textLooksDomainScoped(label, relatedKey)
        || (!human && !astro)
      ) ? sanitizedLabel : null;
      if (label && isGenericExplainabilityPhrase(label) && !human && !astro) {
        return [];
      }
      if (human && keepLabel && isSemanticallyDuplicateText(human, keepLabel)) {
        return [{
          id: `today-${relatedKey}-factor-${index + 1}`,
          label: keepLabel,
          explanationHuman: null,
          explanationAstro: shouldSuppressAstroText(astro, null, null, human) ? null : astro,
          value: null,
          impact: null,
          source: "today_supporting_factor",
          relatedKey,
        }];
      }
      const safeValue = sanitizeHumanFacingText(factor.value);
      if (!keepLabel && !human && !astro && !safeValue) {
        return [];
      }
      return [{
        id: `today-${relatedKey}-factor-${index + 1}`,
        label: keepLabel,
        explanationHuman: human,
        explanationAstro: shouldSuppressAstroText(astro, null, null, human) ? null : astro,
        value: safeValue || null,
        impact: null,
        source: "today_supporting_factor",
        relatedKey,
      }];
    })).map(preferAstroExplanationWhenHumanDuplicatesLabel);
}

function buildItemDisclosureFactors(
  factors: Array<{ label: string; explanation_human: string; explanation_astro?: string | null; value?: string | null }> | undefined,
  itemText: string,
  whyText?: string | null,
): NormalizedDetailFactor[] {
  return dedupeNormalizedFactors((factors ?? []).filter((factor) => {
    const label = String(factor?.label || "").trim();
    const human = String(factor?.explanation_human || "").trim();
    if (!label && !human) return false;
    if (isLikelyRawSemanticKey(label)) return false;
    if (isGenericExplainabilityPhrase(human)) return false;
    if (isSemanticallyDuplicateText(human, itemText) || isSemanticallyDuplicateText(human, whyText)) return false;
    if (isSemanticallyDuplicateText(label, itemText) || isSemanticallyDuplicateText(label, whyText)) return false;
    return true;
  }).map((factor, index) => {
    const human = String(factor.explanation_human || "").trim();
    const astro = String(factor.explanation_astro || "").trim();
    return {
      id: `today-item-factor-${index + 1}`,
      label: String(factor.label || "").trim() || `Фактор ${index + 1}`,
      explanationHuman: human,
      explanationAstro: shouldSuppressAstroText(astro, itemText, whyText, human) ? null : astro,
      value: String(factor.value || "").trim() || null,
      impact: null,
      source: "today_supporting_factor",
      relatedKey: null,
    };
  })).map(preferAstroExplanationWhenHumanDuplicatesLabel);
}

function filterNormalizedItemFactors(factors: NormalizedDetailFactor[] | undefined, itemText: string, whyText?: string | null): NormalizedDetailFactor[] {
  return dedupeNormalizedFactors((factors ?? []).flatMap((factor) => {
    if (isLikelyRawSemanticKey(factor.label)) return [];
    if (isGenericExplainabilityPhrase(factor.explanationHuman)) return [];
    if (isSemanticallyDuplicateText(factor.explanationHuman, itemText) || isSemanticallyDuplicateText(factor.explanationHuman, whyText)) return [];
    if (isSemanticallyDuplicateText(factor.label, itemText) || isSemanticallyDuplicateText(factor.label, whyText)) return [];
    return [{
      ...factor,
      explanationAstro: shouldSuppressAstroText(factor.explanationAstro, itemText, whyText, factor.explanationHuman) ? null : factor.explanationAstro,
    }];
  })).map(preferAstroExplanationWhenHumanDuplicatesLabel);
}

function normalizeItemDisclosureBody(body: string | null | undefined, itemText: string, factors: NormalizedDetailFactor[]): string | null {
  const normalizedBody = String(body || "").trim();
  if (!normalizedBody) return null;
  if (isSemanticallyDuplicateText(normalizedBody, itemText)) {
    return factors.length ? null : normalizedBody;
  }
  return normalizedBody;
}

function formatWindowMeta(window: DayBriefDto["windows"][number]): string | null {
  const parts = [window.start && window.end ? `${window.start}–${window.end}` : null].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}

function normalizeSemanticLabel(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function shouldShowWindowModeBadge(window: DayBriefDto["windows"][number]): boolean {
  const modeLabel = normalizeSemanticLabel(WINDOW_MODE_COPY[window.mode].label);
  const windowLabel = normalizeSemanticLabel(window.label);
  if (!windowLabel) return true;
  return !windowLabel.includes(modeLabel) && !modeLabel.includes(windowLabel);
}

export function TodayVerdict({ brief }: { brief: DayBriefDto }) {
  const copy = DAY_MODE_COPY[brief.summary.day_type];
  const moonContext = brief.context.label || brief.context.moon_phase || null;
  return (
    <section data-testid="today-verdict" className="relative overflow-hidden rounded-[32px] border border-indigo-100 bg-[linear-gradient(145deg,#0f172a_0%,#1e1b4b_55%,#312e81_100%)] p-6 text-white shadow-[0_30px_70px_-45px_rgba(15,23,42,0.85)]">
      <div className="pointer-events-none absolute -left-16 top-6 h-48 w-48 rounded-full bg-amber-300/20 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 bottom-0 h-60 w-60 rounded-full bg-fuchsia-500/20 blur-3xl" />
      <div className="relative z-10 flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-200">Вердикт дня</p>
          <div data-testid="today-day-mode" className={`mt-3 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold ${copy.badgeClass}`}>
            {copy.label}
          </div>
          <h1 className="mt-5 text-2xl font-semibold leading-tight text-white">{brief.summary.headline}</h1>
          <p className="mt-3 text-base leading-relaxed text-white/85">{brief.summary.subhead}</p>
        </div>
        <div data-testid="today-moon-context" className="rounded-[24px] border border-white/20 bg-white/10 p-4 text-center shadow-lg shadow-slate-950/20 sm:max-w-[220px]">
          <div className="text-4xl" aria-hidden>{brief.context.moon_emoji || "🌙"}</div>
          {moonContext ? <p className="mt-3 text-sm leading-relaxed text-white/85">{moonContext}</p> : <p className="mt-3 text-sm leading-relaxed text-white/85">Персональный контекст дня</p>}
        </div>
      </div>
    </section>
  );
}

export function TodayScores({ brief, onScoreTap }: { brief: DayBriefDto; onScoreTap: (scoreKey: string, scoreValue: number) => void }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2" aria-label="Day brief scores">
      {brief.scores.map((score) => <TodayScoreCard key={score.key} brief={brief} score={score} onScoreTap={onScoreTap} />)}
    </section>
  );
}

function TodayScoreCard({
  brief,
  score,
  onScoreTap,
}: {
  brief: DayBriefDto;
  score: DayBriefDto["scores"][number];
  onScoreTap: (scoreKey: string, scoreValue: number) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const disclosure = buildScoreDisclosureContent(score, brief);
  const hasDetails = Boolean(String(disclosure.body || "").trim()) || Boolean(disclosure.factors?.length);

  const handleCardClick = useCallback(() => {
    onScoreTap(score.key, score.value);
    if (hasDetails) {
      setIsOpen((current) => !current);
    }
  }, [hasDetails, onScoreTap, score.key, score.value]);

  const panelId = `today-score-details-panel-${score.key}`;

  return (
    <article
      data-testid={`today-score-${score.key}`}
      className="rounded-[24px] border border-slate-200 bg-white/90 p-4 text-left shadow-sm transition hover:border-indigo-200 hover:shadow-md"
    >
      <button
        type="button"
        className="block w-full text-left"
        aria-label={`${score.title}: ${score.value}`}
        aria-expanded={hasDetails ? isOpen : undefined}
        aria-controls={hasDetails ? panelId : undefined}
        onClick={handleCardClick}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">{score.title}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{score.value}</p>
          </div>
          <ConsumerStatusBadge
            label={score.status === "green" ? "Сильная зона" : score.status === "red" ? "Зона риска" : "Нужна аккуратность"}
            tone={score.status === "green" ? "emerald" : score.status === "red" ? "rose" : "amber"}
          />
        </div>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">{score.advice}</p>
      </button>
      <div id={panelId}>
        <DetailDisclosureCard
          testId={`today-score-details-${score.key}`}
          title={disclosure.title}
          body={disclosure.body}
          factors={disclosure.factors}
          compact
          isOpen={isOpen}
          onToggle={() => setIsOpen((current) => !current)}
        />
      </div>
    </article>
  );
}

export function TodayWindows({ brief }: { brief: DayBriefDto }) {
  const detailItems = useMemo(() => normalizeTodayDetailItems(brief), [brief]);
  return (
    <ConsumerPanel data-testid="today-windows" className="p-5 sm:p-6">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
        <Clock3 size={18} className="text-indigo-500" />
        Временные окна
      </div>
      <div className="mt-4 grid gap-3">
        {brief.windows.map((window) => {
          const detailItem = detailItems.find((item) => item.id === window.id && item.source === "today_window");
          const modeCopy = WINDOW_MODE_COPY[window.mode];
          const meta = formatWindowMeta(window);
          return (
            <article key={window.id} className={`rounded-[24px] border p-4 shadow-sm ${modeCopy.className}`}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{window.label}</p>
                  {meta ? <p className="mt-1 text-xs text-slate-500">{meta}</p> : null}
                  <DetailEvidenceChips impact={detailItem?.impact} />
                </div>
                {shouldShowWindowModeBadge(window) ? <span className="rounded-full bg-white/80 px-3 py-1 text-[11px] font-semibold text-slate-700">{modeCopy.label}</span> : null}
              </div>
              <p className="mt-3 text-sm leading-relaxed text-slate-700">{window.advice}</p>
              <DetailDisclosureCard
                testId={`today-window-details-${window.id}`}
                title="Почему окно такое"
                body={detailItem?.body ?? window.details?.why_text}
                factors={detailItem?.factors ?? []}
              />
            </article>
          );
        })}
        {!brief.windows.length && (
          <p className="text-sm text-slate-500">Сегодня лучше держать ровный ритм без резких разворотов.</p>
        )}
      </div>
    </ConsumerPanel>
  );
}

function ItemList({ title, testId, items, icon, detailItems }: { title: string; testId: string; items: DayBriefDto["best_uses"] | DayBriefDto["risks"]; icon: "good" | "risk"; detailItems: NormalizedDetailItem[] }) {
  return (
    <ConsumerPanel data-testid={testId} className="p-5 sm:p-6">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
        {icon === "risk" ? <AlertTriangle size={18} className="text-rose-500" /> : <Sparkles size={18} className="text-emerald-500" />}
        {title}
      </div>
      <div className="mt-4 grid gap-3">
        {items.map((item) => {
          const timeframe = formatItemTimeframe(item.timeframe);
          const detailTestId = icon === "risk" ? `today-risks-details-${item.id}` : `today-actions-details-${item.id}`;
          const normalizedItem = detailItems.find((candidate) => candidate.id === item.id);
          const disclosureFactors = normalizedItem?.factors?.length ? filterNormalizedItemFactors(normalizedItem.factors, item.text, item.why_text) : buildItemDisclosureFactors(item.supporting_factors, item.text, item.why_text);
          const disclosureBody = normalizeItemDisclosureBody(normalizedItem?.body ?? item.why_text, item.text, disclosureFactors);
          return (
            <article key={item.id} className="rounded-[22px] border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm leading-relaxed text-slate-700">{item.text}</p>
              </div>
              <DetailEvidenceChips timeframe={timeframe} impact={normalizedItem?.impact} />
              <DetailDisclosureCard
                testId={detailTestId}
                title={icon === "risk" ? "Почему это важно" : "Почему это в приоритете"}
                body={disclosureBody}
                factors={disclosureFactors}
              />
            </article>
          );
        })}
      </div>
    </ConsumerPanel>
  );
}

export function TodayActions({ brief }: { brief: DayBriefDto }) {
  const detailItems = useMemo(() => normalizeTodayDetailItems(brief).filter((item) => item.source === "today_best_use"), [brief]);
  return <ItemList title="Лучше использовать" testId="today-actions" items={brief.best_uses} icon="good" detailItems={detailItems} />;
}

export function TodayRisks({ brief }: { brief: DayBriefDto }) {
  const detailItems = useMemo(() => normalizeTodayDetailItems(brief).filter((item) => item.source === "today_risk"), [brief]);
  return <ItemList title="Риски дня" testId="today-risks" items={brief.risks} icon="risk" detailItems={detailItems} />;
}

// FN-CONTRACT: FN-TODAY-EXPLAINABILITY
// purpose: Render the today explainability panel from normalized factor cards and detail items.
export function TodayExplainability({ brief }: { brief: DayBriefDto }) {
  const confidence = Math.round(brief.explainability.confidence * 100);
  const cards = buildTodayExplainabilityCards(brief);
  const leadText = pickExplainabilityLead(cards);
  return (
    <ConsumerPanel data-testid="today-explainability" className="p-5 sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Почему такой день</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{leadText}</p>
        </div>
        <div className="rounded-[20px] border border-slate-200 bg-slate-50 px-4 py-3 text-right">
          <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">Уверенность</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{confidence}%</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">Факторов: {brief.explainability.factor_count}</span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((factor) => (
          <article key={factor.id} className="rounded-[20px] border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-900">{factor.label}</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{factor.explanation_human}</p>
            {factor.explanation_astro ? <p className="mt-2 text-xs leading-relaxed text-slate-500">{factor.explanation_astro}</p> : null}
          </article>
        ))}
      </div>
    </ConsumerPanel>
  );
}

export function TodayCtaPanel({ brief, onCta }: { brief: DayBriefDto; onCta: (ctaId: string, href: string, entryPoint: string, block: string) => void }) {
  const primary = brief.cta?.primary ?? { type: "open_week", label: "Открыть неделю", href: "/week" };
  const secondary = brief.cta?.secondary ?? { type: brief.premium?.subscription_active ? "open_history" : "open_premium", label: brief.premium?.subscription_active ? "История разборов" : "Открыть premium", href: brief.premium?.subscription_active ? "/reports/history" : "/reports" };

  return (
    <ConsumerPanel data-testid="today-cta-panel" className="p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Следующий шаг</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{brief.premium?.show_upgrade_cta ? "Разблокируйте следующий уровень разбора и недельную карту." : "Продолжайте в недельную карту или откройте историю разборов."}</p>
        </div>
        <div className="flex flex-col gap-3 sm:min-w-[220px]">
          <Link
            href={primary.href}
            data-testid="today-cta-week"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            onClick={() => onCta(primary.type, primary.href, "daybrief_primary", "CTA_PRIMARY")}
          >
            {primary.label}
            <ArrowRight size={16} />
          </Link>
          <Link
            href={secondary.href}
            data-testid="today-cta-premium"
            className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            onClick={() => onCta(secondary.type, secondary.href, "daybrief_secondary", "CTA_SECONDARY")}
          >
            {secondary.label}
          </Link>
        </div>
      </div>
    </ConsumerPanel>
  );
}
