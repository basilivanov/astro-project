import { normalizeTodayDetailItems, normalizeWeekDetailItems } from '../../lib/detail-layer';
import type { DayBriefDto } from '../../lib/day-brief';
import type { WeekBrief } from '../../lib/week-brief';

describe('detail-layer normalization', () => {
  it('normalizes Today detail items into a shared contract', () => {
    const brief: DayBriefDto = {
      version: 'day_brief_v1',
      date: '2026-04-01',
      personalization_level: 'personal',
      fallback_mode: false,
      summary: { headline: 'Фокус', subhead: 'День собран', day_type: 'push' },
      context: {},
      scores: [{
        key: 'focus',
        title: 'Фокус',
        value: 81,
        status: 'green',
        advice: 'Держи курс',
        details: { why_text: 'Ментальная ясность выше обычного', supporting_factors: [{ label: 'Меркурий', explanation_human: 'Даёт структуру', value: 'strong' }] },
      }],
      windows: [{
        id: 'w-1', start: '09:00', end: '11:00', label: 'Утреннее окно', mode: 'best', advice: 'Назначай главное',
        details: { why_text: 'Решения принимаются легче', supporting_factors: [{ label: 'Луна', explanation_human: 'Меньше шума' }] },
      }],
      best_uses: [{ id: 'a-1', text: 'Закрыть важную задачу', factor_id: 'f-1', impact: 'high', timeframe: 'morning' }],
      risks: [{ id: 'r-1', text: 'Не распыляться', factor_id: 'f-2', impact: 'medium', timeframe: 'evening', why_text: 'К вечеру падает точность', supporting_factors: [{ label: 'Сатурн', explanation_human: 'Требует темпа помедленнее' }] }],
      personalized_factors: [{ id: 'pf-1', label: 'Марс', impact: 'high', explanation_human: 'Поддерживает инициативу' }],
      explainability: { confidence: 0.8, birth_time_used: true, factor_count: 2 },
      premium: null,
      cta: null,
      legacy: null,
    };

    const items = normalizeTodayDetailItems(brief);
    expect(items.map((item) => item.source)).toEqual(['today_score', 'today_window', 'today_best_use', 'today_risk']);
    expect(items[0]).toEqual(expect.objectContaining({ id: 'today-score-focus', title: 'Фокус', body: 'Ментальная ясность выше обычного', relatedKey: 'focus' }));
    expect(items[0].factors[0]).toEqual(expect.objectContaining({ label: 'Меркурий', explanationHuman: 'Даёт структуру', source: 'today_supporting_factor' }));
    expect(items[1]).toEqual(expect.objectContaining({ id: 'w-1', timeframe: '09:00–11:00', source: 'today_window' }));
    expect(items[2]).toEqual(expect.objectContaining({ id: 'a-1', impact: 'high', timeframe: 'morning', source: 'today_best_use' }));
    expect(items[3]).toEqual(expect.objectContaining({ id: 'r-1', body: 'К вечеру падает точность', impact: 'medium', source: 'today_risk' }));
  });

  it('normalizes Week detail items into the same contract', () => {
    const brief: WeekBrief = {
      domains: [{ key: 'work', title: 'Работа', why_text: 'Нужен приоритет', supporting_factors: [{ label: 'Солнце', explanation_human: 'Собирает внимание' }] }],
      best_uses: [{ id: 'wa-1', text: 'Сфокусироваться на одном спринте', impact: 'high', timeframe: 'week_start' }],
      risks: [{ id: 'wr-1', text: 'Не брать лишнее', why_text: 'Перегрузка быстро проявится', supporting_factors: [{ label: 'Нептун', explanation_human: 'Размывает границы' }] }],
      major_factors: [{ id: 'wf-1', label: 'Юпитер', impact: 'medium', explanation_human: 'Расширяет окно возможностей' }],
    };

    const items = normalizeWeekDetailItems(brief);
    expect(items.map((item) => item.source)).toEqual(['week_domain', 'week_action', 'week_risk', 'week_factor']);
    expect(items[0]).toEqual(expect.objectContaining({ id: 'work', title: 'Работа', body: 'Нужен приоритет', source: 'week_domain' }));
    expect(items[0].factors[0]).toEqual(expect.objectContaining({ label: 'Солнце', source: 'week_supporting_factor' }));
    expect(items[1]).toEqual(expect.objectContaining({ id: 'wa-1', title: 'Сфокусироваться на одном спринте', impact: 'high', source: 'week_action' }));
    expect(items[2]).toEqual(expect.objectContaining({ id: 'wr-1', body: 'Перегрузка быстро проявится', source: 'week_risk' }));
    expect(items[3]).toEqual(expect.objectContaining({ id: 'wf-1', title: 'Юпитер', body: 'Расширяет окно возможностей', impact: 'medium', source: 'week_factor' }));
    expect(items[3].factors[0]).toEqual(expect.objectContaining({ source: 'week_major_factor', label: 'Юпитер' }));
  });
});
