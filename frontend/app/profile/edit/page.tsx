"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Save } from "lucide-react";

import GeoAutocomplete from "../../../components/GeoAutocomplete";
import { EmptyState, ErrorState, LoadingState } from "../../../components/ui-states";
import { ConsumerPageShell, ConsumerPanel } from "../../../components/consumer-page-shell";
import {
  setCatalogAnalyticsContext,
  startCatalogCorrelation,
  trackCatalogEvent,
} from "../../../components/catalog/catalog-analytics";
import { useTelegram } from "../../../hooks/useTelegram";
import { CorrelationManager, correlatedFetch } from "../../../lib/correlation";

type EditableProfile = {
  full_name: string;
  birth_date: string;
  birth_time: string;
  birth_time_known: boolean;
  birth_place: string;
  birth_lat: number;
  birth_lon: number;
  birth_timezone: string;
  sun_sign: string;
};

const ZODIAC_SIGNS = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
];

const EMPTY_PROFILE_FORM: EditableProfile = {
  full_name: "",
  birth_date: "",
  birth_time: "12:00",
  birth_time_known: true,
  birth_place: "",
  birth_lat: 0,
  birth_lon: 0,
  birth_timezone: "",
  sun_sign: "",
};

// START_MODULE_CONTRACT: M-PROFILE-EDIT-PAGE
// purpose: Render profile editing form with strict-GRACE semantic blocks and correlation-aware telemetry.
// owns:
//   - frontend/app/profile/edit/page.tsx
// inputs:
//   - Telegram session, profile API payload, geo autocomplete selections, form edits
// outputs:
//   - persisted profile changes and profile-edit telemetry
// dependencies:
//   - ../../../hooks/useTelegram
//   - ../../../components/catalog/catalog-analytics
//   - ../../../components/GeoAutocomplete
//   - ../../../lib/correlation
// invariants:
//   - profile edit telemetry uses `trackCatalogEvent` with `surface: "profile_edit"`
//   - page keeps current UX, copy, and form fields unchanged
// non_goals:
//   - changing profile overview UX or catalog checkout flows
// END_MODULE_CONTRACT: M-PROFILE-EDIT-PAGE

// START_MODULE_MAP: M-PROFILE-EDIT-PAGE
// entrypoints:
//   - ProfileEditPage (default export)
// helpers:
//   - EMPTY_PROFILE_FORM
// owned_tests:
//   - frontend/e2e/profile-edit.spec.ts
//   - frontend/e2e/profile.referral.spec.ts
// adjacent_modules:
//   - frontend/app/profile/page.tsx
//   - frontend/components/catalog/catalog-analytics.ts
//   - frontend/hooks/useTelegram.ts
// END_MODULE_MAP: M-PROFILE-EDIT-PAGE

