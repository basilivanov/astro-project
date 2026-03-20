"use client";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "../hooks/useTelegram";
import { MoonCard } from "../components/MoonCard";
import { TrafficLights } from "../components/TrafficLights";
import { ArrowRight, Bug, Compass, Map, MessageCircle, Sparkles } from "lucide-react";
import Link from "next/link";
import { LandingContent } from "../components/landing/LandingContent";
import { EmptyState, ErrorState, LoadingState } from "../components/ui-states";
import { TrialStatusWidget } from "../components/TrialStatusWidget";
import {
    ConsumerHero,
    ConsumerMetaPill,
    ConsumerPageShell,
    ConsumerPanel,
    ConsumerStatusBadge,
} from "../components/consumer-page-shell";

type FeedState = "ready" | "fallback" | "empty";
type FeedLight = "green" | "yellow" | "red" | "gray";

type FastHitViewModel = { transit: string; natal: string; type: string; summary: string; orb?: number };
type FeedViewModel = {
    date: string;
    moon_sign: string;
    moon_phase: string;
    moon_emoji: string;
    general_vibe: string;
    traffic_lights: {
        health: FeedLight;
        money: FeedLight;
        love: FeedLight;
    };
    moon?: { sign?: string; phase?: string; emoji?: string };
    fast_hits?: FastHitViewModel[];
    personalization_level?: string | null;
    meta?: Record<string, unknown> | null;
};

type ProfileViewModel = {
    full_name?: string | null;
    birth_date?: string | null;
    subscription_active_until?: string | null;
    referral_code?: string | null;
};

type FeedSurfaceState = FeedState | "loading" | "error";

type MockFeedStateOverride = FeedState | "error" | undefined;

type MockWindow = Window & {
    MOCK_FEED_OVERRIDE?: unknown;
    MOCK_FEED_STATE?: MockFeedStateOverride;
    MOCK_PROFILE_OVERRIDE?: unknown;
};

const DEFAULT_VIBE = "День лучше прожить в спокойном темпе: держитесь простых решений и не перегружайте себя лишним.";
const DEFAULT_LIGHTS: FeedViewModel["traffic_lights"] = {
    health: "gray",
    money: "gray",
    love: "gray",
};

const buildMockProfile = (): ProfileViewModel => ({
    full_name: "Debug User",
    birth_date: "2000-01-01",
    subscription_active_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    referral_code: "DEBUG123",
});

const buildMockFeed = (): FeedViewModel => ({
    date: "Сегодня",
    moon_sign: "Овен",
    moon_phase: "Растущая Луна",
    moon_emoji: "🌙",
    general_vibe: "Фокус на рутине и стабильных шагах.",
    traffic_lights: { health: "green", money: "yellow", love: "red" },
    moon: { sign: "Овен", phase: "Растущая Луна", emoji: "🌙" },
    fast_hits: [{ transit: "Venus", natal: "Venus", type: "Соединение", summary: "Венера соединение Венера" }],
    personalization_level: "personalized_v2",
    meta: { cache_scope: "mock-scope", personalization_level: "personalized_v2" },
});

const FEED_GUIDANCE_STEPS = [
    {
        id: "tone",
        title: "Считайте тон дня",
        description: "Лунный ориентир задаёт общий темп и помогает не тратить внимание на лишнее.",
        icon: Sparkles,
        iconClassName: "bg-indigo-50 text-indigo-600",
    },
    {
        id: "priorities",
        title: "Проверьте три сферы",
        description: "Светофор быстро показывает, где можно усиливать действия, а где лучше держать запас.",
        icon: Compass,
        iconClassName: "bg-amber-50 text-amber-600",
    },
    {
        id: "deeper",
        title: "Углубляйтесь по задаче",
        description: "Если нужен не фон дня, а решение по теме, переходите в хорар или полный каталог разборов.",
        icon: ArrowRight,
        iconClassName: "bg-emerald-50 text-emerald-600",
    },
] as const;

