"use client";

import { useEffect, useState } from "react";
import { Check, Clock3, Users } from "lucide-react";

export function TrialStatusWidget({ activeUntil, referralCode }: { activeUntil: string | null, referralCode: string | null }) {
    const [daysLeft, setDaysLeft] = useState(0);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        if (activeUntil) {
            const end = new Date(activeUntil).getTime();
            const now = new Date().getTime();
            const diff = Math.max(0, Math.ceil((end - now) / (1000 * 60 * 60 * 24)));
            setDaysLeft(diff);
        }
    }, [activeUntil]);

    useEffect(() => {
        if (!copied) return;
        const timer = window.setTimeout(() => setCopied(false), 2000);
        return () => window.clearTimeout(timer);
    }, [copied]);

    const copyLink = async () => {
        if (!referralCode) return;
        const link = `https://t.me/AstroGraceBot?start=ref_${referralCode}`;
        await navigator.clipboard.writeText(link);
        setCopied(true);
    };

    if (!activeUntil) return null;

    return (
        <section className="rounded-[28px] border border-white/70 bg-white/90 p-5 shadow-[0_24px_60px_-36px_rgba(15,23,42,0.28)] backdrop-blur-xl animate-in fade-in slide-in-from-top-4 duration-700">
            <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                    <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-700">Premium доступ</p>
                    <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-950">Пробный период активен</h2>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                        Уже открыты ежедневная сводка и недельный навигатор. Продлить можно реферальной ссылкой без выхода из сценария.
                    </p>
                </div>
                <div className={`rounded-2xl border px-4 py-3 text-center shadow-sm ${daysLeft > 3 ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-amber-100 bg-amber-50 text-amber-800'}`}>
                    <p className="text-[10px] font-black uppercase tracking-[0.18em]">Осталось</p>
                    <p className="mt-1 text-lg font-black">{daysLeft} дн.</p>
                </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
                <div className="rounded-[22px] border border-slate-100 bg-slate-50/80 p-4">
                    <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">
                        <Clock3 size={16} className="text-indigo-500" />
                        Что включено сейчас
                    </div>
                    <p className="mt-2 text-sm font-semibold text-slate-800">Прогноз на день + Неделя</p>
                    <p className="mt-1 text-sm leading-relaxed text-slate-500">
                        Скопируйте ссылку и отправьте другу, чтобы получить дополнительные 14 дней.
                    </p>
                </div>

                <button
                    onClick={copyLink}
                    className={`inline-flex items-center justify-center gap-2 rounded-[22px] px-4 py-4 text-sm font-black transition-all active:scale-[0.98] ${copied ? "border border-emerald-200 bg-emerald-50 text-emerald-700" : "bg-slate-900 text-white shadow-lg shadow-slate-200 hover:bg-slate-800"}`}
                >
                    {copied ? <Check size={18} /> : <Users size={18} className="text-indigo-200" />}
                    {copied ? "Скопировано" : "Продлить доступ"}
                </button>
            </div>
        </section>
    );
}
