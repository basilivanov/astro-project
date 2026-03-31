import Link from "next/link";
import { AlertTriangle, ArrowRight, ChevronDown, Clock3, Sparkles } from "lucide-react";
import { ConsumerPanel, ConsumerStatusBadge } from "../consumer-page-shell";
import { TrafficLights } from "../TrafficLights";
import type { DayBriefDto } from "../../lib/day-brief";

const DAY_MODE_COPY: Record<DayBriefDto["summary"]["day_type"], { label: string; badgeClass: string }> = {
  push: { label: "День для рывка", badgeClass: "border border-emerald-200 bg-emerald-50 text-emerald-900" },
  balance: { label: "День в балансе", badgeClass: "border border-amber-200 bg-amber-50 text-amber-900" },
  caution: { label: "Осторожный день", badgeClass: "border border-rose-200 bg-rose-50 text-rose-900" },
  deep_focus: { label: "Глубокий фокус", badgeClass: "border border-indigo-200 bg-indigo-50 text-indigo-900" },
  recovery: { label: "День на восстановление", badgeClass: "border border-slate-200 bg-slate-50 text-slate-800" },
};

const WINDOW_MODE_COPY = {
  best: { label: "Лучшее окно", className: "border-emerald-100 bg-emerald-50" },
  soft: { label: "Мягкое окно", className: "border-amber-100 bg-amber-50" },
  caution: { label: "С осторожностью", className: "border-rose-100 bg-rose-50" },
} as const;

function formatItemTimeframe(value: string | null | undefined): string | null {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return null;
  const map: Record<string, string | null> = {
    morning: "Утро",
    afternoon: "День",
    day: "День",
    evening: "Вечер",
    all_day: null,
    allday: null,
    all: null,
    high: null,
    medium: null,
    low: null,
  };
  if (normalized in map) return map[normalized] ?? null;
  return /^[a-z0-9_-]+$/.test(normalized) ? null : String(value).trim();
}

function formatImpact(value: string | null | undefined): string | null {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return null;
  const map: Record<string, string | null> = {
    high: null,
    medium: null,
    low: null,
  };
  if (normalized in map) return map[normalized] ?? null;
  return /^[a-z0-9_-]+$/.test(normalized) ? null : String(value).trim();
}