export default function FeedPage() {
    const { user, initData, isReady, mode } = useTelegram();
    const router = useRouter();
    const [feed, setFeed] = useState<FeedViewModel | null>(null);
    const [profile, setProfile] = useState<ProfileViewModel | null>(null);
    const [feedState, setFeedState] = useState<FeedState>("ready");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const shouldShowLanding = !loading && (mode === "guest" || mode === "none" || !user || !initData);

    const loadFeedPage = async () => {
        if (!user || !initData) {
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const [profileResult, feedResult] = await Promise.allSettled([
                fetchJson("/api/users/me", { headers: { "X-Telegram-Auth": initData } }),
                fetchJson(`/api/feed/today${mode === "mock" ? "?debug=true" : ""}`, {
                    headers: mode === "mock"
                        ? { "X-Telegram-Auth": initData, "X-Feed-Debug": "1" }
                        : { "X-Telegram-Auth": initData },
                }),
            ]);

            if (profileResult.status !== "fulfilled") {
                throw new Error(toErrorMessage(profileResult.reason, "Не удалось загрузить профиль"));
            }

            const nextProfile = normalizeProfile(profileResult.value);
            setProfile(nextProfile);

            if (!nextProfile.birth_date) {
                router.push("/onboarding/profile");
                return;
            }

            if (feedResult.status === "fulfilled") {
                const nextFeed = normalizeFeed(feedResult.value);
                if (nextFeed) {
                    setFeed(nextFeed);
                    setFeedState("ready");
                } else {
                    setFeed(null);
                    setFeedState("empty");
                }
            } else {
                setFeed(buildFallbackFeed());
                setFeedState("fallback");
            }
        } catch (err) {
            setProfile(null);
            setFeed(null);
            setFeedState("empty");
            setError(toErrorMessage(err, "Не удалось загрузить астросводку"));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!isReady) return;
        if (mode === "mock") {
            const mockWindow = window as MockWindow;
            const nextProfile = normalizeMockProfile(mockWindow.MOCK_PROFILE_OVERRIDE);
            const { nextFeed, nextFeedState, nextError } = resolveMockFeedState(
                mockWindow.MOCK_FEED_STATE,
                mockWindow.MOCK_FEED_OVERRIDE,
            );

            setProfile(nextProfile);
            setFeed(nextFeed);
            setFeedState(nextFeedState);
            setError(nextError);
            setLoading(false);
            return;
        }
        if (mode === "telegram" && user && initData) {
            void loadFeedPage();
            return;
        }
        if (mode === "guest" || mode === "none" || !user || !initData) {
            setLoading(false);
            return;
        }
        void loadFeedPage();
    }, [user, initData, isReady, mode, router]);

    if (!isReady) {
        return (
            <FeedLayout state="loading">
                <ConsumerPanel className="p-5">
                    <LoadingState compact />
                </ConsumerPanel>
            </FeedLayout>
        );
    }

    if (shouldShowLanding) {
        return <LandingContent />;
    }

    if (loading) {
        return (
            <FeedLayout state="loading" profile={profile}>
                <ConsumerPanel className="p-5">
                    <LoadingState compact message="Собираем сводку дня..." />
                </ConsumerPanel>
            </FeedLayout>
        );
    }

    if (error) {
        return (
            <FeedLayout state="error" profile={profile}>
                <ConsumerPanel
                    data-testid="feed-error-state"
                    className="border-rose-100 p-5"
                >
                    <ErrorState compact error={error} onRetry={loadFeedPage} />
                </ConsumerPanel>
            </FeedLayout>
        );
    }

    if (!profile) {
        return (
            <FeedLayout state="error">
                <ConsumerPanel
                    data-testid="feed-error-state"
                    className="border-rose-100 p-5"
                >
                    <ErrorState compact error="Профиль пользователя пока недоступен." onRetry={loadFeedPage} />
                </ConsumerPanel>
            </FeedLayout>
        );
    }

    return (
        <FeedLayout state={feed ? feedState : "empty"} profile={profile} dateLabel={feed?.date || "Сегодня"}>
            {feedState === "fallback" && feed && (
                <section data-testid="feed-fallback-banner" className="rounded-[28px] border border-amber-200 bg-amber-50/90 px-4 py-4 shadow-sm">
                    <div className="flex items-start gap-3">
                        <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-amber-500 shadow-sm">
                            <Sparkles size={18} />
                        </div>
                        <div className="min-w-0">
                            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-amber-700">Резервная сводка</p>
                            <p className="mt-1 text-sm leading-relaxed text-amber-900">
                                Основная подсказка дня временно недоступна, поэтому показываем безопасный fallback без выпадения из основного сценария.
                            </p>
                        </div>
                    </div>
                </section>
            )}

            {feed ? (
                <>
                    <MoonCard sign={feed.moon_sign} phase={feed.moon_phase} emoji={feed.moon_emoji} vibe={feed.general_vibe} fastHits={feed.fast_hits} personalizationLevel={feed.personalization_level} />
                    <TrafficLights lights={feed.traffic_lights} personalizationLevel={feed.personalization_level} />
                    {feed.meta ? (
                        <section data-testid="feed-debug-panel" className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50/90 p-4 text-sm text-slate-600">
                            <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">
                                <Bug size={14} /> Internal debug
                            </div>
                            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-relaxed text-slate-700">{JSON.stringify(feed.meta, null, 2)}</pre>
                        </section>
                    ) : null}
                </>
            ) : (
                <ConsumerPanel data-testid="feed-empty-state" className="p-5">
                    <EmptyState
                        compact
                        title="Сводка дня еще не готова"
                        message="На сегодня не пришли данные по Луне или тону дня. Попробуйте обновить страницу чуть позже."
                        actionLabel="Открыть каталог"
                        actionHref="/reports"
                    />
                </ConsumerPanel>
            )}
        </FeedLayout>
    );
}

