"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ConsumerPanel } from "../consumer-page-shell";
import type { DayBriefDto, DayBriefLight, DayBriefScoreKey, DayDomainCard } from "../../lib/day-brief";

const DAY_MODE_COPY: Record<DayBriefDto["hero"]["day_type"], { label: string; badgeClass: string }> = {
  push: { label: "День для рывка", badgeClass: "border border-emerald-200 bg-emerald-50 text-emerald-900" },
  balance: { label: "День в балансе", badgeClass: "border border-amber-200 bg-amber-50 text-amber-900" },
  caution: { label: "Осторожный день", badgeClass: "border border-rose-200 bg-rose-50 text-rose-900" },
  deep_focus: { label: "Глубокий фокус", badgeClass: "border border-indigo-200 bg-indigo-50 text-indigo-900" },
  recovery: { label: "День на восстановление", badgeClass: "border border-slate-200 bg-slate-50 text-slate-800" },
};

const SCORE_ORDER: DayBriefScoreKey[] = ["energy", "money", "love", "focus"];

const SCORE_LABELS: Record<DayBriefLight, string> = {
  green: "Сильная зона",
  yellow: "Зона внимания",
  red: "Зона бережности",
};

const STATE_LABELS = {
  partial_description_only: "Частично",
  partial_why_only: "Частично",
  failed: "Ошибка",
  no_data: "Нет данных",
} as const;

function scoreCardState(domain: DayDomainCard): "complete" | "partial_description_only" | "partial_why_only" | "failed" | "no_data" {
  const hasScore = domain.score_status === "complete" && domain.score !== null;
  const hasDescription = domain.description_status === "complete" && Boolean(domain.description);
  const hasWhy = domain.why_status === "complete" && Boolean(domain.why_astro_text);
  const hardFailure = domain.description_status === "failed" && !hasDescription;

  if (hasScore && hasDescription && hasWhy) return "complete";
  if (hasDescription && !hasWhy) return "partial_description_only";
  if (!hasDescription && hasWhy && hasScore) return "partial_why_only";
  if (hardFailure || (!hasDescription && !hasWhy && (domain.score_status === "failed" || domain.why_status === "failed"))) return "failed";
  return "no_data";
}

function stateCopy(domain: DayDomainCard): { description: string; whyText: string | null } {
  const state = scoreCardState(domain);
  if (state === "failed") {
    return {
      description: "Ошибка расчёта этой сферы. Вернитесь позже: сейчас показываем только честный статус без объяснения.",
      whyText: null,
    };
  }
  if (state === "partial_description_only") {
    return {
      description: domain.description ?? "Сфера рассчитана частично.",
      whyText: "Персональное астрологическое объяснение для этой сферы пока не рассчитано.",
    };
  }
  if (state === "partial_why_only") {
    return {
      description: "Сфера рассчитана частично, поэтому пока доступен только общий итог без устойчивого описания на сегодня.",
      whyText: domain.why_astro_text ?? null,
    };
  }
  return {
    description: "Пока нет устойчивых данных по этой сфере на сегодня.",
    whyText: null,
  };
}

function domainDescription(domain: DayDomainCard): string {
  if (domain.description_status === "complete" && domain.description) {
    return domain.description;
  }
  return stateCopy(domain).description;
}

function domainWhyText(domain: DayDomainCard): string | null {
  if (domain.why_status === "complete" && domain.why_astro_text && scoreCardState(domain) !== "failed") {
    return domain.why_astro_text;
  }
  return stateCopy(domain).whyText;
}

export function TodayVerdict({ brief }: { brief: DayBriefDto }) {
  if (!brief.hero) return null;
  const copy = DAY_MODE_COPY[brief.hero.day_type];
  return (
    <section data-testid="today-verdict" className="relative overflow-hidden rounded-[32px] border border-indigo-200/70 bg-[linear-gradient(145deg,#1e1b4b_0%,#312e81_45%,#4338ca_100%)] p-6 text-white shadow-[0_30px_70px_-45px_rgba(15,23,42,0.85)]">
      <div className="pointer-events-none absolute -left-16 top-6 h-48 w-48 rounded-full bg-amber-300/20 blur-3xl" />
      <div className="pointer-events-none absolute -right-10 bottom-0 h-40 w-40 rounded-full bg-sky-300/10 blur-3xl" />
      <div className="relative flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className={`rounded-full px-3 py-1 text-[11px] font-black uppercase tracking-[0.18em] shadow-sm ${copy.badgeClass}`}>{copy.label}</span>
        </div>
        <div>
          <h1 className="max-w-2xl text-[1.95rem] font-black leading-[1.08] text-white sm:text-[2.25rem]" data-testid="today-hero-title">{brief.hero.title}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-indigo-50/95 sm:text-[15px]">{brief.hero.subtitle}</p>
        </div>
      </div>
    </section>
  );
}

