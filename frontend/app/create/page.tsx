"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useTelegram } from "../hooks/useTelegram";
import { ArrowLeft, Calendar, Loader2 } from "lucide-react";
import Link from "next/link";

function CreatePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useTelegram();
  const type = searchParams.get("type");
  
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      fetch("/api/users/me", { headers: { "X-Telegram-ID": user.id.toString() } })
        .then(res => res.json())
        .then(setProfile)
        .catch(console.error);
    }
  }, [user]);

  const handlePay = async () => {
    setLoading(true);
    // TODO: Implement Draft -> Pay flow
    alert("Оплата будет подключена в следующем шаге (BILL-Integration)");
    setLoading(false);
  };

  if (!type) return (
    <div className="p-10 text-center">
        <p className="text-zinc-500 mb-4">Выберите продукт в каталоге</p>
        <Link href="/reports" className="btn btn-primary">В каталог</Link>
    </div>
  );

  return (
    <div className="p-5 space-y-6 pt-8 pb-24">
      <Link href="/reports" className="flex items-center gap-2 text-zinc-500 mb-4">
        <ArrowLeft size={18} />
        Назад
      </Link>

      <header>
        <h1 className="text-2xl font-black text-white">Оформление заказа</h1>
        <p className="text-zinc-400 text-sm mt-1">Проверьте данные перед расчетом</p>
      </header>

      {/* Product Summary */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-4 flex items-center justify-between">
        <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Продукт</p>
            <p className="font-bold text-white text-lg">{type === 'year_forecast' ? 'Альманах 2026' : type}</p>
        </div>
        <div className="text-right">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Цена</p>
            <p className="font-bold text-purple-400 text-lg">499₽</p>
        </div>
      </div>

      {/* User Data Confirmation */}
      <div className="space-y-4">
        <h3 className="text-white font-bold">Данные для расчета</h3>
        
        {profile ? (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-500">
                        <Calendar size={20} />
                    </div>
                    <div>
                        <p className="text-xs text-zinc-500">Дата и место рождения</p>
                        <p className="text-white font-medium">
                            {profile.birth_date} {profile.birth_time ? `в ${profile.birth_time}` : ""}
                        </p>
                        <p className="text-white/70 text-sm">{profile.birth_place}</p>
                    </div>
                </div>
                <button 
                    onClick={() => router.push("/profile/edit")}
                    className="w-full py-2 text-xs text-zinc-500 hover:text-white border border-zinc-700 rounded-lg transition-colors"
                >
                    Изменить данные
                </button>
            </div>
        ) : (
            <div className="text-center p-4">Загрузка профиля...</div>
        )}
      </div>

      <button 
        onClick={handlePay}
        disabled={loading}
        className="w-full bg-white text-black font-bold py-4 rounded-xl hover:bg-purple-50 active:scale-95 transition-all flex items-center justify-center gap-2"
      >
        {loading && <Loader2 className="animate-spin" size={20} />}
        Оплатить 499₽
      </button>
      
      <p className="text-center text-[10px] text-zinc-600">
        Нажимая кнопку, вы соглашаетесь с условиями оферты.
      </p>
    </div>
  );
}

export default function CreatePage() {
    return (
        <Suspense fallback={<div className="p-10 text-center">Загрузка...</div>}>
            <CreatePageContent />
        </Suspense>
    )
}
