"use client";

import { useCallback, useId, useState } from "react";
import { ChevronDown } from "lucide-react";
import type { NormalizedDetailFactor } from "../../lib/detail-layer";
import { DetailFactorsList } from "./detail-factors-list";

export function DetailDisclosureCard({
  title,
  body,
  factors,
  testId,
  compact,
  isOpen,
  onToggle,
}: {
  title?: string | null;
  body?: string | null;
  factors?: NormalizedDetailFactor[];
  testId: string;
  compact?: boolean;
  isOpen?: boolean;
  onToggle?: () => void;
}) {
  const contentId = useId();
  const [internalOpen, setInternalOpen] = useState(false);
  const open = isOpen ?? internalOpen;
  const normalizedBody = String(body || "").trim();
  const normalizedFactors = Array.isArray(factors) ? factors.filter((item) => item?.label || item?.explanationHuman) : [];
  const hasContent = Boolean(normalizedBody) || normalizedFactors.length > 0;

  const handleToggle = useCallback(() => {
    if (onToggle) {
      onToggle();
      return;
    }
    setInternalOpen((current) => !current);
  }, [onToggle]);

  const handleSummaryClick = useCallback((event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    handleToggle();
  }, [handleToggle]);

  const handleSummaryKeyDown = useCallback((event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    handleToggle();
  }, [handleToggle]);

  if (!hasContent) return null;

  return (
    <details data-testid={testId} open={open} className="group mt-4 rounded-[20px] border border-slate-200/80 bg-slate-50/80 open:border-indigo-200 open:bg-white">
      <summary
        role="button"
        aria-expanded={open}
        aria-controls={contentId}
        tabIndex={0}
        onClick={handleSummaryClick}
        onKeyDown={handleSummaryKeyDown}
        className={`flex w-full cursor-pointer list-none select-none touch-manipulation items-center justify-between gap-3 ${compact ? "p-3 text-[13px]" : "p-4 text-sm"} font-semibold text-slate-700 marker:content-none [-webkit-tap-highlight-color:transparent]`}
      >
        <span>{title || "Почему так"}</span>
        <ChevronDown size={16} className="shrink-0 text-slate-400 transition group-open:rotate-180" aria-hidden />
      </summary>
      <div id={contentId} hidden={!open} className={compact ? "px-3 pb-3" : "px-4 pb-4"}>
        {normalizedBody ? <p className="text-sm leading-relaxed text-slate-700">{normalizedBody}</p> : null}
        <DetailFactorsList factors={normalizedFactors} compact={compact} testId={testId ? `${testId}-factors` : undefined} />
      </div>
    </details>
  );
}
