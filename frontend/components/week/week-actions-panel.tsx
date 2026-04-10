"use client";

// START_MODULE_CONTRACT: M-WEEK-ACTIONS-PANEL
// INTENT: Render weekly action and risk lists with explainability disclosure and factor fallback wiring.
// INPUTS: `week` surface model with actions, risks, and normalized factor evidence.
// OUTPUTS: Two detail panels for actionable guidance and risk monitoring without mutating week state.
// INVARIANTS: Factor fallback stays bounded; disclosure state stays local; action/risk rendering remains behaviorally symmetric.
// SIDE_EFFECTS: React local state for disclosure toggles only.
// DEPENDENCIES: ConsumerPanel shell, detail disclosure primitives, week brief surface model.
// FAILURE_MODES: Missing factor text collapses to filtered empty evidence; absent ids fall back to stable derived keys.
// CALLERS: `frontend/app/week/page.tsx` week detail layout.
// NOTES: Strict-GRACE annotation only; preserve existing UI output and interaction semantics.
// END_MODULE_CONTRACT: M-WEEK-ACTIONS-PANEL

// START_MODULE_MAP: M-WEEK-ACTIONS-PANEL
// EXPORTS: WeekActionsPanel.
// INTERNALS: renderItems.
// DATA_FLOW: week surface -> normalized shared detail-layer lookup -> action/risk list rendering.
// UI_SEAMS: `week-actions-panel`, `week-risks-panel`, disclosure cards, evidence chips.
// END_MODULE_MAP: M-WEEK-ACTIONS-PANEL

import { useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { DetailDisclosureCard } from "../detail/detail-disclosure-card";
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";
import { findDetailLayer } from "../../lib/detail-layer";
import { type WeekSurfaceModel } from "../../lib/week-brief";

// START_FUNCTION_CONTRACT: ActionRiskList
// INTENT: Render a disclosure-enabled list for weekly actions or risks.
// INPUTS: Item collection, test id namespace, week surface model, and semantic item kind.
// OUTPUTS: List markup with evidence chips and disclosure cards.
// INVARIANTS: Disclosure state is local to the rendered list; explainability labels stay aligned to item kind.
// END_FUNCTION_CONTRACT: ActionRiskList
function ActionRiskList({ items, testId, week, kind }: { items: WeekSurfaceModel["actions"]; testId: string; week: WeekSurfaceModel; kind: "action" | "risk" }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const visibleItems = items.filter((item) => item.tag !== "all_week").slice(0, 2);

  if (!visibleItems.length) {
    return <p className="text-sm leading-relaxed text-slate-500">Здесь пока нет отдельного weekly-акцента.</p>;
  }

  return (
    // START_BLOCK: ACTION_RISK_LIST_RENDER
    <ul className="space-y-2" data-testid={testId}>
      {visibleItems.map((item, index) => {
        const itemKey = item.id ?? `${index}`;
        const detailLayer = findDetailLayer(week.detailLayers, {
          source: kind === "risk" ? "week_risk" : "week_action",
          id: item.id ?? `${kind}-${index + 1}`,
          relatedKey: item.factor_id ?? item.id ?? `${kind}-${index + 1}`,
        });
        return (
          <li key={item.id ?? item.text} className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3 text-sm leading-relaxed text-slate-700">
            <p>{item.text}</p>
            <DetailEvidenceChips timeframe={item.timeframe} impact={item.impact === "high" || item.impact === "medium" || item.impact === "low" ? item.impact : null} />
            <DetailDisclosureCard
              testId={`${testId}-explainability-${index + 1}`}
              title={kind === "risk" ? "Почему это важно" : "Почему это в фокусе"}
              body={detailLayer?.body ?? item.why_text}
              factors={detailLayer?.factors ?? []}
              compact
              isOpen={openId === itemKey}
              onToggle={() => setOpenId((current) => (current === itemKey ? null : itemKey))}
            />
          </li>
        );
      })}
    </ul>
    // END_BLOCK: ACTION_RISK_LIST_RENDER
  );
}

// START_FUNCTION_CONTRACT: WeekActionsPanel
// INTENT: Compose the paired weekly action and risk panels.
// INPUTS: Week surface model.
// OUTPUTS: Two-column detail panel layout.
// INVARIANTS: Panel copy and list namespaces remain stable for tests and analytics.
// END_FUNCTION_CONTRACT: WeekActionsPanel
export function WeekActionsPanel({ week }: { week: WeekSurfaceModel }) {
  if (!week.actions.length && !week.risks.length) {
    return null;
  }

  return (
    // START_BLOCK: WEEK_ACTIONS_PANEL_LAYOUT
    <div className="grid gap-4 lg:grid-cols-2">
      <ConsumerPanel className="p-5" data-testid="week-actions-panel">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Действия</p>
        <h2 className="mt-2 text-lg font-black text-slate-950">Лучшее применение недели</h2>
        <div className="mt-4"><ActionRiskList items={week.actions} testId="week-actions-list" week={week} kind="action" /></div>
      </ConsumerPanel>
      <ConsumerPanel className="p-5" data-testid="week-risks-panel">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Риски</p>
        <h2 className="mt-2 text-lg font-black text-slate-950">Что держать под контролем</h2>
        <div className="mt-4"><ActionRiskList items={week.risks} testId="week-risks-list" week={week} kind="risk" /></div>
      </ConsumerPanel>
    </div>
    // END_BLOCK: WEEK_ACTIONS_PANEL_LAYOUT
  );
}
