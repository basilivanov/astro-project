// ############################################################################
// AI_HEADER: MODULE_CATALOG_PAGE
// ROLE: Product catalog / showcase.
// DEPENDENCIES: Link, Lucide icons.
// GRACE_ANCHORS: [CATALOG_DATA, CATALOG_UI]
// ############################################################################

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
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
import { useTelegram } from "../../hooks/useTelegram";
import { CatalogCheckoutResumeBanner } from "../../components/catalog/catalog-checkout-resume";
import {
  setCatalogAnalyticsContext,
  startCatalogCorrelation,
  trackCatalogEvent,
} from "../../components/catalog/catalog-analytics";
import {
  HORARY_PRICE_LABEL,
  SUBSCRIPTION_PRICE_LABEL,
  getRuntimeAccessBadge,
  getRuntimePriceLabel,
  isSubscriptionProductType,
} from "../../lib/product-billing";
import { CATALOG_GRACE_BLOCKS, CATALOG_GRACE_MODULES, withCatalogTrace } from "../../components/catalog/create-shared";

// START_MODULE_CONTRACT: M-REPORTS-CATALOG
// purpose: Render customer-facing catalog surfaces and bridge into checkout and history flows.
// owns:
//   - frontend/app/reports/page.tsx
// inputs:
//   - Telegram user context, query params for checkout/mode
// outputs:
//   - Catalog UI + analytics events for checkout funnel
// dependencies:
//   - catalog analytics helpers, CatalogCheckoutResumeBanner, product-billing utilities
// invariants:
//   - Catalog CTA clicks are logged with semantic blocks
// non_goals:
//   - Backend pricing orchestration or entitlement persistence
// END_MODULE_CONTRACT: M-REPORTS-CATALOG

// START_MODULE_MAP: M-REPORTS-CATALOG
// entrypoints:
//   - CatalogPage (default export)
// semantics:
//   - handleCtaClick => START_BLOCK_CTA_TRACKING
//   - CatalogCheckoutResumeBanner -> inline resume hints
// owned_tests:
//   - frontend/e2e/month-forecast-bridge-storefront.spec.ts
//   - frontend/e2e/year-forecast-bridge-storefront.spec.ts
// END_MODULE_MAP: M-REPORTS-CATALOG

// START_BLOCK: CATALOG_DATA
const PRODUCTS = [
  {
    id: "natal_master",
    title: "Натальная карта",
    desc: "Личный разбор ядра личности, сильных сторон и устойчивых жизненных сценариев.",
    fit: "Подходит как базовая аналитика для самоопоры, решений и дальнейших прогнозов.",
    analyticsLabel: "self_discovery",
    icon: Star,
    iconClassName: "bg-amber-50 text-amber-600 ring-1 ring-amber-100",
    link: "/create?type=natal_master",
  },
  {
    id: "year_forecast",
    title: "Альманах 2026",
    desc: "Годовой прогноз с помесячной логикой, светофорами и опорными окнами.",
    fit: "Для планирования решений, денег, отношений и больших переходов.",
    analyticsLabel: "long_horizon",
    icon: Calendar,
    iconClassName: "bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100",
    link: "/create?type=year_forecast",
  },
  {
    id: "month_forecast",
    title: "Прогноз на месяц",
    desc: "Собранный план на 4 недели: фокус, риски, темп и точки роста.",
    fit: "Когда нужен прикладной ориентир на ближайший горизонт.",
    analyticsLabel: "monthly_planning",
    icon: Sparkles,
    iconClassName: "bg-sky-50 text-sky-600 ring-1 ring-sky-100",
    link: "/create?type=month_forecast",
  },
  {
    id: "solar_return",
    title: "Соляр",
    desc: "Персональный сценарий личного года: главные темы, точки роста и смены фокуса от дня рождения до дня рождения.",
    fit: "Лучше всего для личного перезапуска, планирования цикла и понимания годового вектора.",
    analyticsLabel: "personal_cycle",
    icon: Clock3,
    iconClassName: "bg-orange-50 text-orange-600 ring-1 ring-orange-100",
    link: "/create?type=solar_return",
  },
  {
    id: "synastry",
    title: "Совместимость",
    desc: "Разбор пары: притяжение, напряжение, бытовая совместимость и потенциал союза в долгую.",
    fit: "Нужен, когда важно увидеть динамику отношений, триггеры и ресурс пары.",
    analyticsLabel: "relationship_dynamics",
    icon: Heart,
    iconClassName: "bg-pink-50 text-pink-600 ring-1 ring-pink-100",
    link: "/create?type=synastry",
  },
  {
    id: "horary",
    title: "Вопрос",
    desc: "Точечный хорар под конкретную задачу: ответ по сути, тайминг и скрытые факторы решения.",
    fit: "Оптимален, когда нужен быстрый ответ на один острый вопрос.",
    analyticsLabel: "decision_support",
    icon: HelpCircle,
    iconClassName: "bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100",
    link: "/create?type=horary",
  },
] as const;

