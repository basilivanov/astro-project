"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { ConsumerHero, ConsumerMetaPill, ConsumerStatusBadge } from "../consumer-page-shell";
import ReportStatusPoller from "../report-status-poller";
import { type WeekSurfaceModel, formatWeekDateRange } from "../../lib/week-brief";

const WEEK_TYPE_LABELS: Record<string, string> = {
  push: "Неделя на рывок",
  balance: "Неделя на баланс",
  caution: "Неделя на осторожность",
  deep_work: "Неделя на глубокую работу",
  recovery: "Неделя на восстановление",
  transition: "Неделя на переход",
};

function formatWeekTimezoneLabel(value: string | null | undefined): string | null {
  const raw = String(value || "").trim();
  if (!raw) return null;
  const normalized = raw.toLowerCase();
  if (normalized === "utc") return "UTC";
  if (/^[a-z]+\/[a-z_+-]+(?:\/[a-z_+-]+)?$/i.test(raw)) {
    const city = raw.split("/").pop()?.replace(/_/g, " ").trim();
    return city || null;
  }
  if (/^utc[+-]\d{1,2}(?::\d{2})?$/i.test(raw) || /^[+-]\d{2}:\d{2}$/.test(raw)) {
    return raw.toUpperCase();
  }
  return raw.includes("/") ? raw.split("/").pop()?.replace(/_/g, " ").trim() ?? null : raw;
}

export function WeekHeroMap({
  week,
  primaryHref,
  primaryLabel,
  onPrimaryClick,
}: {
  week: WeekSurfaceModel;
  primaryHref: string;
  primaryLabel: string;
  onPrimaryClick: () => void;
}) {
  const statusTone = week.status === "in_progress" || week.status === "pending" ? "amber" : week.fallbackMode ? "amber" : "emerald";
  const statusLabel = week.status === "in_progress" ? "Неделя в сборке" : week.status === "pending" ? "Неделя запускается" : WEEK_TYPE_LABELS[week.weekType] ?? "Неделя";
  const statusDescription = week.status === "in_progress" || week.status === "pending" ? "Генерируем персональную карту" : formatWeekDateRange(week.weekStart, week.weekEnd);
  const timezoneLabel = formatWeekTimezoneLabel(week.timezone);
  return (
    <ConsumerHero
      eyebrow="Карта недели"
      title={week.headline}
      description={week.subhead}
      status={
        <ConsumerStatusBadge
          label={statusLabel}
          description={statusDescription}
          tone={statusTone}
        />
      }
      meta={
        <>
          <ConsumerMetaPill label="Тема" value={week.theme} />
          <ConsumerMetaPill label="Неделя" value={formatWeekDateRange(week.weekStart, week.weekEnd)} />
          <ConsumerMetaPill label="Локация" value={week.location || "—"} />
          {timezoneLabel ? <ConsumerMetaPill label="Часовой пояс" value={timezoneLabel} /> : null}
        </>
      }
      actions={
        <div className="flex flex-col gap-3" data-testid="week-hero-actions">
          <Link
            href={primaryHref}
            onClick={onPrimaryClick}
            className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-slate-200"
            data-testid="week-primary-cta"
          >
            {primaryLabel}
            <ArrowRight size={16} />
          </Link>
          {week.status === "in_progress" || week.status === "pending" ? (
            <div className="rounded-2xl border border-amber-100 bg-amber-50/60 px-4 py-3 text-xs font-semibold text-amber-900" data-testid="week-generation-status">
              <ReportStatusPoller reportId={week.reportId ?? ""} status={week.status} />
            </div>
          ) : null}
        </div>
      }
    />
  );
}