function DetailDisclosure({
  title,
  body,
  factors,
  testId,
}: {
  title?: string | null;
  body?: string | null;
  factors?: Array<{ label: string; explanation_human: string; explanation_astro?: string | null; value?: string | null }>;
  testId: string;
}) {
  const normalizedBody = String(body || "").trim();
  const normalizedFactors = Array.isArray(factors) ? factors.filter((item) => item?.label || item?.explanation_human) : [];
  if (!normalizedBody && !normalizedFactors.length) return null;
  return (
    <details data-testid={testId} className="group mt-4 rounded-[20px] border border-slate-200/80 bg-slate-50/80 p-4 open:border-indigo-200 open:bg-white">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold text-slate-700 marker:content-none">
        <span>{title || "Почему так"}</span>
        <ChevronDown size={16} className="text-slate-400 transition group-open:rotate-180" />
      </summary>
      {normalizedBody ? <p className="mt-3 text-sm leading-relaxed text-slate-700">{normalizedBody}</p> : null}
      {normalizedFactors.length ? (
        <div className="mt-4 grid gap-3">
          {normalizedFactors.map((factor, index) => (
            <div key={`${factor.label}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-slate-900">{factor.label}</p>
                {factor.value ? <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">{factor.value}</span> : null}
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{factor.explanation_human}</p>
              {factor.explanation_astro ? <p className="mt-2 text-xs leading-relaxed text-slate-500">{factor.explanation_astro}</p> : null}
            </div>
          ))}
        </div>
      ) : null}
    </details>
  );
}

function formatWindowMeta(window: DayBriefDto["windows"][number]): string | null {
  const parts = [window.start && window.end ? `${window.start}–${window.end}` : null].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}

export function TodayVerdict({ brief }: { brief: DayBriefDto }) {
  const copy = DAY_MODE_COPY[brief.summary.day_type];
  const moonContext = brief.context.label || brief.context.moon_phase || null;
  return (
    <section data-testid="today-verdict" className="relative overflow-hidden rounded-[32px] border border-indigo-100 bg-[linear-gradient(145deg,#0f172a_0%,#1e1b4b_55%,#312e81_100%)] p-6 text-white shadow-[0_30px_70px_-45px_rgba(15,23,42,0.85)]">
      <div className="pointer-events-none absolute -left-16 top-6 h-48 w-48 rounded-full bg-amber-300/20 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 bottom-0 h-60 w-60 rounded-full bg-fuchsia-500/20 blur-3xl" />
      <div className="relative z-10 flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-200">Вердикт дня</p>
          <div data-testid="today-day-mode" className={`mt-3 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold ${copy.badgeClass}`}>
            {copy.label}
          </div>
          <h1 className="mt-5 text-2xl font-semibold leading-tight text-white">{brief.summary.headline}</h1>
          <p className="mt-3 text-base leading-relaxed text-white/85">{brief.summary.subhead}</p>
        </div>
        <div data-testid="today-moon-context" className="rounded-[24px] border border-white/20 bg-white/10 p-4 text-center shadow-lg shadow-slate-950/20 sm:max-w-[220px]">
          <div className="text-4xl" aria-hidden>{brief.context.moon_emoji || "🌙"}</div>
          {moonContext ? <p className="mt-3 text-sm leading-relaxed text-white/85">{moonContext}</p> : <p className="mt-3 text-sm leading-relaxed text-white/85">Персональный контекст дня</p>}
        </div>
      </div>
    </section>
  );
}

export function TodayScores({ brief, onScoreTap }: { brief: DayBriefDto; onScoreTap: (scoreKey: string, scoreValue: number) => void }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2" aria-label="Day brief scores">
      {brief.scores.map((score) => (
        <button
          key={score.key}
          type="button"
          data-testid={`today-score-${score.key}`}
          className="rounded-[24px] border border-slate-200 bg-white/90 p-4 text-left shadow-sm transition hover:border-indigo-200 hover:shadow-md"
          onClick={() => onScoreTap(score.key, score.value)}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">{score.title}</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{score.value}</p>
            </div>
            <ConsumerStatusBadge
              label={score.status === "green" ? "Сильная зона" : score.status === "red" ? "Зона риска" : "Нужна аккуратность"}
              tone={score.status === "green" ? "emerald" : score.status === "red" ? "rose" : "amber"}
            />
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">{score.advice}</p>
          <DetailDisclosure
            testId={`today-score-details-${score.key}`}
            title={score.details?.why_title || "Почему такой ритм"}
            body={score.details?.why_text}
            factors={score.details?.supporting_factors}
          />
        </button>
      ))}
    </section>
  );
}

export function TodayLegacyTrafficLights({ brief }: { brief: DayBriefDto }) {
  const lights = {
    health: brief.scores.find((item) => item.key === "energy")?.status ?? "yellow",
    money: brief.scores.find((item) => item.key === "money")?.status ?? "yellow",
    love: brief.scores.find((item) => item.key === "love")?.status ?? "yellow",
  };
  return <TrafficLights lights={lights} personalizationLevel={brief.personalization_level} />;
}

export function TodayWindows({ brief }: { brief: DayBriefDto }) {
  return (
    <ConsumerPanel data-testid="today-windows" className="p-5 sm:p-6">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
        <Clock3 size={18} className="text-indigo-500" />
        Временные окна
      </div>
      <div className="mt-4 grid gap-3">
        {brief.windows.map((window) => {
          const modeCopy = WINDOW_MODE_COPY[window.mode];
          const meta = formatWindowMeta(window);
          return (
            <article key={window.id} className={`rounded-[24px] border p-4 shadow-sm ${modeCopy.className}`}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{window.label}</p>
                  {meta ? <p className="mt-1 text-xs text-slate-500">{meta}</p> : null}
                </div>
                <span className="rounded-full bg-white/80 px-3 py-1 text-[11px] font-semibold text-slate-700">{modeCopy.label}</span>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-slate-700">{window.advice}</p>
              <DetailDisclosure
                testId={`today-window-details-${window.id}`}
                title="Почему окно такое"
                body={window.details?.why_text}
                factors={window.details?.supporting_factors}
              />
            </article>
          );
        })}
        {!brief.windows.length && (
          <p className="text-sm text-slate-500">Сегодня лучше держать ровный ритм без резких разворотов.</p>
        )}
      </div>
    </ConsumerPanel>
  );
}

function ItemList({ title, testId, items, icon }: { title: string; testId: string; items: DayBriefDto["best_uses"] | DayBriefDto["risks"]; icon: "good" | "risk" }) {
  return (
    <ConsumerPanel data-testid={testId} className="p-5 sm:p-6">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
        {icon === "risk" ? <AlertTriangle size={18} className="text-rose-500" /> : <Sparkles size={18} className="text-emerald-500" />}
        {title}
      </div>
      <div className="mt-4 grid gap-3">
        {items.map((item) => {
          const impact = formatImpact(item.impact);
          const timeframe = formatItemTimeframe(item.timeframe);
          const detailTestId = icon === "risk" ? `today-risks-details-${item.id}` : `today-actions-details-${item.id}`;
          return (
            <article key={item.id} className="rounded-[22px] border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm leading-relaxed text-slate-700">{item.text}</p>
                {impact ? <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-500">{impact}</span> : null}
              </div>
              {timeframe ? <p className="mt-2 text-xs text-slate-400">{timeframe}</p> : null}
              <DetailDisclosure
                testId={detailTestId}
                title={icon === "risk" ? "Почему это важно" : "Почему это в приоритете"}
                body={item.why_text}
                factors={item.supporting_factors}
              />
            </article>
          );
        })}
      </div>
    </ConsumerPanel>
  );
}

export function TodayActions({ brief }: { brief: DayBriefDto }) {
  return <ItemList title="Лучше использовать" testId="today-actions" items={brief.best_uses} icon="good" />;
}

export function TodayRisks({ brief }: { brief: DayBriefDto }) {
  return <ItemList title="Риски дня" testId="today-risks" items={brief.risks} icon="risk" />;
}

export function TodayExplainability({ brief }: { brief: DayBriefDto }) {
  const confidence = Math.round(brief.explainability.confidence * 100);
  return (
    <ConsumerPanel data-testid="today-explainability" className="p-5 sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Почему такой день</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">Ключевые сигналы дня собраны в короткий персональный вывод.</p>
        </div>
        <div className="rounded-[20px] border border-slate-200 bg-slate-50 px-4 py-3 text-right">
          <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">Уверенность</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{confidence}%</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">Факторов: {brief.explainability.factor_count}</span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {brief.personalized_factors.slice(0, 3).map((factor) => (
          <article key={factor.id} className="rounded-[20px] border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-900">{factor.label}</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{factor.explanation_human}</p>
          </article>
        ))}
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
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{brief.premium?.show_upgrade_cta ? "Разблокируйте следующий уровень разбора и недельную карту." : "Продолжайте в недельную карту или откройте историю разборов."}</p>
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
            className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            onClick={() => onCta(secondary.type, secondary.href, "daybrief_secondary", "CTA_SECONDARY")}
          >
            {secondary.label}
          </Link>
        </div>
      </div>
    </ConsumerPanel>
  );
}
