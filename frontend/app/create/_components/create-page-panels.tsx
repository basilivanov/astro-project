import { CreditCard, Loader2, ShieldCheck, Sparkles } from "lucide-react";
import type { MouseEventHandler, ReactNode } from "react";

type OfferSummaryProps = {
  isHorary: boolean;
  isSubscriptionProduct: boolean;
  shouldShowOneOffReportUnlockPaywall: boolean;
  type: string | null;
  runtimePriceLabel: string;
  metaLabel: string | null | undefined;
};

type HoraryPack = { label: string; price: number };

type ProductInputPanelProps = {
  isHorary: boolean;
  isSynastry: boolean;
  isSolarReturn: boolean;
  apiPacks: Record<string, HoraryPack> | null;
  selectedPack: string;
  setSelectedPack: (packId: string) => void;
  selectedPackPriceLabel: string;
  shouldShowOneOffReportUnlockPaywall: boolean;
  isSubscriptionProduct: boolean;
  metaLabel: string | null | undefined;
  type: string | null;
  runtimePriceLabel: string;
  error: string | null;
  question: string;
  setQuestion: (value: string) => void;
  partnerName: string;
  setPartnerName: (value: string) => void;
  partnerBirthDate: string;
  setPartnerBirthDate: (value: string) => void;
  partnerBirthLocation: string;
  setPartnerBirthLocation: (value: string) => void;
  solarCurrentLocation: string;
  setSolarCurrentLocation: (value: string) => void;
};

type CheckoutStatusPanelProps = {
  checkoutToken: string | null;
  checkoutState: { status: string; message: string | null };
  isReportUnlockBridge: boolean;
  hasOneOffUnlock: boolean;
  canGeneratePremium: boolean;
  canAskFree: boolean;
  loading: boolean;
  onCreateClick: MouseEventHandler<HTMLButtonElement>;
};

type FooterCtaProps = {
  loading: boolean;
  checkoutBusy: boolean;
  onCheckoutClick: MouseEventHandler<HTMLButtonElement>;
  isHorary: boolean;
  apiPacks: Record<string, HoraryPack> | null;
  selectedPackPriceLabel: string;
  shouldShowOneOffReportUnlockPaywall: boolean;
  getReportUnlockPriceLabel: (type: string | null) => string;
  isSubscriptionProduct: boolean;
  runtimePriceLabel: string;
  horaryPriceLabel: string;
};

// START_MODULE_CONTRACT: M-CREATE-PAGE-PANELS
// purpose: Keep create-page visual surfaces separate from orchestration while preserving selectors and copy.
// inputs:
//   - resolved create-page view-model props from controller
// outputs:
//   - offer summary, product inputs, checkout status panel, sticky CTA
// invariants:
//   - existing `data-testid` selectors and rendered copy remain stable
// END_MODULE_CONTRACT: M-CREATE-PAGE-PANELS

// START_MODULE_MAP: M-CREATE-PAGE-PANELS
// entrypoints:
//   - CreateProductInputPanel
//   - CreateCheckoutStatusPanel
//   - CreateFooterCta
// END_MODULE_MAP: M-CREATE-PAGE-PANELS

