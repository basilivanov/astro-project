export const CANONICAL_PERSONA_MANIFEST_ID = "canonical-astrology-fixtures-v1";
export const CANONICAL_PERSONA_PACK_VERSION = "persona_pack_v1";
export const CANONICAL_PERSONA_TODAY_FIXTURE_ID = "CF-BE-001-baseline-exact-time";
export const CANONICAL_PERSONA_WHOLE_SIGN_FIXTURE_ID = "CF-WS-002-whole-sign-edge";

export type CanonicalPersonaPack = {
  fixtureId: string;
  manifestId: string;
  packVersion: string;
  profile: Record<string, unknown>;
  feed?: Record<string, unknown>;
  week?: {
    reportId: string;
    report: Record<string, unknown>;
    weekBrief: Record<string, unknown>;
    weekMap: Record<string, unknown>;
  };
};

const baselineExactTimePersona: CanonicalPersonaPack = {
  fixtureId: "CF-BE-001-baseline-exact-time",
  manifestId: CANONICAL_PERSONA_MANIFEST_ID,
  packVersion: CANONICAL_PERSONA_PACK_VERSION,
  profile: {
    full_name: "Ava Meridian",
    birth_date: "1992-08-14",
    birth_time: "06:32",
    birth_place: "London, UK",
    timezone: "Europe/London",
    subscription_active_until: "2026-04-15T00:00:00.000Z",
  },
  feed: {
    fixture_id: "CF-BE-001-baseline-exact-time",
    fixture_manifest_id: CANONICAL_PERSONA_MANIFEST_ID,
    fixture_pack_version: CANONICAL_PERSONA_PACK_VERSION,
    persona_pack: {
      fixture_id: "CF-BE-001-baseline-exact-time",
      manifest_id: CANONICAL_PERSONA_MANIFEST_ID,
      version: CANONICAL_PERSONA_PACK_VERSION,
      persona_name: "Ava Meridian",
      scenario_label: "baseline-exact-time",
      invariant_classes: [
        "datetime-normalization",
        "timezone-roundtrip",
        "placidus-baseline-chart-shape",
        "read-surface-regression",
      ],
    },
    day_brief: {
      version: "day_brief_v1",
      date: "2026-03-27",
      personalization_level: "personalized_v2",
      fallback_mode: false,
      summary: {
        headline: "Держите главный вектор узким и точным.",
        subhead: "День лучше проходит через спокойный темп, короткие решения и мягкую коммуникацию.",
        day_type: "deep_focus",
        tone: "active_structured",
      },
      context: {
        moon_sign: "Овен",
        moon_phase: "Растущая Луна",
        moon_emoji: "🌙",
        aspects_count: 3,
        label: "Импульсный лунный фон для коротких и точных решений.",
      },
      scores: [
        {
          key: "energy",
          title: "Энергия",
          value: 72,
          status: "green",
          advice: "Используйте ресурс на один приоритетный блок.",
          factors: [
            {
              title: "Точный ритм",
              text: "Энергия держится лучше, когда день идёт короткими и собранными блоками.",
            },
            {
              title: "Узкий фокус",
              text: "Узкий фокус уменьшает распыление и сохраняет запас к вечеру.",
            },
          ],
        },
        { key: "money", title: "Деньги", value: 62, status: "yellow", advice: "Проверьте цифры и финальные формулировки." },
        { key: "love", title: "Отношения", value: 58, status: "yellow", advice: "Говорите мягко и не перегружайте переписку." },
        { key: "focus", title: "Фокус", value: 81, status: "green", advice: "Сильнее всего работает глубокая одиночная задача." },
      ],
      windows: [
        { id: "morning", start: "09:00", end: "11:30", label: "Собрать ядро дня", mode: "best", advice: "Закройте главную задачу до обеда." },
        { id: "afternoon", start: "14:00", end: "16:00", label: "Мягкие согласования", mode: "soft", advice: "Перепроверьте договорённости и детали." },
      ],
      best_uses: [
        { id: "best-1", text: "Закрыть один глубокий рабочий блок", impact: "high", timeframe: "morning" },
        { id: "best-2", text: "Провести короткий точный созвон", impact: "medium", timeframe: "afternoon" },
      ],
      risks: [
        { id: "risk-1", text: "Не разгоняйте разговоры в конфликтный тон", impact: "high", timeframe: "all_day" },
        { id: "risk-2", text: "Не распыляйте внимание на параллельные мелочи", impact: "medium", timeframe: "morning" },
      ],
      personalized_factors: [
        { id: "factor-1", label: "Лунный драйв", impact: "medium", category: "lunar", explanation_human: "Утром проще быстро войти в темп и взять инициативу." },
        { id: "factor-2", label: "Коммуникационный фильтр", impact: "medium", category: "communication", explanation_human: "Короткие формулировки сегодня работают точнее длинных объяснений." },
      ],
      explainability: { confidence: 0.82, birth_time_used: true, factor_count: 6 },
      premium: { subscription_active: true, subscription_active_until: "2026-04-15T00:00:00.000Z", days_left: 14, show_upgrade_cta: false, show_resume_banner: false },
      cta: {
        primary: { type: "open_week", label: "Открыть неделю", href: "/week" },
        secondary: { type: "open_history", label: "История разборов", href: "/reports/history" },
      },
    },
  },
  week: {
    reportId: "canonical-week-ava-meridian",
    report: { id: "canonical-week-ava-meridian", report_type: "week_forecast", status: "completed" },
    weekBrief: {
      version: "week_brief_v1",
      week_start: "2026-03-23",
      week_end: "2026-03-29",
      personalization_level: "full",
      fallback_mode: false,
      status: "ready",
      summary: {
        headline: "Неделя просит точной сборки и спокойного темпа",
        subhead: "Лучше всего работают короткие циклы, уточнения и своевременный возврат ко второму проходу.",
        week_type: "balance",
        theme: "Настройка темпа и фиксация результата",
      },
      day_cards: [
        { date: "2026-03-23", weekday: "mon", mode: "green", score: 82, headline: "Соберите приоритеты", best_for: ["Планирование"], avoid: ["Суета"], peak_window_label: "до 14:00" },
        { date: "2026-03-24", weekday: "tue", mode: "yellow", score: 63, headline: "Проверяйте стыки", best_for: ["Уточнения"], avoid: ["Конфликты"] },
        { date: "2026-03-25", weekday: "wed", mode: "red", score: 34, headline: "Не форсируйте решения", best_for: ["Рутина"], avoid: ["Сделки"] },
        { date: "2026-03-26", weekday: "thu", mode: "yellow", score: 58, headline: "Вернитесь ко второму проходу", best_for: ["Редактура"], avoid: ["Поспешность"] },
        { date: "2026-03-27", weekday: "fri", mode: "green", score: 80, headline: "Закрепляйте результат", best_for: ["Презентации"], avoid: ["Перегруз"] },
        { date: "2026-03-28", weekday: "sat", mode: "yellow", score: 55, headline: "Снижайте темп", best_for: ["Быт"], avoid: ["Шум"] },
        { date: "2026-03-29", weekday: "sun", mode: "green", score: 76, headline: "Спокойно соберите следующую неделю", best_for: ["План"], avoid: ["Рывок"] },
      ],
      domains: [
        { key: "work_money", title: "Работа и деньги", status: "green", value: 78, headline: "Лучший домен недели", advice: "Фиксируйте договорённости письменно." },
        { key: "relationships", title: "Отношения", status: "yellow", value: 61, headline: "Нужны уточнения", advice: "Не оставляйте двусмысленность." },
        { key: "energy", title: "Энергия", status: "yellow", value: 57, headline: "Берегите ресурс", advice: "Оставляйте окна на восстановление." },
      ],
      best_uses: [
        { id: "a1", text: "Делайте один приоритетный ход за раз." },
        { id: "a2", text: "Возвращайтесь ко второму проходу вместо давления." },
        { id: "a3", text: "Сверяйте ожидания в переговорах заранее." },
      ],
      risks: [
        { id: "r1", text: "Не пытайтесь закрыть то, что ещё не дозрело." },
        { id: "r2", text: "Не распыляйтесь на параллельные обещания." },
      ],
      major_factors: [
        { id: "f1", label: "Фон недели", impact: "high", explanation_human: "Главный выигрыш приходит через точную фиксацию результата." },
        { id: "f2", label: "Тайминг", impact: "medium", explanation_human: "Лучше работают вторые проходы и редактуры, чем силовой рывок." },
      ],
      deep_sections: [
        {
          id: "strategy",
          slug: "week_strategy",
          title: "Стратегия недели",
          summary: "Собирайте неделю в коротких циклах.",
          body_markdown: "# Стратегия недели\n\nДержите ритм спокойным и возвращайтесь ко второму проходу, когда задача не закрывается с первого раза.",
          is_primary: true,
          order: 0,
        },
      ],
      explainability: { confidence: 0.81, birth_time_used: true, factor_count: 4, top_signal_source: "transit_natal" },
      cta: { primary: { type: "custom", label: "Открыть полный отчёт", href: "/read/canonical-week-ava-meridian" } },
      report_ref: { report_id: "canonical-week-ava-meridian", report_type: "week_forecast", source_status: "completed" },
    },
    weekMap: {
      thesis: "Настройка темпа и фиксация результата",
      theme: "Лучше всего работают короткие циклы",
      day_cards: [
        { date: "2026-03-23", weekday: "mon", mode: "green", headline: "Соберите приоритеты", best_for: ["Планирование"], avoid: ["Суета"], score: 0.82 },
        { date: "2026-03-24", weekday: "tue", mode: "yellow", headline: "Проверяйте стыки", best_for: ["Уточнения"], avoid: ["Конфликты"], score: 0.63 },
        { date: "2026-03-25", weekday: "wed", mode: "red", headline: "Не форсируйте решения", best_for: ["Рутина"], avoid: ["Сделки"], score: 0.34 },
        { date: "2026-03-26", weekday: "thu", mode: "yellow", headline: "Вернитесь ко второму проходу", best_for: ["Редактура"], avoid: ["Поспешность"], score: 0.58 },
        { date: "2026-03-27", weekday: "fri", mode: "green", headline: "Закрепляйте результат", best_for: ["Презентации"], avoid: ["Перегруз"], score: 0.8 },
        { date: "2026-03-28", weekday: "sat", mode: "yellow", headline: "Снижайте темп", best_for: ["Быт"], avoid: ["Шум"], score: 0.55 },
        { date: "2026-03-29", weekday: "sun", mode: "green", headline: "Спокойно соберите следующую неделю", best_for: ["План"], avoid: ["Рывок"], score: 0.76 },
      ],
      domains: {
        work: 78,
        relationships: 61,
        energy: 57,
        focus: 74,
      },
    },
  },
};

