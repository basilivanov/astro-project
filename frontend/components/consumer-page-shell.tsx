"use client";

import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "../lib/utils";

type StatusTone = "emerald" | "indigo" | "amber" | "rose" | "slate";

const STATUS_TONE_CLASSES: Record<StatusTone, string> = {
  emerald: "border-emerald-100 bg-emerald-50 text-emerald-800",
  indigo: "border-indigo-100 bg-indigo-50 text-indigo-800",
  amber: "border-amber-100 bg-amber-50 text-amber-800",
  rose: "border-rose-100 bg-rose-50 text-rose-800",
  slate: "border-slate-200 bg-slate-50 text-slate-700",
};

export function ConsumerPageShell({
  children,
  className,
  contentClassName,
  testId,
}: {
  children: ReactNode;
  className?: string;
  contentClassName?: string;
  testId?: string;
}) {
  return (
    <div
      data-testid={testId}
      className={cn(
        "min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.14),transparent_32%),radial-gradient(circle_at_top_right,rgba(251,191,36,0.12),transparent_22%),linear-gradient(180deg,#fffaf4_0%,#f8fafc_100%)]",
        className,
      )}
      suppressHydrationWarning
    >
      <div
        className={cn(
          "mx-auto flex min-h-screen max-w-3xl flex-col gap-5 px-4 pb-28 pt-6 sm:gap-6 sm:px-6 sm:pt-8",
          contentClassName,
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function ConsumerStatusBadge({
  label,
  description,
  tone = "slate",
  className,
}: {
  label: string;
  description?: string;
  tone?: StatusTone;
  className?: string;
}) {
  return (
    <div className={cn("rounded-[22px] border px-4 py-3 shadow-sm", STATUS_TONE_CLASSES[tone], className)}>
      <p className="text-[10px] font-black uppercase tracking-[0.2em]">{label}</p>
      {description ? <p className="mt-1 text-sm font-semibold leading-snug">{description}</p> : null}
    </div>
  );
}

export function ConsumerHero({
  eyebrow,
  title,
  description,
  status,
  meta,
  actions,
  className,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  status?: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "relative overflow-hidden rounded-[32px] border border-white/70 bg-white/88 px-5 py-5 shadow-[0_24px_60px_-32px_rgba(15,23,42,0.35)] backdrop-blur-xl",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-indigo-200/90 to-transparent" />
      <div className="pointer-events-none absolute -right-10 top-0 h-28 w-28 rounded-full bg-indigo-100/80 blur-3xl" />
      <div className="pointer-events-none absolute -left-10 bottom-0 h-24 w-24 rounded-full bg-amber-100/80 blur-3xl" />

      <div className="relative">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <p className="text-[11px] font-black uppercase tracking-[0.26em] text-indigo-700">{eyebrow}</p>
            <h1 className="mt-3 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">{title}</h1>
            {description ? (
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-600 sm:text-[15px]">{description}</p>
            ) : null}
          </div>
          {status ? <div className="shrink-0">{status}</div> : null}
        </div>

        {(meta || actions) && (
          <div className="mt-5 flex flex-col gap-3 border-t border-slate-100/90 pt-4 sm:flex-row sm:items-center sm:justify-between">
            {meta ? <div className="flex flex-wrap gap-2">{meta}</div> : <div />}
            {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
          </div>
        )}
      </div>
    </header>
  );
}

export function ConsumerMetaPill({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/80 bg-slate-50/90 px-3 py-2 text-left shadow-sm",
        className,
      )}
    >
      <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-700">{value}</p>
    </div>
  );
}

export function ConsumerPanel({
  children,
  className,
  ...props
}: ComponentPropsWithoutRef<"section"> & {
  children: ReactNode;
}) {
  return (
    <section
      {...props}
      className={cn(
        "rounded-[28px] border border-white/70 bg-white/90 shadow-[0_24px_60px_-36px_rgba(15,23,42,0.28)] backdrop-blur-xl",
        className,
      )}
    >
      {children}
    </section>
  );
}
