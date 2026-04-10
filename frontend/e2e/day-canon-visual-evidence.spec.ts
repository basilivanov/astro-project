import { expect, test } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';

import { bootstrapMockTelegram, expectNoCrash } from './utils';

type DayBriefDomain = {
  key: 'energy' | 'money' | 'love' | 'focus';
  title: string;
  score_status: 'complete' | 'missing' | 'failed';
  score: number | null;
  status: 'green' | 'yellow' | 'red' | null;
  description_status: 'complete' | 'missing' | 'failed';
  description: string | null;
  why_status: 'complete' | 'missing' | 'failed';
  why_astro_text: string | null;
  evidence_refs: Array<Record<string, unknown>>;
};

const OUT_DIR = '/app/docs/review_evidence/front/day-week/2026-04-10-d479771';

async function ensureOutDir() {
  await fs.mkdir(OUT_DIR, { recursive: true });
}

async function writeShot(page: Parameters<typeof test>[0]['page'], name: string) {
  await page.screenshot({ path: path.join(OUT_DIR, name), fullPage: true });
}

function canonicalDomains(): Record<'energy' | 'money' | 'love' | 'focus', DayBriefDomain> {
  return {
    energy: {
      key: 'energy',
      title: 'Тонус',
      score_status: 'complete',
      score: 74,
      status: 'green',
      description_status: 'complete',
      description: 'Ресурса хватает на один главный блок и спокойное завершение начатого. День лучше работает в собранном темпе без распыления.',
      why_status: 'complete',
      why_astro_text: 'Твой Марс сегодня собирает импульс в одну точку и помогает не разбрасывать силы. Лунный фон поддерживает короткие точные действия без лишнего шума.',
      evidence_refs: [{ kind: 'aspect', ref: 'mars-moon' }],
    },
    money: {
      key: 'money',
      title: 'Работа и деньги',
      score_status: 'complete',
      score: 63,
      status: 'yellow',
      description_status: 'complete',
      description: 'В денежных и рабочих вопросах лучше держаться одной линии и проверять формулировки дважды. Результат приходит через аккуратность, а не через скорость.',
      why_status: 'complete',
      why_astro_text: 'Твой 2-й дом денег и личной цены вопроса сегодня требует точности в цифрах и договорённостях. Твой Меркурий помогает увидеть слабые места до того, как они станут ошибкой.',
      evidence_refs: [{ kind: 'house', ref: 'house-2' }],
    },
    love: {
      key: 'love',
      title: 'Чувства',
      score_status: 'complete',
      score: 58,
      status: 'yellow',
      description_status: 'complete',
      description: 'Контакт лучше строится через мягкий тон и короткие ясные сигналы. Важнее не давить, а оставить собеседнику пространство для ответа.',
      why_status: 'complete',
      why_astro_text: 'Твоя Венера сегодня чувствительнее к оттенкам подачи, поэтому мягкость работает сильнее прямого нажима. Луна поднимает эмоциональный фон и просит говорить бережно.',
      evidence_refs: [{ kind: 'planet', ref: 'venus' }],
    },
    focus: {
      key: 'focus',
      title: 'Фокус',
      score_status: 'complete',
      score: 81,
      status: 'green',
      description_status: 'complete',
      description: 'Ментальная линия сегодня особенно чистая, если не дробить внимание между параллельными задачами. Один глубокий проход даёт лучший результат, чем серия резких переключений.',
      why_status: 'complete',
      why_astro_text: 'Твой Меркурий сегодня держит мысль собранной и лучше работает в одной задаче. Твой 10-й дом карьеры и решений подчёркивает важность главного хода и ясного приоритета.',
      evidence_refs: [{ kind: 'planet', ref: 'mercury' }, { kind: 'house', ref: 'house-10' }],
    },
  };
}

async function mountMock(page: Parameters<typeof test>[0]['page'], dayBrief: Record<string, unknown> | null) {
  await bootstrapMockTelegram(page, {
    feedState: 'ready',
    feedOverride: dayBrief ? { day_brief: dayBrief } : { general_vibe: 'legacy raw payload' },
  });
  await page.setViewportSize({ width: 390, height: 844 });
}

