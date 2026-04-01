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
import { type WeekSurfaceModel } from "../../lib/week-brief";

// START_FUNCTION_CONTRACT: pickSupportingFactors
// INTENT: Resolve bounded fallback factors for a domain when explicit supporting factors are absent.
// INPUTS: Week surface model and optional domain key.
// OUTPUTS: Up to two supporting factors aligned to the requested domain.
// INVARIANTS: Direct category match wins; heuristic label matching stays bounded; final fallback uses week factor head.
// END_FUNCTION_CONTRACT: pickSupportingFactors
function pickSupportingFactors(week: WeekSurfaceModel, domainKey: string | null | undefined) {
  // START_BLOCK: DOMAIN_FACTOR_FALLBACK_SELECTION
  const normalizedKey = String(domainKey ?? "").trim().toLowerCase();
  if (!normalizedKey) {
    return week.factors.slice(0, 2);
  }

  const direct = week.factors.filter((factor) => String(factor.category ?? "").trim().toLowerCase() === normalizedKey);
  if (direct.length) {
    return direct.slice(0, 2);
  }

  const byLabel = week.factors.filter((factor) => {
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
  });

  return (byLabel.length ? byLabel : week.factors).slice(0, 2);
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
      const label = String(factor?.label || "").trim();
      const explanationHuman = String(factor?.explanation_human || "").trim();
      const explanationAstro = String(factor?.explanation_astro || "").trim();
      const value = String(factor?.value || "").trim();
      if (!label && !explanationHuman && !explanationAstro) return null;
      return {
        id: `${relatedKey}-factor-${index + 1}`,
        label: label || `Фактор ${index + 1}`,
        explanationHuman: explanationHuman || explanationAstro,
        explanationAstro: explanationAstro || null,
        value: value || null,
        impact: null,
        source: "week_supporting_factor",
        relatedKey,
      } satisfies NormalizedDetailFactor;
    })
    .filter((item): item is NormalizedDetailFactor => Boolean(item));
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
            return (
              <div key={`${domain.key ?? index}`} className="space-y-3" data-testid={`week-domain-${domain.key ?? index}`}>
                {/* START_BLOCK: WEEK_DOMAIN_CARD_CONTENT */}
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-slate-900">{domain.title}</p>
                    {domain.headline ? <p className="text-xs text-slate-500">{domain.headline}</p> : null}
                  </div>
                  <p className="text-sm font-black text-slate-900">{domain.value ?? 0}/100</p>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div className="h-2 rounded-full bg-slate-900" style={{ width: `${Math.max(0, Math.min(100, domain.value ?? 0))}%` }} />
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
