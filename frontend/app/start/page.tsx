"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "../../hooks/useTelegram";
import { LoadingState } from "../../components/ui-states";

// #START_BLOCK_START_PAGE
/**
 * PURPOSE: Gate entry between auth, onboarding, and feed.
 * INPUT: none
 * OUTPUT: login CTA or loading state while resolving auth
 * CONTEXT: client-only
 * RAISES: none
 */
export default function StartPage() {
    const { user, initData, isReady, mode } = useTelegram();
    const router = useRouter();
    const [status, setStatus] = useState<"init" | "waiting_auth" | "checking_profile">("init");

    useEffect(() => {
        if (!isReady) return;

        if (mode === "mock") {
            setStatus("checking_profile");
            const nextUrl = "/?mock=1";
            router.replace(nextUrl);
            const fallback = window.setTimeout(() => {
                if (window.location.pathname === "/start") {
                    window.location.assign(nextUrl);
                }
            }, 400);
            return () => window.clearTimeout(fallback);
        }

        if (!user || !initData) {
            setStatus("waiting_auth");
            return;
        }

        setStatus("checking_profile");
        
        fetch("/api/users/me", {
            headers: { "X-Telegram-Auth": initData }
        })
        .then(res => {
            if (res.status === 401) throw new Error("Auth failed");
            if (!res.ok) throw new Error("Network error");
            return res.json();
        })
        .then(data => {
            if (data && data.birth_date) {
                // Profile complete -> Go to Feed
                router.replace("/");
            } else {
                // Profile incomplete -> Go to Onboarding
                router.replace("/onboarding/profile");
            }
        })
        .catch(err => {
            console.error(err);
            // If user likely doesn't exist on backend yet, guide them to profile creation
            router.replace("/onboarding/profile");
        });

    }, [user, initData, isReady, mode, router]);

    if (status === "waiting_auth") {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center space-y-6 animate-in fade-in bg-white text-slate-900">
                <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center text-4xl shadow-sm">
                    ✨
                </div>
                <div className="space-y-2">
                    <h1 className="text-2xl font-black text-slate-900">Войти через Telegram</h1>
                    <p className="text-slate-500 max-w-xs mx-auto">
                        Чтобы сохранить ваш прогресс и открыть доступ к прогнозам, нам нужно знать, кто вы.
                    </p>
                </div>
                
                {/* Simulated Login for Browser/Test Mode */}
                <button 
                    onClick={() => window.location.href = "/start?mock=1"}
                    className="btn bg-blue-500 text-white w-full py-4 rounded-xl font-bold hover:bg-blue-600 transition-colors"
                >
                    Тестовый вход (Браузер)
                </button>
                
                <p className="text-xs text-slate-400 mt-8">
                    Если вы видите этот экран внутри Telegram, попробуйте перезапустить мини-приложение.
                </p>
            </div>
        );
    }

    return <LoadingState message={status === "checking_profile" ? "Проверяем профиль..." : "Запуск..."} />;
}
// #END_BLOCK_START_PAGE
