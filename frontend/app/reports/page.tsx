"use client";

import Link from "next/link";
import { ArrowRight, Star, Calendar, Heart, HelpCircle, Clock } from "lucide-react";

const PRODUCTS = [
  {
    id: "year_forecast",
    title: "Альманах 2026",
    desc: "Полная карта года: 12 месяцев, светофоры, стратегия.",
    price: "499₽",
    oldPrice: "990₽",
    icon: Calendar,
    color: "bg-purple-500/20 text-purple-400",
    link: "/create?type=year_forecast"
  },
  {
    id: "month_forecast",
    title: "Прогноз на месяц",
    desc: "Детальный разбор 4 недель. Фокус, риски, деньги.",
    price: "199₽",
    oldPrice: "390₽",
    icon: Star,
    color: "bg-blue-500/20 text-blue-400",
    link: "/create?type=month_forecast"
  },
  {
    id: "solar_return",
    title: "Соляр (Личный год)",
    desc: "Персональный прогноз от Дня Рождения до Дня Рождения.",
    price: "199₽",
    oldPrice: "",
    icon: Clock,
    color: "bg-orange-500/20 text-orange-400",
    link: "/create?type=solar_return"
  },
  {
    id: "synastry",
    title: "Совместимость",
    desc: "Анализ отношений. Конфликты, притяжение, перспективы.",
    price: "199₽",
    oldPrice: "",
    icon: Heart,
    color: "bg-pink-500/20 text-pink-400",
    link: "/create?type=synastry"
  },
  {
    id: "horary",
    title: "Вопрос (Хорар)",
    desc: "Ответ «Да/Нет» на любой конкретный вопрос.",
    price: "199₽",
    oldPrice: "",
    icon: HelpCircle,
    color: "bg-emerald-500/20 text-emerald-400",
    link: "/create?type=horary"
  }
];

export default function CatalogPage() {
  return (
    <div className="p-5 space-y-6 pt-8 pb-24">
      <header>
        <h1 className="text-3xl font-black text-white">Витрина</h1>
        <p className="text-zinc-400 text-sm mt-1">Инструменты для управления судьбой</p>
      </header>

      <div className="grid gap-4">
        {PRODUCTS.map((product) => (
          <Link 
            key={product.id} 
            href={product.link}
            className="block bg-zinc-900/50 border border-zinc-800 rounded-3xl p-5 relative overflow-hidden group active:scale-[0.98] transition-all hover:border-purple-500/30"
          >
            <div className="flex justify-between items-start mb-3">
              <div className={`p-3 rounded-2xl ${product.color}`}>
                <product.icon size={24} />
              </div>
              <div className="text-right">
                <div className="flex items-center justify-end gap-2">
                    {product.oldPrice && <span className="text-xs text-zinc-600 line-through">{product.oldPrice}</span>}
                    <span className="font-bold text-white bg-white/10 px-2 py-1 rounded-lg text-sm">{product.price}</span>
                </div>
              </div>
            </div>
            
            <h3 className="text-lg font-bold text-white mb-1 group-hover:text-purple-400 transition-colors">{product.title}</h3>
            <p className="text-zinc-500 text-sm leading-relaxed pr-8">{product.desc}</p>
            
            <div className="absolute bottom-5 right-5 text-zinc-600 group-hover:text-white transition-colors">
                <ArrowRight size={20} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