const SUBSCRIPTION_PRODUCTS_COUNT = PRODUCTS.filter((product) =>
  isSubscriptionProductType(product.id),
).length;
// END_BLOCK: CATALOG_DATA

// START_BLOCK: CATALOG_UI
export default function CatalogPage() {
  const searchParams = useSearchParams();
  const checkoutToken = searchParams.get("checkout");
  const entryPoint = searchParams.get("entry_point");
  const entrySemanticBlock = searchParams.get("entry_semantic_block");
  const mockEnabled = searchParams.get("mock") === "1";
  const runtimeEnabled = searchParams.get("runtime") === "1";
  const { user, initData, isReady, mode } = useTelegram();
  const flowId = checkoutToken ? "catalog_checkout_resume" : "catalog_catalog_view";
  const [viewCorrelationId, setViewCorrelationId] = useState<string | null>(null);
  // START_CONTRACT: FN-BOOTSTRAP-CATALOG-CONTEXT
  // purpose: Start catalog flow correlation and seed shared analytics context for catalog/checkout/resume chain.
  // inputs: checkout token and current telegram user id.
  // side_effects: updates shared catalog analytics context.
  // END_CONTRACT: FN-BOOTSTRAP-CATALOG-CONTEXT
  useEffect(() => {
    // START_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
    const correlationId = startCatalogCorrelation(flowId);
    setViewCorrelationId(correlationId);
    setCatalogAnalyticsContext({
      user_id: user?.id,
      checkout_token: checkoutToken ?? undefined,
      correlation_id: correlationId,
      flow_id: flowId,
    });
    // END_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
  }, [checkoutToken, flowId, user?.id]);

  // START_CONTRACT: FN-HANDLE-CATALOG-CTA
  // purpose: Track catalog CTA clicks with canonical module/contract/block metadata.
  // inputs: report type and UI entry point.
  // END_CONTRACT: FN-HANDLE-CATALOG-CTA
  const handleCtaClick = useCallback((reportType: string, entryPoint: string) => {
    void trackCatalogEvent("catalog.checkout_start", withCatalogTrace({
      surface: "catalog",
      report_type: reportType,
      entry_point: entryPoint,
    }, {
      module: CATALOG_GRACE_MODULES.reportsCatalog,
      contract: "FN-HANDLE-CATALOG-CTA",
      block: CATALOG_GRACE_BLOCKS.catalog.ctaTracking,
    }));
  }, []);

  const subscriptionProducts = PRODUCTS.filter((product) => isSubscriptionProductType(product.id));
  const oneOffProducts = PRODUCTS.filter((product) => !isSubscriptionProductType(product.id));

  // START_CONTRACT: FN-RENDER-CATALOG-SECTION
  // purpose: Render catalog product cards without sacrificing JSX readability while preserving canonical CTA tracing.
  // inputs: product config and index.
  // returns: catalog card link node.
  // END_CONTRACT: FN-RENDER-CATALOG-SECTION

  const renderCatalogSection = useCallback((product: (typeof PRODUCTS)[number], idx: number) => (
    <Link
      key={product.id}
      href={product.link}
      data-testid={`catalog-card-${product.id}`}
      data-block="CATALOG_SECTION"
      data-semantic-block="CATALOG_SECTION"
      onClick={() => handleCtaClick(product.id, `catalog-card-${product.id}`)}
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
              <div className="flex flex-col items-end gap-2">
                <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">
                  {getRuntimeAccessBadge(product.id)}
                </p>
                <ConsumerMetaPill label="analytics" value={product.analyticsLabel} />
              </div>
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
  ), [handleCtaClick]);


  return (
    <ConsumerPageShell
      testId="reports-catalog-page"
      analyticsEvent={{
        event_name: "catalog.catalog_view",
        payload: withCatalogTrace(
          {
            surface: "catalog",
            entry_point: "catalog-page-shell",
            flow_id: flowId,
          },
          {
            module: CATALOG_GRACE_MODULES.reportsCatalog,
            contract: "FN-RENDER-CATALOG-SHELL",
            block: CATALOG_GRACE_BLOCKS.catalog.analyticsBootstrap,
            correlation_id: viewCorrelationId ?? undefined,
          },
        ),
      }}
    >
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
              onClick={() => handleCtaClick("horary", "catalog-hero")}
              className="inline-flex items-center justify-center rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              Задать быстрый вопрос
            </Link>
          </>
        }
      />

      <CatalogCheckoutResumeBanner
        surface="catalog"
        entryPoint="catalog-inline-resume"
        checkoutToken={checkoutToken}
        mockEnabled={mockEnabled}
        runtimeEnabled={runtimeEnabled}
        initData={initData}
        isReady={isReady}
        mode={mode}
      />

      <ConsumerPanel data-testid="catalog-billing-note" className="overflow-hidden">
        <div className="grid gap-4 p-5 sm:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] sm:p-6">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">
              Как устроен доступ
            </p>
            <h2 className="mt-3 text-xl font-black tracking-tight text-slate-950">
              Подписка для регулярной навигации, разовые товары для точечной аналитики
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              Подписка покрывает регулярные прогнозы, а отдельные товары — натал, соляр, совместимость и хорар — дают законченный разбор под конкретный запрос без продления.
            </p>
          </div>

          <div className="grid gap-3">
            <div className="rounded-[24px] border border-indigo-100 bg-indigo-50/80 p-4" data-testid="catalog-subscription-summary">
              <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-700">
                Подписка {SUBSCRIPTION_PRICE_LABEL}
              </p>
              <p className="mt-2 text-sm font-semibold leading-relaxed text-indigo-950">
                Годовой и месячный прогнозы для регулярного планирования, решений, денег и отношений.
              </p>
            </div>
            <div className="rounded-[24px] border border-emerald-100 bg-emerald-50/80 p-4" data-testid="catalog-oneoff-summary">
              <p className="text-[11px] font-black uppercase tracking-[0.22em] text-emerald-700">
                Разовые товары 199–299₽
              </p>
              <p className="mt-2 text-sm font-semibold leading-relaxed text-emerald-950">
                Натал, соляр, совместимость и хорар — законченные аналитические продукты под конкретную задачу.
              </p>
            </div>
          </div>
        </div>
      </ConsumerPanel>

      <section className="grid gap-4" aria-label="Подписка" data-testid="catalog-subscription-section">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">Подписка</p>
            <h2 className="mt-2 text-xl font-black tracking-tight text-slate-950">Регулярные прогнозы</h2>
          </div>
          <ConsumerStatusBadge label="Доступ" description={SUBSCRIPTION_PRICE_LABEL} tone="indigo" />
        </div>
        {subscriptionProducts.map(renderCatalogSection)}
      </section>

      <section className="grid gap-4" aria-label="Разовые товары" data-testid="catalog-oneoff-section">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">Разовые товары</p>
            <h2 className="mt-2 text-xl font-black tracking-tight text-slate-950">Точечные разборы</h2>
          </div>
          <ConsumerStatusBadge label="Цены" description="299₽ · 199₽" tone="emerald" />
        </div>
        {oneOffProducts.map((product, idx) => renderCatalogSection(product, idx + subscriptionProducts.length))}
      </section>
    </ConsumerPageShell>
  );
}
// #END_BLOCK_CATALOG_UI
