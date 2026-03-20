"use client";

import { useEffect, useState } from "react";
import { useTelegram } from "../../hooks/useTelegram";
import { Gift, Copy, Check, Share2, Users } from "lucide-react";
import Link from "next/link";

export default function SharePage() {
  const { user, initData } = useTelegram();
  const [profile, setProfile] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (user && initData) {
      fetch("/api/users/me", { headers: { "X-Telegram-Auth": initData } })
        .then((res) => res.json())
        .then(setProfile)
        .catch(console.error);
    }
  }, [user, initData]);

  const copyLink = () => {
    if (!profile?.referral_code) return;
    const link = `https://t.me/AstroGraceBot?start=ref_${profile.referral_code}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = () => {
    if (!profile?.referral_code) return;
    const link = `https://t.me/AstroGraceBot?start=ref_${profile.referral_code}`;
    const text = "✨ Попробуй AstroGrace! 14 дней премиум-прогнозов бесплатно по моей ссылке.";
    const url = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`;
    window.open(url, "_blank");
  };

  if (!profile) return <div className="p-10 text-center text-slate-400">Загрузка...</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-indigo-900 p-6 flex flex-col justify-center text-white pb-32">
      <div className="max-w-md mx-auto w-full space-y-8 text-center">
        
        <div className="relative">
            <div className="w-24 h-24 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center mx-auto text-yellow-300 shadow-2xl shadow-purple-500/50">
                <Gift size={48} />
            </div>
            <div className="absolute top-0 right-1/2 translate-x-12 -translate-y-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full rotate-12">
                WIN-WIN
            </div>
        </div>

        <div>
            <h1 className="text-3xl font-black mb-3">Дари и получай</h1>
            <p className="text-purple-100/80 text-lg leading-relaxed">
                Отправь другу <span className="text-white font-bold">14 дней Premium</span>. 
                Когда он активирует бота, ты тоже получишь <span className="text-white font-bold">+14 дней</span>.
            </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/10 space-y-4">
            <div className="flex items-center gap-4 text-left">
                <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center shrink-0">1</div>
                <div>
                    <p className="font-bold">Отправь ссылку</p>
                    <p className="text-xs text-purple-200">Друг получит приветственный бонус.</p>
                </div>
            </div>
            <div className="w-0.5 h-6 bg-white/10 ml-5"></div>
            <div className="flex items-center gap-4 text-left">
                <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center shrink-0">2</div>
                <div>
                    <p className="font-bold">Друг запускает бота</p>
                    <p className="text-xs text-purple-200">Ему не нужно платить.</p>
                </div>
            </div>
            <div className="w-0.5 h-6 bg-white/10 ml-5"></div>
            <div className="flex items-center gap-4 text-left">
                <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center shrink-0 text-white">
                    <Check size={20} />
                </div>
                <div>
                    <p className="font-bold">Вы оба в плюсе!</p>
                    <p className="text-xs text-purple-200">Подписка продлевается автоматически.</p>
                </div>
            </div>
        </div>

        <div className="space-y-3">
            <button 
                onClick={handleShare}
                className="w-full bg-white text-purple-700 font-bold py-4 rounded-xl shadow-lg shadow-purple-900/20 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
                <Share2 size={20} />
                Отправить в Telegram
            </button>
            
            <button 
                onClick={copyLink}
                className="w-full bg-purple-800/50 text-purple-200 font-bold py-4 rounded-xl hover:bg-purple-800 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
                {copied ? <Check size={20} /> : <Copy size={20} />}
                {copied ? "Скопировано" : "Копировать ссылку"}
            </button>
        </div>
        
        <p className="text-xs text-purple-300/50">
            Количество приглашений не ограничено.
        </p>
      </div>
    </div>
  );
}
