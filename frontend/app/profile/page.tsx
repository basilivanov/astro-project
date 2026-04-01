"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { User as UserIcon, Settings, Clock, ShieldQuestion, ChevronRight, Copy, Check, Gift } from "lucide-react";
import Link from "next/link";

import { LoadingState } from "../../components/ui-states";
import {
  setCatalogAnalyticsContext,
  startCatalogCorrelation,
  trackCatalogEvent,
} from "../../components/catalog/catalog-analytics";
import { useTelegram } from "../../hooks/useTelegram";
import { CorrelationManager, correlatedFetch } from "../../lib/correlation";
import { LegalFooterBlock } from "../../components/legal-links";

type ProfileData = {
  full_name: string;
  telegram_id: number;
  days_left: number;
  is_partner: boolean;
  referral_code: string;
  subscription_active_until: string;
};

type AudienceMode = "client" | "admin";

type MenuLinkProps = {
  href: string;
  icon: typeof Clock;
  label: string;
  analyticsCtaId: string;
  correlationId: string;
};

const buildMockProfile = (): ProfileData => ({
  full_name: "Debug User",
  telegram_id: 123456789,
  days_left: 7,
  is_partner: false,
  referral_code: "DEBUG123",
  subscription_active_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
});

const VASILY_CHAT_IDS = new Set<number>([123456789]);
const AUDIENCE_STORAGE_KEY = "profile_audience_mode";

// START_MODULE_CONTRACT: M-PROFILE-PAGE
// purpose: Render the profile overview with strict-GRACE semantics and correlation-aware telemetry.
// owns:
//   - frontend/app/profile/page.tsx
// inputs:
//   - Telegram runtime session, profile API payload, clipboard interaction
// outputs:
//   - profile overview UI with referral CTA and navigation links
//   - correlation-aware catalog analytics for profile surface actions
// dependencies:
//   - ../../hooks/useTelegram
//   - ../../components/catalog/catalog-analytics
//   - ../../lib/correlation
// invariants:
//   - profile telemetry uses `trackCatalogEvent` with `surface: "profile"`
//   - UX copy and primary layout remain unchanged
// non_goals:
//   - editing profile fields or handling backend profile mutations
// END_MODULE_CONTRACT: M-PROFILE-PAGE

// START_MODULE_MAP: M-PROFILE-PAGE
// entrypoints:
//   - ProfilePage (default export)
// helpers:
//   - buildMockProfile
//   - MenuLink
// owned_tests:
//   - frontend/e2e/core-ux.spec.ts
// adjacent_modules:
//   - frontend/app/profile/edit/page.tsx
//   - frontend/components/catalog/catalog-analytics.ts
//   - frontend/hooks/useTelegram.ts
// END_MODULE_MAP: M-PROFILE-PAGE