function OfferSummaryCard(props: OfferSummaryProps) {
  const {
    isSubscriptionProduct,
    shouldShowOneOffReportUnlockPaywall,
    metaLabel,
    type,
    runtimePriceLabel,
  } = props;

  return (
    <section
      aria-labelledby="create-offer-summary-heading"
      data-testid="create-offer-summary"
      className="space-y-3"
    >
      <h2 id="create-offer-summary-heading" className="sr-only">
        Сводка предложения
      </h2>
      <div
        role="region"
        aria-label="Offer summary card"
        data-testid="create-offer-card"
        className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-6"
      >
        <div>
          <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-400">
            {shouldShowOneOffReportUnlockPaywall
              ? "Разовая разблокировка"
              : isSubscriptionProduct
                ? "Разовый доступ"
                : "Разовая покупка"}
          </p>
          <p className="mt-2 text-lg font-bold text-slate-800">{metaLabel || type}</p>
        </div>
        <p className="text-lg font-bold text-purple-600">{runtimePriceLabel}</p>
      </div>
      {shouldShowOneOffReportUnlockPaywall ? (
        <div data-testid="create-one-off-note" className="rounded-3xl border border-emerald-100 bg-white p-5 shadow-sm">
          <p className="text-sm font-semibold text-slate-800">
            В этом slice разбор открывается одной разовой оплатой без подписки и trial.
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            После оплаты доступ останется на аккаунте до момента, когда вы реально запустите генерацию отчёта.
          </p>
        </div>
      ) : isSubscriptionProduct ? (
        <div data-testid="create-subscription-note" className="rounded-3xl border border-purple-100 bg-white p-5 shadow-sm">
          <p className="text-sm font-semibold text-slate-800">
            Этот разбор в текущем публичном контуре оформляется как разовая покупка.
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            После оплаты откроются персональные разборы: Натал, Неделя, Месяц, Год, Соляр и Совместимость.
          </p>
        </div>
      ) : null}
    </section>
  );
}

function Field({ label, children, testId }: { label: string; children: ReactNode; testId: string }) {
  return (
    <label data-testid={testId} className="space-y-2">
      <span className="text-sm font-semibold text-slate-700">{label}</span>
      {children}
    </label>
  );
}

