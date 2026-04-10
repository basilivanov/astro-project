import React from 'react';
import { render, screen } from '@testing-library/react';

import { WeekDeepSections } from '../../../components/week/week-deep-sections';
import { type WeekSurfaceModel } from '../../../lib/week-brief';

const baseWeek: WeekSurfaceModel = {
  surfaceMode: 'canonical',
  headline: 'Неделя собрана',
  subhead: 'Короткая карта',
  weekType: 'balance',
  theme: 'Ровный темп',
  weekStart: '2026-04-01',
  weekEnd: '2026-04-07',
  status: 'ready',
  fallbackMode: false,
  usesCanonicalWeekBrief: true,
  dayCards: [],
  domains: [],
  actions: [],
  risks: [],
  factors: [],
  detailLayers: [],
  deepSections: [],
  explainability: { confidence: 0.7, birth_time_used: true, factor_count: 0, timing_precision: null, top_signal_source: null, explanation_depth: null },
  explainabilityDetailItems: [],
  confidenceLabel: 'Высокая опора',
  confidenceShortLabel: 'высокая',
  birthTimeLabel: 'с точным временем рождения',
  topSignalLabel: null,
  cta: { primary: null, secondary: null },
  reportId: null,
  sectionsCount: 0,
  waitMessage: null,
  location: 'Москва',
  timezone: 'Europe/Moscow',
  personalizationLevel: null,
};

describe('WeekDeepSections', () => {
  it('renders stable empty-state copy when deep sections are absent', () => {
    render(<WeekDeepSections week={baseWeek} />);

    expect(screen.getByTestId('week-deep-sections-empty')).toBeInTheDocument();
    expect(screen.getByTestId('week-deep-sections-empty')).toHaveTextContent('Длинное чтение');
    expect(screen.getByTestId('week-deep-sections-empty-copy')).toHaveTextContent('Пока здесь остаётся только короткая недельная карта.');
  });

  it('does not leak raw slug-like titles or fallback summary in deep fallback path', () => {
    render(
      <WeekDeepSections
        week={{
          ...baseWeek,
          deepSections: [
            {
              id: 'week_strategy',
              slug: 'week_strategy',
              title: 'week_strategy',
              summary: 'week_strategy',
              body_markdown: 'week_strategy',
              is_primary: true,
              order: 0,
            },
          ],
        }}
      />,
    );

    expect(screen.getByTestId('week-deep-sections')).toBeInTheDocument();
    expect(screen.getByText('Раздел 1')).toBeInTheDocument();
    expect(screen.queryByText('week_strategy')).not.toBeInTheDocument();
    expect(screen.queryByTestId('report-fallback-card')).not.toBeInTheDocument();
  });

  it('preserves readable user-facing fallback copy for deep sections', () => {
    const fallbackPhrase = 'Неделя требует спокойного темпа и аккуратной расстановки приоритетов.';

    render(
      <WeekDeepSections
        week={{
          ...baseWeek,
          deepSections: [
            {
              id: 'week-strategy',
              slug: 'week_strategy',
              title: null,
              summary: fallbackPhrase,
              body_markdown: fallbackPhrase,
              is_primary: true,
              order: 0,
            },
          ],
        }}
      />,
    );

    expect(screen.getByTestId('report-fallback-card')).toHaveTextContent(fallbackPhrase);
    expect(screen.getByText('Короткая версия раздела')).toBeInTheDocument();
    expect(screen.getAllByText(fallbackPhrase).length).toBeGreaterThanOrEqual(1);
  });
});
