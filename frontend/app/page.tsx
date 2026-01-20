"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "./hooks/useTelegram";
import { MoonCard } from "./components/MoonCard";
import { TrafficLights } from "./components/TrafficLights";
import { Loader2, ArrowRight, MessageCircleQuestion } from "lucide-react";

export default function FeedPage() {
    const { user } = useTelegram();
    const router = useRouter();
    const [feed, setFeed] = useState<any>(null);

    useEffect(() => {
        if (user) {
            // Check onboarding status
            fetch("/api/users/me", { headers: { "X-Telegram-ID": user.id.toString() } })
                .then(res => res.json())
                .then(profile => {
                    if (!profile.birth_date) {
                        router.push("/onboarding");
                    }
                })
                .catch(console.error);
        }

        // Fetch feed (public)
        fetch("/api/feed/today")
            .then(res => res.json())
            .then(data => setFeed(data))
            .catch(console.error);
    }, [user, router]);

    if (!feed) return (
        <div className="min-h-screen flex flex-col items-center justify-center text-purple-400 bg-black gap-4">
            <Loader2 className="animate-spin" size={40} />
            <p className="text-zinc-500 text-sm animate-pulse">Связываемся со звездами...</p>
        </div>
    );

    return (
        <div className="p-5 space-y-8 pt-8 pb-24">
            <header className="flex justify-between items-end px-1">
                <div className="space-y-1">
                    <p className="text-purple-400 text-xs font-bold uppercase tracking-[0.2em]">Сегодня</p>
                    <h1 className="text-4xl font-black text-white tracking-tight">{feed.date}</h1>
                </div>
                {/* {user && <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-bold">{user.first_name[0]}</div>} */}
            </header>

            <section className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <MoonCard 
                    sign={feed.moon_sign} 
                    phase={feed.moon_phase} 
                    emoji={feed.moon_emoji} 
                    vibe={feed.general_vibe} 
                />
            </section>

            <section className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
                <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider px-1">Навигатор дня</h3>
                <TrafficLights lights={feed.traffic_lights} />
            </section>

            <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
                <button className="w-full bg-zinc-900/50 backdrop-blur-sm border border-zinc-800/50 rounded-3xl p-5 flex items-center justify-between group active:scale-95 transition-all hover:border-purple-500/30">
                    <div className="flex items-center gap-4">
                        <div className="bg-purple-500/10 p-3 rounded-2xl text-purple-400">
                            <MessageCircleQuestion size={24} />
                        </div>
                        <div className="text-left">
                            <p className="text-white font-bold text-lg">Задать вопрос</p>
                            <p className="text-zinc-500 text-xs font-medium">Хорарный ответ • 299₽</p>
                        </div>
                    </div>
                    <div className="bg-white text-black p-3 rounded-full group-hover:bg-purple-400 group-hover:scale-110 transition-all shadow-lg shadow-white/10">
                        <ArrowRight size={20} />
                    </div>
                </button>
            </section>
        </div>
    )
}