"use client";

import { useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { type WeekSurfaceModel } from "../../lib/week-brief";

function pickSupportingFactors(week: WeekSurfaceModel, domainKey: string | null | undefined) {
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
}

function resolveDomainFactors(week: WeekSurfaceModel, domain: WeekSurfaceModel["domains"][number]) {
  if (domain.supporting_factors?.length) {
    return domain.supporting_factors;
  }
  return pickSupportingFactors(week, domain.key);
}

export function WeekDomainPanel({ week }: { week: WeekSurfaceModel }) {
  const [openKey, setOpenKey] = useState<string | null>(null);

  return (
    <ConsumerPanel className="p-5" data-testid="week-domain-panel">
      <div className="space-y-4">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Домены недели</p>
          <h2 className="mt-2 text-lg font-black text-slate-950">Где держится опора недели</h2>
        </div>
        <div className="space-y-4">
          {week.domains.map((domain, index) => (
            <div key={`${domain.key ?? index}`} className="space-y-3" data-testid={`week-domain-${domain.key ?? index}`}>
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
              {domain.why_text || resolveDomainFactors(week, domain).length ? (
                <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-3" data-testid={`week-domain-explainability-${domain.key ?? index}`}>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-bold text-slate-700">Что повлияло</p>
                    <button
                      type="button"
                      onClick={() => setOpenKey((current) => (current === (domain.key ?? `${index}`) ? null : (domain.key ?? `${index}`)))}
                      className="text-[11px] font-bold text-slate-500 transition-colors hover:text-slate-800"
                      data-testid={`week-domain-explainability-toggle-${domain.key ?? index}`}
                    >
                      {openKey === (domain.key ?? `${index}`) ? "Скрыть" : "Открыть"}
                    </button>
                  </div>
                  <div className="mt-2 space-y-2" hidden={openKey !== (domain.key ?? `${index}`)}>
                    {domain.why_text ? <p className="text-xs leading-relaxed text-slate-600">{domain.why_text}</p> : null}
                    {resolveDomainFactors(week, domain).map((factor, factorIndex) => (
                      <div key={factor.id ?? factorIndex} className="rounded-2xl bg-white px-3 py-2">
                        <p className="text-xs font-bold text-slate-900">{factor.label}</p>
                        <p className="mt-1 text-xs leading-relaxed text-slate-600">{factor.explanation_human ?? factor.explanation_astro ?? "Этот фактор поддерживает текущий тон домена."}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </ConsumerPanel>
  );
}
