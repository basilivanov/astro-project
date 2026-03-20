import { Target, Zap, ShieldAlert, Heart, TrendingUp } from "lucide-react";

export function LandingFeatures() {
  const features = [
    { icon: Target, title: "Фокус внимания", desc: "Главная тема периода одной фразой." },
    { icon: ShieldAlert, title: "Риски и ловушки", desc: "Где постелить соломку, чтобы не упасть." },
    { icon: Zap, title: "Окна возможностей", desc: "Лучшее время для старта важных дел." },
    { icon: Heart, title: "Отношения", desc: "Динамика чувств, кризисы и сближение." },
    { icon: TrendingUp, title: "Деньги", desc: "Финансовые потоки и бизнес-стратегии." },
  ];

  return (
    <section className="px-6 py-10 bg-white/50 backdrop-blur-sm border-y border-slate-100/50">
        <h2 className="text-2xl font-black text-slate-900 mb-8 text-center">Что внутри?</h2>
        <div className="space-y-4 max-w-lg mx-auto">
            {features.map((f, i) => (
                <div key={i} className="flex items-start gap-4 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
                    <div className="p-3 bg-purple-50 text-purple-600 rounded-xl shrink-0">
                        <f.icon size={20} strokeWidth={2} />
                    </div>
                    <div>
                        <h3 className="font-bold text-slate-800 text-sm">{f.title}</h3>
                        <p className="text-xs text-slate-500 leading-snug mt-1">{f.desc}</p>
                    </div>
                </div>
            ))}
        </div>
    </section>
  );
}
