// ############################################################################
// AI_HEADER: MODULE_CATALOG_PAGE
// ROLE: Product catalog / showcase.
// DEPENDENCIES: Link, Lucide icons.
// GRACE_ANCHORS: [CATALOG_DATA, CATALOG_UI]
// ############################################################################

"use client";

import Link from "next/link";
import {
  ArrowRight,
  Calendar,
  Clock3,
  Heart,
  HelpCircle,
  Sparkles,
  Star,
} from "lucide-react";
import {
  ConsumerHero,
  ConsumerMetaPill,
  ConsumerPageShell,
  ConsumerPanel,
  ConsumerStatusBadge,
} from "../../components/consumer-page-shell";
import {
  HORARY_PRICE_LABEL,
  SUBSCRIPTION_PRICE_LABEL,
  getRuntimeAccessBadge,
  getRuntimePriceLabel,
  isSubscriptionProductType,
} from "../../lib/product-billing";

// #START_BLOCK_CATALOG_DATA
const PRODUCTS = [
  {
    id: "natal_master",
    title: "Натальная карта",
    desc: "Глубокий разбор личности, сильных сторон и личной стратегии.",
    fit: "База для понимания себя и своих повторяющихся сценариев.",
    icon: Star,
    iconClassName: "bg-amber-50 text-amber-600 ring-1 ring-amber-100",
    link: "/create?type=natal_master",
  },
  {
    id: "year_forecast",
    title: "Альманах 2026",
    desc: "Годовой прогноз с помесячной логикой, светофорами и опорными окнами.",
    fit: "Для планирования решений, денег, отношений и больших переходов.",
    icon: Calendar,
    iconClassName: "bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100",
    link: "/create?type=year_forecast",
  },
  {
    id: "month_forecast",
    title: "Прогноз на месяц",
    desc: "Собранный план на 4 недели: фокус, риски, темп и точки роста.",
    fit: "Когда нужен прикладной ориентир на ближайший горизонт.",
    icon: Sparkles,
    iconClassName: "bg-sky-50 text-sky-600 ring-1 ring-sky-100",
    link: "/create?type=month_forecast",
  },
  {
    id: "solar_return",
    title: "Соляр",
    desc: "Персональный сценарий от дня рождения до дня рождения с акцентом на главный вектор года.",
    fit: "Подходит, если нужен фокус на личный новый цикл.",
    icon: Clock3,
    iconClassName: "bg-orange-50 text-orange-600 ring-1 ring-orange-100",
    link: "/create?type=solar_return",
  },
  {
    id: "synastry",
    title: "Совместимость",
    desc: "Разбор пары: точки притяжения, напряжения и жизнеспособности союза.",
    fit: "Для понимания динамики отношений и общих сценариев.",
    icon: Heart,
    iconClassName: "bg-pink-50 text-pink-600 ring-1 ring-pink-100",
    link: "/create?type=synastry",
  },
  {
    id: "horary",
    title: "Вопрос",
    desc: "Точечный хорар под конкретную задачу с ответом по сути, без лишнего объема.",
    fit: "Лучший формат, когда нужен быстрый ответ на один вопрос.",
    icon: HelpCircle,
    iconClassName: "bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100",
    link: "/create?type=horary",
  },
] as const;

const SUBSCRIPTION_PRODUCTS_COUNT = PRODUCTS.filter((product) =>
  isSubscriptionProductType(product.id),
).length;
// #END_BLOCK_CATALOG_DATA

