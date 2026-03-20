"use client";

import { useEffect, useState } from "react";
import { useTelegram } from "../../hooks/useTelegram";
import { User, Settings, Clock, ShieldQuestion, ChevronRight, Copy, Check, Gift } from "lucide-react";
import Link from "next/link";
import { LoadingState } from "../../components/ui-states";

const buildMockProfile = () => ({
  full_name: "Debug User",
  telegram_id: 123456789,
  days_left: 7,
  is_partner: false,
  referral_code: "DEBUG123",
  subscription_active_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
});

export default function ProfilePage() {
  const { user, initData, mode, isReady } = useTelegram();
  const [profile, setProfile] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isReady) return;
    if (mode === "mock") {
      setProfile(buildMockProfile());
      return;
    }
    if (user && initData) {
      fetch("/api/users/me", { headers: { "X-Telegram-Auth": initData } })
        .then((res) => res.json())
        .then(setProfile)
        .catch(console.error);
    }
  }, [user, initData, mode, isReady]);

  const copyLink = () => {
    if (!user || !profile?.referral_code) return;
    const link = `https://t.me/AstroGraceBot?start=ref_${profile.referral_code}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isReady || !profile) return <LoadingState />;

  return (
    <div data-testid="profile-content" className="p-6 space-y-8 pt-10 pb-32" suppressHydrationWarning>
      <div className="flex items-center gap-5">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-100 to-white flex items-center justify-center text-3xl font-bold text-purple-400 overflow-hidden ring-4 ring-purple-50">
            {user?.photo_url ? <img src={user.photo_url} alt="" /> : (user?.first_name?.[0] || "U")}
        </div>
        <div>
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">{profile.full_name}</h1>
            <p className="text-slate-400 text-xs font-medium uppercase mt-1">ID: {profile.telegram_id}</p>
        </div>
      </div>

      <div className="bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-3xl p-7 text-white shadow-xl">
            <p className="text-purple-100 text-xs font-bold uppercase tracking-widest mb-2">Premium</p>
            <div className="flex items-baseline gap-1 my-3">
                <span className="text-5xl font-black tracking-tighter">{profile.days_left}</span>
                <span className="text-lg opacity-80 font-medium">дней</span>
            </div>
      </div>

      <div className="bg-white rounded-3xl p-6 border border-purple-50 shadow-lg relative overflow-hidden">
        <div className="flex items-center gap-4 mb-5 relative z-10">
            <div className="w-12 h-12 bg-orange-50 text-orange-500 rounded-2xl flex items-center justify-center"><Gift size={24} /></div>
            <div>
                <h3 className="font-bold text-slate-800 text-lg">Подарок за друга</h3>
                <p className="text-sm text-slate-500 mt-0.5">+14 дней бесплатно</p>
            </div>
        </div>
        <button onClick={copyLink} className="w-full bg-slate-50 text-slate-600 font-medium py-3.5 rounded-xl border border-slate-100">
            {copied ? <span className="text-green-600">Ссылка скопирована</span> : "Копировать ссылку"}
        </button>
      </div>

      <div className="space-y-3">
        <MenuLink icon={Clock} label="История заказов" href="/reports/history" />
        <MenuLink icon={ShieldQuestion} label="Поддержка" href="/support" />
        <MenuLink icon={Settings} label="Настройки" href="/profile/edit" />
      </div>
    </div>
  );
}

function MenuLink({ icon: Icon, label, href }: { icon: any, label: string, href: string }) {
    return (
        <Link href={href} className="flex items-center justify-between p-4 rounded-2xl bg-white border border-slate-50 shadow-sm transition-all active:scale-[0.98]">
            <div className="flex items-center gap-4">
                <div className={`p-2 rounded-xl bg-slate-50 text-slate-400`}><Icon size={20} /></div>
                <span className="font-medium text-slate-700">{label}</span>
            </div>
            <ChevronRight size={18} className="text-slate-300" />
        </Link>
    )
}