// ############################################################################
// AI_HEADER: MODULE_CREATE_PAGE
// ROLE: Order confirmation and payment initialization.
// DEPENDENCIES: useTelegram, api/users/me.
// GRACE_ANCHORS: [CREATE_PAGE_LOGIC, CREATE_PAGE_UI]
// ############################################################################

"use client";

import { useEffect, useRef, useState, type MouseEventHandler } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CreditCard, Loader2, ShieldCheck, Sparkles } from "lucide-react";

import { useTelegram } from "../../hooks/useTelegram";
import { CorrelationManager, correlatedFetch } from "../../lib/correlation";
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
  setCatalogAnalyticsContext,
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
  CATALOG_GRACE_BLOCKS,
  CATALOG_GRACE_MODULES,
  withCatalogTrace,
} from "../../components/catalog/create-shared";

// START_MODULE_CONTRACT: M-CREATE-CHECKOUT
// purpose: Enforce strict-GRACE catalog/create flow for forecast checkout, unlock resume, and report generation handoff.
// owns:
//   - frontend/app/create/create-page-client.tsx
// inputs:
//   - Telegram init data, selected product type, checkout token, hydrated product-input drafts
// outputs:
//   - Billing session mutations via /api/billing/pay and /api/billing/sessions/{token}
//   - Report creation requests via /api/reports/create and read/week navigation targets
// dependencies:
//   - ../../lib/correlation for correlation IDs
//   - ../../lib/product-billing for runtime pricing/entitlement policy
//   - ../../components/catalog/catalog-analytics for FLOW-FORECAST-CATALOG telemetry
//   - ../../components/catalog/create-shared for GRACE module/block trace labels
// side_effects:
//   - persists/restores product-input drafts in sessionStorage during one-off resume flows
//   - emits strict trace telemetry with module/contract/block/correlation_id on every tracked event
// invariants:
//   - flow_id remains FLOW-FORECAST-CATALOG across create-page telemetry
//   - CTA and product-input surfaces keep semantic wrappers + stable data-testid selectors
//   - one-off resume never auto-creates before draft hydration completes
// failure_policy:
//   - surface errors to UI state and emit block-aware error telemetry
// trace_obligations:
//   - all create-page events include module, contract, block, semantic_block, correlation_id
//   - key contracts expose TOKEN_RESOLUTION, CTA_PRIMARY, CTA_CANCEL, PRODUCT_INPUT_SYN semantic blocks
// non_goals:
//   - rendering the catalog index/history or changing backend contract shapes
// END_MODULE_CONTRACT: M-CREATE-CHECKOUT

// START_MODULE_MAP: M-CREATE-CHECKOUT
// flow_id: FLOW-FORECAST-CATALOG
// entrypoints:
//   - CreatePageContent
//   - CreatePageClient
// contracts:
//   - FN-ENSURE-CORRELATION-ID
//   - FN-LOG-UI-ERROR
//   - FN-HANDLE-CREATE-REPORT
//   - FN-HANDLE-CHECKOUT
//   - FN-SYNC-CHECKOUT-SESSION
//   - FN-RENDER-PRODUCT-INPUT-PANEL
// key_flows:
//   - TOKEN_RESOLUTION -> restore draft -> resume/create redirect
//   - CTA_PRIMARY -> checkout/create button events and provider transitions
//   - CTA_CANCEL -> back/catalog escape routes
//   - PRODUCT_INPUT_SYN -> synastry/solar product input hydration and payload sync
// owned_tests:
//   - frontend/e2e/report-create.spec.ts
//   - frontend/e2e/report-failure.spec.ts
// adjacent_modules:
//   - frontend/components/catalog/catalog-analytics.ts
//   - frontend/components/catalog/catalog-checkout-resume.tsx
//   - frontend/lib/home-analytics.ts
// END_MODULE_MAP: M-CREATE-CHECKOUT

function appendQueryParam(path: string, key: string, value: string): string {
  const glue = path.includes("?") ? "&" : "?";
  return `${path}${glue}${key}=${encodeURIComponent(value)}`;
}