function FeedLayout({
    children,
    profile,
    state,
    dateLabel = "Сегодня",
}: {
    children: ReactNode;
    profile?: ProfileViewModel | null;
    state: FeedSurfaceState;
    dateLabel?: string;
}) {
    const meta = FEED_STATE_META[state];

    return (
        <ConsumerPageShell testId="feed-page">
            <ConsumerHero
                eyebrow={profile?.full_name ? `Привет, ${profile.full_name}` : "Астро-сводка"}
                title={dateLabel}
                description="Короткий ориентир на день: сначала настроение и ритм, затем быстрый разбор ключевых сфер без перегруза."
                status={<ConsumerStatusBadge label={meta.label} description={meta.description} tone={meta.tone} />}
                meta={
                    <>
                        <ConsumerMetaPill label="Формат" value="Луна дня, тон и светофор сфер" />
                        <ConsumerMetaPill label="Чтение" value="30 секунд сверху вниз" />
                    </>
                }
            />

            {profile ? (
                <TrialStatusWidget
                    activeUntil={profile.subscription_active_until || null}
                    referralCode={profile.referral_code || null}
                />
            ) : null}

            {state !== "loading" && state !== "error" ? (
                <ConsumerPanel data-testid="feed-guidance-panel" className="p-4 sm:p-5">
                    <div className="flex items-start gap-3">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 shadow-sm">
                            <Compass size={20} />
                        </div>
                        <div className="min-w-0">
                            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Как читать сегодня</p>
                            <h2 className="mt-2 text-lg font-black tracking-tight text-slate-950 sm:text-xl">
                                Сначала общий ритм, затем только нужная глубина
                            </h2>
                            <p className="mt-2 text-sm leading-relaxed text-slate-500">
                                Дневная лента рассчитана на быстрый проход: поймите настрой дня, проверьте зоны внимания и только потом уходите в более глубокие сценарии.
                            </p>
                        </div>
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-3">
                        {FEED_GUIDANCE_STEPS.map((step, index) => (
                            <article key={step.id} className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                                <div className="flex items-start gap-3">
                                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl shadow-sm ${step.iconClassName}`}>
                                        <step.icon size={18} />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
                                            Шаг {index + 1}
                                        </p>
                                        <p className="mt-2 text-sm font-black leading-snug text-slate-900">{step.title}</p>
                                    </div>
                                </div>
                                <p className="mt-3 text-sm leading-relaxed text-slate-500">{step.description}</p>
                            </article>
                        ))}
                    </div>
                </ConsumerPanel>
            ) : null}

            {children}

            <section className="space-y-3">
                <div className="px-1">
                    <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Продолжить глубже</p>
                    <h2 className="mt-2 text-xl font-black tracking-tight text-slate-950">Следующий слой персонального разбора</h2>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                        Когда дневной ориентир уже понятен, выберите точечный ответ или обновите основу профиля для более точных прогнозов.
                    </p>
                </div>

                <section className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <Link
                        href="/create?type=horary"
                        className="group rounded-[28px] border border-white/70 bg-white/90 p-4 shadow-[0_24px_60px_-36px_rgba(15,23,42,0.28)] transition-all hover:-translate-y-0.5"
                    >
                        <div className="flex flex-col gap-3">
                            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 shadow-sm">
                                <MessageCircle size={20} />
                            </div>
                            <div>
                                <p className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">Точечный ответ</p>
                                <p className="mt-2 font-black text-slate-900">Хорар</p>
                                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                                    Когда нужен короткий ответ по одной ситуации без длинного сценария.
                                </p>
                            </div>
                        </div>
                    </Link>
                    <Link
                        href="/profile"
                        className="group rounded-[28px] border border-white/70 bg-white/90 p-4 shadow-[0_24px_60px_-36px_rgba(15,23,42,0.28)] transition-all hover:-translate-y-0.5"
                    >
                        <div className="flex flex-col gap-3">
                            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 shadow-sm">
                                <Map size={20} />
                            </div>
                            <div>
                                <p className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">Основа прогноза</p>
                                <p className="mt-2 font-black text-slate-900">Профиль</p>
                                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                                    Проверьте данные рождения, если сводка кажется слишком общей или неполной.
                                </p>
                            </div>
                        </div>
                    </Link>
                </section>

                <Link
                    href="/reports"
                    className="flex w-full items-center justify-between rounded-[30px] border border-slate-900/10 bg-[linear-gradient(135deg,#111827_0%,#312e81_100%)] p-5 text-white shadow-[0_24px_60px_-36px_rgba(17,24,39,0.6)]"
                >
                    <div>
                        <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-200">Полный каталог</p>
                        <p className="mt-2 text-lg font-black">Каталог разборов</p>
                        <p className="mt-2 max-w-xl text-sm leading-relaxed text-indigo-100/80">
                            Год, месяц, совместимость и другие продукты в одной витрине без смены сценария.
                        </p>
                    </div>
                    <ArrowRight size={20} />
                </Link>
            </section>
        </ConsumerPageShell>
    );
}

const FEED_STATE_META: Record<FeedSurfaceState, { label: string; description: string; tone: "emerald" | "indigo" | "amber" | "rose" | "slate" }> = {
    ready: {
        label: "Сводка готова",
        description: "Показываем основной дневной сценарий.",
        tone: "emerald",
    },
    fallback: {
        label: "Резервный режим",
        description: "Есть безопасная замена, пока основной фид недоступен.",
        tone: "amber",
    },
    empty: {
        label: "Ждем обновление",
        description: "Дневные данные еще не пришли.",
        tone: "slate",
    },
    loading: {
        label: "Собираем сводку",
        description: "Проверяем профиль и текущие данные дня.",
        tone: "indigo",
    },
    error: {
        label: "Нужен повтор",
        description: "Не удалось обновить сводку с первого раза.",
        tone: "rose",
    },
};

const buildFallbackFeed = (): FeedViewModel => ({
    date: "Сегодня",
    moon_sign: "Луна дня",
    moon_phase: "Данные уточняются",
    moon_emoji: "✨",
    general_vibe: DEFAULT_VIBE,
    traffic_lights: { ...DEFAULT_LIGHTS },
    moon: { sign: "Луна дня", phase: "Данные уточняются", emoji: "✨" },
    fast_hits: [],
    personalization_level: "anonymous",
    meta: null,
});

const resolveMockFeedState = (
    state: MockFeedStateOverride,
    override: unknown,
) => {
    if (state === "error") {
        return {
            nextFeed: null,
            nextFeedState: "empty" as const,
            nextError: "Не удалось загрузить астросводку. Попробуйте обновить экран еще раз.",
        };
    }

    if (state === "empty") {
        return {
            nextFeed: null,
            nextFeedState: "empty" as const,
            nextError: null,
        };
    }

    if (state === "fallback") {
        return {
            nextFeed: normalizeFeed(override) || buildFallbackFeed(),
            nextFeedState: "fallback" as const,
            nextError: null,
        };
    }

    return {
        nextFeed: normalizeFeed(override) || buildMockFeed(),
        nextFeedState: "ready" as const,
        nextError: null,
    };
};

const normalizeMockProfile = (override: unknown): ProfileViewModel => {
    if (!isPlainObject(override)) {
        return buildMockProfile();
    }

    const baseProfile = buildMockProfile();
    return {
        ...baseProfile,
        ...normalizeProfile({ ...baseProfile, ...override }),
    };
};

const normalizeProfile = (value: unknown): ProfileViewModel => {
    if (!isPlainObject(value)) {
        throw new Error("Профиль пользователя вернулся в неполном формате");
    }

    return {
        full_name: typeof value.full_name === "string" ? value.full_name : null,
        birth_date: typeof value.birth_date === "string" ? value.birth_date : null,
        subscription_active_until: typeof value.subscription_active_until === "string" ? value.subscription_active_until : null,
        referral_code: typeof value.referral_code === "string" ? value.referral_code : null,
    };
};

const normalizeFeed = (value: unknown): FeedViewModel | null => {
    if (!isPlainObject(value)) {
        return null;
    }

    const hasMeaningfulContent = [
        value.date,
        value.moon_sign,
        value.moon_phase,
        value.general_vibe,
    ].some(hasText);

    if (!hasMeaningfulContent) {
        return null;
    }

    return {
        date: hasText(value.date) ? value.date : "Сегодня",
        moon_sign: hasText(value.moon_sign) ? value.moon_sign : "Луна дня",
        moon_phase: hasText(value.moon_phase) ? value.moon_phase : "Ритм дня",
        moon_emoji: hasText(value.moon_emoji) ? value.moon_emoji : "✨",
        general_vibe: hasText(value.general_vibe) ? value.general_vibe : DEFAULT_VIBE,
        traffic_lights: normalizeLights(value.traffic_lights),
    };
};

const normalizeLights = (value: unknown): FeedViewModel["traffic_lights"] => {
    if (!isPlainObject(value)) {
        return DEFAULT_LIGHTS;
    }

    return {
        health: normalizeLight(value.health),
        money: normalizeLight(value.money),
        love: normalizeLight(value.love),
    };
};

const normalizeLight = (value: unknown): FeedLight => {
    if (value === "green" || value === "yellow" || value === "red") {
        return value;
    }

    return "gray";
};

const hasText = (value: unknown): value is string =>
    typeof value === "string" && value.trim().length > 0;

const isPlainObject = (value: unknown): value is Record<string, any> =>
    typeof value === "object" && value !== null && !Array.isArray(value);

const toErrorMessage = (error: unknown, fallback: string) => {
    if (error instanceof Error && error.message.trim().length > 0) {
        return error.message;
    }

    return fallback;
};

const fetchJson = async (input: RequestInfo | URL, init?: RequestInit) => {
    const response = await fetch(input, init);

    if (!response.ok) {
        let message = `Ошибка API: ${response.status}`;
        try {
            const payload = await response.json();
            if (payload?.detail && typeof payload.detail === "string") {
                message = payload.detail;
            }
        } catch {
            // Keep the fallback message when the response body is empty or invalid.
        }
        throw new Error(message);
    }

    return response.json();
};
