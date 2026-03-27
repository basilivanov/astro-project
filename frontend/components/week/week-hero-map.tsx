"use client";

import Link from "next/link";
import { ArrowRight, CalendarDays, Sparkles } from "lucide-react";

import { ConsumerHero, ConsumerMetaPill, ConsumerStatusBadge } from "../consumer-page-shell";
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
  return (
    <ConsumerHero
      eyebrow="Карта недели"
      title={week.headline}
      description={week.subhead}
      status={
        <ConsumerStatusBadge
          label={WEEK_TYPE_LABELS[week.weekType] ?? "Неделя"}
          description={formatWeekDateRange(week.weekStart, week.weekEnd)}
          tone={week.fallbackMode ? "amber" : "emerald"}
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
        <Link
          href={primaryHref}
          onClick={onPrimaryClick}
          className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-slate-200"
          data-testid="week-primary-cta"
        >
          {primaryLabel}
          <ArrowRight size={16} />
        </Link>
      }
    />
  );
}
