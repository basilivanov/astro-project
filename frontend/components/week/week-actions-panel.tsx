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
// INTERNALS: supportingFactors, itemSupportingFactors, mapItemFactors, renderItems.
// DATA_FLOW: week surface -> factor selection -> disclosure factor normalization -> action/risk list rendering.
// UI_SEAMS: `week-actions-panel`, `week-risks-panel`, disclosure cards, evidence chips.
// END_MODULE_MAP: M-WEEK-ACTIONS-PANEL

import { useState } from "react";

import { ConsumerPanel } from "../consumer-page-shell";
import { DetailDisclosureCard } from "../detail/detail-disclosure-card";
import { DetailEvidenceChips } from "../detail/detail-evidence-chips";
import type { NormalizedDetailFactor } from "../../lib/detail-layer";
import { type WeekSurfaceModel } from "../../lib/week-brief";

// START_FUNCTION_CONTRACT: supportingFactors
// INTENT: Resolve bounded fallback evidence for an action/risk item by optional factor id.
// INPUTS: week surface model and optional supporting factor id.
// OUTPUTS: Up to two supporting factors.
// INVARIANTS: Exact id matches win; fallback remains bounded to first two factors.
// END_FUNCTION_CONTRACT: supportingFactors
function supportingFactors(week: WeekSurfaceModel, factorId?: string | null) {
  // START_BLOCK: SUPPORTING_FACTOR_RESOLUTION
  if (factorId) {
    const exact = week.factors.filter((factor) => factor.id === factorId);
    if (exact.length) return exact;
  }
  return [];
  // END_BLOCK: SUPPORTING_FACTOR_RESOLUTION
}

// START_FUNCTION_CONTRACT: itemSupportingFactors
// INTENT: Prefer item-level supporting factors and otherwise reuse week-level fallback evidence.
// INPUTS: week surface model and a normalized action item.
// OUTPUTS: Supporting factor list suitable for disclosure rendering.
// INVARIANTS: Explicit item factors override fallback selection.
// END_FUNCTION_CONTRACT: itemSupportingFactors
function itemSupportingFactors(week: WeekSurfaceModel, item: WeekSurfaceModel["actions"][number]) {
  // START_BLOCK: ITEM_FACTOR_SOURCE_SELECTION
  if (item.supporting_factors?.length) {
    return item.supporting_factors;
  }
  return supportingFactors(week, item.factor_id);
  // END_BLOCK: ITEM_FACTOR_SOURCE_SELECTION
}

// START_FUNCTION_CONTRACT: mapItemFactors
// INTENT: Normalize raw week supporting factors into detail-layer disclosure factors.
// INPUTS: Supporting factors and related entity key.
// OUTPUTS: Filtered normalized factor list for disclosure cards.
// INVARIANTS: Empty evidence entries are dropped; ids remain deterministic per related key.
// END_FUNCTION_CONTRACT: mapItemFactors
function mapItemFactors(
  factors: ReturnType<typeof itemSupportingFactors>,
  relatedKey: string,
): NormalizedDetailFactor[] {
  // START_BLOCK: DISCLOSURE_FACTOR_NORMALIZATION
  return factors
    .map((factor, index) => {
      const label = String(factor?.label || "").trim();
      const explanationHuman = String(factor?.explanation_human || "").trim();
      const explanationAstro = String(factor?.explanation_astro || "").trim();
      const value = String(factor?.value || "").trim();
      const normalizedValue = value.toLowerCase();
      if (!label && !explanationHuman && !explanationAstro) return null;
      if (/^[a-z]+:[a-z0-9_-]+$/.test(label.toLowerCase()) && !explanationHuman) return null;
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
  // END_BLOCK: DISCLOSURE_FACTOR_NORMALIZATION
}

// START_FUNCTION_CONTRACT: renderItems
// INTENT: Render a disclosure-enabled list for weekly actions or risks.
// INPUTS: Item collection, test id namespace, week surface model, and semantic item kind.
// OUTPUTS: List markup with evidence chips and disclosure cards.
// INVARIANTS: Disclosure state is local to the rendered list; explainability labels stay aligned to item kind.
// END_FUNCTION_CONTRACT: renderItems
function renderItems(items: WeekSurfaceModel["actions"], testId: string, week: WeekSurfaceModel, kind: "action" | "risk") {
  const [openId, setOpenId] = useState<string | null>(null);
  const visibleItems = items.filter((item) => item.tag !== "all_week");

  return (
    // START_BLOCK: ACTION_RISK_LIST_RENDER
    <ul className="space-y-2" data-testid={testId}>
      {visibleItems.map((item, index) => {
        const itemKey = item.id ?? `${index}`;
        return (
          <li key={item.id ?? item.text} className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3 text-sm leading-relaxed text-slate-700">
            <p>{item.text}</p>
            <DetailEvidenceChips timeframe={item.timeframe} impact={item.impact === "high" || item.impact === "medium" || item.impact === "low" ? item.impact : null} />
            <DetailDisclosureCard
              testId={`${testId}-explainability-${index + 1}`}
              title={kind === "risk" ? "Почему это важно" : "Почему это в фокусе"}
              body={item.why_text}
              factors={mapItemFactors(itemSupportingFactors(week, item), String(item.factor_id ?? item.id ?? `${kind}-${index + 1}`))}
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
  return (
    // START_BLOCK: WEEK_ACTIONS_PANEL_LAYOUT
    <div className="grid gap-4 lg:grid-cols-2">
      <ConsumerPanel className="p-5" data-testid="week-actions-panel">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Действия</p>
        <h2 className="mt-2 text-lg font-black text-slate-950">Что делать на этой неделе</h2>
        <div className="mt-4">{renderItems(week.actions, "week-actions-list", week, "action")}</div>
      </ConsumerPanel>
      <ConsumerPanel className="p-5" data-testid="week-risks-panel">
        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Риски</p>
        <h2 className="mt-2 text-lg font-black text-slate-950">Что держать под контролем</h2>
        <div className="mt-4">{renderItems(week.risks, "week-risks-list", week, "risk")}</div>
      </ConsumerPanel>
    </div>
    // END_BLOCK: WEEK_ACTIONS_PANEL_LAYOUT
  );
}