export function TodayScores({ brief, onScoreTap }: { brief: DayBriefDto; onScoreTap: (scoreKey: string, scoreValue: number) => void }) {
  return (
    <ConsumerPanel data-testid="today-scores" className="p-5 sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Сферы дня</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">Только четыре ключевые зоны и одно астрологическое объяснение для каждой.</p>
        </div>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {SCORE_ORDER.map((key) => {
          const domain = brief.domains[key];
          const state = scoreCardState(domain);
          const scoreValue = domain.score ?? 0;
          return (
            <article key={key} data-testid={`today-score-${key}`} className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{domain.title}</p>
                  <p className="mt-3 text-3xl font-semibold text-slate-950">{domain.score_status === "complete" && domain.score !== null ? scoreValue : "--"}</p>
                </div>
                <span
                  data-testid={`today-score-status-${key}`}
                  className={[
                    "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold",
                    domain.status === "green" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "",
                    domain.status === "yellow" ? "border-amber-200 bg-amber-50 text-amber-700" : "",
                    domain.status === "red" ? "border-rose-200 bg-rose-50 text-rose-700" : "",
                    !domain.status && state === "failed" ? "border-slate-200 bg-slate-100 text-slate-600" : "",
                    !domain.status && state !== "failed" ? "border-slate-200 bg-slate-50 text-slate-500" : "",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "h-2.5 w-2.5 rounded-full",
                      domain.status === "green" ? "bg-emerald-500" : "",
                      domain.status === "yellow" ? "bg-amber-500" : "",
                      domain.status === "red" ? "bg-rose-500" : "",
                      !domain.status && state === "failed" ? "bg-slate-400" : "",
                      !domain.status && state !== "failed" ? "bg-slate-300" : "",
                    ].join(" ")}
                  />
                  {domain.status ? SCORE_LABELS[domain.status] : STATE_LABELS[state]}
                </span>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-slate-700">{domainDescription(domain)}</p>
              {domainWhyText(domain) ? (
                <details data-testid={`today-score-details-${key}`} className="mt-4 rounded-[18px] border border-slate-200 bg-slate-50/70 px-4 py-3">
                  <summary className="cursor-pointer list-none text-sm font-semibold text-slate-900">Что повлияло</summary>
                  <p className="mt-3 text-sm leading-relaxed text-slate-700">{domainWhyText(domain)}</p>
                </details>
              ) : null}
              {domain.score_status === "complete" && domain.score !== null ? (
                <button
                  type="button"
                  className="sr-only"
                  aria-label={`${domain.title}: ${scoreValue}`}
                  onClick={() => onScoreTap(key, scoreValue)}
                />
              ) : null}
            </article>
          );
        })}
      </div>
    </ConsumerPanel>
  );
}

export function TodayCtaPanel({ brief, onCta }: { brief: DayBriefDto; onCta: (ctaId: string, href: string, entryPoint: string, block: string) => void }) {
  const primary = brief.cta?.primary ?? null;
  const secondary = brief.cta?.secondary ?? null;
  if (!primary && !secondary) return null;

  return (
    <ConsumerPanel data-testid="today-cta-panel" className="p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Следующий шаг</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">Перейдите в недельную карту или откройте историю разборов.</p>
        </div>
        <div className="flex flex-col gap-3 sm:min-w-[220px]">
          {primary ? (
            <Link
              href={primary.href}
              data-testid="today-cta-primary"
              className="inline-flex items-center justify-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              onClick={() => onCta(primary.type, primary.href, "daybrief_primary", "CTA_PRIMARY")}
            >
              {primary.label}
              <ArrowRight size={16} />
            </Link>
          ) : null}
          {secondary ? (
            <Link
              href={secondary.href}
              data-testid="today-cta-secondary"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:border-slate-300 hover:bg-slate-50"
              onClick={() => onCta(secondary.type, secondary.href, "daybrief_secondary", "CTA_SECONDARY")}
            >
              {secondary.label}
            </Link>
          ) : null}
        </div>
      </div>
    </ConsumerPanel>
  );
}
