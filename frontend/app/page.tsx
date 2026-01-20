"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTelegram } from "./hooks/useTelegram";
import { MoonCard } from "./components/MoonCard";
import { TrafficLights } from "./components/TrafficLights";
import { Loader2, ArrowRight, Sparkles, Lock } from "lucide-react";
import Link from "next/link";

export default function FeedPage() {
    const { user } = useTelegram();
    const router = useRouter();
    const [feed, setFeed] = useState<any>(null);
    const [tab, setTab] = useState<'today' | 'tomorrow'>('today');

    useEffect(() => {
        if (user) {
            fetch("/api/users/me", { headers: { "X-Telegram-ID": user.id.toString() } })
                .then(res => res.json())
                .then(profile => {
                    if (!profile.birth_date) {
                        router.push("/onboarding");
                    }
                })
                .catch(console.error);
        }

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
            {/* Header & Tabs */}
            <header className="flex justify-between items-center px-1">
                <div>
                    <p className="text-purple-400 text-xs font-bold uppercase tracking-widest mb-1">Астро-Сводка</p>
                    <h1 className="text-3xl font-black text-white">{feed.date}</h1>
                </div>
                {/* <div className="flex bg-zinc-900 rounded-lg p-1 border border-zinc-800">
                    <button 
                        onClick={() => setTab('today')}
                        className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${tab === 'today' ? 'bg-zinc-700 text-white' : 'text-zinc-500'}`}
                    >
                        Сегодня
                    </button>
                    <button 
                        onClick={() => setTab('tomorrow')}
                        className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${tab === 'tomorrow' ? 'bg-zinc-700 text-white' : 'text-zinc-500'}`}
                    >
                        Завтра
                    </button>
                </div> */}
            </header>

            {/* Moon Card */}
            <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                <MoonCard 
                    sign={feed.moon_sign} 
                    phase={feed.moon_phase} 
                    emoji={feed.moon_emoji} 
                    vibe={feed.general_vibe} 
                />
            </section>

            {/* Traffic Lights */}
            <section className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
                <div className="flex items-center justify-between px-1">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Навигатор дня</h3>
                    {tab === 'tomorrow' && <Lock size={12} className="text-zinc-600" />}
                </div>
                <TrafficLights lights={feed.traffic_lights} />
            </section>

            {/* Banner: Year Forecast */}
            <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
                <Link href="/reports" className="block w-full bg-gradient-to-r from-purple-900/40 to-black border border-purple-500/30 rounded-3xl p-5 relative overflow-hidden group">
                    <div className="relative z-10 flex items-center justify-between">
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-purple-300">
                                <Sparkles size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Главное</span>
                            </div>
                            <p className="text-white font-bold text-lg leading-tight">Твой Альманах 2026</p>
                            <p className="text-zinc-400 text-xs">Стратегия на 12 месяцев</p>
                        </div>
                        <div className="bg-white text-black p-3 rounded-full group-hover:bg-purple-400 group-hover:scale-110 transition-all">
                            <ArrowRight size={20} />
                        </div>
                    </div>
                    <div className="absolute top-0 right-0 w-32 h-full bg-gradient-to-l from-purple-500/10 to-transparent"></div>
                </Link>
            </section>
        </div>
    )
}