export function CreateProductInputPanel(props: ProductInputPanelProps) {
  const {
    isHorary,
    isSynastry,
    isSolarReturn,
    apiPacks,
    selectedPack,
    setSelectedPack,
    shouldShowOneOffReportUnlockPaywall,
    isSubscriptionProduct,
    metaLabel,
    type,
    runtimePriceLabel,
    error,
    question,
    setQuestion,
    partnerName,
    setPartnerName,
    partnerBirthDate,
    setPartnerBirthDate,
    partnerBirthLocation,
    setPartnerBirthLocation,
    solarCurrentLocation,
    setSolarCurrentLocation,
  } = props;

  if (isHorary && apiPacks) {
    return (
      <section data-testid="create-horary-pack-list" className="space-y-3">
        {Object.entries(apiPacks).map(([packId, pack]) => (
          <div
            key={packId}
            onClick={() => setSelectedPack(packId)}
            className={`cursor-pointer rounded-2xl border p-4 transition-all ${
              selectedPack === packId
                ? "border-purple-600 bg-white ring-1 ring-purple-600"
                : "border-slate-200 bg-white"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-bold text-slate-800">{pack.label}</p>
              </div>
              <p className="text-lg font-bold text-purple-600">{Math.round(pack.price)}₽</p>
            </div>
          </div>
        ))}
      </section>
    );
  }

  return (
    <>
      <OfferSummaryCard
        isHorary={isHorary}
        isSubscriptionProduct={isSubscriptionProduct}
        shouldShowOneOffReportUnlockPaywall={shouldShowOneOffReportUnlockPaywall}
        metaLabel={metaLabel}
        type={type}
        runtimePriceLabel={runtimePriceLabel}
      />
      {error && (
        <div className="animate-in fade-in slide-in-from-top-2 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600 duration-300">
          {error}
        </div>
      )}
      <section data-testid="create-product-input-panel" className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        {isHorary ? (
          <Field label="Ваш вопрос" testId="create-horary-question-field">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Например: когда лучше выйти на новую работу?"
              data-testid="create-horary-question-input"
              className="min-h-[140px] w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500"
            />
          </Field>
        ) : null}

        {isSynastry ? (
          <>
            <Field label="Имя партнёра" testId="create-synastry-partner-name-field">
              <input
                value={partnerName}
                onChange={(event) => setPartnerName(event.target.value)}
                data-testid="create-synastry-partner-name-input"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500"
              />
            </Field>
            <Field label="Дата и время рождения партнёра" testId="create-synastry-partner-birth-date-field">
              <input
                value={partnerBirthDate}
                onChange={(event) => setPartnerBirthDate(event.target.value)}
                placeholder="YYYY-MM-DD HH:mm"
                data-testid="create-synastry-partner-birth-date-input"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500"
              />
            </Field>
            <Field label="Место рождения партнёра" testId="create-synastry-partner-birth-location-field">
              <input
                value={partnerBirthLocation}
                onChange={(event) => setPartnerBirthLocation(event.target.value)}
                data-testid="create-synastry-partner-birth-location-input"
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500"
              />
            </Field>
          </>
        ) : null}

        {isSolarReturn ? (
          <Field label="Город, где вы встретите соляр" testId="create-solar-location-field">
            <input
              value={solarCurrentLocation}
              onChange={(event) => setSolarCurrentLocation(event.target.value)}
              data-testid="create-solar-location-input"
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500"
            />
          </Field>
        ) : null}
      </section>
    </>
  );
}

export function CreateCheckoutStatusPanel(props: CheckoutStatusPanelProps) {
  const {
    checkoutToken,
    checkoutState,
    isReportUnlockBridge,
    hasOneOffUnlock,
    canGeneratePremium,
    canAskFree,
    loading,
    onCreateClick,
  } = props;

  if (!checkoutToken && !(isReportUnlockBridge && hasOneOffUnlock) && !canGeneratePremium && !canAskFree) {
    return null;
  }

  return (
    <section data-testid="create-checkout-status-panel" className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="mt-1 rounded-full bg-emerald-50 p-2 text-emerald-600">
          <ShieldCheck size={18} />
        </div>
        <div className="space-y-2">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-400">Статус доступа</p>
          <p className="text-sm font-semibold text-slate-800">
            {checkoutToken
              ? checkoutState.message || "Проверяем статус оплаты и доступ к генерации."
              : hasOneOffUnlock
                ? "Разовая разблокировка уже активна. Можно запускать генерацию."
                : canGeneratePremium || canAskFree
                  ? "Доступ уже разрешён. Можно запускать генерацию."
                  : "Для продолжения нужен активный доступ."}
          </p>
          {(checkoutToken || hasOneOffUnlock || canGeneratePremium || canAskFree) && (
            <button
              type="button"
              onClick={onCreateClick}
              disabled={loading || checkoutState.status === "checking"}
              data-testid="create-generate-button"
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-purple-200 disabled:opacity-60"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
              {hasOneOffUnlock ? "Сформировать по разблокировке" : "Сформировать за 0₽"}
            </button>
          )}
        </div>
      </div>
    </section>
  );
}

export function CreateFooterCta(props: FooterCtaProps) {
  const {
    loading,
    checkoutBusy,
    onCheckoutClick,
    isHorary,
    apiPacks,
    selectedPackPriceLabel,
    shouldShowOneOffReportUnlockPaywall,
    getReportUnlockPriceLabel,
    isSubscriptionProduct,
    runtimePriceLabel,
    horaryPriceLabel,
  } = props;

  return (
    <section aria-label="Checkout primary action" data-grace-block="CTA_PRIMARY" data-testid="create-footer-cta" className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-white via-white/90 to-transparent p-6">
      <button
        onClick={onCheckoutClick}
        disabled={loading || checkoutBusy}
        data-testid="create-checkout-submit"
        className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 font-bold text-white shadow-xl shadow-purple-200 disabled:opacity-60"
      >
        {loading || checkoutBusy ? <Loader2 className="animate-spin" size={20} /> : <CreditCard size={20} />}
        {isHorary && apiPacks
          ? `Оплатить ${selectedPackPriceLabel}`
          : shouldShowOneOffReportUnlockPaywall
            ? `Оплатить ${getReportUnlockPriceLabel(null)}`
            : isSubscriptionProduct
              ? `Оплатить разово ${runtimePriceLabel}`
              : `Оплатить ${horaryPriceLabel}`}
      </button>
    </section>
  );
}
