"use client";

import { useState, useEffect } from "react";
import { X, Star, MessageSquare, Send } from "lucide-react";
import { useTelegram } from "../hooks/useTelegram";

export function MicroFeedback({ reportId }: { reportId: string }) {
  const { user, initData } = useTelegram();
  const [visible, setVisible] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [step, setStep] = useState<"rating" | "comment" | "sent">("rating");

  useEffect(() => {
    const timer = setTimeout(() => {
        const key = `feedback_${reportId}`;
        if (!localStorage.getItem(key)) {
            setVisible(true);
        }
    }, 45000); // 45 sec delay
    return () => clearTimeout(timer);
  }, [reportId]);

  const handleRate = (value: number) => {
    setRating(value);
    setStep("comment");
  };

  const handleSubmit = async () => {
    setStep("sent");
    localStorage.setItem(`feedback_${reportId}`, "1");
    
    try {
        await fetch(`/api/reports/${reportId}/feedback`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(initData ? { "X-Telegram-Auth": initData } : {})
            },
            body: JSON.stringify({
                rating,
                comment: comment.trim() || undefined,
                telegram_id: user?.id
            })
        });
    } catch (e) {
        console.error("Feedback submission failed", e);
    }
    
    setTimeout(() => setVisible(false), 2000);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-6 left-6 right-6 bg-white rounded-2xl shadow-2xl p-5 border border-purple-100 z-50 animate-in slide-in-from-bottom-10 fade-in duration-500">
      <button onClick={() => setVisible(false)} className="absolute top-2 right-2 text-slate-300 hover:text-slate-500 transition-colors">
        <X size={18} />
      </button>
      
      {step === "rating" && (
          <div className="text-center space-y-4 pt-2">
            <p className="text-sm font-bold text-slate-800">Как вам этот разбор?</p>
            <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                    <button 
                        key={star}
                        onClick={() => handleRate(star)}
                        className="text-3xl hover:scale-110 active:scale-95 transition-transform text-amber-400"
                    >
                        {star <= rating ? "★" : "☆"}
                    </button>
                ))}
            </div>
          </div>
      )}

      {step === "comment" && (
          <div className="space-y-4 pt-2 animate-in fade-in zoom-in duration-300">
            <div className="flex justify-between items-center px-1">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Оценка: {rating}/5</p>
                <button onClick={() => setStep("rating")} className="text-[10px] text-purple-500 font-bold hover:underline">Изменить</button>
            </div>
            <textarea 
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Что понравилось или чего не хватило?"
                className="w-full bg-slate-50 border border-slate-100 rounded-xl p-3 text-sm text-slate-700 outline-none focus:ring-2 focus:ring-purple-500/10 focus:border-purple-200 transition-all min-h-[80px]"
            />
            <button 
                onClick={handleSubmit}
                className="w-full bg-slate-900 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 active:scale-[0.98] transition-all"
            >
                Отправить <Send size={16} />
            </button>
          </div>
      )}

      {step === "sent" && (
          <div className="text-center py-4 animate-in fade-in zoom-in duration-300">
              <div className="w-12 h-12 bg-green-50 text-green-500 rounded-full flex items-center justify-center mx-auto mb-3">
                  <MessageSquare size={24} />
              </div>
              <p className="text-green-600 font-bold text-sm">Спасибо за ваш отзыв! 🌸</p>
          </div>
      )}
    </div>
  );
}
