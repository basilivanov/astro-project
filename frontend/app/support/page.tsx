"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useTelegram } from "../../hooks/useTelegram";
import { ChevronLeft, Send, MessageSquare, CheckCircle2, Loader2 } from "lucide-react";

function SupportPageContent() {
  const { user, initData } = useTelegram();
  const searchParams = useSearchParams();
  const router = useRouter();
  const topicParam = searchParams.get("topic");

  const [topic, setTopic] = useState(topicParam || "other");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (topicParam) setTopic(topicParam);
  }, [topicParam]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !initData || !message.trim()) return;

    setLoading(true);
    try {
      const response = await fetch("/api/support/tickets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Telegram-Auth": initData,
        },
        body: JSON.stringify({
          topic,
          message,
        }),
      });

      if (!response.ok) throw new Error("Failed to send ticket");
      
      setSuccess(true);
    } catch (err) {
      console.error(err);
      alert("Ошибка при отправке сообщения. Попробуйте позже.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="p-6 flex flex-col items-center justify-center min-h-[80vh] text-center space-y-6">
        <div className="w-20 h-20 bg-green-50 text-green-500 rounded-full flex items-center justify-center">
            <CheckCircle2 size={48} />
        </div>
        <div>
            <h1 className="text-2xl font-bold text-slate-800">Сообщение отправлено</h1>
            <p className="text-slate-500 mt-2">Мы ответим вам в Telegram в ближайшее время.</p>
        </div>
        <button 
            onClick={() => router.back()}
            className="w-full bg-slate-900 text-white font-bold py-4 rounded-xl"
        >
            Вернуться назад
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8 pt-10 pb-32">
      <div className="flex items-center gap-2 mb-2">
        <button onClick={() => router.back()} className="p-2 -ml-2 text-slate-400 hover:text-purple-600 transition-colors">
            <ChevronLeft size={28} strokeWidth={1.5} />
        </button>
        <h1 className="text-2xl font-bold text-slate-800">Поддержка</h1>
      </div>

      <div className="bg-purple-50 rounded-2xl p-5 flex gap-4 items-start border border-purple-100">
        <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-purple-600 shrink-0 shadow-sm">
            <MessageSquare size={20} />
        </div>
        <p className="text-sm text-purple-900/70 leading-relaxed">
            Напишите ваш вопрос или пожелание. Мы читаем каждое сообщение и отвечаем в течение дня.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Тема обращения</label>
            <select 
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-2xl p-4 text-slate-700 outline-none focus:border-purple-400 transition-colors appearance-none"
            >
                <option value="other">Общий вопрос</option>
                <option value="partner">Стать партнером</option>
                <option value="payout">Вывод средств</option>
                <option value="error">Ошибка в расчете</option>
                <option value="billing">Проблемы с оплатой</option>
            </select>
        </div>

        <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Ваше сообщение</label>
            <textarea 
                required
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Опишите ситуацию подробнее..."
                className="w-full bg-white border border-slate-200 rounded-2xl p-4 text-slate-700 outline-none focus:border-purple-400 transition-colors min-h-[160px] resize-none"
            />
        </div>

        <button 
            type="submit"
            disabled={loading || !message.trim()}
            className="w-full bg-purple-600 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-2 shadow-lg shadow-purple-200 active:scale-[0.98] transition-all disabled:opacity-50 disabled:active:scale-100"
        >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
            Отправить сообщение
        </button>
      </form>
    </div>
  );
}

export default function SupportPage() {
    return (
        <Suspense fallback={<div className="p-10 text-center">Загрузка...</div>}>
            <SupportPageContent />
        </Suspense>
    )
}
