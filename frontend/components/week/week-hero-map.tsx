"use client";

import Link from "next/link";
import { ArrowRight, CalendarDays, Sparkles } from "lucide-react";

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
          <ConsumerMetaPill label="Тема" value={week.theme} icon={<Sparkles size={14} />} />
          <ConsumerMetaPill label="Неделя" value={formatWeekDateRange(week.weekStart, week.weekEnd)} icon={<CalendarDays size={14} />} />
          <ConsumerMetaPill label="Локация" value={week.location || "—"} />
          <ConsumerMetaPill label="Часовой пояс" value={week.timezone || "—"} />
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
          ) : week.fallbackMode ? (
            <div className="rounded-2xl border border-amber-100 bg-amber-50/60 px-4 py-3 text-xs text-amber-900" data-testid="week-fallback-indicator">
              Карта построена в безопасном режиме — проверяем детали, контент уже можно читать.
            </div>
          ) : null}
        </div>
      }
    />
  );
}
