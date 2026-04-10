import { hasAnyCompleteDayDomain, hasCompleteDayDomain, normalizeDayBriefPayload } from '../../lib/day-brief';

describe('day-brief helpers', () => {
  it('returns null for non-canonical payloads', () => {
    expect(normalizeDayBriefPayload(null)).toBeNull();
    expect(normalizeDayBriefPayload('bad payload')).toBeNull();
    expect(normalizeDayBriefPayload({ general_vibe: 'legacy' })).toBeNull();
    expect(normalizeDayBriefPayload({ day_brief: { version: 'day_brief_v1' } })).toBeNull();
    expect(normalizeDayBriefPayload({ day_brief: { version: 'day_brief_v2' } })).toBeNull();
  });

  it('normalizes strict canonical payload into hero plus four domains only', () => {
    const result = normalizeDayBriefPayload({
      day_brief: {
        version: 'day_brief_canon_v1',
        status: 'complete',
        date: '2026-04-10',
        personalization_level: 'personalized_v2',
        hero: {
          title: 'Канонический день',
          subtitle: 'Только hero и четыре сферы',
          day_type: 'balance',
          tone: 'steady',
        },
        domains: {
          energy: {
            key: 'energy',
            title: 'Тонус',
            score_status: 'complete',
            score: 78,
            status: 'green',
            description_status: 'complete',
            description: 'Есть ресурс на главный блок дня.',
            why_status: 'complete',
            why_astro_text: 'Твой Марс сегодня держит собранный темп.',
            evidence_refs: [{ id: 'factor-1' }],
          },
          money: {
            key: 'money',
            title: 'Работа и деньги',
            score_status: 'complete',
            score: 64,
            status: 'yellow',
            description_status: 'complete',
            description: 'Нужны точные цифры и одна рабочая линия.',
            why_status: 'complete',
            why_astro_text: 'Твой 2-й дом денег просит внимательной проверки условий.',
            evidence_refs: [],
          },
          love: {
            key: 'love',
            title: 'Чувства',
            score_status: 'missing',
            score: null,
            status: null,
            description_status: 'missing',
            description: null,
            why_status: 'missing',
            why_astro_text: null,
            evidence_refs: [],
          },
          focus: {
            key: 'focus',
            title: 'Фокус',
            score_status: 'failed',
            score: null,
            status: null,
            description_status: 'failed',
            description: null,
            why_status: 'failed',
            why_astro_text: null,
            evidence_refs: [],
          },
        },
        premium: {
          subscription_active: false,
          show_upgrade_cta: true,
        },
      },
    }, { subscription_active_until: '2026-05-01' });

    expect(result).not.toBeNull();
    expect(result?.state).toBe('ready');
    expect(result?.usesCanonicalDayBrief).toBe(true);
    expect(result?.brief.version).toBe('day_brief_canon_v1');
    expect(result?.brief.status).toBe('complete');
    expect(result?.brief.hero).toEqual(expect.objectContaining({
      title: 'Канонический день',
      subtitle: 'Только hero и четыре сферы',
      day_type: 'balance',
    }));
    expect(Object.keys(result?.brief.domains || {})).toEqual(['energy', 'money', 'love', 'focus']);
    expect((result?.brief as any).windows).toBeUndefined();
    expect((result?.brief as any).best_uses).toBeUndefined();
    expect((result?.brief as any).risks).toBeUndefined();
    expect((result?.brief as any).legacy).toBeUndefined();
  });

  it('derives no_data surface when canonical payload has no complete domains', () => {
    const result = normalizeDayBriefPayload({
      version: 'day_brief_canon_v1',
      status: 'partial',
      date: '2026-04-10',
      personalization_level: 'personalized_v2',
      hero: { title: 'День без полного слоя', subtitle: 'Часть полей отсутствует', day_type: 'balance' },
      domains: {
        energy: { key: 'energy', title: 'Тонус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        money: { key: 'money', title: 'Работа и деньги', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        love: { key: 'love', title: 'Чувства', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        focus: { key: 'focus', title: 'Фокус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
      },
    });

    expect(result?.state).toBe('no_data');
    expect(hasAnyCompleteDayDomain(result!.brief)).toBe(false);
  });

  it('derives error surface when canonical payload is failed', () => {
    const result = normalizeDayBriefPayload({
      version: 'day_brief_canon_v1',
      status: 'failed',
      date: '2026-04-10',
      personalization_level: 'personalized_v2',
      hero: { title: 'Ошибка', subtitle: 'Расчёт не завершён', day_type: 'balance' },
      domains: {
        energy: { key: 'energy', title: 'Тонус', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
        money: { key: 'money', title: 'Работа и деньги', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
        love: { key: 'love', title: 'Чувства', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
        focus: { key: 'focus', title: 'Фокус', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
      },
    });

    expect(result?.state).toBe('error');
  });

  it('tracks complete domain status precisely', () => {
    const result = normalizeDayBriefPayload({
      version: 'day_brief_canon_v1',
      status: 'partial',
      date: '2026-04-10',
      personalization_level: 'personalized_v2',
      hero: { title: 'Частичный день', subtitle: 'Одна сфера готова', day_type: 'balance' },
      domains: {
        energy: { key: 'energy', title: 'Тонус', score_status: 'complete', score: 80, status: 'green', description_status: 'complete', description: 'Есть ресурс.', why_status: 'complete', why_astro_text: 'Твой Марс собран.', evidence_refs: [] },
        money: { key: 'money', title: 'Работа и деньги', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        love: { key: 'love', title: 'Чувства', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        focus: { key: 'focus', title: 'Фокус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
      },
    });

    expect(hasCompleteDayDomain(result!.brief, 'energy')).toBe(true);
    expect(hasCompleteDayDomain(result!.brief, 'money')).toBe(false);
    expect(hasAnyCompleteDayDomain(result!.brief)).toBe(true);
  });
});
