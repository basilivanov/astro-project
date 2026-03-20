export function LandingFAQ() {
  const items = [
    { q: "Нужно ли точное время рождения?", a: "Для Натала и Соляра — очень желательно (бирки из роддома). Если времени нет, мы построим Космограмму (без домов), это всё равно даст 70% информации. Для Хорара (вопроса) ваше время рождения не нужно." },
    { q: "Это гадание?", a: "Нет. Это структурный анализ астрономических циклов с помощью нейросети. Мы не предсказываем фатальное будущее, а показываем вероятные сценарии, риски и возможности. Решение всегда за вами." },
    { q: "Сколько ждать отчет?", a: "Генерация занимает от 1 до 3 минут. Вы получите уведомление, когда всё будет готово." },
    { q: "Как вы храните данные?", a: "Мы используем данные только для расчета карты. Они не передаются третьим лицам в рекламных целях." },
  ];

  return (
    <section className="px-6 py-10 bg-slate-50 border-t border-slate-100">
        <h2 className="text-2xl font-black text-slate-900 mb-6 text-center">Частые вопросы</h2>
        <div className="space-y-3 max-w-lg mx-auto">
            {items.map((item, i) => (
                <details key={i} className="bg-white rounded-xl border border-slate-200 overflow-hidden group">
                    <summary className="flex items-center justify-between p-4 font-bold text-slate-800 cursor-pointer list-none select-none">
                        {item.q}
                        <span className="text-purple-500 transition-transform group-open:rotate-180">▼</span>
                    </summary>
                    <div className="px-4 pb-4 text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-3">
                        {item.a}
                    </div>
                </details>
            ))}
        </div>
    </section>
  );
}
