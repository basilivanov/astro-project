import { confidenceBucket, formatWeekDateRange, mapWeekReportToWeekBrief } from '../../lib/week-brief';

describe('week-brief helpers', () => {
  it('maps structured week brief payloads into the UI surface', () => {
    const surface = mapWeekReportToWeekBrief({
      weekBrief: {
        version: 'v1',
        week_start: '2026-04-01',
        week_end: '2026-04-07',
        personalization_level: 'full',
        fallback_mode: false,
        status: 'ready',
        summary: {
          headline: '  Важная неделя  ',
          subhead: '  Меньше шума, больше темпа  ',
          week_type: 'deep_work',
          theme: 'Спокойная стратегия',
        },
        day_cards: [
          {
            date: '2026-04-01',
            weekday: 'wed',
            mode: 'green',
            score: 88,
            headline: 'Фокус на главном',
            best_for: ['Стратегия'],
            avoid: ['Перегруз'],
            peak_window_label: 'Утро',
          },
        ],
        domains: [
          {
            key: 'work',
            title: 'Работа и деньги',
            status: 'green',
            value: 82,
            headline: 'Работа и деньги: 82/100',
            advice: 'Действуйте ритмично',
          },
        ],
        best_uses: [{ id: 'a-1', text: 'Делать главное', impact: 'high' }],
        risks: [{ id: 'r-1', text: 'Не спорить на износе' }],
        major_factors: [{ id: 'f-1', label: 'Сатурн', impact: 'high', weight: 0.7 }],
        deep_sections: [{ id: 's-1', slug: 'focus', title: 'Фокус', summary: 'Коротко', body_markdown: 'Детали', is_primary: true, order: 0 }],
        explainability: {
          confidence: 0.81,
          birth_time_used: true,
          factor_count: 5,
          top_signal_source: 'transit_natal',
        },
        cta: {
          primary: { href: '/reports/1', label: 'Открыть' },
        },
        report_ref: {
          report_id: 'rep-1',
        },
      },
    });

    expect(surface).toEqual(expect.objectContaining({
      headline: 'Важная неделя',
      subhead: 'Меньше шума, больше темпа',
      theme: 'Спокойная стратегия',
      weekType: 'deep_work',
      status: 'ready',
      weekStart: '2026-04-01',
      weekEnd: '2026-04-07',
      personalizationLevel: 'full',
      fallbackMode: false,
      reportId: 'rep-1',
      confidenceLabel: 'Высокая опора на текущие данные',
      confidenceShortLabel: 'высокая',
      birthTimeLabel: 'учтено точное время рождения',
      topSignalLabel: 'личная натальная опора и текущие транзиты',
      sectionsCount: 1,
      waitMessage: null,
    }));
    expect(surface.dayCards).toHaveLength(1);
    expect(surface.dayStrip).toHaveLength(1);
    expect(surface.dayStrip[0]).toEqual(expect.objectContaining({
      weekday: 'СР, 1 апр',
      score: 88,
      headline: 'Фокус на главном',
      lead: null,
      supporting_factors: [],
    }));
    expect(surface.domains).toHaveLength(1);
    expect(surface.actions[0]).toEqual(expect.objectContaining({ id: 'a-1', impact: 'high' }));
    expect(surface.risks[0]).toEqual(expect.objectContaining({ id: 'r-1', text: 'Не спорить на износе' }));
    expect(surface.factors[0]).toEqual(expect.objectContaining({ id: 'f-1', label: 'Сатурн', weight: 0.7 }));
    expect(surface.explainability).toEqual(expect.objectContaining({ confidence: 0.81, factor_count: 5 }));
    expect(surface.cta.primary?.href).toBe('/reports/1');
  });

  it('falls back to legacy data, chunks, and pending status helpers', () => {
    const surface = mapWeekReportToWeekBrief({
      legacyWeekMap: {
        thesis: '  Лог недели собирается  ',
        theme: '  Осторожная неделя  ',
        week_start: '2026-04-08',
        timezone: 'Europe/Moscow',
        location: 'Moscow',
        day_cards: [
          { date: '2026-04-08', weekday: 'Понедельник', mode: 'GREEN', score: 0.82, best_for: ['  запуск  '], avoid: ['  спешка '] },
          { date: '2026-04-09', weekday: 'fri', mode: 'mystery', score: 2.6 },
          { date: '2026-04-10', weekday: null, mode: null, score: Number.NaN },
        ],
        domains: { work: 72, unknown: 44 },
        actions: ['  сделать главное  ', ''],
        risks: ['  не перегореть  '],
        major_factors: [
          { label: 'Марс', category: 'drive', impact_pct: 40, explanation: 'Даёт тягу к действию' },
          { label: null, impact_pct: 10, explanation: 'Слабый фон' },
        ],
        explainability: { confidence: 0.5, used_exact_birth_time: false },
      },
      chunks: [
        { id: 'c-1', section: 'summary', title: '  Секция 1 ', content: '  Короткий текст секции  ' },
        { id: 'c-2', section: 'details', content: { summary: 'Структурный вывод' } },
      ],
      latestReportId: 'rep-legacy',
      sourceStatus: 'pending',
    });

    expect(surface).toEqual(expect.objectContaining({
      headline: 'Лог недели собирается',
      subhead: 'Осторожная неделя',
      theme: 'Осторожная неделя',
      weekType: 'balance',
      status: 'pending',
      weekStart: '2026-04-08',
      weekEnd: null,
      timezone: 'Europe/Moscow',
      location: 'Moscow',
      personalizationLevel: null,
      fallbackMode: false,
      reportId: 'rep-legacy',
      confidenceLabel: 'Хорошая опора на текущие данные',
      confidenceShortLabel: 'хорошая',
      birthTimeLabel: 'без точного времени рождения',
      topSignalLabel: null,
      sectionsCount: 2,
      waitMessage: 'Лог недели собирается',
    }));
    expect(surface.dayCards).toEqual([
      expect.objectContaining({ weekday: 'mon', mode: 'green', score: 82, best_for: ['запуск'], avoid: ['спешка'] }),
      expect.objectContaining({ weekday: 'fri', mode: 'red', score: 35 }),
      expect.objectContaining({ weekday: null, mode: 'red', score: 50 }),
    ]);
    expect(surface.dayStrip).toHaveLength(3);
    expect(surface.dayStrip[0]).toEqual(expect.objectContaining({ weekday: 'ПН, 8 апр', best_for: ['запуск'], avoid: ['спешка'], headline: 'Фокус на запуск' }));
    expect(surface.domains).toEqual([
      expect.objectContaining({ key: 'work', title: 'Работа и деньги', status: 'green', headline: 'Работа и деньги: 72/100' }),
      expect.objectContaining({ key: 'unknown', title: 'unknown', status: 'red', headline: 'unknown: 44/100' }),
    ]);
    expect(surface.actions).toEqual([{ id: 'action-1', text: 'сделать главное' }]);
    expect(surface.risks).toEqual([{ id: 'risk-1', text: 'не перегореть' }]);
    expect(surface.factors).toEqual([
      expect.objectContaining({ id: 'factor-1', label: 'Марс', impact: 'high', weight: 0.4 }),
      expect.objectContaining({ id: 'factor-2', label: 'Фактор 2', impact: 'low', weight: 0.1 }),
    ]);
    expect(surface.deepSections).toEqual([
      expect.objectContaining({ id: 'c-1', slug: 'summary', title: '  Секция 1 ', summary: 'Короткий текст секции', body_markdown: '  Короткий текст секции  ', is_primary: true, order: 0 }),
      expect.objectContaining({ id: 'c-2', slug: 'details', title: 'details', summary: 'Структурный вывод', body_markdown: JSON.stringify({ summary: 'Структурный вывод' }), is_primary: false, order: 1 }),
    ]);
    expect(surface.explainability).toEqual(expect.objectContaining({ confidence: 0.5, birth_time_used: false, factor_count: 2 }));
  });

  it('keeps explicit brief actions, factors, sections, and in-progress state stable', () => {
    const surface = mapWeekReportToWeekBrief({
      weekBrief: {
        status: 'in_progress',
        fallback_mode: true,
        summary: {
          headline: '  ',
          subhead: '',
          theme: '  ',
          week_type: 'transition',
        },
        best_uses: [
          { id: null, text: '  Сфокусироваться  ', factor_id: 'factor-x', impact: 'medium', timeframe: 'am' },
          { id: 'hidden-action', text: '  Скрыть по тегу  ', tag: 'all_week' },
          { text: '   ' },
        ],
        risks: [
          { text: '  Не распыляться  ' },
          { id: 'hidden-risk', text: '  Тоже скрыть  ', tag: 'all_week' },
        ],
        major_factors: [],
        deep_sections: [],
        explainability: {
          confidence: 0.2,
          birth_time_used: false,
          factor_count: 0,
          top_signal_source: 'timing',
        },
        cta: {
          secondary: { href: '/fallback', label: 'Подробнее' },
        },
        report_ref: {
          source_status: 'in_progress',
        },
      },
      legacyWeekMap: {
        thesis: '  Черновик недели  ',
        theme: '  Лёгкая перенастройка  ',
        actions: ['legacy action'],
        risks: ['legacy risk'],
        major_factors: [{ label: 'Неприменимо', impact_pct: 90 }],
      },
      chunks: [{ id: 'ignored', section: 'ignored', content: 'ignored' }],
      sourceStatus: 'pending',
    });

    expect(surface).toEqual(expect.objectContaining({
      headline: 'Черновик недели',
      subhead: 'Лёгкая перенастройка',
      theme: 'Лёгкая перенастройка',
      weekType: 'transition',
      status: 'in_progress',
      fallbackMode: true,
      confidenceLabel: 'Ориентир предварительный',
      confidenceShortLabel: 'предварительная',
      birthTimeLabel: 'без точного времени рождения',
      topSignalLabel: 'тайминг недели',
      sectionsCount: 1,
      waitMessage: 'Черновик недели',
    }));
    expect(surface.actions).toEqual([
      { id: 'action-1', text: 'Сфокусироваться', factor_id: 'factor-x', impact: 'medium', timeframe: 'am', why_text: null, supporting_factors: [], tag: null },
    ]);
    expect(surface.risks).toEqual([
      { id: 'risk-1', text: 'Не распыляться', factor_id: null, impact: null, timeframe: null, why_text: null, supporting_factors: [], tag: null },
    ]);
    expect(surface.factors).toEqual([]);
    expect(surface.deepSections).toEqual([
      expect.objectContaining({ id: 'ignored', slug: 'ignored', title: 'ignored', body_markdown: 'ignored', is_primary: true, order: 0 }),
    ]);
    expect(surface.cta).toEqual({ primary: null, secondary: { href: '/fallback', label: 'Подробнее' } });
  });

  it('uses source status and fallbacks when brief status is absent', () => {
    const surface = mapWeekReportToWeekBrief({
      weekBrief: {
        summary: {
          headline: '  Короткий фокус  ',
          subhead: '  Держим ритм  ',
        },
      },
      sourceStatus: 'in_progress',
    });

    expect(surface).toEqual(expect.objectContaining({
      headline: 'Короткий фокус',
      subhead: 'Держим ритм',
      theme: 'Карта недели',
      weekType: 'balance',
      status: 'in_progress',
      waitMessage: 'Неделя собирается, лог уже в работе',
      confidenceLabel: null,
      confidenceShortLabel: null,
      topSignalLabel: null,
      birthTimeLabel: 'без точного времени рождения',
      sectionsCount: 0,
    }));
    expect(surface.dayCards).toEqual([]);
    expect(surface.domains).toEqual([]);
    expect(surface.actions).toEqual([]);
    expect(surface.risks).toEqual([]);
    expect(surface.factors).toEqual([]);
    expect(surface.deepSections).toEqual([]);
  });

  it('formats week ranges and confidence buckets deterministically', () => {
    expect(formatWeekDateRange('2026-04-01', '2026-04-07')).toBe('1 апр. — 7 апр.');
    expect(formatWeekDateRange('2026-04-01', null)).toBe('1 апр.');
    expect(formatWeekDateRange(null, '2026-04-07')).toBe('7 апр.');
    expect(formatWeekDateRange('not-a-date', null)).toBe('not-a-date');
    expect(formatWeekDateRange(null, null)).toBe('Неделя без даты');

    expect(confidenceBucket(0.9)).toBe('high');
    expect(confidenceBucket(0.75)).toBe('high');
    expect(confidenceBucket(0.45)).toBe('medium');
    expect(confidenceBucket(0.44)).toBe('low');
    expect(confidenceBucket(0.1)).toBe('low');
    expect(confidenceBucket(undefined)).toBe('unknown');
    expect(confidenceBucket(null)).toBe('unknown');
  });
});
