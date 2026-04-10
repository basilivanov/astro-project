import {
  confidenceBucket,
  formatWeekDateRange,
  hasExplicitWeekMigrationPayload,
  mapCanonicalWeekBriefToSurface,
  mapLegacyWeekMigrationToSurface,
  mapWeekReportToWeekBrief,
} from '../../lib/week-brief';

describe('week-brief helpers', () => {
  it('maps canonical week_brief payloads without legacy mixing', () => {
    const surface = mapCanonicalWeekBriefToSurface({
      weekBrief: {
        version: 'week_brief_v1',
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
            details: {
              why_text: 'День уже несёт понятный фокус.',
              supporting_factors: [{ label: 'Солнце', explanation_human: 'Собирает внимание' }],
            },
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
            why_text: 'Нужен один приоритет',
            supporting_factors: [{ label: 'Сатурн', explanation_human: 'Держит структуру' }],
          },
        ],
        best_uses: [{ id: 'a-1', text: 'Делать главное', impact: 'high', why_text: 'Фокус даёт лучший выход.' }],
        risks: [{ id: 'r-1', text: 'Не спорить на износе', why_text: 'Перегруз быстро накопится.' }],
        major_factors: [{ id: 'f-1', label: 'Сатурн', impact: 'high', weight: 0.7, explanation_human: 'Держит каркас недели.' }],
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
      surfaceMode: 'canonical',
      headline: 'Важная неделя',
      subhead: 'Меньше шума, больше темпа',
      theme: 'Спокойная стратегия',
      weekType: 'deep_work',
      status: 'ready',
      weekStart: '2026-03-30',
      weekEnd: '2026-04-05',
      personalizationLevel: 'full',
      fallbackMode: false,
      usesCanonicalWeekBrief: true,
      reportId: 'rep-1',
      confidenceLabel: 'Высокая опора на текущие данные',
      confidenceShortLabel: 'высокая',
      birthTimeLabel: 'учтено точное время рождения',
      topSignalLabel: 'личная натальная опора и текущие транзиты',
      sectionsCount: 1,
      waitMessage: null,
    }));
    expect(surface.dayStrip).toHaveLength(7);
    expect(surface.dayStrip[0]).toEqual(expect.objectContaining({
      weekday: 'ПН, 30 мар',
      score: null,
      headline: null,
    }));
    expect(surface.dayStrip[2]).toEqual(expect.objectContaining({
      weekday: 'СР, 1 апр',
      score: 88,
      headline: 'Фокус на главном',
      lead: null,
      practical: [],
      supporting_factors: [],
      details: { why_text: null, why_title: null, supporting_factors: [] },
    }));
    expect(surface.detailLayers).toEqual(expect.arrayContaining([
      expect.objectContaining({ source: 'week_day', body: 'День уже несёт понятный фокус.' }),
      expect.objectContaining({ source: 'week_domain', relatedKey: 'work' }),
      expect.objectContaining({ source: 'week_action', id: 'a-1' }),
      expect.objectContaining({ source: 'week_risk', id: 'r-1' }),
      expect.objectContaining({ source: 'week_factor', id: 'f-1' }),
    ]));
  });

  it('maps legacy week_map and chunks only into an explicit compatibility surface', () => {
    const surface = mapLegacyWeekMigrationToSurface({
      legacyWeekMap: {
        thesis: '  Лог недели собирается  ',
        theme: '  Осторожная неделя  ',
        week_start: '2026-04-08',
        timezone: 'Europe/Moscow',
        location: 'Moscow',
        day_cards: [
          { date: '2026-04-08', weekday: 'Понедельник', mode: 'GREEN', score: 0.82, best_for: ['  запуск  '], avoid: ['  спешка '] },
          { date: '2026-04-09', weekday: 'fri', mode: 'mystery', score: 2.6 },
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
      surfaceMode: 'compatibility',
      headline: 'Лог недели собирается',
      subhead: 'Осторожная неделя',
      theme: 'Осторожная неделя',
      weekType: 'balance',
      status: 'pending',
      weekStart: '2026-04-06',
      weekEnd: '2026-04-12',
      timezone: 'Europe/Moscow',
      location: null,
      personalizationLevel: null,
      fallbackMode: true,
      usesCanonicalWeekBrief: false,
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
    ]);
    expect(surface.dayStrip).toHaveLength(7);
    expect(surface.dayStrip[0]).toEqual(expect.objectContaining({ weekday: 'ПН, 6 апр', score: 82 }));
    expect(surface.dayStrip[2]).toEqual(expect.objectContaining({ weekday: 'СР, 8 апр', best_for: ['запуск'], avoid: ['спешка'], headline: 'Фокус: запуск' }));
    expect(surface.dayStrip[6]).toEqual(expect.objectContaining({ weekday: 'ВС, 12 апр', score: null }));
    expect(surface.domains).toEqual([
      expect.objectContaining({ key: 'work', title: 'Работа и деньги', status: 'green', headline: 'Работа и деньги: 72/100' }),
      expect.objectContaining({ key: 'unknown', title: 'Общий фокус', status: 'red', headline: 'Общий фокус: 44/100' }),
    ]);
    expect(surface.actions).toEqual([expect.objectContaining({ id: 'action-1', text: 'сделать главное' })]);
    expect(surface.risks).toEqual([expect.objectContaining({ id: 'risk-1', text: 'не перегореть' })]);
    expect(surface.deepSections).toEqual([
      expect.objectContaining({ id: 'c-1', slug: 'summary', title: 'Секция 1', summary: 'Короткий текст секции', body_markdown: '  Короткий текст секции  ', is_primary: true, order: 0 }),
      expect.objectContaining({ id: 'c-2', slug: 'details', title: 'Раздел 2', summary: 'Структурный вывод', body_markdown: JSON.stringify({ summary: 'Структурный вывод' }), is_primary: false, order: 1 }),
    ]);
    expect(surface.detailLayers.some((item) => item.source === 'week_domain')).toBe(true);
  });

  it('fails closed instead of mapping legacy payload through the product entrypoint', () => {
    const canonical = mapWeekReportToWeekBrief({
      weekBrief: {
        summary: {
          headline: '  Короткий фокус  ',
          subhead: '  Держим ритм  ',
        },
      },
      sourceStatus: 'in_progress',
    });

    const degraded = mapWeekReportToWeekBrief({
      legacyWeekMap: {
        thesis: '  Черновик недели  ',
        theme: '  Лёгкая перенастройка  ',
        actions: ['legacy action'],
        risks: ['legacy risk'],
      },
      chunks: [{ id: 'ignored', section: 'ignored', content: 'ignored' }],
      sourceStatus: 'pending',
    });

    expect(canonical).toEqual(expect.objectContaining({
      surfaceMode: 'canonical',
      headline: 'Короткий фокус',
      subhead: 'Держим ритм',
      status: 'in_progress',
      usesCanonicalWeekBrief: true,
      waitMessage: 'Персональная неделя собирается и скоро станет доступна целиком.',
      sectionsCount: 0,
    }));
    expect(degraded).toBeNull();
  });

  it('ignores legacy compatibility inputs when canonical week_brief is present', () => {
    const surface = mapWeekReportToWeekBrief({
      weekBrief: {
        version: 'week_brief_v1',
        summary: {
          headline: 'Каноническая неделя',
          subhead: 'Только week_brief формирует happy-path',
          week_type: 'push',
        },
        day_cards: [
          {
            date: '2026-04-10',
            weekday: 'fri',
            mode: 'green',
            score: 91,
            headline: 'Работать по главному приоритету',
          },
        ],
      },
      legacyWeekMap: {
        thesis: 'Legacy не должен перетереть canonical path',
        theme: 'compatibility only',
        day_cards: [{ weekday: 'Понедельник', headline: 'Legacy headline' }],
        actions: ['legacy action'],
        risks: ['legacy risk'],
      },
      chunks: [{ id: 'legacy-chunk', section: 'legacy', content: 'legacy deep section' }],
      sourceStatus: 'ready',
    });

    expect(surface.surfaceMode).toBe('canonical');
    expect(surface.usesCanonicalWeekBrief).toBe(true);
    expect(surface.headline).toBe('Каноническая неделя');
    expect(surface.subhead).toBe('Только week_brief формирует happy-path');
    expect(surface.dayStrip[4]).toEqual(expect.objectContaining({
      weekday: 'ПТ, 10 апр',
      headline: 'Работать по главному приоритету',
    }));
    expect(surface.actions).toEqual([]);
    expect(surface.risks).toEqual([]);
    expect(surface.deepSections).toEqual([]);
  });

  it('formats week ranges and confidence buckets deterministically', () => {
    expect(formatWeekDateRange('2026-04-01', '2026-04-07')).toBe('1 апр. — 7 апр.');
    expect(formatWeekDateRange('2026-04-01', null)).toBe('1 апр.');
    expect(formatWeekDateRange(null, '2026-04-07')).toBe('7 апр.');
    expect(formatWeekDateRange('not-a-date', null)).toBe('not-a-date');
    expect(formatWeekDateRange(null, null)).toBe('Диапазон уточняется');

    expect(confidenceBucket(0.9)).toBe('high');
    expect(confidenceBucket(0.75)).toBe('high');
    expect(confidenceBucket(0.45)).toBe('medium');
    expect(confidenceBucket(0.44)).toBe('low');
    expect(confidenceBucket(undefined)).toBe('unknown');
    expect(confidenceBucket(null)).toBe('unknown');
  });

  it('keeps migration payload detection out of the product route', () => {
    expect(hasExplicitWeekMigrationPayload({ legacyWeekMap: null, chunks: null })).toBe(false);
    expect(hasExplicitWeekMigrationPayload({ legacyWeekMap: undefined, chunks: [] })).toBe(false);
    expect(hasExplicitWeekMigrationPayload({ legacyWeekMap: { thesis: 'Legacy payload' }, chunks: null })).toBe(true);
    expect(hasExplicitWeekMigrationPayload({ legacyWeekMap: null, chunks: [{ id: 'chunk-1', content: 'legacy chunk' }] })).toBe(true);
  });
});
