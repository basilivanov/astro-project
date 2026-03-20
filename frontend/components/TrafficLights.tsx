import { Activity, Heart, Wallet } from "lucide-react";

type LightTone = "green" | "yellow" | "red" | "gray";

const LIGHT_STYLES: Record<
  LightTone,
  {
    card: string;
    iconWrap: string;
    eyebrow: string;
    description: string;
  }
> = {
  green: {
    card: "border-emerald-200 bg-emerald-50 text-emerald-900",
    iconWrap: "bg-white text-emerald-600 shadow-sm shadow-emerald-200/70",
    eyebrow: "Можно усиливать",
    description: "Есть поддержка для действий и роста. Хорошо закреплять полезные решения.",
  },
  yellow: {
    card: "border-amber-200 bg-amber-50 text-amber-900",
    iconWrap: "bg-white text-amber-600 shadow-sm shadow-amber-200/70",
    eyebrow: "Нужен запас",
    description: "Лучше держать ритм под контролем и не закладывать лишний риск.",
  },
  red: {
    card: "border-rose-200 bg-rose-50 text-rose-900",
    iconWrap: "bg-white text-rose-600 shadow-sm shadow-rose-200/70",
    eyebrow: "Не форсировать",
    description: "Снизьте давление и скорость. Здесь важнее аккуратность, чем прорыв.",
  },
  gray: {
    card: "border-slate-200 bg-slate-50 text-slate-800",
    iconWrap: "bg-white text-slate-500 shadow-sm shadow-slate-200/70",
    eyebrow: "Нейтрально",
    description: "Сначала наблюдайте за контекстом. Явного сигнала на усиление пока нет.",
  },
};

const ITEMS = [
  { key: "health", label: "Тонус", icon: Activity },
  { key: "money", label: "Деньги", icon: Wallet },
  { key: "love", label: "Чувства", icon: Heart },
] as const;

export function TrafficLights({
  lights,
  personalizationLevel,
}: {
  lights?: Partial<Record<(typeof ITEMS)[number]["key"], LightTone>>;
  personalizationLevel?: string | null;
}) {
  return (
    <section data-testid="traffic-lights" className="rounded-[28px] border border-white/70 bg-white/90 p-5 shadow-[0_24px_60px_-36px_rgba(15,23,42,0.28)] backdrop-blur-xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.22em] text-indigo-700">Сферы дня</p>
          <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-950">Где усиливать, а где держать запас</h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
            Светофор помогает быстро понять, какие темы сегодня идут легче, а где нужен более экономный режим.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600 shadow-sm">
{personalizationLevel === "personalized_v2" ? "Персональный режим" : "3 зоны внимания"}
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        {ITEMS.map((item) => {
          const status = lights?.[item.key] ?? "gray";
          const tone = LIGHT_STYLES[status];

          return (
            <article
              key={item.key}
              data-testid={`traffic-light-${item.key}-${status}`}
              className={`rounded-[24px] border p-4 shadow-sm transition-transform duration-200 sm:min-h-[192px] ${tone.card}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-black tracking-tight">{item.label}</p>
                  <p className="mt-1 text-[11px] font-black uppercase tracking-[0.18em] opacity-80">
                    {tone.eyebrow}
                  </p>
                </div>
                <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${tone.iconWrap}`}>
                  <item.icon size={22} strokeWidth={2.2} />
                </div>
              </div>
              <p className="mt-4 text-sm leading-relaxed opacity-90">{tone.description}</p>
            </article>
          );
        })}
      </div>

      <div className="mt-4 grid gap-2 rounded-[22px] border border-slate-100 bg-slate-50/80 p-3 text-[11px] font-medium text-slate-500 sm:grid-cols-3">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
          <span>Зелёный: можно усиливать</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-amber-500" />
          <span>Жёлтый: идите с запасом</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-rose-500" />
          <span>Красный: не форсируйте</span>
        </div>
      </div>
    </section>
  );
}