// #START_BLOCK_CATALOG_UI
export default function CatalogPage() {
  return (
    <ConsumerPageShell testId="reports-catalog-page">
      <ConsumerHero
        eyebrow="Каталог"
        title="Разборы и прогнозы"
        description="Здесь собраны все форматы: от быстрого хорара до глубоких персональных разборов. Структура и копирайт выстроены так, чтобы сразу было понятно, что брать под конкретную задачу."
        status={
          <ConsumerStatusBadge
            label="Премиум-доступ"
            description={`Подписка ${SUBSCRIPTION_PRICE_LABEL} открывает все персональные разборы`}
            tone="indigo"
          />
        }
        meta={
          <>
            <ConsumerMetaPill label="Форматов" value={String(PRODUCTS.length)} />
            <ConsumerMetaPill label="По подписке" value={`${SUBSCRIPTION_PRODUCTS_COUNT} разборов`} />
            <ConsumerMetaPill label="Разовый вопрос" value={HORARY_PRICE_LABEL} />
          </>
        }
        actions={
          <>
            <Link
              href="/reports/history"
              className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700"
            >
              История разборов
            </Link>
            <Link
              href="/create?type=horary&entry=catalog-hero"
              className="inline-flex items-center justify-center rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              Задать быстрый вопрос
            </Link>
          </>
        }
      />

      <ConsumerPanel data-testid="catalog-billing-note" className="overflow-hidden">
        <div className="grid gap-4 p-5 sm:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] sm:p-6">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">
              Как устроен доступ
            </p>
            <h2 className="mt-3 text-xl font-black tracking-tight text-slate-950">
              Один платежный сценарий для глубины, отдельный формат для точечного вопроса
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              Натал, прогнозы, соляр и совместимость идут через подписку. Хорар остается разовым
              продуктом, когда нужен быстрый ответ без подключения полного пакета.
            </p>
          </div>

          <div className="grid gap-3">
            <div className="rounded-[24px] border border-indigo-100 bg-indigo-50/80 p-4">
              <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-700">
                Подписка {SUBSCRIPTION_PRICE_LABEL}
              </p>
              <p className="mt-2 text-sm font-semibold leading-relaxed text-indigo-950">
                Открывает натал, прогнозы, соляр и совместимость без разовых доплат в каталоге.
              </p>
            </div>
            <div className="rounded-[24px] border border-emerald-100 bg-emerald-50/80 p-4">
              <p className="text-[11px] font-black uppercase tracking-[0.22em] text-emerald-700">
                Хорар {HORARY_PRICE_LABEL}
              </p>
              <p className="mt-2 text-sm font-semibold leading-relaxed text-emerald-950">
                Точечный разбор для одной ситуации, когда не нужен полный пакет подписки.
              </p>
            </div>
          </div>
        </div>
      </ConsumerPanel>

      <section className="grid gap-4" aria-label="Каталог разборов">
        {PRODUCTS.map((product, idx) => (
          <Link
            key={product.id}
            href={product.link}
            className="group block"
            style={{ animationDelay: `${idx * 40}ms` }}
          >
            <ConsumerPanel className="overflow-hidden border-white/80 p-5 transition duration-200 group-hover:-translate-y-0.5 group-hover:border-indigo-100 group-hover:shadow-[0_28px_70px_-38px_rgba(79,70,229,0.35)] sm:p-6">
              <div className="flex flex-col gap-5">
                <div className="flex items-start justify-between gap-4">
                  <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${product.iconClassName}`}>
                    <product.icon size={22} />
                  </div>
                  <div className="min-w-0 text-right">
                    <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
                      {getRuntimeAccessBadge(product.id)}
                    </p>
                    <span className="mt-2 inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm font-bold text-slate-700">
                      {getRuntimePriceLabel(product.id)}
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <h3 className="text-2xl font-black tracking-tight text-slate-950 transition-colors group-hover:text-indigo-700">
                      {product.title}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-600 sm:text-[15px]">
                      {product.desc}
                    </p>
                  </div>
                  <div className="rounded-[22px] border border-slate-100 bg-slate-50/80 px-4 py-3">
                    <p className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">
                      Лучше всего подходит
                    </p>
                    <p className="mt-2 text-sm font-semibold leading-relaxed text-slate-700">
                      {product.fit}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-slate-100 pt-4">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-700">
                      {isSubscriptionProductType(product.id)
                        ? "Открыть оформление по подписке"
                        : "Перейти к быстрому заказу"}
                    </p>
                    <p className="mt-1 text-xs font-medium text-slate-500">
                      Без лишних шагов, сразу к нужному сценарию.
                    </p>
                  </div>
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-400 transition group-hover:border-indigo-200 group-hover:text-indigo-600">
                    <ArrowRight size={18} />
                  </span>
                </div>
              </div>
            </ConsumerPanel>
          </Link>
        ))}
      </section>
    </ConsumerPageShell>
  );
}
// #END_BLOCK_CATALOG_UI
