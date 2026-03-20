import { MoonStar, Sparkles } from "lucide-react";

const SIGNS: Record<string, string> = {
  Aries: "Овен ♈",
  Taurus: "Телец ♉",
  Gemini: "Близнецы ♊",
  Cancer: "Рак ♋",
  Leo: "Лев ♌",
  Virgo: "Дева ♍",
  Libra: "Весы ♎",
  Scorpio: "Скорпион ♏",
  Sagittarius: "Стрелец ♐",
  Capricorn: "Козерог ♑",
  Aquarius: "Водолей ♒",
  Pisces: "Рыбы ♓",
};

type FastHit = { summary: string; transit?: string; natal?: string; type?: string };

export function MoonCard({
  sign,
  phase,
  emoji,
  vibe,
  fastHits,
  personalizationLevel,
}: {
  sign: string;
  phase: string;
  emoji: string;
  vibe: string;
  fastHits?: FastHit[];
  personalizationLevel?: string | null;
}) {
  const displaySign = SIGNS[sign] || sign;

  return (
    <section data-testid="moon-card" className="relative overflow-hidden rounded-[32px] border border-slate-900/10 bg-[linear-gradient(145deg,#0f172a_0%,#312e81_52%,#4c1d95_100%)] p-6 text-white shadow-[0_28px_70px_-36px_rgba(49,46,129,0.75)]">
      <div className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-fuchsia-400/25 blur-3xl" />
      <div className="pointer-events-none absolute -left-10 bottom-0 h-28 w-28 rounded-full bg-amber-300/20 blur-3xl" />

      <div className="relative z-10">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-indigo-200">Лунный ориентир</p>
            <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/10 px-3 py-1.5 text-xs font-semibold text-indigo-50 backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.8)]" />
              {phase}
            </div>
            <h2 className="mt-4 text-3xl font-black tracking-tight sm:text-[2rem]">{displaySign}</h2>
            <p className="mt-2 max-w-lg text-sm leading-relaxed text-indigo-100/80">
              Главный эмоциональный тон и общий темп дня без лишней астротерминологии.
            </p>
          </div>

          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-[24px] border border-white/12 bg-white/10 text-4xl shadow-lg shadow-slate-950/20 backdrop-blur">
            {emoji}
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <div className="rounded-[24px] border border-white/10 bg-white/8 p-4 backdrop-blur">
            <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.18em] text-indigo-200">
              <MoonStar size={16} />
              Что важно уловить
            </div>
            <p className="mt-3 text-sm leading-relaxed text-indigo-50">{vibe}</p>
          </div>

          <div className="rounded-[24px] border border-white/10 bg-white/8 p-4 backdrop-blur">
            <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.18em] text-amber-100">
              <Sparkles size={16} />
              Что срабатывает быстрее всего
            </div>
            {fastHits && fastHits.length ? (
              <p className="mt-3 text-sm leading-relaxed text-indigo-50/90">
                {fastHits.slice(0, 2).map((hit) => hit.summary).join(". ")}. Это стоит читать как фон решений, а не как голый список аспектов.
              </p>
            ) : (
              <p className="mt-3 text-sm leading-relaxed text-indigo-50/90">
                Сначала считайте настроение дня, затем проверьте светофор сфер ниже.
              </p>
            )}
            {personalizationLevel ? <p className="mt-3 text-[11px] uppercase tracking-[0.16em] text-indigo-200">Режим: {personalizationLevel}</p> : null}
          </div>
        </div>
      </div>
    </section>
  );
}
