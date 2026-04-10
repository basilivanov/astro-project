import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { WeekExplainabilityPanel } from '../../components/week/week-explainability-panel';
import type { WeekSurfaceModel } from '../../lib/week-brief';

const makeWeek = (): WeekSurfaceModel => ({
  surfaceMode: 'canonical',
  headline: 'Неделя держит фокус',
  subhead: 'Делайте меньше, но точнее',
  theme: 'Фокус и ритм',
  weekType: 'balance',
  status: 'ready',
  weekStart: '2026-03-30',
  weekEnd: '2026-04-05',
  timezone: 'Europe/Moscow',
  location: 'Moscow',
  personalizationLevel: 'personal',
  fallbackMode: false,
  reportId: 'week-1',
  usesCanonicalWeekBrief: true,
  dayCards: [],
  domains: [],
  actions: [],
  risks: [],
  factors: [
    {
      id: 'factor-1',
      label: 'Фон недели',
      impact: 'high',
      category: 'transit',
      explanation_human: 'Собирайте главное в короткие циклы.',
      explanation_astro: null,
      source_models: null,
      weight: 0.42,
    },
  ],
  detailLayers: [],
  deepSections: [],
  explainabilitySummary: 'Высокая опора на текущие данные. Учтено точное время рождения. Главный слой влияния: личная натальная опора и текущие транзиты.',
  explainabilityDetailItems: [
    { id: 'week-explainability-confidence', title: 'Надёжность сигнала', body: 'Высокая опора на текущие данные', value: '81%' },
    { id: 'week-explainability-birth-time', title: 'Контекст рождения', body: 'Точная карта рождения добавляет больше персональной опоры в недельную интерпретацию.', value: 'Точное время учтено' },
    { id: 'week-explainability-top-signal', title: 'Главный слой влияния', body: 'Именно этот слой сильнее всего формирует краткую weekly summary и рекомендации.', value: 'личная натальная опора и текущие транзиты' },
  ],
  explainability: {
    confidence: 0.81,
    birth_time_used: true,
    factor_count: 1,
    timing_precision: null,
    top_signal_source: 'transit_natal',
    explanation_depth: null,
  },
  confidenceLabel: 'Высокая опора на текущие данные',
  confidenceShortLabel: 'высокая',
  birthTimeLabel: 'учтено точное время рождения',
  topSignalLabel: 'личная натальная опора и текущие транзиты',
  cta: { primary: null, secondary: null },
  sectionsCount: 0,
  waitMessage: null,
});

describe('WeekExplainabilityPanel', () => {
  it('keeps details collapsed until the visible toggle opens them', () => {
    render(<WeekExplainabilityPanel week={makeWeek()} />);

    expect(screen.getByTestId('week-explainability-summary')).toHaveTextContent('Высокая опора на текущие данные. Учтено точное время рождения.');
    expect(screen.getByTestId('week-explainability-chips')).toHaveTextContent('Уверенность: 81%');
    expect(screen.getByTestId('week-explainability-toggle')).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByTestId('week-explainability-details')).not.toBeVisible();

    fireEvent.click(screen.getByTestId('week-explainability-toggle'));

    expect(screen.getByTestId('week-explainability-toggle')).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByTestId('week-explainability-details')).toBeVisible();
    expect(screen.getByTestId('week-explainability-top-layer')).toHaveTextContent('Надёжность сигнала');
    expect(screen.getByTestId('week-explainability-top-layer')).toHaveTextContent('Контекст рождения');
    expect(screen.getByTestId('week-explainability-top-layer')).toHaveTextContent('Главный слой влияния');
    expect(screen.getByTestId('week-explainability-footnote')).toHaveTextContent('короткая опора к чтению');

    fireEvent.click(screen.getByTestId('week-explainability-toggle'));

    expect(screen.getByTestId('week-explainability-toggle')).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByTestId('week-explainability-details')).not.toBeVisible();
  });
});
