import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { WeekExplainabilityPanel } from '../../components/week/week-explainability-panel';
import type { WeekSurfaceModel } from '../../lib/week-brief';

const makeWeek = (): WeekSurfaceModel => ({
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
  deepSections: [],
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
    expect(screen.queryByTestId('week-factor-1')).not.toBeVisible();

    fireEvent.click(screen.getByTestId('week-explainability-toggle'));

    expect(screen.getByTestId('week-explainability-toggle')).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByTestId('week-explainability-details')).toBeVisible();
    expect(screen.getByTestId('week-explainability-details')).toHaveTextContent('Основа: личная натальная опора и текущие транзиты');
    expect(screen.getByTestId('week-factor-1')).toBeVisible();
    expect(screen.getByTestId('week-factor-impact-1')).toHaveTextContent('Основной');

    fireEvent.click(screen.getByTestId('week-explainability-toggle'));

    expect(screen.getByTestId('week-explainability-toggle')).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByTestId('week-explainability-details')).not.toBeVisible();
  });
});
