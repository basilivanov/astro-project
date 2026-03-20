"use client";

import { useEffect, useState } from "react";
import { useTelegram } from "../../hooks/useTelegram";
import { Wallet, Users, ArrowUpRight, HelpCircle, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function PartnerPage() {
  const { user, initData } = useTelegram();
  const [profile, setProfile] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    if (user && initData) {
      fetch("/api/users/me", { headers: { "X-Telegram-Auth": initData } })
        .then((res) => res.json())
        .then(setProfile)
        .catch(console.error);
    }
  }, [user, initData]);

  if (!profile) return <div className="p-10 text-center text-slate-400 font-light">Загрузка...</div>;

  return (
    <div className="p-6 space-y-6 pt-10 pb-32">
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <button onClick={() => router.back()} className="p-2 -ml-2 text-slate-400 hover:text-purple-600 transition-colors">
            <ChevronLeft size={28} strokeWidth={1.5} />
        </button>
        <h1 className="text-2xl font-bold text-slate-800">Кабинет партнера</h1>
      </div>

      {/* Balance Card - Emerald Gradient */}
      <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-3xl p-7 relative overflow-hidden shadow-xl shadow-teal-500/20 text-white">
        <div className="relative z-10">
            <p className="text-emerald-100 text-xs font-bold uppercase tracking-wider mb-2">Ваш Баланс</p>
            <div className="flex items-baseline gap-1 mb-6">
                <span className="text-5xl font-black tracking-tighter">{profile.balance}</span>
                <span className="text-2xl opacity-80 font-medium">₽</span>
            </div>
            
            <div className="flex items-center gap-2 mb-6">
                 <div className="bg-white/20 px-3 py-1 rounded-full text-xs backdrop-blur-md border border-white/10">
                    Доступно к выводу
                 </div>
            </div>
            
            <Link 
                href="/support?topic=payout"
                className="flex items-center justify-center gap-2 w-full bg-white text-teal-700 font-bold py-3.5 rounded-xl hover:bg-emerald-50 active:scale-[0.98] transition-all shadow-lg"
            >
                <ArrowUpRight size={20} />
                Вывести средства
            </Link>
        </div>
        
        <div className="absolute -right-12 -top-12 w-48 h-48 bg-white/10 blur-3xl rounded-full"></div>
        <div className="absolute -left-10 bottom-0 w-32 h-32 bg-teal-900/10 blur-2xl rounded-full"></div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 text-slate-400 mb-3">
                <Users size={18} />
                <span className="text-xs font-medium uppercase tracking-wide">Рефералы</span>
            </div>
            <p className="text-3xl font-black text-slate-800">{profile.referrals_count || 0}</p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 text-slate-400 mb-3">
                <Wallet size={18} />
                <span className="text-xs font-medium uppercase tracking-wide">Ставка</span>
            </div>
            <p className="text-3xl font-black text-purple-600">20%</p>
        </div>
      </div>

      {/* Info Block */}
      <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100">
        <h3 className="flex items-center gap-2 font-bold text-slate-700 mb-4">
            <HelpCircle size={20} className="text-slate-400" />
            Условия программы
        </h3>
        <ul className="space-y-4 text-sm text-slate-500">
            <li className="flex gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-2 shrink-0"></span>
                <span>Вы получаете <b className="text-slate-700">20%</b> с каждой оплаты приглашенного пользователя.</span>
            </li>
            <li className="flex gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-2 shrink-0"></span>
                <span>Деньги зачисляются на баланс мгновенно.</span>
            </li>
            <li className="flex gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-2 shrink-0"></span>
                <span>Вывод средств возможен от <b className="text-slate-700">1000₽</b> на любую карту РФ.</span>
            </li>
        </ul>
      </div>
    </div>
  );
}