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
// INTERNALS: pickSupportingFactors, resolveDomainFactors, mapDomainFactors.
// DATA_FLOW: week domains -> per-domain factor normalization -> panel rendering -> disclosure toggles.
// UI_SEAMS: `week-domain-panel`, `week-domain-*`, `week-domain-explainability-*`.
// END_MODULE_MAP: M-WEEK-DOMAIN-PANEL

import { useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { DetailDisclosureCard } from "../detail/detail-disclosure-card";
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";
import type { NormalizedDetailFactor } from "../../lib/detail-layer";
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

// START_FUNCTION_CONTRACT: pickSupportingFactors
// INTENT: Resolve bounded fallback factors for a domain when explicit supporting factors are absent.
// INPUTS: Week surface model and optional domain key.
// OUTPUTS: Up to two supporting factors aligned to the requested domain.
// INVARIANTS: Direct category match wins; heuristic label matching stays bounded; no unrelated global factor fallback.
// END_FUNCTION_CONTRACT: pickSupportingFactors
function pickSupportingFactors(week: WeekSurfaceModel, domainKey: string | null | undefined) {
  // START_BLOCK: DOMAIN_FACTOR_FALLBACK_SELECTION
  const normalizedKey = String(domainKey ?? "").trim().toLowerCase();
  if (!normalizedKey) {
    return [];
  }

  return week.factors.filter((factor) => {
    if (String(factor.category ?? "").trim().toLowerCase() === normalizedKey) {
      return true;
    }
    const label = String(factor.label ?? "").trim().toLowerCase();
    return normalizedKey.includes("work")
      ? label.includes("работ") || label.includes("деньг")
      : normalizedKey.includes("relation")
        ? label.includes("отнош") || label.includes("контакт")
        : normalizedKey.includes("energy")
          ? label.includes("энерг") || label.includes("ресурс")
          : normalizedKey.includes("focus")
            ? label.includes("фокус") || label.includes("ритм") || label.includes("тайм")
            : false;
  }).filter((factor) => {
    const label = String(factor.label ?? "").trim();
    const human = String(factor.explanation_human ?? "").trim();
    const astro = String(factor.explanation_astro ?? "").trim();
    return Boolean(label || human || astro);
  });
  // END_BLOCK: DOMAIN_FACTOR_FALLBACK_SELECTION
}

// START_FUNCTION_CONTRACT: resolveDomainFactors
// INTENT: Prefer explicit domain factors and otherwise derive fallback factors from the week surface.
// INPUTS: Week surface model and a single domain card.
// OUTPUTS: Supporting factors for one domain disclosure.
// INVARIANTS: Explicit domain factors override heuristics.
// END_FUNCTION_CONTRACT: resolveDomainFactors
function resolveDomainFactors(week: WeekSurfaceModel, domain: WeekSurfaceModel["domains"][number]) {
  // START_BLOCK: DOMAIN_FACTOR_SOURCE_SELECTION
  if (domain.supporting_factors?.length) {
    return domain.supporting_factors;
  }
  return pickSupportingFactors(week, domain.key);
  // END_BLOCK: DOMAIN_FACTOR_SOURCE_SELECTION
}

function pickFactorLabel(factor: ReturnType<typeof resolveDomainFactors>[number]) {
  const rawLabel = String(factor?.label || "").trim();
  const explanationAstro = String(factor?.explanation_astro || "").trim();
  if (rawLabel && !/^[a-z]+:[a-z0-9_-]+$/.test(rawLabel.toLowerCase())) {
    return rawLabel;
  }
  if (explanationAstro) {
    const astroLead = explanationAstro.split(/[—:.]/)[0]?.trim();
    if (astroLead) return astroLead;
  }
  return rawLabel;
}

// START_FUNCTION_CONTRACT: mapDomainFactors
// INTENT: Normalize domain supporting factors for the shared detail disclosure layer.
// INPUTS: Raw domain factors and domain identifier.
// OUTPUTS: Filtered normalized detail factors.
// INVARIANTS: Output ids remain deterministic; empty factor rows are excluded.
// END_FUNCTION_CONTRACT: mapDomainFactors
function mapDomainFactors(
  factors: ReturnType<typeof resolveDomainFactors>,
  relatedKey: string,
): NormalizedDetailFactor[] {
  // START_BLOCK: DOMAIN_FACTOR_NORMALIZATION
  return factors
    .map((factor, index) => {
      const label = pickFactorLabel(factor);
      const explanationHuman = String(factor?.explanation_human || "").trim();
      const explanationAstro = String(factor?.explanation_astro || "").trim();
      const value = String(factor?.value || "").trim();
      const normalizedValue = value.toLowerCase();
      if (!label && !explanationHuman && !explanationAstro) return null;
      if (/^[a-z]+:[a-z0-9_-]+$/.test(label.toLowerCase()) && !explanationHuman && !explanationAstro) return null;
      return {
        id: `${relatedKey}-factor-${index + 1}`,
        label: /^[a-z]+:[a-z0-9_-]+$/.test(label.toLowerCase()) ? '' : label,
        explanationHuman: explanationHuman || explanationAstro,
        explanationAstro: explanationAstro || null,
        value: ["green", "yellow", "red", "high", "medium", "background"].includes(normalizedValue) ? null : (value || null),
        impact: null,
        source: "week_supporting_factor",
        relatedKey,
      } satisfies NormalizedDetailFactor;
    })
    .filter((item): item is NormalizedDetailFactor => Boolean(item && (item.label || item.explanationHuman || item.explanationAstro || item.value)));
  // END_BLOCK: DOMAIN_FACTOR_NORMALIZATION
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
                    {domain.headline ? <p className="text-xs text-slate-500">{domain.headline}</p> : null}
                  </div>
                  <div className={`rounded-full border px-2.5 py-1 text-xs font-black uppercase tracking-[0.18em] ${statusStyle.badge}`} data-testid={`week-domain-status-${domain.key ?? index}`}>
                    {domain.value ?? 0}/100
                  </div>
                </div>
                <div className={`h-2 rounded-full ${statusStyle.track}`}>
                  <div className={`h-2 rounded-full ${statusStyle.progress}`} style={{ width: `${Math.max(0, Math.min(100, domain.value ?? 0))}%` }} />
                </div>
                <p className="text-xs leading-relaxed text-slate-600" data-testid={`week-domain-guidance-${domain.key ?? index}`}>
                  {domain.advice?.trim() || "Держите решения в этой зоне простыми и проверяемыми."}
                </p>
                <DetailEvidenceChips values={[domain.value != null ? `${domain.value}/100` : null]} />
                <DetailDisclosureCard
                  testId={`week-domain-explainability-${domain.key ?? index}`}
                  title="Что повлияло"
                  body={domain.why_text}
                  factors={mapDomainFactors(resolveDomainFactors(week, domain), String(domain.key ?? `week-domain-${index + 1}`))}
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
