"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ConsumerPanel, ConsumerStatusBadge } from "../consumer-page-shell";
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

function scoreBadgeTone(status: DayBriefLight | null): string {
  if (status === "green") return "success";
  if (status === "red") return "warning";
  return "neutral";
}

function scoreCardState(domain: DayDomainCard): "complete" | "no_data" | "error" {
  const hasScore = domain.score_status === "complete" && domain.score !== null;
  const hasDescription = domain.description_status === "complete" && Boolean(domain.description);
  const hasWhy = domain.why_status === "complete" && Boolean(domain.why_astro_text);
  if (hasScore && hasDescription && hasWhy) {
    return "complete";
  }
  if (domain.score_status === "failed" || domain.description_status === "failed" || domain.why_status === "failed") {
    return "error";
  }
  return "no_data";
}

function stateCopy(domain: DayDomainCard): { description: string; whyText: string } {
  if (scoreCardState(domain) === "error") {
    return {
      description: "Ошибка расчёта этой сферы.",
      whyText: "Причина для этой сферы не рассчитана.",
    };
  }
  return {
    description: "Нет данных по этой сфере.",
    whyText: "Для этой сферы пока нет персонального астрологического объяснения.",
  };
}

function domainDescription(domain: DayDomainCard): string {
  if (domain.description_status === "complete" && domain.description) {
    return domain.description;
  }
  return stateCopy(domain).description;
}

function domainWhyText(domain: DayDomainCard): string {
  if (domain.why_status === "complete" && domain.why_astro_text) {
    return domain.why_astro_text;
  }
  return stateCopy(domain).whyText;
}

export function TodayVerdict({ brief }: { brief: DayBriefDto }) {
  const copy = DAY_MODE_COPY[brief.hero.day_type];
  return (
    <section data-testid="today-verdict" className="relative overflow-hidden rounded-[32px] border border-indigo-100 bg-[linear-gradient(145deg,#0f172a_0%,#1e1b4b_55%,#312e81_100%)] p-6 text-white shadow-[0_30px_70px_-45px_rgba(15,23,42,0.85)]">
      <div className="pointer-events-none absolute -left-16 top-6 h-48 w-48 rounded-full bg-amber-300/20 blur-3xl" />
      <div className="pointer-events-none absolute -right-10 bottom-0 h-40 w-40 rounded-full bg-sky-300/10 blur-3xl" />
      <div className="relative flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className={`rounded-full px-3 py-1 text-[11px] font-black uppercase tracking-[0.18em] ${copy.badgeClass}`}>{copy.label}</span>
        </div>
        <div>
          <h1 className="text-3xl font-semibold leading-tight sm:text-[2rem]" data-testid="today-hero-title">{brief.hero.title}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-100/90 sm:text-base">{brief.hero.subtitle}</p>
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
                <ConsumerStatusBadge tone={scoreBadgeTone(domain.status)}>{domain.status ? SCORE_LABELS[domain.status] : state === "error" ? "Ошибка" : "Нет данных"}</ConsumerStatusBadge>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-slate-700">{domainDescription(domain)}</p>
              <details data-testid={`today-score-details-${key}`} className="mt-4 rounded-[18px] border border-slate-200 bg-slate-50/70 px-4 py-3" open>
                <summary className="cursor-pointer list-none text-sm font-semibold text-slate-900">Что повлияло</summary>
                <p className="mt-3 text-sm leading-relaxed text-slate-700">{domainWhyText(domain)}</p>
              </details>
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
  const primary = brief.cta?.primary ?? { type: "open_week", label: "Открыть неделю", href: "/week" };
  const secondary = brief.cta?.secondary ?? { type: brief.premium?.subscription_active ? "open_history" : "open_premium", label: brief.premium?.subscription_active ? "История разборов" : "Открыть premium", href: brief.premium?.subscription_active ? "/reports/history" : "/reports" };

  return (
    <ConsumerPanel data-testid="today-cta-panel" className="p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Следующий шаг</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">Перейдите в недельную карту или откройте историю разборов.</p>
        </div>
        <div className="flex flex-col gap-3 sm:min-w-[220px]">
          <Link
            href={primary.href}
            data-testid="today-cta-week"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            onClick={() => onCta(primary.type, primary.href, "daybrief_primary", "CTA_PRIMARY")}
          >
            {primary.label}
            <ArrowRight size={16} />
          </Link>
          <Link
            href={secondary.href}
            data-testid="today-cta-premium"
            className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:border-slate-300 hover:bg-slate-50"
            onClick={() => onCta(secondary.type, secondary.href, "daybrief_secondary", "CTA_SECONDARY")}
          >
            {secondary.label}
          </Link>
        </div>
      </div>
    </ConsumerPanel>
  );
}