function toSemanticBlock(blockId: string): string {
  return `CREATE_PAGE:${blockId}`;
}

function makeCreateTrace(
  contract: string,
  block: string,
  correlationId: string,
  meta: CatalogEventPayload = {},
) {
  return withCatalogTrace(
    {
      surface: "create",
      flow_id: "FLOW-FORECAST-CATALOG",
      ...meta,
    },
    {
      module: CATALOG_GRACE_MODULES.createCheckout,
      contract,
      block,
      semantic_block: toSemanticBlock(block),
      correlation_id: correlationId,
    },
  );
}

function CreatePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, initData, mode, isReady } = useTelegram();

  const type = searchParams.get("type");
  const checkoutToken = searchParams.get("checkout");
  const entryPoint = searchParams.get("entry_point");
  const entrySemanticBlock = searchParams.get("entry_semantic_block");
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

  const correlationIdRef = useRef<string | null>(null);
  if (!correlationIdRef.current) {
    const flowName = checkoutToken ? "catalog_checkout_resume" : "catalog_checkout";
    correlationIdRef.current = CorrelationManager.newCorrelation(flowName);
  }

  // START_CONTRACT: FN-ENSURE-CORRELATION-ID
  // purpose: Resolve stable create-page correlation id for strict GRACE trace continuity.
  // inputs: none.
  // outputs: correlation id string reused across checkout/create/resume events.
  // trace_obligations: stamps FLOW-FORECAST-CATALOG telemetry with correlation continuity.
  // END_CONTRACT: FN-ENSURE-CORRELATION-ID
  const ensureCorrelationId = () => {
    // START_BLOCK: TOKEN_RESOLUTION
    if (!correlationIdRef.current) {
      correlationIdRef.current = CorrelationManager.ensureCorrelationId();
    }
    return correlationIdRef.current;
    // END_BLOCK: TOKEN_RESOLUTION
  };

  type FetchInput = Parameters<typeof fetch>[0];
  const fetchWithCorrelation = (input: FetchInput, init?: RequestInit) =>
    correlatedFetch(input, init, { correlationId: ensureCorrelationId() });

  // START_CONTRACT: FN-LOG-UI-ERROR
  // purpose: Emit strict block-aware create-page error telemetry.
  // inputs: action, error, optional metadata, optional block id.
  // outputs: async analytics dispatch via catalog telemetry pipeline.
  // END_CONTRACT: FN-LOG-UI-ERROR
  const logUiError = (
    action: string,
    error: unknown,
    extra?: Record<string, unknown>,
    blockId?: string,
  ) => {
    const message = error instanceof Error ? error.message : String(error);
    const correlationId = ensureCorrelationId();
    const block = blockId ?? action.toUpperCase();
    void trackCatalogEvent(
      "ui.error",
      makeCreateTrace("FN-LOG-UI-ERROR", block, correlationId, {
        action,
        message,
        ...extra,
      }),
      {
        correlationId,
        flowId: "FLOW-FORECAST-CATALOG",
        block,
      },
    );
  };

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
  const checkoutMode = resolveCheckoutMode({
    isReportUnlockCheckout: shouldShowOneOffReportUnlockPaywall,
    isHorary,
  });
  const analyticsFlags = normalizeCatalogFlags({
    has_subscription_access: hasResolvedReportAccess,
    has_one_off_unlock: hasOneOffUnlock,
    report_unlock_bridge: isReportUnlockBridge,
    should_show_one_off_paywall: shouldShowOneOffReportUnlockPaywall,
  });

  useEffect(() => {
    setCatalogAnalyticsContext({
      user_id: user?.id ?? null,
      checkout_token: checkoutToken,
      correlation_id: ensureCorrelationId(),
      flow_id: "FLOW-FORECAST-CATALOG",
      flags: analyticsFlags,
    });
  }, [analyticsFlags, checkoutToken, entryPoint, entrySemanticBlock, user?.id]);

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
        const response = await fetchWithCorrelation(url.toString(), {
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
        logUiError("profile_load", loadError);
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

    fetchWithCorrelation("/api/billing/packs")
      .then((res) => res.json())
      .then(setApiPacks)
      .catch((packError) => {
        logUiError("billing_packs_load", packError);
      });
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
    // START_BLOCK: CREATE_REPORT_GUARDS
    const createPayload = payloadOverride || buildCreatePayload();
    const validationError = validateCreateInputs(createPayload);
    if (validationError) {
      setError(validationError);
      void trackCatalogEvent("catalog.create_report_blocked", {
        surface: "create",
        report_type: type,
        checkout_mode: checkoutMode,
        block: "CREATE_REPORT_GUARDS",
        semantic_block: toSemanticBlock("CREATE_REPORT_GUARDS"),
      });
      return;
    }
    if (!type || !initData) {
      return;
    }
    // END_BLOCK: CREATE_REPORT_GUARDS

    // START_BLOCK: CREATE_REPORT_INIT
    setLoading(true);
    setError(null);
    void trackCatalogEvent("catalog.create_report_start", {
      surface: "create",
      report_type: type,
      checkout_mode: checkoutMode,
      block: "CREATE_REPORT_INIT",
      semantic_block: toSemanticBlock("CREATE_REPORT_INIT"),
    });
    // END_BLOCK: CREATE_REPORT_INIT

    try {
        // START_BLOCK: CREATE_REPORT_REQUEST
        const response = await fetchWithCorrelation("/api/reports/create", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Telegram-Auth": initData,
          },
          body: JSON.stringify(createPayload),
        });
        // END_BLOCK: CREATE_REPORT_REQUEST

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        void trackCatalogEvent("catalog.create_report_failed", {
          surface: "create",
          report_type: type,
          checkout_mode: checkoutMode,
          status: String(response.status),
          block: "CREATE_REPORT_RESULT_ERROR",
          semantic_block: toSemanticBlock("CREATE_REPORT_RESULT_ERROR"),
        });
        if (response.status === 402) {
          setError(formatCreateAccessError(isReportUnlockBridge));
        } else {
          setError(payload.detail || "Не удалось запустить генерацию отчета. Попробуйте позже.");
        }
        return;
      }

      // START_BLOCK: CREATE_REPORT_RESULT
      const data = await response.json();
      clearDraft();
      void trackCatalogEvent("catalog.create_report_succeeded", {
        surface: "create",
        report_type: type,
        checkout_mode: checkoutMode,
        block: "CREATE_REPORT_RESULT",
        semantic_block: toSemanticBlock("CREATE_REPORT_RESULT"),
      });

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
      // END_BLOCK: CREATE_REPORT_RESULT
      } catch (createError) {
        logUiError("create_report", createError, { report_type: type });
        void trackCatalogEvent("catalog.create_report_failed", {
          surface: "create",
          report_type: type,
          checkout_mode: checkoutMode,
          block: "CREATE_REPORT_ERROR",
          semantic_block: toSemanticBlock("CREATE_REPORT_ERROR"),
        });
        setError(createError instanceof Error ? createError.message : "Не удалось сформировать разбор.");
      } finally {
        setLoading(false);
      }
  };

  // START_CONTRACT: FN-HANDLE-CTA-PRIMARY
  // purpose: Route primary CTA clicks into create-report execution with explicit GRACE blocks.
  // inputs: button click from horary or premium unlocked states.
  // outputs: report generation side effect via handleCreateReport.
  // END_CONTRACT: FN-HANDLE-CTA-PRIMARY
  const handleHorarySubmitClick: MouseEventHandler<HTMLButtonElement> = () => {
    void trackCatalogEvent(
      "catalog.create_cta_primary",
      makeCreateTrace("FN-HANDLE-CTA-PRIMARY", "CTA_PRIMARY", ensureCorrelationId(), {
        report_type: type,
        checkout_mode: checkoutMode,
        cta_id: "create-horary-submit",
      }),
      {
        correlationId: ensureCorrelationId(),
        flowId: "FLOW-FORECAST-CATALOG",
        block: "CTA_PRIMARY",
      },
    );
    void handleCreateReport();
  };

  const handlePremiumGenerateClick: MouseEventHandler<HTMLButtonElement> = () => {
    void trackCatalogEvent(
      "catalog.create_cta_primary",
      makeCreateTrace("FN-HANDLE-CTA-PRIMARY", "CTA_PRIMARY", ensureCorrelationId(), {
        report_type: type,
        checkout_mode: checkoutMode,
        cta_id: "create-premium-generate",
      }),
      {
        correlationId: ensureCorrelationId(),
        flowId: "FLOW-FORECAST-CATALOG",
        block: "CTA_PRIMARY",
      },
    );
    void handleCreateReport();
  };

  // START_CONTRACT: FN-SYNC-CHECKOUT-SESSION
  // purpose: Resume one-off checkout, restore draft payloads, and auto-create after success.
  // inputs: checkout token, initData, hydrated product-input draft state.
  // outputs: checkout state transitions and optional read/create navigation.
  // trace_obligations: TOKEN_RESOLUTION and CTA_PRIMARY resume events stay correlated.
  // END_CONTRACT: FN-SYNC-CHECKOUT-SESSION
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
        const response = await fetchWithCorrelation(`/api/billing/sessions/${checkoutToken}`, {
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
        logUiError("checkout_session_sync", sessionError, { checkout_token: checkoutToken });
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

  // START_CONTRACT: FN-HANDLE-CHECKOUT
  // purpose: Build checkout payloads and route user into provider or mock completion.
  // inputs: current create-page state, product-input draft, pricing/runtime flags.
  // outputs: billing provider redirect, resume redirect, or immediate create-report handoff.
  // trace_obligations: CTA_PRIMARY block covers checkout init/payload/result/error events.
  // END_CONTRACT: FN-HANDLE-CHECKOUT
  const handleCheckout = async () => {
    // #START_BLOCK_CHECKOUT_GUARDS
    if (!user || !initData || !type) {
      return;
    }
    // #END_BLOCK_CHECKOUT_GUARDS

    // #START_BLOCK_CHECKOUT_INIT
    setLoading(true);
    setError(null);
    void trackCatalogEvent("catalog.checkout_handle_start", withCatalogTrace({
      surface: "create",
      report_type: type,
      checkout_mode: checkoutMode,
    }, {
      module: CATALOG_GRACE_MODULES.createCheckout,
      contract: "FN-HANDLE-CHECKOUT",
      block: CATALOG_GRACE_BLOCKS.create.checkoutInit,
      semantic_block: toSemanticBlock("CHECKOUT_INIT"),
      correlation_id: ensureCorrelationId(),
    }));
    // #END_BLOCK_CHECKOUT_INIT

    try {
      // #START_BLOCK_CHECKOUT_PAYLOAD
      const isReportUnlockCheckout = shouldShowOneOffReportUnlockPaywall;
      const reportUnlockDraftPayload = isReportUnlockCheckout ? buildCreatePayload() : null;
      const payload: Record<string, unknown> = {
        description: `Оплата: ${meta?.label || type}`,
        is_recurring: !isHorary && !isReportUnlockCheckout,
        product_type: isReportUnlockCheckout ? type : isHorary ? "horary" : "subscription",
        consent_flow: "create_checkout",
        consent_accepted: true,
        legal_versions: {
          terms: "offer_terms_ru_2026-04-01",
          privacy: "privacy_policy_ru_2026-04-01",
          data_processing: "data_processing_consent_ru_2026-04-01",
          payments: "payments_refunds_ru_2026-04-01",
        },
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

      void trackCatalogEvent("catalog.checkout_payload_ready", withCatalogTrace({
        surface: "create",
        report_type: type,
        checkout_mode: checkoutMode,
      }, {
        module: CATALOG_GRACE_MODULES.createCheckout,
        contract: "FN-HANDLE-CHECKOUT",
        block: CATALOG_GRACE_BLOCKS.create.checkoutPayload,
        semantic_block: toSemanticBlock("CHECKOUT_PAYLOAD"),
        correlation_id: ensureCorrelationId(),
      }));
      // #END_BLOCK_CHECKOUT_PAYLOAD

      // #START_BLOCK_CHECKOUT_REQUEST
      const response = await fetchWithCorrelation("/api/billing/pay", {
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
      // #END_BLOCK_CHECKOUT_REQUEST

      // #START_BLOCK_CHECKOUT_RESULT
      if (data.url) {
        void trackCatalogEvent("catalog.checkout_provider_redirect", withCatalogTrace({
          surface: "create",
          report_type: type,
          checkout_mode: checkoutMode,
        }, {
          module: CATALOG_GRACE_MODULES.createCheckout,
          contract: "FN-HANDLE-CHECKOUT",
          block: CATALOG_GRACE_BLOCKS.create.checkoutRedirect,
          semantic_block: toSemanticBlock("CHECKOUT_RESULT_REDIRECT"),
          correlation_id: ensureCorrelationId(),
        }));
        window.location.href = data.url;
        return;
      }

      if (!data.mock) {
        void trackCatalogEvent("catalog.checkout_provider_wait", withCatalogTrace({
          surface: "create",
          report_type: type,
          checkout_mode: checkoutMode,
        }, {
          module: CATALOG_GRACE_MODULES.createCheckout,
          contract: "FN-HANDLE-CHECKOUT",
          block: CATALOG_GRACE_BLOCKS.create.checkoutProvider,
          semantic_block: toSemanticBlock("CHECKOUT_RESULT_PROVIDER"),
          correlation_id: ensureCorrelationId(),
        }));
        return;
      }

      void trackCatalogEvent("catalog.mock_payment_success", makeCreateTrace("FN-HANDLE-CHECKOUT", "CTA_PRIMARY", ensureCorrelationId(), {
        report_type: type,
        checkout_mode: checkoutMode,
        status: "mock_success",
        metadata: { product: type || payload.pack_id },
      }), {
        correlationId: ensureCorrelationId(),
        flowId: "FLOW-FORECAST-CATALOG",
        block: "CTA_PRIMARY",
      });

      if (isReportUnlockCheckout && data.checkout_token) {
        const billingCompleteUrl = new URL("/billing/complete", window.location.origin);
        billingCompleteUrl.searchParams.set("checkout", data.checkout_token);
        if (mode === "mock" || mockQueryEnabled) {
          billingCompleteUrl.searchParams.set("mock", "1");
          billingCompleteUrl.searchParams.set("runtime", "1");
        }
        void trackCatalogEvent("catalog.checkout_resume_redirect", withCatalogTrace({
          surface: "create",
          report_type: type,
          checkout_mode: checkoutMode,
          checkout_token: data.checkout_token,
        }, {
          module: CATALOG_GRACE_MODULES.createCheckout,
          contract: "FN-HANDLE-CHECKOUT",
          block: CATALOG_GRACE_BLOCKS.create.checkoutResume,
          semantic_block: toSemanticBlock("CHECKOUT_RESULT_RESUME"),
          correlation_id: ensureCorrelationId(),
        }));
        router.push(`${billingCompleteUrl.pathname}${billingCompleteUrl.search}`);
        return;
      }

      if (isHorary && effectiveProfile?.can_ask_horary === false && payload.pack_id) {
        const url = new URL("/api/users/me", window.location.origin);
        const profileResponse = await fetchWithCorrelation(url.toString(), {
          headers: { "X-Telegram-Auth": initData },
        });
        const nextProfile = (await profileResponse.json()) as CreateProfile;
        setProfile(nextProfile);
        setProfileResolved(true);
        setLoading(false);
        return;
      }

      await handleCreateReport();
      // #END_BLOCK_CHECKOUT_RESULT
    } catch (payError) {
      // #START_BLOCK_CHECKOUT_ERROR
      void trackCatalogEvent("catalog.checkout_handle_error", {
        surface: "create",
        report_type: type,
        checkout_mode: checkoutMode,
        block: "CHECKOUT_ERROR",
        semantic_block: toSemanticBlock("CHECKOUT_ERROR"),
      });
      logUiError("billing_pay", payError, { report_type: type }, "CHECKOUT_ERROR");
      setError("Произошла ошибка при инициализации оплаты. Попробуйте еще раз.");
      // #END_BLOCK_CHECKOUT_ERROR
    } finally {
      setLoading(false);
    }
  };

  // START_CONTRACT: FN-RENDER-PRODUCT-INPUT-PANEL
  // purpose: Render semantic product-input wrappers for synastry/solar create flows.
  // inputs: current product type, draft state, profile fallback.
  // outputs: semantic section wrappers with stable data-testid selectors.
  // trace_obligations: PRODUCT_INPUT_SYN block names remain addressable in DOM/telemetry.
  // END_CONTRACT: FN-RENDER-PRODUCT-INPUT-PANEL
  const renderProductInputPanel = () => {
    if (isSynastry) {
      return (
        <section
          aria-label="Partner compatibility inputs"
          data-grace-block="PRODUCT_INPUT_SYN"
          data-testid="create-synastry-block"
          className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
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
          <div className="space-y-3" data-testid="create-product-input-group-synastry">
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
        </section>
      );
    }

    if (isSolarReturn) {
      const fallbackLabel =
        effectiveProfile?.current_location || effectiveProfile?.birth_place || "текущую локацию из профиля";

      return (
        <section
          aria-label="Solar return inputs"
          data-grace-block="PRODUCT_INPUT_SYN"
          data-testid="create-solar-block"
          className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
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
          <div data-testid="create-product-input-group-solar">
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
        </section>
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
      <main
        data-testid="create-loading"
        aria-busy="true"
        className="flex min-h-screen items-center justify-center bg-slate-50 font-light text-slate-400"
      >
        <Loader2 className="mr-2 animate-spin text-purple-400" />
        Загрузка...
      </main>
    );
  }

  if (error && !effectiveProfile) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-[#fdfbf7] p-10 text-center">
        <section className="max-w-sm rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600">
          {error}
        </section>
      </main>
    );
  }

  if (!type) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-[#fdfbf7] p-10 text-center">
        <section aria-labelledby="create-empty-state-heading" className="flex w-full max-w-sm flex-col items-center">
        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-slate-100 text-slate-300">
          <ArrowLeft size={32} />
        </div>
        <h1 id="create-empty-state-heading" className="mb-2 text-2xl font-black text-slate-800">Продукт не выбран</h1>
        <p className="mx-auto mb-8 max-w-xs text-slate-500">
          Пожалуйста, выберите интересующий вас разбор в каталоге предложений.
        </p>
        <div className="flex w-full max-w-xs flex-col gap-3" data-testid="create-empty-state-actions">
          <Link
            href="/reports"
            data-grace-block="CTA_CANCEL"
            data-testid="create-empty-state-catalog"
            className="w-full rounded-2xl bg-slate-900 py-4 text-center font-bold text-white shadow-lg shadow-slate-200 transition-all active:scale-95"
          >
            Перейти в каталог
          </Link>
          <button
            onClick={() => router.back()}
            data-grace-block="CTA_CANCEL"
            data-testid="create-empty-state-back"
            className="w-full rounded-2xl border border-slate-100 bg-white py-4 text-center font-bold text-slate-500 transition-all active:scale-95"
          >
            Назад
          </button>
        </div>
        </section>
      </main>
    );
  }

  if (isHorary && canAskFree) {
    return (
      <main data-testid="create-page" className="min-h-screen space-y-6 bg-slate-50 px-6 pb-24 pt-6">
        <header>
          <h1 className="text-2xl font-black text-slate-900">Задать вопрос</h1>
        </header>
        <section aria-label="Horary question form" className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            data-testid="create-horary-textarea"
            placeholder="Например: Стоит ли мне менять работу сейчас?"
            className="h-32 w-full resize-none rounded-xl border-none bg-slate-50 p-3 text-slate-800 focus:ring-2 focus:ring-purple-200"
          />
        </section>
        {error && (
          <section className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600">
            {error}
          </section>
        )}
        <section aria-label="Create horary primary action" data-grace-block="CTA_PRIMARY" data-testid="create-footer-cta" className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-white via-white/90 to-transparent p-6">
          <button
            onClick={handleHorarySubmitClick}
            disabled={loading || !question.trim()}
            data-testid="create-horary-submit"
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 font-bold text-white shadow-xl shadow-purple-200 disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <ShieldCheck size={20} />}
            Получить ответ
          </button>
        </section>
      </main>
    );
  }

  if (canGeneratePremium) {
    return (
      <main data-testid="create-page" className="min-h-screen space-y-6 bg-slate-50 px-6 pb-24 pt-6">
        <header>
          <h1 className="text-2xl font-black text-slate-900">Сформировать разбор</h1>
        </header>
        <section aria-label="Premium offer summary" className="flex items-center justify-between rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
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
        </section>
        {renderCheckoutStatusPanel()}
        {hasOneOffUnlock && (
          <section
            data-testid="create-one-off-unlock-note"
            className="rounded-3xl border border-emerald-100 bg-white p-5 shadow-sm"
          >
            <p className="text-sm font-semibold text-slate-800">
              Доступно разблокировок: {availableUnlocks}
            </p>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Этот разбор можно собрать без новой оплаты. Если генерация завершится ошибкой, повторный платёж не потребуется.
            </p>
          </section>
        )}
        {error && (
          <section className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600">
            {error}
          </section>
        )}
        {renderProductInputPanel()}
        <section aria-label="Create premium primary action" data-grace-block="CTA_PRIMARY" data-testid="create-footer-cta" className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-white via-white/90 to-transparent p-6">
          <button
            onClick={handlePremiumGenerateClick}
            disabled={loading}
            data-testid="create-premium-generate"
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 font-bold text-white shadow-xl shadow-purple-200"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
            {hasOneOffUnlock ? "Сформировать по разблокировке" : "Сформировать за 0₽"}
          </button>
        </section>
      </main>
    );
  }

  return (
    <main data-testid="create-page" className="min-h-screen space-y-6 bg-slate-50 px-6 pb-24 pt-6">
      <header>
        <h1 className="text-2xl font-black text-slate-900">
          {isHorary
            ? "Купить вопросы"
            : shouldShowOneOffReportUnlockPaywall
              ? "Разовая разблокировка"
              : isSubscriptionProduct
                ? "Подписка GRACE"
                : "Оформление заказа"}
        </h1>
      </header>
      {renderCheckoutStatusPanel()}
      {isHorary && apiPacks ? (
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
      ) : (
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
                В этом slice разбор открывается одной разовой оплатой без подписки и trial.
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
                Этот разбор в текущем публичном контуре оформляется как разовая покупка.
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                После оплаты откроются персональные разборы: Натал, Неделя, Месяц, Год, Соляр и Совместимость.
              </p>
            </div>
          ) : null}
        </section>
      )}
      {error && (
        <div className="animate-in fade-in slide-in-from-top-2 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm font-medium text-red-600 duration-300">
          {error}
        </div>
      )}
      {renderProductInputPanel()}
      <section aria-label="Checkout primary action" data-grace-block="CTA_PRIMARY" data-testid="create-footer-cta" className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-white via-white/90 to-transparent p-6">
        <button
          onClick={handleCheckout}
          disabled={loading || checkoutBusy}
          data-testid="create-checkout-submit"
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 font-bold text-white shadow-xl shadow-purple-200 disabled:opacity-60"
        >
          {loading || checkoutBusy ? <Loader2 className="animate-spin" size={20} /> : <CreditCard size={20} />}
          {isHorary && apiPacks
            ? `Оплатить ${selectedPackPriceLabel}`
            : shouldShowOneOffReportUnlockPaywall
              ? `Оплатить ${getReportUnlockPriceLabel(type)}`
              : isSubscriptionProduct
                ? `Оплатить разово ${runtimePriceLabel}`
                : `Оплатить ${HORARY_PRICE_LABEL}`}
        </button>
      </section>
    </main>
  );
}

export default function CreatePageClient() {
  return <CreatePageContent />;
}
