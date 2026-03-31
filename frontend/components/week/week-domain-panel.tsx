"use client";

import { ConsumerPanel } from "../consumer-page-shell";
import { type WeekSurfaceModel } from "../../lib/week-brief";

export function WeekDomainPanel({ week }: { week: WeekSurfaceModel }) {
  return (
    <ConsumerPanel className="p-5" data-testid="week-domain-panel">
      <div className="space-y-4">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Домены недели</p>
          <h2 className="mt-2 text-lg font-black text-slate-950">Где держится опора недели</h2>
        </div>
        <div className="space-y-4">
          {week.domains.map((domain, index) => (
            <div key={`${domain.key ?? index}`} className="space-y-2" data-testid={`week-domain-${domain.key ?? index}`}>
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
            </div>
          ))}
        </div>
      </div>
    </ConsumerPanel>
  );
}
