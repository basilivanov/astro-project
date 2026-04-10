"use client";

// START_MODULE_CONTRACT: M-WEEK-DOMAIN-PANEL
// INTENT: Render domain-specific week summaries with explainability disclosure.
// INPUTS: `week` surface model containing domain cards and factors.
// OUTPUTS: Responsive panel grid for work/love/energy/etc domain interpretation.
// INVARIANTS: Only domains with narrative content render; factor evidence stays attached to the originating domain.
// SIDE_EFFECTS: Local disclosure state for per-domain detail cards only.
// DEPENDENCIES: ConsumerPanel shell, detail disclosure primitives, week brief model.
// FAILURE_MODES: Missing factor evidence degrades to empty disclosure factors; absent titles fall back to domain id.
// CALLERS: `frontend/app/week/page.tsx` detail stack.
// NOTES: Adds semantic structure only.
// END_MODULE_CONTRACT: M-WEEK-DOMAIN-PANEL

// START_MODULE_MAP: M-WEEK-DOMAIN-PANEL
// EXPORTS: WeekDomainPanel.
// INTERNALS: normalizeDomainStatus.
// DATA_FLOW: week domains -> normalized shared detail-layer lookup -> panel rendering -> disclosure toggles.
// UI_SEAMS: `week-domain-panel`, `week-domain-*`, `week-domain-explainability-*`.
// END_MODULE_MAP: M-WEEK-DOMAIN-PANEL

import { useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { DetailDisclosureCard } from "../detail/detail-disclosure-card";
import { findDetailLayer, type NormalizedDetailFactor } from "../../lib/detail-layer";
import { type LightStatus, type WeekSurfaceModel } from "../../lib/week-brief";

const DOMAIN_STATUS_STYLES: Record<LightStatus, { badge: string; progress: string; track: string; card: string }> = {
  green: {
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
    progress: "bg-emerald-500",
    track: "bg-emerald-100",
    card: "border-emerald-200/80 bg-emerald-50/40",
  },
  yellow: {
    badge: "border-amber-200 bg-amber-50 text-amber-700",
    progress: "bg-amber-500",
    track: "bg-amber-100",
    card: "border-amber-200/80 bg-amber-50/40",
  },
  red: {
    badge: "border-rose-200 bg-rose-50 text-rose-700",
    progress: "bg-rose-500",
    track: "bg-rose-100",
    card: "border-rose-200/80 bg-rose-50/40",
  },
};

function normalizeDomainStatus(value: string | null | undefined, score: number | null | undefined): LightStatus {
  const normalizedValue = String(value ?? "").trim().toLowerCase();
  if (normalizedValue === "green" || normalizedValue === "yellow" || normalizedValue === "red") {
    return normalizedValue as LightStatus;
  }
  const numericScore = Number(score ?? 0);
  if (numericScore >= 70) return "green";
  if (numericScore >= 45) return "yellow";
  return "red";
}

function normalizeHeadlineText(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function resolveVisibleDomainHeadline(domain: WeekSurfaceModel["domains"][number]): string | null {
  const headline = String(domain.headline || "").trim();
  if (!headline) return null;

  const normalizedHeadline = normalizeHeadlineText(headline);
  const normalizedTitle = normalizeHeadlineText(domain.title);
  const normalizedScore = typeof domain.value === "number" ? normalizeHeadlineText(`${domain.value}/100`) : "";

  if (!normalizedHeadline) return null;
  if (normalizedTitle && normalizedHeadline === normalizedTitle) return null;
  if (normalizedTitle && normalizedScore && normalizedHeadline.includes(normalizedTitle) && normalizedHeadline.includes(normalizedScore)) {
    return null;
  }
  if (/^(focus|energy|work|money|relationships|love)$/i.test(headline)) {
    return null;
  }

  return headline;
}

function normalizeComparableText(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function buildGenericWeekDomainExplanation(domain: WeekSurfaceModel["domains"][number]): string {
  const key = normalizeComparableText(domain.key);
  const domainCopy: Record<string, string> = {
    work: "Неделя просит держать работу и деньги в одном проверяемом контуре: без лишних обещаний и со ставкой на фиксируемый результат.",
    relationships: "Неделя просит меньше достраивать за другого и больше держаться за спокойный тон, ясные ожидания и короткие разговоры по делу.",
    love: "Неделя лучше проживается через ясные сигналы и мягкий тон, а не через эмоциональное давление и угадывание мотивов.",
    energy: "Неделя держится на темпе, буфере ресурса и способности не превращать каждый день в спринт.",
    focus: "Неделя лучше всего складывается через один главный приоритет, короткие циклы и защиту внимания от распыления.",
  };
  return domainCopy[key] ?? "Неделя лучше всего складывается через один короткий приоритет и спокойный управляемый ритм.";
}

function factorMatchesDomain(factor: WeekSurfaceModel["factors"][number], domainKey: string | null | undefined): boolean {
  const key = normalizeComparableText(domainKey);
  const category = normalizeComparableText(factor.category);
  const label = normalizeComparableText(factor.label);
  const aliases: Record<string, string[]> = {
    work: ["work", "money", "career", "работ", "деньг", "финанс"],
    relationships: ["relationships", "love", "relation", "отнош", "любов", "контакт"],
    love: ["love", "relationships", "relation", "отнош", "любов", "контакт"],
    energy: ["energy", "ресурс", "энерг", "ритм", "тонус"],
    focus: ["focus", "фокус", "вниман", "структур", "концентрац"],
  };
  return (aliases[key] ?? [key]).some((needle) => category.includes(needle) || label.includes(needle));
}

function deriveFallbackFactors(week: WeekSurfaceModel, domain: WeekSurfaceModel["domains"][number], index: number): NormalizedDetailFactor[] {
  return (week.factors ?? [])
    .filter((factor) => factorMatchesDomain(factor, domain.key))
    .slice(0, 2)
    .map((factor, factorIndex) => ({
      id: factor.id?.trim() || `week-domain-${index + 1}-fallback-factor-${factorIndex + 1}`,
      label: factor.label?.trim() || `Фактор ${factorIndex + 1}`,
      explanationHuman: factor.explanation_human?.trim() || factor.explanation_astro?.trim() || "",
      explanationAstro: factor.explanation_astro?.trim() || null,
      value: null,
      impact: factor.impact === "high" || factor.impact === "medium" || factor.impact === "low" ? factor.impact : null,
      source: "week_major_factor",
      relatedKey: domain.key ?? null,
    }));
}

// START_FUNCTION_CONTRACT: WeekDomainPanel
// INTENT: Compose weekly domain cards with optional explainability disclosure.
// INPUTS: Week surface model.
// OUTPUTS: Grid of domain cards grouped under a shared panel shell.
// INVARIANTS: Rendering order follows `week.domains`; disclosure state is keyed by domain id.
// END_FUNCTION_CONTRACT: WeekDomainPanel
export function WeekDomainPanel({ week }: { week: WeekSurfaceModel }) {
  const [openKey, setOpenKey] = useState<string | null>(null);

  return (
    // START_BLOCK: WEEK_DOMAIN_PANEL_CONTAINER
    <ConsumerPanel className="p-5" data-testid="week-domain-panel">
      <div className="space-y-4">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Домены недели</p>
          <h2 className="mt-2 text-lg font-black text-slate-950">Где держится опора недели</h2>
        </div>
        <div className="space-y-4">
          {week.domains.map((domain, index) => {
            const domainKey = domain.key ?? `${index}`;
            const domainStatus = normalizeDomainStatus(domain.status, domain.value);
            const statusStyle = DOMAIN_STATUS_STYLES[domainStatus];
            const visibleHeadline = resolveVisibleDomainHeadline(domain);
            const detailLayer = findDetailLayer(week.detailLayers, {
              source: "week_domain",
              id: String(domain.key ?? `week-domain-${index + 1}`),
              relatedKey: String(domain.key ?? `week-domain-${index + 1}`),
            });
            const fallbackFactors = detailLayer?.factors?.length ? [] : deriveFallbackFactors(week, domain, index);
            const disclosureBody = detailLayer?.body ?? domain.why_text ?? buildGenericWeekDomainExplanation(domain);
            return (
              <div
                key={`${domain.key ?? index}`}
                className={`space-y-3 rounded-3xl border p-4 ${statusStyle.card}`}
                data-testid={`week-domain-${domain.key ?? index}`}
                data-domain-status={domainStatus}
              >
                {/* START_BLOCK: WEEK_DOMAIN_CARD_CONTENT */}
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-slate-900">{domain.title}</p>
                    {visibleHeadline ? <p className="text-xs text-slate-500">{visibleHeadline}</p> : null}
                  </div>
                  <div className={`rounded-full border px-2.5 py-1 text-xs font-black uppercase tracking-[0.18em] ${statusStyle.badge}`} data-testid={`week-domain-status-${domain.key ?? index}`}>
                    {domain.value ?? 0}/100
                  </div>
                </div>
                <p className="text-xs leading-relaxed text-slate-600" data-testid={`week-domain-guidance-${domain.key ?? index}`}>
                  {domain.advice?.trim() || "Держите решения в этой зоне простыми и проверяемыми."}
                </p>
                <DetailDisclosureCard
                  testId={`week-domain-explainability-${domain.key ?? index}`}
                  title="Что повлияло"
                  body={disclosureBody}
                  factors={detailLayer?.factors?.length ? detailLayer.factors : fallbackFactors}
                  compact
                  isOpen={openKey === domainKey}
                  onToggle={() => setOpenKey((current) => (current === domainKey ? null : domainKey))}
                />
                {/* END_BLOCK: WEEK_DOMAIN_CARD_CONTENT */}
              </div>
            );
          })}
        </div>
      </div>
    </ConsumerPanel>
    // END_BLOCK: WEEK_DOMAIN_PANEL_CONTAINER
  );
}