export default function ProfileEditPage() {
  const { user, initData, isReady, mode } = useTelegram();
  const isMockHelperLane = mode === "mock";
  const isCanonicalTelegramLane = mode === "telegram" && Boolean(user) && Boolean(initData);
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<EditableProfile | null>(null);
  const [form, setForm] = useState<EditableProfile>(EMPTY_PROFILE_FORM);
  const [pageState, setPageState] = useState<"loading" | "ready" | "auth_required" | "error">("loading");
  const [pageError, setPageError] = useState<string | null>(null);
  const correlationIdRef = useRef<string | null>(null);

  if (!correlationIdRef.current) {
    correlationIdRef.current = startCatalogCorrelation("profile_edit_page");
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

  const logProfileEditError = (action: string, error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    setPageError(message);
    setPageState("error");
    void trackCatalogEvent(
      "catalog.profile_edit_error",
      {
        surface: "profile_edit",
        action,
        status: "error",
        message,
        block: "profile_edit_data_flow",
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

    // START_BLOCK: PROFILE_EDIT_DATA_FLOW
    void trackCatalogEvent(
      "catalog.profile_edit_view",
      {
        surface: "profile_edit",
        action: isMockHelperLane ? "view_helper_mock" : isCanonicalTelegramLane ? "view_live" : "view_auth_gate",
        block: "profile_edit_data_flow",
      },
      { correlationId: ensureCorrelationId() },
    );

    if (!isCanonicalTelegramLane && !isMockHelperLane) {
      setProfile(null);
      setPageError(null);
      setPageState("auth_required");
      return;
    }

    if (user && initData) {
      setPageState("loading");
      setPageError(null);
      fetchWithCorrelation("/api/users/me", { headers: { "X-Telegram-Auth": initData } })
        .then((res) => res.json())
        .then((data: EditableProfile) => {
          setProfile(data);
          setForm({
            full_name: data.full_name || "",
            birth_date: data.birth_date || "",
            birth_time: data.birth_time || "12:00",
            birth_time_known: data.birth_time_known ?? true,
            birth_place: data.birth_place || "",
            birth_lat: data.birth_lat || 0,
            birth_lon: data.birth_lon || 0,
            birth_timezone: data.birth_timezone || "",
            sun_sign: data.sun_sign || "",
          });
          setPageState("ready");
          void trackCatalogEvent(
            "catalog.profile_edit_loaded",
            {
              surface: "profile_edit",
              action: "profile_load",
              status: "success",
              block: "profile_edit_data_flow",
            },
            { correlationId: ensureCorrelationId() },
          );
        })
        .catch((error) => {
          logProfileEditError("profile_load", error);
        });
    }
    // END_BLOCK: PROFILE_EDIT_DATA_FLOW
  }, [user, initData, isCanonicalTelegramLane, isMockHelperLane, isReady]);

  const handleSave = async () => {
    if ((!isCanonicalTelegramLane && !isMockHelperLane) || !user || !initData) {
      return;
    }

    // START_BLOCK: PROFILE_SAVE_FLOW
    setLoading(true);
    void trackCatalogEvent(
      "catalog.profile_edit_save_start",
      {
        surface: "profile_edit",
        action: "profile_save",
        cta_id: "profile_edit_save",
        block: "profile_save_flow",
      },
      { correlationId: ensureCorrelationId() },
    );

    try {
      const currentTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const res = await fetchWithCorrelation("/api/users/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Telegram-Auth": initData,
        },
        body: JSON.stringify({ ...form, current_timezone: currentTz }),
      });

      if (res.ok) {
        void trackCatalogEvent(
          "catalog.profile_edit_save_success",
          {
            surface: "profile_edit",
            action: "profile_save",
            status: "success",
            cta_id: "profile_edit_save",
            block: "profile_save_flow",
          },
          { correlationId: ensureCorrelationId() },
        );
        router.push("/profile");
      } else {
        void trackCatalogEvent(
          "catalog.profile_edit_save_error",
          {
            surface: "profile_edit",
            action: "profile_save",
            status: "error",
            cta_id: "profile_edit_save",
            block: "profile_save_flow",
          },
          { correlationId: ensureCorrelationId() },
        );
        alert("Ошибка сохранения");
      }
    } catch (error) {
      logProfileEditError("profile_save", error);
    } finally {
      setLoading(false);
    }
    // END_BLOCK: PROFILE_SAVE_FLOW
  };

  if (pageState === "loading" || !isReady) {
    return <LoadingState />;
  }

  if (pageState === "auth_required") {
    return (
      <ConsumerPageShell testId="profile-edit-page">
        <ConsumerPanel className="p-5">
          <EmptyState
            compact
            title="Настройки доступны после входа через Telegram"
            message="Для редактирования профиля нужен подписанный Telegram WebApp initData. Guest и без-Telegram режимы здесь не считаются канонической auth lane."
            actionLabel="Открыть вход"
            actionHref="/start"
          />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (pageState === "error") {
    return (
      <ConsumerPageShell testId="profile-edit-page">
        <ConsumerPanel className="p-5">
          <ErrorState compact error={pageError ?? "Не удалось загрузить настройки профиля"} />
        </ConsumerPanel>
      </ConsumerPageShell>
    );
  }

  if (!profile) {
    return <LoadingState />;
  }

  return (
    <main className="p-6 space-y-6 pt-10 pb-32 bg-slate-50 min-h-screen">
      <header className="flex items-center gap-2 mb-4">
        <Link href="/profile" className="p-2 -ml-2 text-slate-400 hover:text-purple-600 transition-colors">
          <ArrowLeft size={28} strokeWidth={1.5} />
        </Link>
        <h1 className="text-2xl font-bold text-slate-800">Настройки профиля</h1>
      </header>

      <section className="space-y-4" aria-label="Форма профиля">
        <section className="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Имя</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Дата рождения</label>
            <input
              type="date"
              value={form.birth_date}
              onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
              className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800"
            />
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center ml-1">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">Время рождения</label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!form.birth_time_known}
                  onChange={(e) => setForm({ ...form, birth_time_known: !e.target.checked })}
                  className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-[10px] font-bold text-slate-500 uppercase">Неизвестно</span>
              </label>
            </div>
            {form.birth_time_known && (
              <input
                type="time"
                value={form.birth_time}
                onChange={(e) => setForm({ ...form, birth_time: e.target.value })}
                className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800 animate-in fade-in duration-200"
              />
            )}
          </div>

          {!form.birth_date && (
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Знак Зодиака (если нет даты)</label>
              <select
                value={form.sun_sign}
                onChange={(e) => setForm({ ...form, sun_sign: e.target.value })}
                className="w-full p-3 bg-slate-50 rounded-xl border-none focus:ring-2 focus:ring-purple-200 text-slate-800 appearance-none"
              >
                <option value="">Выберите знак</option>
                {ZODIAC_SIGNS.map((sign) => <option key={sign} value={sign}>{sign}</option>)}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Место рождения</label>
            <GeoAutocomplete
              defaultValue={form.birth_place}
              onSelect={(city, lat, lon, tz) => setForm({ ...form, birth_place: city, birth_lat: lat, birth_lon: lon, birth_timezone: tz })}
            />
          </div>
        </section>
      </section>

      <footer className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-slate-50 via-slate-50/90 to-transparent z-50">
        <button
          onClick={() => void handleSave()}
          disabled={loading}
          className="w-full bg-slate-900 text-white font-bold py-4 rounded-2xl hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-xl"
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
          Сохранить изменения
        </button>
      </footer>
    </main>
  );
}
