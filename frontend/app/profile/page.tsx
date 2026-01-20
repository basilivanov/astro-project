"use client";

import { useEffect, useState } from "react";
import { useTelegram } from "../hooks/useTelegram";
import { User, Settings, Gift, Clock, ShieldQuestion, ChevronRight, Copy, Check } from "lucide-react";

export default function ProfilePage() {
  const { user } = useTelegram();
  const [profile, setProfile] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (user) {
      fetch("/api/users/me", { headers: { "X-Telegram-ID": user.id.toString() } })
        .then((res) => res.json())
        .then(setProfile)
        .catch(console.error);
    }
  }, [user]);

  const copyLink = () => {
    if (!user || !profile?.referral_code) return;
    const link = `https://t.me/AstroGraceBot?start=${profile.referral_code}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!profile) return <div className="p-10 text-center text-zinc-500">Загрузка профиля...</div>;

  return (
    <div className="p-5 space-y-8 pt-8 pb-24">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center text-2xl font-bold text-zinc-500 overflow-hidden">
            {user?.photo_url ? <img src={user.photo_url} alt="" /> : (user?.first_name?.[0] || "U")}
        </div>
        <div>
            <h1 className="text-xl font-bold text-white">{profile.full_name}</h1>
            <p className="text-zinc-500 text-xs">ID: {profile.telegram_id}</p>
        </div>
      </div>

      {/* Subscription Card */}
      <div className="bg-gradient-to-br from-purple-900/50 to-zinc-900 border border-purple-500/30 rounded-3xl p-6 relative overflow-hidden">
        <div className="relative z-10">
            <p className="text-purple-300 text-xs font-bold uppercase tracking-wider mb-1">Подписка</p>
            <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black text-white">{profile.days_left}</span>
                <span className="text-sm text-white/80">дней осталось</span>
            </div>
            <p className="text-xs text-white/50 mt-2">Доступ ко всем прогнозам и ленте.</p>
            <button className="mt-4 w-full bg-white text-black font-bold py-3 rounded-xl hover:bg-purple-50 active:scale-95 transition-all">
                Продлить за 299₽
            </button>
        </div>
        <div className="absolute -right-6 -top-6 w-32 h-32 bg-purple-600/20 blur-3xl rounded-full"></div>
      </div>

      {/* Referral Block */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-5">
        <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-orange-500/20 text-orange-400 rounded-xl">
                <Gift size={20} />
            </div>
            <div>
                <h3 className="font-bold text-white">Бесплатные дни</h3>
                <p className="text-xs text-zinc-500">Пригласи друга, получи +15 дней</p>
            </div>
        </div>
        <button 
            onClick={copyLink}
            className="w-full flex items-center justify-center gap-2 bg-zinc-800 text-white py-3 rounded-xl hover:bg-zinc-700 active:scale-95 transition-all"
        >
            {copied ? <Check size={18} /> : <Copy size={18} />}
            {copied ? "Скопировано" : "Копировать ссылку"}
        </button>
      </div>

      {/* Menu */}
      <div className="space-y-2">
        <MenuLink icon={Clock} label="История заказов" href="/reports/history" />
        <MenuLink icon={ShieldQuestion} label="Поддержка" href="/support" />
        <MenuLink icon={Settings} label="Настройки" href="/profile/edit" />
      </div>
    </div>
  );
}

function MenuLink({ icon: Icon, label, href }: { icon: any, label: string, href: string }) {
    return (
        <a href={href} className="flex items-center justify-between p-4 bg-zinc-900/30 rounded-2xl active:bg-zinc-800 transition-colors">
            <div className="flex items-center gap-3 text-white">
                <Icon size={20} className="text-zinc-500" />
                <span>{label}</span>
            </div>
            <ChevronRight size={16} className="text-zinc-600" />
        </a>
    )
}