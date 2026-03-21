// ############################################################################
// AI_HEADER: MODULE_CREATE_PAGE
// ROLE: Order confirmation and payment initialization.
// DEPENDENCIES: useTelegram, api/users/me.
// GRACE_ANCHORS: [CREATE_PAGE_LOGIC, CREATE_PAGE_UI]
// ############################################################################

"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CreditCard, Loader2, ShieldCheck, Sparkles } from "lucide-react";

import { useTelegram } from "../../hooks/useTelegram";
import { trackEvent } from "../lib/analytics";
import {
  getReportUnlockPriceLabel,
  getReportUnlockPriceValue,
  getRuntimePriceLabel,
  getRuntimePriceValue,
  HORARY_PRICE_LABEL,
  isHoraryProductType,
  isReportUnlockBridgeEnabled,
  isSubscriptionProductType,
  SUBSCRIPTION_PRICE_LABEL,
} from "../../lib/product-billing";
import {
  CatalogEventPayload,
  normalizeCatalogFlags,
  resolveCheckoutMode,
  trackCatalogEvent,
} from "../../components/catalog/catalog-analytics";
import {
  type CheckoutSessionState,
  type CreateProfile,
  type ProductInputDraft,
  PRODUCT_META,
  MOCK_INIT_DATA,
  EMPTY_PRODUCT_INPUT_DRAFT,
  getDraftStorageKey,
  buildMockProfile,
  formatCreateAccessError,
} from "../../components/catalog/create-shared";

function appendQueryParam(path: string, key: string, value: string): string {
  const glue = path.includes("?") ? "&" : "?";
  return `${path}${glue}${key}=${encodeURIComponent(value)}`;
}

function CreatePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, initData, mode, isReady } = useTelegram();

  const type = searchParams.get("type");
  const checkoutToken = searchParams.get("checkout");
  const mockQueryEnabled = searchParams.get("mock") === "1";
  const runtimeQueryEnabled = searchParams.get("runtime") === "1" || Boolean(checkoutToken);
  const meta = type ? PRODUCT_META[type] : null;
  const isHorary = isHoraryProductType(type);
  const isSynastry = type === "synastry";
  const isSolarReturn = type === "solar_return";
  const isSubscriptionProduct = isSubscriptionProductType(type);

  const [profile, setProfile] = useState<CreateProfile | null>(null);
  const [profileResolved, setProfileResolved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [selectedPack, setSelectedPack] = useState("pack_1");
  const [apiPacks, setApiPacks] = useState<Record<string, { label: string; price: number }> | null>(null);
  const [clientMockSignal, setClientMockSignal] = useState(false);
  const [checkoutState, setCheckoutState] = useState<CheckoutSessionState>({
    status: checkoutToken ? "checking" : "idle",
    message: null,
  });
  const [productInputDraftHydrated, setProductInputDraftHydrated] = useState(
    !isSynastry && !isSolarReturn,
  );
  const [partnerName, setPartnerName] = useState("");
  const [partnerBirthDate, setPartnerBirthDate] = useState("");
  const [partnerBirthLocation, setPartnerBirthLocation] = useState("");
  const [solarCurrentLocation, setSolarCurrentLocation] = useState("");

  const checkoutCreateAttemptRef = useRef<string | null>(null);
  const productInputDraftRef = useRef<ProductInputDraft>(EMPTY_PRODUCT_INPUT_DRAFT);

  const selectedPackPriceLabel = apiPacks?.[selectedPack]
    ? `${Math.round(apiPacks[selectedPack].price)}₽`
    : HORARY_PRICE_LABEL;

  const shouldUseMockProfile =
    clientMockSignal ||
    mockQueryEnabled ||
    mode === "mock" ||
    initData === MOCK_INIT_DATA ||
    user?.id === 123456789;
  const effectiveProfile = profile || (shouldUseMockProfile ? buildMockProfile() : null);
  const featureFlags = effectiveProfile?.feature_flags;
  const isReportUnlockBridge = isReportUnlockBridgeEnabled(type, featureFlags);
  const reportAccess = type ? effectiveProfile?.report_access?.[type] : undefined;
  const fallbackUnlocks = type ? effectiveProfile?.report_unlocks?.[type] ?? 0 : 0;
  const availableUnlocks =
    reportAccess?.granted_via === "report_entitlement"
      ? reportAccess.remaining_unlocks ?? fallbackUnlocks
      : fallbackUnlocks;
  const hasOneOffUnlock = isReportUnlockBridge &&
    (reportAccess
      ? reportAccess.allowed === true && reportAccess.granted_via === "report_entitlement"
      : availableUnlocks > 0);
  const canAskFree = effectiveProfile?.can_ask_horary === true;
  const hasResolvedReportAccess = !isHorary &&
    (reportAccess ? reportAccess.allowed === true : effectiveProfile?.can_access_premium === true);
  const canGeneratePremium = !isHorary && (hasResolvedReportAccess || hasOneOffUnlock);
  const shouldShowOneOffReportUnlockPaywall =
    !isHorary && isReportUnlockBridge && !hasResolvedReportAccess && !hasOneOffUnlock;
  const runtimePriceLabel = shouldShowOneOffReportUnlockPaywall
    ? getReportUnlockPriceLabel(type)
    : getRuntimePriceLabel(type);
  const waitingForProfile = Boolean(initData) && !profileResolved && !error;
  const checkoutBusy = ["checking", "pending", "succeeded", "creating"].includes(checkoutState.status);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      const tg = (window as Window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
      const hasMockSession = window.sessionStorage.getItem("mock_telegram_user") === "1";
      const hasMockInitData = tg?.initData === MOCK_INIT_DATA;
      setClientMockSignal(hasMockSession || mockQueryEnabled || hasMockInitData);
    } catch {
      setClientMockSignal(mockQueryEnabled);
    }
  }, [mockQueryEnabled]);

  useEffect(() => {
    setProductInputDraftHydrated(!isSynastry && !isSolarReturn);
    if (!isSynastry && !isSolarReturn) {
      productInputDraftRef.current = EMPTY_PRODUCT_INPUT_DRAFT;
    }
  }, [isSolarReturn, isSynastry]);

  useEffect(() => {
    if (typeof window === "undefined" || !type || (!isSynastry && !isSolarReturn)) {
      productInputDraftRef.current = EMPTY_PRODUCT_INPUT_DRAFT;
      setProductInputDraftHydrated(true);
      return;
    }

    try {
      const rawDraft = window.sessionStorage.getItem(getDraftStorageKey(type));
      const draft = rawDraft
        ? { ...EMPTY_PRODUCT_INPUT_DRAFT, ...JSON.parse(rawDraft) }
        : EMPTY_PRODUCT_INPUT_DRAFT;

      productInputDraftRef.current = draft;
      setPartnerName(draft.partnerName || "");
      setPartnerBirthDate(draft.partnerBirthDate || "");
      setPartnerBirthLocation(draft.partnerBirthLocation || "");
      setSolarCurrentLocation(draft.solarCurrentLocation || "");
    } catch {
      window.sessionStorage.removeItem(getDraftStorageKey(type));
      productInputDraftRef.current = EMPTY_PRODUCT_INPUT_DRAFT;
      setPartnerName("");
      setPartnerBirthDate("");
      setPartnerBirthLocation("");
      setSolarCurrentLocation("");
    } finally {
      setProductInputDraftHydrated(true);
    }
  }, [isSolarReturn, isSynastry, type]);

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !type ||
      (!isSynastry && !isSolarReturn) ||
      !productInputDraftHydrated
    ) {
      return;
    }

    const draft: ProductInputDraft = {
      partnerName,
      partnerBirthDate,
      partnerBirthLocation,
      solarCurrentLocation,
    };

    window.sessionStorage.setItem(getDraftStorageKey(type), JSON.stringify(draft));
  }, [
    isSolarReturn,
    isSynastry,
    partnerBirthDate,
    partnerBirthLocation,
    partnerName,
    productInputDraftHydrated,
    solarCurrentLocation,
    type,
  ]);

  useEffect(() => {
    if (typeof window === "undefined" || type !== "solar_return" || solarCurrentLocation.trim()) {
      return;
    }

    const fallbackLocation = effectiveProfile?.current_location || effectiveProfile?.birth_place || "";
    if (fallbackLocation) {
      productInputDraftRef.current = {
        ...productInputDraftRef.current,
        solarCurrentLocation: fallbackLocation,
      };
      setSolarCurrentLocation(fallbackLocation);
    }
  }, [effectiveProfile, solarCurrentLocation, type]);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (!initData) {
      setProfileResolved(true);
      return;
    }

    let cancelled = false;

    const loadProfile = async () => {
      try {
        if (shouldUseMockProfile && !runtimeQueryEnabled) {
          if (!cancelled) {
            setProfile(buildMockProfile());
            setProfileResolved(true);
          }
          return;
        }

        const url = new URL("/api/users/me", window.location.origin);
        const response = await fetch(url.toString(), {
          headers: { "X-Telegram-Auth": initData },
        });

        if (!response.ok) {
          throw new Error("profile_load_failed");
        }

        const nextProfile = (await response.json()) as CreateProfile;
        if (!cancelled) {
          setProfile(nextProfile);
          setProfileResolved(true);
        }
      } catch (loadError) {
        console.error(loadError);
        if (!cancelled) {
          if (shouldUseMockProfile) {
            setProfile(buildMockProfile());
          } else {
            setError("Не удалось загрузить профиль для оформления.");
          }
          setProfileResolved(true);
        }
      }
    };

    void loadProfile();

    return () => {
      cancelled = true;
    };
  }, [initData, isReady, runtimeQueryEnabled, shouldUseMockProfile]);

  useEffect(() => {
    if (!isHorary || apiPacks) {
      return;
    }

    fetch("/api/billing/packs")
      .then((res) => res.json())
      .then(setApiPacks)
      .catch((packError) => console.error(packError));
  }, [apiPacks, isHorary]);

  const clearDraft = () => {
    if (typeof window === "undefined" || !type || (!isSynastry && !isSolarReturn)) {
      return;
    }
    window.sessionStorage.removeItem(getDraftStorageKey(type));
  };

  const restoreProductDraft = (
    draftOverride?: Record<string, string | undefined> | null,
  ) => {
    if (!type || (!isSynastry && !isSolarReturn) || !draftOverride) {
      return;
    }

    const nextDraft: ProductInputDraft = {
      ...productInputDraftRef.current,
    };

    if (isSynastry) {
      if (typeof draftOverride.partner_name === "string") {
        nextDraft.partnerName = draftOverride.partner_name;
      }
      if (typeof draftOverride.partner_birth_date === "string") {
        nextDraft.partnerBirthDate = draftOverride.partner_birth_date;
      }
      if (typeof draftOverride.partner_birth_location === "string") {
        nextDraft.partnerBirthLocation = draftOverride.partner_birth_location;
      }
    }

    if (isSolarReturn && typeof draftOverride.solar_current_location === "string") {
      nextDraft.solarCurrentLocation = draftOverride.solar_current_location;
    }

    const draftChanged =
      nextDraft.partnerName !== productInputDraftRef.current.partnerName ||
      nextDraft.partnerBirthDate !== productInputDraftRef.current.partnerBirthDate ||
      nextDraft.partnerBirthLocation !== productInputDraftRef.current.partnerBirthLocation ||
      nextDraft.solarCurrentLocation !== productInputDraftRef.current.solarCurrentLocation;

    if (!draftChanged) {
      return;
    }

    productInputDraftRef.current = nextDraft;
    setPartnerName(nextDraft.partnerName);
    setPartnerBirthDate(nextDraft.partnerBirthDate);
    setPartnerBirthLocation(nextDraft.partnerBirthLocation);
    setSolarCurrentLocation(nextDraft.solarCurrentLocation);

    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(getDraftStorageKey(type), JSON.stringify(nextDraft));
    }
  };

  const validateCreateInputs = (
    payloadOverride?: Record<string, string | undefined>,
  ) => {
    if (isHorary && !question.trim()) {
      return "Пожалуйста, введите вопрос.";
    }
    const partnerBirthDateValue =
      payloadOverride?.partner_birth_date ?? productInputDraftRef.current.partnerBirthDate;
    const partnerBirthLocationValue =
      payloadOverride?.partner_birth_location ?? productInputDraftRef.current.partnerBirthLocation;

    if (
      isSynastry &&
      (!(partnerBirthDateValue || "").trim() || !(partnerBirthLocationValue || "").trim())
    ) {
      return "Для совместимости нужны дата/время и место рождения партнёра.";
    }
    return null;
  };

  const buildCreatePayload = () => {
    const productInputDraft = productInputDraftRef.current;
    const payload: Record<string, string | undefined> = {
      report_type: type || undefined,
      question: isHorary ? question : undefined,
    };

    if (isSynastry) {
      payload.partner_name = productInputDraft.partnerName.trim() || undefined;
      payload.partner_birth_date = productInputDraft.partnerBirthDate.trim() || undefined;
      payload.partner_birth_location = productInputDraft.partnerBirthLocation.trim() || undefined;
    }

    if (isSolarReturn) {
      payload.solar_current_location = productInputDraft.solarCurrentLocation.trim() || undefined;
    }

    return payload;
  };

  const buildCheckoutReturnPath = () => {
    if (!type) {
      return "/reports";
    }

    let returnPath = `/create?type=${type}`;
    if (mode === "mock" || mockQueryEnabled) {
      returnPath = appendQueryParam(returnPath, "mock", "1");
      returnPath = appendQueryParam(returnPath, "runtime", "1");
    }
    return returnPath;
  };

  const handleCreateReport = async (
    payloadOverride?: Record<string, string | undefined>,
  ) => {
    const createPayload = payloadOverride || buildCreatePayload();
    const validationError = validateCreateInputs(createPayload);
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!type || !initData) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/reports/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Telegram-Auth": initData,
        },
        body: JSON.stringify(createPayload),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        if (response.status === 402) {
          setError(formatCreateAccessError(isReportUnlockBridge));
        } else {
          setError(payload.detail || "Не удалось запустить генерацию отчета. Попробуйте позже.");
        }
        return;
      }

      const data = await response.json();
      clearDraft();

      if (type === "week_forecast") {
        const weekUrl = new URL("/week", window.location.origin);
        if (mode === "mock" || mockQueryEnabled) {
          weekUrl.searchParams.set("mock", "1");
        }
        router.push(`${weekUrl.pathname}${weekUrl.search}`);
      } else {
        const readUrl = new URL(`/read/${data.report_id}`, window.location.origin);
        if (mode === "mock" || mockQueryEnabled) {
          readUrl.searchParams.set("mock", "1");
        }
        router.push(`${readUrl.pathname}${readUrl.search}`);
      }
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Не удалось сформировать разбор.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Resume only after draft-backed inputs are restored, otherwise product-specific
    // fields like solar_current_location can be lost during the auto-create step.
    if (!checkoutToken || !isReportUnlockBridge || !initData || !type || !productInputDraftHydrated) {
      return;
    }

    let cancelled = false;
    let timeoutId: number | undefined;

    const syncCheckoutSession = async () => {
      try {
        const response = await fetch(`/api/billing/sessions/${checkoutToken}`, {
          headers: { "X-Telegram-Auth": initData },
        });

        if (!response.ok) {
          throw new Error("checkout_session_unavailable");
        }

        const session = (await response.json()) as {
          status?: string;
          draft_payload?: Record<string, string | undefined> | null;
          resumed_report_id?: string | null;
        };

        if (cancelled) {
          return;
        }

        restoreProductDraft(session.draft_payload || undefined);

        if (session.resumed_report_id) {
          const readUrl = new URL(`/read/${session.resumed_report_id}`, window.location.origin);
          if (mode === "mock" || mockQueryEnabled) {
            readUrl.searchParams.set("mock", "1");
          }
          router.replace(`${readUrl.pathname}${readUrl.search}`);
          return;
        }

        if (session.status === "succeeded") {
          setCheckoutState({
            status: "succeeded",
            message: "Оплата подтверждена. Запускаем разбор без повторного платежа.",
          });
          if (checkoutCreateAttemptRef.current === checkoutToken) {
            return;
          }
          checkoutCreateAttemptRef.current = checkoutToken;
          await handleCreateReport(session.draft_payload || undefined);
          return;
        }

        if (session.status === "pending" || session.status === "created") {
          setCheckoutState({
            status: "pending",
            message: "Ждем подтверждения оплаты. Как только провайдер вернет успех, разбор запустится автоматически.",
          });
          timeoutId = window.setTimeout(() => {
            void syncCheckoutSession();
          }, 1500);
          return;
        }

        if (session.status === "canceled") {
          setCheckoutState({
            status: "canceled",
            message: "Оплата была отменена. Можно повторить попытку с этого же экрана.",
          });
          return;
        }

        if (session.status === "failed") {
          setCheckoutState({
            status: "failed",
            message: "Платежная сессия завершилась с ошибкой. Попробуйте снова.",
          });
        }
      } catch (sessionError) {
        console.error(sessionError);
        if (!cancelled) {
          setCheckoutState({
            status: "failed",
            message: "Не удалось проверить состояние оплаты. Обновите экран или повторите позже.",
          });
        }
      }
    };

    void syncCheckoutSession();

    return () => {
      cancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [
    checkoutToken,
    initData,
    isReportUnlockBridge,
    mockQueryEnabled,
    mode,
    productInputDraftHydrated,
    router,
    type,
  ]);

  const handlePay = async () => {
    if (!user || !initData || !type) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const isReportUnlockCheckout = shouldShowOneOffReportUnlockPaywall;
      const reportUnlockDraftPayload = isReportUnlockCheckout ? buildCreatePayload() : null;
      const payload: Record<string, unknown> = {
        description: `Оплата: ${meta?.label || type}`,
        is_recurring: !isHorary && !isReportUnlockCheckout,
        product_type: isReportUnlockCheckout ? type : isHorary ? "horary" : "subscription",
      };

      if (isReportUnlockCheckout) {
        payload.amount = getReportUnlockPriceValue(type);
        payload.return_path = buildCheckoutReturnPath();
        payload.draft_payload = reportUnlockDraftPayload;
        if (
          typeof window !== "undefined" &&
          type &&
          (isSynastry || isSolarReturn)
        ) {
          window.sessionStorage.setItem(
            getDraftStorageKey(type),
            JSON.stringify(productInputDraftRef.current),
          );
        }
      } else if (isHorary && effectiveProfile?.can_ask_horary === false) {
        payload.pack_id = selectedPack;
        payload.amount = 0;
      } else {
        payload.amount = getRuntimePriceValue(type);
      }

      const response = await fetch("/api/billing/pay", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Telegram-Auth": initData,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Payment initialization failed");
      }

      const data = (await response.json()) as {
        url?: string;
        mock?: boolean;
        checkout_token?: string;
      };

      if (data.url) {
        window.location.href = data.url;
        return;
      }

      if (!data.mock) {
        return;
      }

      trackEvent("mock_payment_success", {
        metadata: { product: type || payload.pack_id },
      });

      if (isReportUnlockCheckout && data.checkout_token) {
        const billingCompleteUrl = new URL("/billing/complete", window.location.origin);
        billingCompleteUrl.searchParams.set("checkout", data.checkout_token);
        if (mode === "mock" || mockQueryEnabled) {
          billingCompleteUrl.searchParams.set("mock", "1");
          billingCompleteUrl.searchParams.set("runtime", "1");
        }
        router.push(`${billingCompleteUrl.pathname}${billingCompleteUrl.search}`);
        return;
      }

      if (isHorary && effectiveProfile?.can_ask_horary === false && payload.pack_id) {
        const url = new URL("/api/users/me", window.location.origin);
        const profileResponse = await fetch(url.toString(), {
          headers: { "X-Telegram-Auth": initData },
        });
        const nextProfile = (await profileResponse.json()) as CreateProfile;
        setProfile(nextProfile);
        setProfileResolved(true);
        setLoading(false);
        return;
      }

      await handleCreateReport();
    } catch (payError) {
      console.error(payError);
      setError("Произошла ошибка при инициализации оплаты. Попробуйте еще раз.");
    } finally {
      setLoading(false);
    }
  };

  const renderProductInputPanel = () => {
    if (isSynastry) {
      return (
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-400">
              Нужно для расчёта
            </p>
            <p className="mt-2 text-lg font-bold text-slate-800">Данные партнёра</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Имя можно не указывать, но дата, время и место рождения нужны обязательно.
              Чем точнее время, тем честнее совместимость по домам и аспектам.
            </p>
          </div>
          <div className="space-y-3">
            <div>
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                Имя партнёра
              </label>
              <input
                value={partnerName}
                onChange={(event) => {
                  productInputDraftRef.current = {
                    ...productInputDraftRef.current,
                    partnerName: event.target.value,
                  };
                  setPartnerName(event.target.value);
                  setError(null);
                }}
                data-testid="create-synastry-partner-name"
                placeholder="Необязательно"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-800 outline-none transition focus:border-purple-300 focus:bg-white"
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                Дата и время рождения
              </label>
              <input
                value={partnerBirthDate}
                onChange={(event) => {
                  productInputDraftRef.current = {
                    ...productInputDraftRef.current,
                    partnerBirthDate: event.target.value,
                  };
                  setPartnerBirthDate(event.target.value);
                  setError(null);
                }}
                data-testid="create-synastry-partner-birth-date"
                type="datetime-local"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-800 outline-none transition focus:border-purple-300 focus:bg-white"
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                Место рождения
              </label>
              <input
                value={partnerBirthLocation}
                onChange={(event) => {
                  productInputDraftRef.current = {
                    ...productInputDraftRef.current,
                    partnerBirthLocation: event.target.value,
                  };
                  setPartnerBirthLocation(event.target.value);
                  setError(null);
                }}
                data-testid="create-synastry-partner-birth-location"
                placeholder="Город, страна"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-800 outline-none transition focus:border-purple-300 focus:bg-white"
              />
            </div>
          </div>
        </div>
      );
    }

    if (isSolarReturn) {
      const fallbackLabel =
        effectiveProfile?.current_location || effectiveProfile?.birth_place || "текущую локацию из профиля";

      return (
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-400">
              Семантика Соляра
            </p>
            <p className="mt-2 text-lg font-bold text-slate-800">Город активного личного года</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Сейчас в B2C-flow используется один город: там, где проходит активный соляр.
              Если оставить поле пустым, возьмём {fallbackLabel}.
            </p>
          </div>
          <div>
            <label className="mb-2 block text-xs font-black uppercase tracking-[0.18em] text-slate-400">
              Город активного Соляра
            </label>
            <input
              value={solarCurrentLocation}
              onChange={(event) => {
                productInputDraftRef.current = {
                  ...productInputDraftRef.current,
                  solarCurrentLocation: event.target.value,
                };
                setSolarCurrentLocation(event.target.value);
                setError(null);
              }}
              data-testid="create-solar-current-location"
              placeholder="Например: Тбилиси, Грузия"
              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-800 outline-none transition focus:border-purple-300 focus:bg-white"
            />
          </div>
        </div>
      );
    }

    return null;
  };

  const renderCheckoutStatusPanel = () => {
    if (!checkoutToken || !isReportUnlockBridge || !checkoutState.message) {
      return null;
    }

    const toneClass =
      checkoutState.status === "failed" || checkoutState.status === "canceled"
        ? "border-rose-100 bg-rose-50 text-rose-700"
        : "border-emerald-100 bg-emerald-50 text-emerald-700";

    return (
      <div
        data-testid="create-checkout-status"
        className={`rounded-3xl border p-5 text-sm font-medium shadow-sm ${toneClass}`}
      >
        {checkoutState.message}
      </div>
    );
  };

  if (!isReady || waitingForProfile) {
    return (
      <div
        data-testid="create-loading"
        className="flex min-h-screen items-center justify-center bg-slate-50 font-light text-slate-400"
      >
        <Loader2 className="mr-2 animate-spin text-purple-400" />
        Загрузка...
      </div>
    );
  }

  if (error && !effectiveProfile) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#fdfbf7] p-10 text-center">
        <div className="max-w-sm rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600">
          {error}
        </div>
      </div>
    );
  }

  if (!type) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#fdfbf7] p-10 text-center">
        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-slate-100 text-slate-300">
          <ArrowLeft size={32} />
        </div>
        <h2 className="mb-2 text-2xl font-black text-slate-800">Продукт не выбран</h2>
        <p className="mx-auto mb-8 max-w-xs text-slate-500">
          Пожалуйста, выберите интересующий вас разбор в каталоге предложений.
        </p>
        <div className="flex w-full max-w-xs flex-col gap-3">
          <Link
            href="/reports"
            className="w-full rounded-2xl bg-slate-900 py-4 text-center font-bold text-white shadow-lg shadow-slate-200 transition-all active:scale-95"
          >
            Перейти в каталог
          </Link>
          <button
            onClick={() => router.back()}
            className="w-full rounded-2xl border border-slate-100 bg-white py-4 text-center font-bold text-slate-500 transition-all active:scale-95"
          >
            Назад
          </button>
        </div>
      </div>
    );
  }

  if (isHorary && canAskFree) {
    return (
      <div className="min-h-screen space-y-6 bg-slate-50 px-6 pb-24 pt-6">
        <h1 className="text-2xl font-black text-slate-900">Задать вопрос</h1>
        <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            data-testid="create-horary-textarea"
            placeholder="Например: Стоит ли мне менять работу сейчас?"
            className="h-32 w-full resize-none rounded-xl border-none bg-slate-50 p-3 text-slate-800 focus:ring-2 focus:ring-purple-200"
          />
        </div>
        {error && (
          <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600">
            {error}
          </div>
        )}
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-white via-white/90 to-transparent p-6">
          <button
            onClick={handleCreateReport}
            disabled={loading || !question.trim()}
            data-testid="create-horary-submit"
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 font-bold text-white shadow-xl shadow-purple-200 disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <ShieldCheck size={20} />}
            Получить ответ
          </button>
        </div>
      </div>
    );
  }

  if (canGeneratePremium) {
    return (
      <div className="min-h-screen space-y-6 bg-slate-50 px-6 pb-24 pt-6">
        <h1 className="text-2xl font-black text-slate-900">Сформировать разбор</h1>
        <div className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <p className="text-lg font-bold text-slate-800">{meta?.label || type}</p>
            {hasOneOffUnlock && (
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                Разовый unlock уже на аккаунте и спишется только при успешном создании отчёта.
              </p>
            )}
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-100 text-purple-600">
            <Sparkles size={24} />
          </div>
        </div>
        {renderCheckoutStatusPanel()}
        {hasOneOffUnlock && (
          <div
            data-testid="create-one-off-unlock-note"
            className="rounded-3xl border border-emerald-100 bg-white p-5 shadow-sm"
          >
            <p className="text-sm font-semibold text-slate-800">
              Доступно разблокировок: {availableUnlocks}
            </p>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Этот разбор можно собрать без новой оплаты. Если генерация завершится ошибкой, повторный платёж не потребуется.
            </p>
          </div>
        )}
        {error && (
          <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600">
            {error}
          </div>
        )}
        {renderProductInputPanel()}
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-white via-white/90 to-transparent p-6">
          <button
            onClick={handleCreateReport}
            disabled={loading}
            data-testid="create-premium-generate"
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 font-bold text-white shadow-xl shadow-purple-200"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
            {hasOneOffUnlock ? "Сформировать по разблокировке" : "Сформировать за 0₽"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen space-y-6 bg-slate-50 px-6 pb-24 pt-6">
      <h1 className="text-2xl font-black text-slate-900">
        {isHorary
          ? "Купить вопросы"
          : shouldShowOneOffReportUnlockPaywall
            ? "Разовая разблокировка"
            : isSubscriptionProduct
              ? "Подписка GRACE"
              : "Оформление заказа"}
      </h1>
      {renderCheckoutStatusPanel()}
      {isHorary && apiPacks ? (
        <div className="space-y-3">
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
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-6">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-400">
                {shouldShowOneOffReportUnlockPaywall
                  ? "Разовая разблокировка"
                  : isSubscriptionProduct
                    ? "Доступ по подписке"
                    : "Разовая покупка"}
              </p>
              <p className="mt-2 text-lg font-bold text-slate-800">{meta?.label || type}</p>
            </div>
            <p className="text-lg font-bold text-purple-600">{runtimePriceLabel}</p>
          </div>
          {shouldShowOneOffReportUnlockPaywall ? (
            <div
              data-testid="create-one-off-note"
              className="rounded-3xl border border-emerald-100 bg-white p-5 shadow-sm"
            >
              <p className="text-sm font-semibold text-slate-800">
                В этом slice разбор идет не через подписку, а через один разовый unlock.
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                После оплаты доступ останется на аккаунте до момента, когда вы реально запустите генерацию отчёта.
              </p>
            </div>
          ) : isSubscriptionProduct ? (
            <div
              data-testid="create-subscription-note"
              className="rounded-3xl border border-purple-100 bg-white p-5 shadow-sm"
            >
              <p className="text-sm font-semibold text-slate-800">
                Этот разбор сейчас открывается через подписку.
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                После оплаты откроются персональные разборы: Натал, Неделя, Месяц, Год, Соляр и Совместимость.
              </p>
            </div>
          ) : null}
        </div>
      )}
      {error && (
        <div className="animate-in fade-in slide-in-from-top-2 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600 duration-300">
          {error}
        </div>
      )}
      {renderProductInputPanel()}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-white via-white/90 to-transparent p-6">
        <button
          onClick={handlePay}
          disabled={loading || checkoutBusy}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 font-bold text-white shadow-xl shadow-purple-200 disabled:opacity-60"
        >
          {loading || checkoutBusy ? <Loader2 className="animate-spin" size={20} /> : <CreditCard size={20} />}
          {isHorary && apiPacks
            ? `Оплатить ${selectedPackPriceLabel}`
            : shouldShowOneOffReportUnlockPaywall
              ? `Оплатить ${getReportUnlockPriceLabel(type)}`
              : isSubscriptionProduct
                ? `Оформить подписку ${SUBSCRIPTION_PRICE_LABEL}`
                : `Оплатить ${HORARY_PRICE_LABEL}`}
        </button>
      </div>
    </div>
  );
}

export default function CreatePageClient() {
  return <CreatePageContent />;
}
