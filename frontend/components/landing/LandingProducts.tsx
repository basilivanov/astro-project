import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { getRuntimeAccessBadge, getRuntimePriceLabel, isSubscriptionProductType } from "../../lib/product-billing";

export function LandingProducts() {
  const products = [
    { id: "year_forecast", title: "Альманах 2026", desc: "Стратегия на год по месяцам", tag: "Хит" },
    { id: "month_forecast", title: "Прогноз на месяц", desc: "Тактический план по неделям" },
    { id: "natal_master", title: "Натальная карта", desc: "Глубокий разбор личности" },
    { id: "solar_return", title: "Соляр (Личный год)", desc: "Прогноз от Дня Рождения" },
    { id: "synastry", title: "Совместимость", desc: "Анализ отношений и перспективы" },
    { id: "horary_answer", title: "Вопрос (Хорар)", desc: "Точный ответ Да/Нет" },
  ];

  return (
    <section className="px-6 py-10">
        <h2 className="text-2xl font-black text-slate-900 mb-6 text-center">Выбери формат</h2>
        <div className="grid gap-4 max-w-lg mx-auto">
            {products.map(p => (
                <Link key={p.id} href={`/create?type=${p.id}`} className="group relative block bg-white rounded-2xl p-5 border border-slate-100 shadow-sm overflow-hidden transition-all hover:border-purple-200 active:scale-[0.98]">
                    <div className="flex justify-between items-center relative z-10">
                        <div>
                            {p.tag && (
                                <span className="inline-block px-2 py-0.5 rounded-md bg-gradient-to-r from-purple-500 to-indigo-500 text-white text-[10px] font-bold uppercase mb-2 shadow-sm">
                                    {p.tag}
                                </span>
                            )}
                            <h3 className="font-bold text-slate-800 text-lg">{p.title}</h3>
                            <p className="text-sm text-slate-500">{p.desc}</p>
                            {isSubscriptionProductType(p.id) && (
                              <p className="mt-2 text-[11px] font-black uppercase tracking-[0.18em] text-purple-600">
                                {getRuntimeAccessBadge(p.id)}
                              </p>
                            )}
                        </div>
                        <div className="text-right">
                            <p className="text-lg font-black text-purple-600">{getRuntimePriceLabel(p.id)}</p>
                            <div className="mt-2 w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                                <ArrowRight size={16} />
                            </div>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    </section>
  );
}
