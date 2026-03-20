"use client";

import type { ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "../lib/utils";

export function ForecastSectionCard({
  index,
  title,
  preview,
  anchorId,
  expanded,
  onToggle,
  children,
  badge,
  meta,
  className,
}: {
  index: number;
  title: string;
  preview?: string | null;
  anchorId?: string;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
  badge?: string | null;
  meta?: string;
  className?: string;
}) {
  const indexLabel = String(index).padStart(2, "0");

  return (
    <section
      id={anchorId}
      className={cn(
        "scroll-mt-24 overflow-hidden rounded-[28px] border border-white/70 bg-white/90 shadow-[0_22px_60px_-36px_rgba(15,23,42,0.28)] backdrop-blur-xl transition-all sm:scroll-mt-28",
        className,
      )}
    >
      <button
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full items-start justify-between gap-4 px-5 py-5 text-left transition-colors hover:bg-slate-50/80 sm:px-6"
      >
        <div className="flex min-w-0 items-start gap-4">
          <div className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-indigo-100 bg-indigo-50 text-[11px] font-black uppercase tracking-[0.22em] text-indigo-700 shadow-sm">
            {indexLabel}
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
                {meta || `Секция ${indexLabel}`}
              </span>
              {badge ? (
                <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-black uppercase tracking-[0.16em] text-amber-700">
                  {badge}
                </span>
              ) : null}
            </div>
            <h3 className="mt-2 text-base font-black tracking-tight text-slate-900 sm:text-lg">{title}</h3>
            {preview ? (
              <p className="mt-2 pr-2 text-sm leading-relaxed text-slate-500 sm:text-[15px]">{preview}</p>
            ) : null}
          </div>
        </div>

        <span className="mt-1 inline-flex shrink-0 items-center gap-1 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.16em] text-slate-500 shadow-sm">
          {expanded ? "Свернуть" : "Открыть"}
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </button>

      {expanded ? (
        <div className="border-t border-slate-100/90 px-5 pb-6 pt-5 sm:px-6">
          {children}
        </div>
      ) : null}
    </section>
  );
}
