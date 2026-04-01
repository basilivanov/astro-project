import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { WeekActionsPanel } from '../../../components/week/week-actions-panel';
import { WeekDomainPanel } from '../../../components/week/week-domain-panel';
import type { WeekSurfaceModel } from '../../../lib/week-brief';

const baseWeek: WeekSurfaceModel = {
  headline: 'Неделя',
  subhead: 'Фокус недели',
  theme: 'Тема',
  weekType: 'balance',
  status: 'ready',
  weekStart: '2026-04-01',
  weekEnd: '2026-04-07',
  timezone: 'Europe/Moscow',
  location: 'Moscow',
  personalizationLevel: 'personal',
  fallbackMode: false,
  reportId: 'week-1',
  dayCards: [],
  domains: [
    {
      key: 'work',
      title: 'Работа и деньги',
      status: 'green',
      value: 74,
      headline: 'Работа и деньги: 74/100',
      advice: 'Держите приоритет простым.',
      why_text: 'Неделя лучше работает через один главный фокус.',
      supporting_factors: [{ label: 'Солнце', explanation_human: 'Собирает внимание', value: 'Сильный сигнал' }],
    },
  ],
  actions: [
    {
      id: 'action-1',
      text: 'Закрыть один глубокий рабочий цикл',
      factor_id: 'factor-1',
      impact: 'high',
      timeframe: 'Начало недели',
      why_text: 'Импульс лучше удерживается без переключений.',
      supporting_factors: [{ label: 'Марс', explanation_human: 'Даёт тягу к завершению' }],
    },
  ],
  risks: [
    {
      id: 'risk-1',
      text: 'Не обещать больше, чем удержите',
      factor_id: 'factor-2',
      impact: 'medium',
      timeframe: 'Вся неделя',
      why_text: 'Перегрузка проявится быстро.',
      supporting_factors: [{ label: 'Нептун', explanation_human: 'Размывает границы' }],
    },
  ],
  factors: [
    { id: 'factor-1', label: 'Марс', impact: 'high', category: 'work', explanation_human: 'Драйвит действие', explanation_astro: null, source_models: [], weight: 0.5 },
    { id: 'factor-2', label: 'Нептун', impact: 'medium', category: 'work', explanation_human: 'Нужны границы', explanation_astro: null, source_models: [], weight: 0.2 },
  ],
  deepSections: [],
  explainability: { confidence: 0.8, birth_time_used: true, factor_count: 2, timing_precision: null, top_signal_source: null, explanation_depth: null },
  confidenceLabel: 'Высокая опора',
  confidenceShortLabel: 'высокая',
  birthTimeLabel: 'с точным временем рождения',
  topSignalLabel: null,
  cta: { primary: null, secondary: null },
  sectionsCount: 0,
  waitMessage: null,
};

describe('Week unified detail panels', () => {
  it('renders domain explainability via detail disclosure card', () => {
    render(<WeekDomainPanel week={baseWeek} />);

    expect(screen.getByTestId('week-domain-explainability-work')).toHaveTextContent('Что повлияло');
    expect(screen.getByTestId('detail-evidence-chips')).toHaveTextContent('green');
    expect(screen.getByTestId('detail-evidence-chips')).toHaveTextContent('74/100');

    fireEvent.click(screen.getByRole('button', { name: 'Что повлияло' }));
    expect(screen.getByTestId('week-domain-explainability-work-factors')).toHaveTextContent('Солнце');
    expect(screen.getByTestId('week-domain-explainability-work')).toHaveTextContent('Неделя лучше работает через один главный фокус.');
  });

  it('renders action and risk explainability via unified detail layer', () => {
    render(<WeekActionsPanel week={baseWeek} />);

    expect(screen.getByTestId('week-actions-list-explainability-1')).toHaveTextContent('Почему это в фокусе');
    expect(screen.getByTestId('week-risks-list-explainability-1')).toHaveTextContent('Почему это важно');
    expect(screen.getAllByTestId('detail-evidence-chips')[0]).toHaveTextContent('Начало недели');

    fireEvent.click(screen.getByRole('button', { name: 'Почему это в фокусе' }));
    expect(screen.getByTestId('week-actions-list-explainability-1-factors')).toHaveTextContent('Марс');

    fireEvent.click(screen.getByRole('button', { name: 'Почему это важно' }));
    expect(screen.getByTestId('week-risks-list-explainability-1-factors')).toHaveTextContent('Нептун');
  });
});
