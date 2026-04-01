import Link from "next/link";

type LegalSection = {
  title: string;
  paragraphs?: string[];
  bullets?: string[];
};

type LegalPageLayoutProps = {
  eyebrow?: string;
  title: string;
  subtitle: string;
  statusNote?: string;
  sections: LegalSection[];
  assumptions?: string[];
  supportTopic?: string;
};

export default function LegalPageLayout({
  eyebrow = "Legal",
  title,
  subtitle,
  statusNote,
  sections,
  assumptions = [],
  supportTopic = "billing",
}: LegalPageLayoutProps) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-6 pb-24 pt-10 text-slate-900">
      <header className="rounded-3xl bg-slate-950 px-6 py-8 text-white shadow-sm">
        <p className="text-xs font-black uppercase tracking-[0.24em] text-purple-200">{eyebrow}</p>
        <h1 className="mt-3 text-3xl font-black sm:text-4xl">{title}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-200 sm:text-base">{subtitle}</p>
        {statusNote ? <p className="mt-4 text-xs font-semibold uppercase tracking-[0.16em] text-amber-200">{statusNote}</p> : null}
      </header>

      {sections.map((section) => (
        <section key={section.title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">{section.title}</h2>
          {section.paragraphs?.length ? (
            <div className="mt-4 space-y-3 text-sm leading-relaxed text-slate-700 sm:text-base">
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          ) : null}
          {section.bullets?.length ? (
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-700 sm:text-base">
              {section.bullets.map((bullet) => (
                <li key={bullet} className="rounded-2xl bg-slate-50 px-4 py-3">
                  {bullet}
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ))}

      {assumptions.length ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-amber-950">Что ещё уточняется</h2>
          <p className="mt-3 text-sm leading-relaxed text-amber-900 sm:text-base">
            Ниже перечислены допущения и открытые вопросы из текущего legal draft. Они оставлены видимыми, чтобы не маскировать
            ещё не подтверждённые юридические и операционные детали.
          </p>
          <ul className="mt-4 space-y-3 text-sm leading-relaxed text-amber-900 sm:text-base">
            {assumptions.map((item) => (
              <li key={item} className="rounded-2xl bg-white/80 px-4 py-3">
                {item}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm text-sm leading-relaxed text-slate-700 sm:text-base">
        <p>
          Для уточнений по юридическим условиям, оплате или персональным данным используйте страницу{' '}
          <Link href={`/support?topic=${supportTopic}`} className="font-semibold text-purple-700 hover:text-purple-800">
            поддержки
          </Link>
          .
        </p>
      </section>
    </div>
  );
}
