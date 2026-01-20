"use client";

import { useEffect, useState } from "react";
import { useTelegram } from "../hooks/useTelegram";
import { Copy, Gift, CreditCard, Settings, Loader2 } from "lucide-react";

export default function ProfilePage() {
    const { user } = useTelegram();
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) {
            // In dev environment, API URL might need to be explicit if not proxying
            // Using relative path assuming Next.js proxy rewrite or CORS
            const apiUrl = "/api/users/me"; 
            
            fetch(apiUrl, {
                headers: {
                    "X-Telegram-ID": user.id.toString()
                }
            })
            .then(res => {
                if (!res.ok) throw new Error("Failed");
                return res.json();
            })
            .then(data => setProfile(data))
            .catch(err => {
                console.error(err);
                // Mock fallback for UI dev if API fails
                setProfile({
                    full_name: user.first_name,
                    telegram_id: user.id,
                    days_left: 0,
                    balance: 0,
                    subscription_active_until: null
                });
            })
            .finally(() => setLoading(false));
        } else {
            // Waiting for telegram auth
            setTimeout(() => setLoading(false), 2000); 
        }
    }, [user]);

    if (loading) return (
        <div className="h-screen flex items-center justify-center text-purple-400">
            <Loader2 className="animate-spin" size={32} />
        </div>
    );

    if (!user) return <div className="p-8 text-center text-zinc-500">Пожалуйста, откройте через Telegram</div>;

    const refLink = `https://t.me/AstroGraceBot?start=ref_${user.id}`;

    const handlePayment = async () => {
        if (!user) return;
        try {
            const res = await fetch("/api/billing/pay", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-Telegram-ID": user.id.toString()
                },
                body: JSON.stringify({
                    amount: 990.00,
                    description: "Подписка AstroGrace Premium (30 дней)",
                    is_recurring: true
                })
            });
            const data = await res.json();
            if (data.url) {
                if (window.Telegram?.WebApp) {
                    window.Telegram.WebApp.openLink(data.url);
                } else {
                    window.location.href = data.url;
                }
            } else {
                alert("Ошибка: " + JSON.stringify(data));
            }
        } catch (e) {
            console.error(e);
            alert("Не удалось создать платеж. Проверьте настройки магазина.");
        }
    };

    return (
        <div className="p-4 space-y-6 pt-8">
            {/* Header */}
            <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-2xl font-bold shadow-lg shadow-purple-500/20">
                    {profile?.full_name?.[0] || user.first_name?.[0] || "U"}
                </div>
                <div>
                    <h1 className="text-xl font-bold">{profile?.full_name || user.first_name}</h1>
                    <p className="text-zinc-400 text-sm font-mono">ID: {user.id}</p>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 gap-3">
                <div className="bg-zinc-900/50 p-4 rounded-2xl border border-zinc-800 backdrop-blur-sm">
                    <p className="text-xs text-zinc-500 uppercase font-bold mb-1 tracking-wider">Подписка</p>
                    <p className={profile?.days_left > 0 ? "text-xl font-bold text-green-400" : "text-xl font-bold text-zinc-400"}>
                        {profile?.days_left > 0 ? `${profile.days_left} дн.` : "Inactive"}
                    </p>
                </div>
                <div className="bg-zinc-900/50 p-4 rounded-2xl border border-zinc-800 backdrop-blur-sm">
                    <p className="text-xs text-zinc-500 uppercase font-bold mb-1 tracking-wider">Баланс</p>
                    <p className="text-xl font-bold text-white">
                        {profile?.balance || 0} ₽
                    </p>
                </div>
            </div>

            {/* Actions */}
            <div className="space-y-3">
                <button 
                    onClick={handlePayment}
                    className="w-full bg-white text-black font-bold py-4 rounded-2xl flex items-center justify-center gap-2 active:scale-95 transition-transform"
                >
                    <CreditCard size={20} />
                    {profile?.days_left > 0 ? "Продлить подписку" : "Активировать за 990₽"}
                </button>
                
                <div className="bg-zinc-900/50 rounded-2xl p-5 border border-zinc-800 space-y-4">
                     <div className="flex items-center gap-2 text-purple-400 font-bold">
                        <Gift size={20} />
                        <span>Пригласи друга — получи 15 дней</span>
                     </div>
                     <p className="text-sm text-zinc-400 leading-relaxed">
                        Отправь ссылку другу. Когда он запустит бота, вы оба получите <strong>+15 дней Premium доступа</strong> бесплатно.
                     </p>
                     <div className="flex items-center gap-2 bg-black/40 p-3 rounded-xl border border-zinc-800/50">
                        <code className="text-xs text-zinc-300 flex-1 truncate font-mono select-all">{refLink}</code>
                        <button 
                            onClick={() => {
                                navigator.clipboard.writeText(refLink);
                                // Optional: native haptic feedback
                                if (window.navigator.vibrate) window.navigator.vibrate(50);
                            }}
                            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                        >
                            <Copy size={16} className="text-zinc-500" />
                        </button>
                     </div>
                </div>
            </div>
            
            <button className="w-full py-4 text-zinc-500 font-medium flex items-center justify-center gap-2">
                <Settings size={18} />
                Настройки профиля
            </button>
        </div>
    )
}