export default function ProfilePage() {
  const { user, initData, mode, isReady } = useTelegram();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [copied, setCopied] = useState(false);
  const [audienceMode, setAudienceMode] = useState<AudienceMode>("client");
  const correlationIdRef = useRef<string | null>(null);

  if (!correlationIdRef.current) {
    correlationIdRef.current = startCatalogCorrelation("profile_page");
  }

  const ensureCorrelationId = () => {
    if (!correlationIdRef.current) {
      correlationIdRef.current = CorrelationManager.ensureCorrelationId();
    }
    return correlationIdRef.current;
  };

  type FetchInput = Parameters<typeof fetch>[0];
  const fetchWithCorrelation = (input: FetchInput, init?: RequestInit) =>
    correlatedFetch(input, init, { correlationId: ensureCorrelationId() });

  const logProfileError = (action: string, error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    void trackCatalogEvent(
      "catalog.profile_error",
      {
        surface: "profile",
        action,
        status: "error",
        message,
        block: "profile_data_flow",
      },
      { correlationId: ensureCorrelationId() },
    );
  };

  useEffect(() => {
    // START_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
    setCatalogAnalyticsContext({
      user_id: user?.id,
      correlation_id: ensureCorrelationId(),
    });
    // END_BLOCK: ANALYTICS_CONTEXT_BOOTSTRAP
  }, [user]);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    // START_BLOCK: PROFILE_DATA_FLOW
    void trackCatalogEvent(
      "catalog.profile_view",
      {
        surface: "profile",
        action: mode === "mock" ? "view_mock" : "view_live",
        block: "profile_data_flow",
      },
      { correlationId: ensureCorrelationId() },
    );

    if (mode === "mock") {
      setProfile(buildMockProfile());
      return;
    }

    if (user && initData) {
      fetchWithCorrelation("/api/users/me", { headers: { "X-Telegram-Auth": initData } })
        .then((res) => res.json())
        .then((data: ProfileData) => {
          setProfile(data);
          void trackCatalogEvent(
            "catalog.profile_loaded",
            {
              surface: "profile",
              action: "profile_load",
              status: "success",
              block: "profile_data_flow",
            },
            { correlationId: ensureCorrelationId() },
          );
        })
        .catch((error) => {
          logProfileError("profile_load", error);
        });
    }
    // END_BLOCK: PROFILE_DATA_FLOW
  }, [user, initData, mode, isReady]);

  const isVasilyProfile = useMemo(() => {
    const telegramId = profile?.telegram_id ?? user?.id ?? null;
    if (telegramId && VASILY_CHAT_IDS.has(telegramId)) {
      return true;
    }

    if (typeof window === "undefined") {
      return false;
    }

    return window.localStorage.getItem("force_vasily_profile") === "1";
  }, [profile?.telegram_id, user?.id]);

  useEffect(() => {
    if (!isVasilyProfile || typeof window === "undefined") {
      return;
    }

    const persistedMode = window.localStorage.getItem(AUDIENCE_STORAGE_KEY);
    if (persistedMode === "admin" || persistedMode === "client") {
      setAudienceMode(persistedMode);
    }
  }, [isVasilyProfile]);

  const handleAudienceSwitch = (nextMode: AudienceMode) => {
    setAudienceMode(nextMode);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(AUDIENCE_STORAGE_KEY, nextMode);
    }
    void trackCatalogEvent(
      "catalog.profile_mode_switch",
      {
        surface: "profile",
        action: "toggle_mode",
        mode: nextMode,
        block: "profile_mode_switch",
      },
      { correlationId: ensureCorrelationId() },
    );
  };

  const copyLink = async () => {
    if (!user || !profile?.referral_code) {
      return;
    }

    // START_BLOCK: REFERRAL_CTA
    const link = `https://t.me/AstroGraceBot?start=ref_${profile.referral_code}`;
    await navigator.clipboard.writeText(link);
    setCopied(true);
    void trackCatalogEvent(
      "catalog.profile_referral_copy",
      {
        surface: "profile",
        action: "copy_referral_link",
        cta_id: "profile_referral_copy",
        status: "success",
        block: "referral_cta",
      },
      { correlationId: ensureCorrelationId() },
    );
    setTimeout(() => setCopied(false), 2000);
    // END_BLOCK: REFERRAL_CTA
  };

  if (!isReady || !profile) {
    return <LoadingState />;
  }

  const correlationId = ensureCorrelationId();

  return (
    <main data-testid="profile-content" className="p-6 space-y-8 pt-10 pb-32" suppressHydrationWarning>
      <section className="flex items-center gap-5" aria-label="Профиль пользователя">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-100 to-white flex items-center justify-center text-3xl font-bold text-purple-400 overflow-hidden ring-4 ring-purple-50">
          {user?.photo_url ? <img src={user.photo_url} alt="" /> : (user?.first_name?.[0] || "U")}
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">{profile.full_name}</h1>
          <p className="text-slate-400 text-xs font-medium uppercase mt-1">ID: {profile.telegram_id}</p>
        </div>
      </section>

      <section className="bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-3xl p-7 text-white shadow-xl" aria-label="Статус подписки">
        <p className="text-purple-100 text-xs font-bold uppercase tracking-widest mb-2">Premium</p>
        <div className="flex items-baseline gap-1 my-3">
          <span className="text-5xl font-black tracking-tighter">{profile.days_left}</span>
          <span className="text-lg opacity-80 font-medium">дней</span>
        </div>
      </section>

      <section className="bg-white rounded-3xl p-6 border border-purple-50 shadow-lg relative overflow-hidden" aria-label="Реферальная программа">
        <div className="flex items-center gap-4 mb-5 relative z-10">
          <div className="w-12 h-12 bg-orange-50 text-orange-500 rounded-2xl flex items-center justify-center"><Gift size={24} /></div>
          <div>
            <h2 className="font-bold text-slate-800 text-lg">Подарок за друга</h2>
            <p className="text-sm text-slate-500 mt-0.5">+14 дней бесплатно</p>
          </div>
        </div>
        <button onClick={() => void copyLink()} className="w-full bg-slate-50 text-slate-600 font-medium py-3.5 rounded-xl border border-slate-100">
          {copied ? <span className="text-green-600">Ссылка скопирована</span> : "Копировать ссылку"}
        </button>
      </section>

      {isVasilyProfile ? (
        <section
          data-testid="profile-audience-switcher"
          className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          aria-label="Режим Василия"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-400">Режим работы</p>
              <h2 className="mt-2 text-lg font-bold text-slate-800">Клиент / Админ</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                Быстро переключай сценарий: как клиент покупать продления и отчёты, как админ — открывать выдачу и контроль заказов.
              </p>
            </div>
            <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
              chat_id {profile.telegram_id}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            {(["client", "admin"] as const).map((nextMode) => {
              const active = audienceMode === nextMode;
              const title = nextMode === "client" ? "Клиент" : "Админ";
              const desc = nextMode === "client"
                ? "Продление подписки и покупка отчётов"
                : "Выдача отчётов и контроль заказов";

              return (
                <button
                  key={nextMode}
                  type="button"
                  onClick={() => handleAudienceSwitch(nextMode)}
                  className={`rounded-2xl border px-4 py-4 text-left transition ${active ? "border-violet-500 bg-violet-50 text-violet-900" : "border-slate-200 bg-slate-50 text-slate-600"}`}
                  aria-pressed={active}
                >
                  <div className="text-sm font-bold">{title}</div>
                  <div className="mt-1 text-xs leading-relaxed opacity-80">{desc}</div>
                </button>
              );
            })}
          </div>

          <div
            data-testid="profile-audience-cta"
            className="mt-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-600"
          >
            {audienceMode === "client" ? (
              <>
                Для продления подписки и покупки разовых отчётов открой <Link className="font-semibold text-violet-700" href="/reports">магазин</Link>.
              </>
            ) : (
              <>
                Для выдачи отчётов и ручного контроля открой <Link className="font-semibold text-violet-700" href="/admin/reports">админ-выдачу</Link>.
              </>
            )}
          </div>
        </section>
      ) : null}

      <nav className="space-y-3" aria-label="Разделы профиля">
        <MenuLink href="/reports/history" icon={Clock} label="История заказов" analyticsCtaId="profile_history" correlationId={correlationId} />
        <MenuLink href="/support" icon={ShieldQuestion} label="Поддержка" analyticsCtaId="profile_support" correlationId={correlationId} />
        <MenuLink href="/profile/edit" icon={Settings} label="Настройки" analyticsCtaId="profile_settings" correlationId={correlationId} />
      </nav>
    
      <section className="rounded-3xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-600 shadow-sm" aria-label="Юридическая информация">
        <p className="text-xs font-bold uppercase tracking-[0.24em] text-slate-500">Legal</p>
        <LegalFooterBlock className="mt-3" />
      </section>
</main>
  );
}

function MenuLink({ icon: Icon, label, href, analyticsCtaId, correlationId }: MenuLinkProps) {
  const handleClick = () => {
    void trackCatalogEvent(
      "catalog.profile_navigation_click",
      {
        surface: "profile",
        action: "navigate",
        cta_id: analyticsCtaId,
        cta_href: href,
        block: "profile_navigation",
      },
      { correlationId },
    );
  };

  return (
    <Link href={href} onClick={handleClick} className="flex items-center justify-between p-4 rounded-2xl bg-white border border-slate-50 shadow-sm transition-all active:scale-[0.98]">
      <div className="flex items-center gap-4">
        <div className="p-2 rounded-xl bg-slate-50 text-slate-400"><Icon size={20} /></div>
        <span className="font-medium text-slate-700">{label}</span>
      </div>
      <ChevronRight size={18} className="text-slate-300" />
    </Link>
  );
}
