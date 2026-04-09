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
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";
import { findDetailLayer } from "../../lib/detail-layer";
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
            const detailLayer = findDetailLayer(week.detailLayers, {
              source: "week_domain",
              id: String(domain.key ?? `week-domain-${index + 1}`),
              relatedKey: String(domain.key ?? `week-domain-${index + 1}`),
            });
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
                  body={detailLayer?.body ?? domain.why_text}
                  factors={detailLayer?.factors ?? []}
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