test.describe('day canon branch-visible visual evidence', () => {
  test('refreshes canonical Today screenshots', async ({ page }) => {
    await ensureOutDir();
    await mountMock(page, {
      version: 'day_brief_canon_v1',
      status: 'complete',
      date: '2026-04-10',
      personalization_level: 'personalized_v2',
      hero: {
        title: 'День лучше проходит через один главный вектор.',
        subtitle: 'Собирайте ресурс в четыре ключевые сферы и не подменяйте их общим фоном.',
        day_type: 'deep_focus',
        tone: 'steady',
      },
      domains: canonicalDomains(),
      cta: {
        primary: { type: 'open_week', label: 'Открыть неделю', href: '/week' },
        secondary: { type: 'open_history', label: 'История разборов', href: '/reports/history' },
      },
      premium: { subscription_active: true, subscription_active_until: '2026-04-30T00:00:00.000Z' },
    });

    await page.goto('/?mock=1', { waitUntil: 'networkidle' });
    await expectNoCrash(page);
    await expect(page.getByTestId('today-verdict')).toBeVisible();
    await expect(page.getByTestId('today-scores')).toBeVisible();

    await writeShot(page, 'today-canonical-top.png');

    const domains: Array<['energy' | 'money' | 'love' | 'focus', string]> = [
      ['energy', 'today-canonical-domain-energy-expanded.png'],
      ['money', 'today-canonical-domain-money-expanded.png'],
      ['love', 'today-canonical-domain-love-expanded.png'],
      ['focus', 'today-canonical-domain-focus-expanded.png'],
    ];

    for (const [key, file] of domains) {
      await expect(page.getByTestId(`today-score-${key}`)).toBeVisible();
      await page.getByTestId(`today-score-${key}`).screenshot({ path: path.join(OUT_DIR, file) });
    }
  });

  test('refreshes explicit no-data screenshot', async ({ page }) => {
    await ensureOutDir();
    await mountMock(page, {
      version: 'day_brief_canon_v1',
      status: 'partial',
      date: '2026-04-10',
      personalization_level: 'personalized_v2',
      hero: {
        title: 'Данных пока недостаточно.',
        subtitle: 'Канонический слой не собрался по всем сферам.',
        day_type: 'balance',
      },
      domains: {
        energy: { key: 'energy', title: 'Тонус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        money: { key: 'money', title: 'Работа и деньги', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        love: { key: 'love', title: 'Чувства', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
        focus: { key: 'focus', title: 'Фокус', score_status: 'missing', score: null, status: null, description_status: 'missing', description: null, why_status: 'missing', why_astro_text: null, evidence_refs: [] },
      },
      cta: { primary: { type: 'open_week', label: 'Открыть неделю', href: '/week' } },
    });

    await page.goto('/?mock=1', { waitUntil: 'networkidle' });
    await expectNoCrash(page);
    await expect(page.getByTestId('today-no-data-state')).toBeVisible();
    await writeShot(page, 'today-no-data.png');
  });

  test('refreshes explicit error screenshot', async ({ page }) => {
    await ensureOutDir();
    await mountMock(page, {
      version: 'day_brief_canon_v1',
      status: 'failed',
      date: '2026-04-10',
      personalization_level: 'personalized_v2',
      hero: {
        title: 'Расчёт дня не завершён.',
        subtitle: 'Канонический слой вернул честную ошибку без fallback-подмены.',
        day_type: 'caution',
      },
      domains: {
        energy: { key: 'energy', title: 'Тонус', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
        money: { key: 'money', title: 'Работа и деньги', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
        love: { key: 'love', title: 'Чувства', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
        focus: { key: 'focus', title: 'Фокус', score_status: 'failed', score: null, status: null, description_status: 'failed', description: null, why_status: 'failed', why_astro_text: null, evidence_refs: [] },
      },
      cta: { primary: { type: 'open_week', label: 'Открыть неделю', href: '/week' } },
    });

    await page.goto('/?mock=1', { waitUntil: 'networkidle' });
    await expectNoCrash(page);
    await expect(page.getByTestId('today-error-state')).toBeVisible();
    await writeShot(page, 'today-error.png');
  });

  test('refreshes explicit domain-failed screenshot', async ({ page }) => {
    await ensureOutDir();
    const domains = canonicalDomains();
    domains.money = {
      ...domains.money,
      score_status: 'failed',
      score: null,
      status: null,
      description_status: 'failed',
      description: null,
      why_status: 'failed',
      why_astro_text: null,
    };

    await mountMock(page, {
      version: 'day_brief_canon_v1',
      status: 'partial',
      date: '2026-04-10',
      personalization_level: 'personalized_v2',
      hero: {
        title: 'День лучше проходит через один главный вектор.',
        subtitle: 'Одна из сфер не собрала расчёт и показана честно.',
        day_type: 'deep_focus',
      },
      domains,
      cta: { primary: { type: 'open_week', label: 'Открыть неделю', href: '/week' } },
    });

    await page.goto('/?mock=1', { waitUntil: 'networkidle' });
    await expectNoCrash(page);
    await expect(page.getByTestId('today-score-money')).toBeVisible();
    await page.getByTestId('today-score-money').screenshot({ path: path.join(OUT_DIR, 'today-domain-failed.png') });
  });
});
