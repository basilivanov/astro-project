import { buildLegacyDayBrief, normalizeDayBriefPayload } from '../../lib/day-brief';

describe('day-brief helpers', () => {
  it('builds a deterministic legacy fallback brief from legacy payload', () => {
    const brief = buildLegacyDayBrief({
      general_vibe: '  Спокойный фокус на одном главном деле.  ',
      personalization_level: 'personal',
      traffic_lights: {
        health: 'green',
        work: 'red',
        love: 'yellow',
      },
      moon: {
        sign: 'Рак',
        phase: 'waxing',
        emoji: '🌔',
      },
      favorable_time_windows: [
        { start: '08:00', end: '10:00', label: 'Ранний старт', advice: 'Лови инерцию.' },
      ],
      fast_hits: [
        { text: 'Закрыть короткий, но важный вопрос', impact: 'high' },
        { text: 'Не распыляться на второстепенное' },
      ],
      advice: [
        'Двигать один приоритет',
        'Проверять договорённости',
      ],
      risks: ['Не спорить на эмоциях'],
      factors: [
        { label: 'Луна', impact: 'high', explanation: 'Эмоциональный фон усиливает интуицию.' },
      ],
    }, '2026-04-10');

    expect(brief.version).toBe('day_brief_v1');
    expect(brief.fallback_mode).toBe(true);
    expect(brief.personalization_level).toBe('personal');
    expect(brief.summary.headline).toContain('Спокойный фокус');
    expect(brief.context).toEqual(expect.objectContaining({
      moon_sign: 'Рак',
      moon_phase: 'waxing',
      moon_emoji: '🌔',
    }));
    expect(brief.scores).toEqual([
      expect.objectContaining({ key: 'energy', value: 78, status: 'green' }),
      expect.objectContaining({ key: 'money', value: 57, status: 'yellow' }),
      expect.objectContaining({ key: 'love', value: 56, status: 'yellow' }),
      expect.objectContaining({ key: 'focus', value: 72, status: 'yellow' }),
    ]);
    expect(brief.windows[0]).toEqual(expect.objectContaining({
      id: 'window-0',
      start: '09:00',
      end: '11:00',
      label: 'Окно дня',
      mode: 'soft',
    }));
    expect(brief.best_uses).toEqual([
      expect.objectContaining({ id: 'energy-best', text: 'Соберите ритм тела и не перегружайте себя.', impact: 'medium', timeframe: 'all_day' }),
    ]);
    expect(brief.risks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: 'money-risk', text: 'Перепроверьте цифры и договорённости.' }),
      expect.objectContaining({ id: 'love-risk', text: 'Говорите мягче и уточняйте ожидания.' }),
      expect.objectContaining({ id: 'focus-risk', text: '  Спокойный фокус на одном главном деле.  ' }),
    ]));
    expect(brief.personalized_factors[0]).toEqual(expect.objectContaining({
      id: 'legacy-factor-0',
      label: 'Фактор 1',
      impact: 'medium',
      category: 'legacy_fast_hit',
      source_models: ['mixed'],
    }));
    expect(brief.personalized_factors[0].explanation_human).toContain('Спокойный фокус');
    expect(brief.explainability).toEqual(expect.objectContaining({
      confidence: 0.72,
      factor_count: 2,
      timing_precision: 'approximate',
      top_signal_source: 'mixed',
      explanation_depth: 'standard',
    }));
    expect(brief.premium).toEqual(expect.objectContaining({
      subscription_active: true,
      subscription_active_until: '2026-04-10',
      show_upgrade_cta: false,
    }));
    expect(brief.cta).toEqual(expect.objectContaining({
      primary: expect.objectContaining({ type: 'open_week', href: '/week' }),
      secondary: expect.objectContaining({ type: 'open_history', href: '/reports/history' }),
    }));
    expect(brief.legacy).toEqual(expect.objectContaining({ general_vibe: '  Спокойный фокус на одном главном деле.  ' }));
  });

  it('normalizes v1 payload data and clamps invalid values', () => {
    const result = normalizeDayBriefPayload({
      day_brief: {
        version: 'day_brief_v1',
        date: '2026-04-01',
        personalization_level: 'full',
        fallback_mode: true,
        summary: {
          headline: 'Точный день',
          subhead: 'Сначала структура',
          day_type: 'invalid',
          tone: 'calm',
        },
        context: {
          moon_sign: 'Телец',
          moon_phase: 'full',
          aspects_count: 'bad',
        },
        scores: [
          {
            key: 'invalid',
            value: 150,
            status: 'invalid',
            details: { supporting_factors: [{ label: 'A', explanation_human: 'B', value: 10 }] },
          },
        ],
        windows: [
          {
            mode: 'bad',
            details: { why_title: 'Почему', supporting_factors: [{}] },
          },
        ],
        best_uses: [{ text: 'Сделать главное', impact: 'medium', supporting_factors: [{}] }],
        risks: [{ text: 'Избегать шума', impact: 'bad', why_text: 'Падает концентрация' }],
        personalized_factors: [{ impact: 'bad', source_models: ['m1', 2, 'm2'], weight: 0.4 }],
        explainability: {
          confidence: 0.61,
          birth_time_used: true,
          factor_count: 4,
          timing_precision: 'wrong',
          top_signal_source: 'transits',
          explanation_depth: 'full',
        },
        premium: {
          subscription_active: false,
          show_upgrade_cta: true,
        },
        cta: {
          primary: { type: 'open_today', label: 'Сегодня', href: '/today' },
          secondary: { type: 'mystery', label: 'Дальше', href: '/next' },
        },
        legacy: { source: 'api' },
      },
    }, { subscription_active_until: '2026-05-01' });

    expect(result).not.toBeNull();
    expect(result?.state).toBe('fallback');
    expect(result?.premiumActiveUntil).toBe('2026-05-01');
    expect(result?.brief.summary).toEqual(expect.objectContaining({
      headline: 'Точный день',
      subhead: 'Сначала структура',
      day_type: 'balance',
      tone: 'calm',
    }));
    expect(result?.brief.context).toEqual(expect.objectContaining({
      moon_sign: 'Телец',
      moon_phase: 'full',
      moon_emoji: '🌙',
      aspects_count: null,
    }));
    expect(result?.brief.scores[0]).toEqual(expect.objectContaining({
      key: 'energy',
      title: 'Фокус',
      value: 100,
      status: 'yellow',
      advice: 'Действуйте спокойно и без резких перегрузок.',
      details: expect.objectContaining({
        why_title: null,
        why_text: 'Сегодня здесь лучше идти через спокойную точность, а не через голый напор.',
        supporting_factors: [expect.objectContaining({ label: 'A', explanation_human: 'B', value: null })],
      }),
    }));
    expect(result?.brief.windows[0]).toEqual(expect.objectContaining({
      id: 'window-0',
      start: '09:00',
      end: '11:00',
      label: 'Рабочее окно',
      mode: 'soft',
      advice: 'Держите спокойный темп и проверяйте детали.',
    }));
    expect(result?.brief.best_uses[0]).toEqual(expect.objectContaining({
      id: 'item-0',
      impact: 'medium',
      supporting_factors: [expect.objectContaining({ label: 'Фактор дня' })],
    }));
    expect(result?.brief.risks[0]).toEqual(expect.objectContaining({
      impact: null,
      why_text: 'Падает концентрация',
    }));
    expect(result?.brief.personalized_factors[0]).toEqual(expect.objectContaining({
      id: 'factor-0',
      label: 'Фактор 1',
      impact: 'medium',
      source_models: ['m1', 'm2'],
      weight: 0.4,
    }));
    expect(result?.brief.explainability).toEqual(expect.objectContaining({
      confidence: 0.61,
      birth_time_used: true,
      factor_count: 4,
      timing_precision: null,
      top_signal_source: 'transits',
      explanation_depth: 'full',
    }));
    expect(result?.brief.premium).toEqual(expect.objectContaining({
      subscription_active: false,
      subscription_active_until: '2026-05-01',
      show_upgrade_cta: true,
      show_resume_banner: false,
    }));
    expect(result?.brief.cta).toEqual(expect.objectContaining({
      primary: expect.objectContaining({ type: 'open_today', href: '/today' }),
      secondary: expect.objectContaining({ type: 'mystery', href: '/next' }),
    }));
    expect(result?.brief.legacy).toEqual({ source: 'api' });
  });

  it('falls back to legacy mapping when payload is missing v1 brief', () => {
    const result = normalizeDayBriefPayload(
      { general_vibe: 'Legacy fallback headline', traffic_lights: { work: 'green' } },
      { subscription_active_until: null },
    );

    expect(result).not.toBeNull();
    expect(result?.state).toBe('fallback');
    expect(result?.brief.fallback_mode).toBe(true);
    expect(result?.brief.summary.headline).toContain('Legacy fallback headline');
    expect(result?.brief.scores[1]).toEqual(expect.objectContaining({ key: 'money', status: 'yellow', value: 57 }));
  });

  it('does not inject explainability factors into unrelated score disclosures', () => {
    const result = normalizeDayBriefPayload({
      day_brief: {
        version: 'day_brief_v1',
        date: '2026-04-02',
        personalization_level: 'personalized_v2',
        fallback_mode: false,
        summary: { headline: 'Точный день', subhead: 'Сначала структура', day_type: 'balance' },
        context: {},
        scores: [
          {
            key: 'energy',
            title: 'Энергия',
            value: 72,
            status: 'green',
            advice: 'Берегите темп.',
            details: { why_text: 'Нужен спокойный ритм.', supporting_factors: [] },
          },
          {
            key: 'money',
            title: 'Деньги',
            value: 68,
            status: 'green',
            advice: 'Проверьте договорённости.',
            details: { why_text: 'Важны точные цифры.', supporting_factors: [{ label: 'Венера усиливает Venus', explanation_human: 'Редкий поддерживающий фактор даёт зелёный свет для точного и подготовленного шага.' }] },
          },
        ],
        windows: [],
        best_uses: [],
        risks: [],
        personalized_factors: [
          {
            id: 'rare_booster_1',
            label: 'Венера усиливает Venus',
            impact: 'high',
            explanation_human: 'Редкий поддерживающий фактор даёт зелёный свет для точного и подготовленного шага.',
            explanation_astro: 'Транзитный фактор «Венера усиливает Venus» формирует один из главных дневных сигналов.',
            source_models: ['transit_natal'],
          },
        ],
        explainability: {
          confidence: 0.74,
          birth_time_used: true,
          factor_count: 1,
          timing_precision: 'exact',
          top_signal_source: 'transit_natal',
          explanation_depth: 'standard',
          selected_factors: [
            {
              id: 'rare_booster_1',
              label: 'Венера усиливает Venus',
              explanation_human: 'Редкий поддерживающий фактор даёт зелёный свет для точного и подготовленного шага.',
              domain: 'money',
              signal: 0.82,
            },
          ],
        },
      },
    });

    expect(result?.brief.scores[0].details?.supporting_factors).toEqual([]);
    expect(result?.brief.scores[1].details?.supporting_factors).toEqual([
      expect.objectContaining({ label: 'Венера усиливает Venus' }),
    ]);
  });

  it('returns null for non-object payloads', () => {
    expect(normalizeDayBriefPayload(null)).toBeNull();
    expect(normalizeDayBriefPayload('bad payload')).toBeNull();
  });

  it('builds legacy defaults when optional legacy sections are absent', () => {
    const brief = buildLegacyDayBrief({}, null);

    expect(brief.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(brief.summary).toEqual(expect.objectContaining({
      headline: 'День требует аккуратного темпа и собранности.',
      subhead: 'Legacy feed адаптирован во временный DayBrief до полного отключения старого формата.',
      day_type: 'balance',
      tone: null,
    }));
    expect(brief.context).toEqual(expect.objectContaining({
      moon_sign: null,
      moon_phase: null,
      moon_emoji: '🌙',
      aspects_count: 0,
      label: null,
    }));
    expect(brief.windows).toEqual([]);
    expect(brief.best_uses).toEqual([
      expect.objectContaining({ id: 'legacy-best', text: 'День лучше прожить в спокойном темпе.', impact: 'medium' }),
    ]);
    expect(brief.risks).toEqual([
      expect.objectContaining({ id: 'energy-risk', text: 'Соберите ритм тела и не перегружайте себя.', impact: 'medium' }),
      expect.objectContaining({ id: 'money-risk', text: 'Перепроверьте цифры и договорённости.', impact: 'medium' }),
      expect.objectContaining({ id: 'love-risk', text: 'Говорите мягче и уточняйте ожидания.', impact: 'medium' }),
    ]);
    expect(brief.personalized_factors).toEqual([]);
    expect(brief.explainability).toEqual(expect.objectContaining({
      confidence: 0.48,
      factor_count: 0,
      timing_precision: null,
      top_signal_source: null,
      explanation_depth: 'minimal',
    }));
    expect(brief.premium).toEqual(expect.objectContaining({
      subscription_active: false,
      subscription_active_until: null,
      show_upgrade_cta: true,
      show_resume_banner: false,
    }));
    expect(brief.cta).toEqual(expect.objectContaining({
      primary: expect.objectContaining({ type: 'open_week', href: '/week' }),
      secondary: expect.objectContaining({ type: 'open_premium', href: '/reports' }),
    }));
    expect(brief.legacy).toEqual({});
  });

  it('normalizes ready v1 payload with default premium and cta fallbacks', () => {
    const result = normalizeDayBriefPayload({
      day_brief: {
        version: 'day_brief_v1',
        date: '2026-04-02',
        personalization_level: 'light',
        summary: {
          headline: 'Ровный день',
          subhead: 'Без лишнего шума',
          day_type: 'push',
        },
        context: {
          moon_sign: '',
          moon_phase: '',
          label: '',
        },
        scores: 'bad',
        windows: 'bad',
        best_uses: 'bad',
        risks: 'bad',
        personalized_factors: 'bad',
        explainability: {
          confidence: 'bad',
          birth_time_used: 'bad',
          factor_count: 'bad',
          explanation_depth: 'bad',
        },
      },
    });

    expect(result).not.toBeNull();
    expect(result?.state).toBe('ready');
    expect(result?.premiumActiveUntil).toBeNull();
    expect(result?.brief.context).toEqual(expect.objectContaining({
      moon_sign: null,
      moon_phase: null,
      moon_emoji: '🌙',
      label: null,
    }));
    expect(result?.brief.scores).toEqual([]);
    expect(result?.brief.windows).toEqual([]);
    expect(result?.brief.best_uses).toEqual([]);
    expect(result?.brief.risks).toEqual([]);
    expect(result?.brief.personalized_factors).toEqual([]);
    expect(result?.brief.explainability).toEqual(expect.objectContaining({
      confidence: 0,
      birth_time_used: false,
      factor_count: 0,
      timing_precision: null,
      top_signal_source: null,
      explanation_depth: null,
    }));
    expect(result?.brief.premium).toEqual(expect.objectContaining({
      subscription_active: false,
      subscription_active_until: null,
      show_upgrade_cta: true,
      show_resume_banner: false,
    }));
    expect(result?.brief.cta).toEqual(expect.objectContaining({
      primary: expect.objectContaining({ type: 'open_week', href: '/week' }),
      secondary: expect.objectContaining({ type: 'open_premium', href: '/reports' }),
    }));
    expect(result?.brief.legacy).toBeNull();
  });
});