const wholeSignEdgePersona: CanonicalPersonaPack = {
  fixtureId: "CF-WS-002-whole-sign-edge",
  manifestId: CANONICAL_PERSONA_MANIFEST_ID,
  packVersion: CANONICAL_PERSONA_PACK_VERSION,
  profile: {
    full_name: "Mira North",
    birth_date: "1980-10-30",
    birth_time: "19:50",
    birth_place: "Monchegorsk, RU",
    timezone: "Europe/Moscow",
    subscription_active_until: "2026-04-15T00:00:00.000Z",
  },
  week: {
    reportId: "canonical-week-mira-north",
    report: {
      id: "canonical-week-mira-north",
      report_type: "natal_master",
      status: "completed",
      client_name: "Mira North",
      fixture_id: "CF-WS-002-whole-sign-edge",
      fixture_manifest_id: CANONICAL_PERSONA_MANIFEST_ID,
      birth_date_local: "1980-10-30T19:50:00",
      birth_timezone: "Europe/Moscow",
      birth_time_known: true,
    },
    weekBrief: {
      summary: "Высокая широта не ломает разбор, когда safe mode домов виден прямо на экране.",
      personalization_level: "full",
      explainability: { confidence: 0.79, birth_time_used: true, factor_count: 3 },
      cta: { primary: { type: "custom", label: "Открыть полный отчёт", href: "/read/canonical-week-mira-north" } },
    },
    weekMap: {
      thesis: "Safe mode держит астрологическую непрерывность",
      theme: "Whole Sign остаётся видимым на высоких широтах",
      day_cards: [
        { date: "2026-03-23", weekday: "mon", mode: "yellow", headline: "Проверьте основу", best_for: ["Верификация"], avoid: ["Доверие по умолчанию"], score: 0.62 },
      ],
      domains: { work: 64, relationships: 52, energy: 49, focus: 68 },
    },
  },
};

const canonicalPersonas: Record<string, CanonicalPersonaPack> = {
  [baselineExactTimePersona.fixtureId]: baselineExactTimePersona,
  [wholeSignEdgePersona.fixtureId]: wholeSignEdgePersona,
};

export function buildCanonicalTodayPersonaPack(fixtureId: string = CANONICAL_PERSONA_TODAY_FIXTURE_ID): CanonicalPersonaPack {
  const pack = canonicalPersonas[fixtureId];
  if (!pack) {
    throw new Error(`Unknown canonical today persona fixture: ${fixtureId}`);
  }
  return pack;
}

export function buildCanonicalWeekPersonaPack(fixtureId: string = CANONICAL_PERSONA_TODAY_FIXTURE_ID): CanonicalPersonaPack {
  const pack = canonicalPersonas[fixtureId];
  if (!pack?.week) {
    throw new Error(`Unknown canonical week persona fixture: ${fixtureId}`);
  }
  return pack;
}
