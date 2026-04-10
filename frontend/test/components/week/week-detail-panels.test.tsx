import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { WeekActionsPanel } from '../../../components/week/week-actions-panel';
import { WeekDayDrawer } from '../../../components/week/week-day-drawer';
import { WeekDayGrid } from '../../../components/week/week-day-grid';
import { WeekDomainPanel } from '../../../components/week/week-domain-panel';
import type { WeekSurfaceModel } from '../../../lib/week-brief';

const baseWeek: WeekSurfaceModel = {
  surfaceMode: 'canonical',
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
  usesCanonicalWeekBrief: true,
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
  detailLayers: [
    {
      id: 'work',
      title: 'Работа и деньги',
      body: 'Неделя лучше работает через один главный фокус.',
      timeframe: null,
      impact: null,
      factors: [{ id: 'work-factor-1', label: 'Солнце', explanationHuman: 'Собирает внимание', explanationAstro: null, value: 'Сильный сигнал', impact: null, source: 'week_supporting_factor', relatedKey: 'work' }],
      source: 'week_domain',
      relatedKey: 'work',
    },
    {
      id: 'action-1',
      title: 'Закрыть один глубокий рабочий цикл',
      body: 'Импульс лучше удерживается без переключений.',
      timeframe: 'Начало недели',
      impact: 'high',
      factors: [{ id: 'action-1-factor-1', label: 'Марс', explanationHuman: 'Даёт тягу к завершению', explanationAstro: null, value: null, impact: null, source: 'week_supporting_factor', relatedKey: 'factor-1' }],
      source: 'week_action',
      relatedKey: 'factor-1',
    },
    {
      id: 'risk-1',
      title: 'Не обещать больше, чем удержите',
      body: 'Перегрузка проявится быстро.',
      timeframe: 'Вся неделя',
      impact: 'medium',
      factors: [{ id: 'risk-1-factor-1', label: 'Нептун', explanationHuman: 'Размывает границы', explanationAstro: null, value: null, impact: null, source: 'week_supporting_factor', relatedKey: 'factor-2' }],
      source: 'week_risk',
      relatedKey: 'factor-2',
    },
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
  it('binds domain styling to status and score fallback', () => {
    const week = {
      ...baseWeek,
      domains: [
        { ...baseWeek.domains[0], key: 'work', status: 'green', value: 74 },
        { ...baseWeek.domains[0], key: 'energy', title: 'Энергия', status: 'yellow', value: 52 },
        { ...baseWeek.domains[0], key: 'focus', title: 'Фокус', status: null, value: 21 },
      ],
    };

    render(<WeekDomainPanel week={week} />);

    expect(screen.getByTestId('week-domain-work')).toHaveAttribute('data-domain-status', 'green');
    expect(screen.getByTestId('week-domain-energy')).toHaveAttribute('data-domain-status', 'yellow');
    expect(screen.getByTestId('week-domain-focus')).toHaveAttribute('data-domain-status', 'red');
  });

  it('renders domain explainability via detail disclosure card', () => {
    render(<WeekDomainPanel week={baseWeek} />);

    expect(screen.getByTestId('week-domain-explainability-work')).toHaveTextContent('Что повлияло');
    expect(screen.getByTestId('week-domain-status-work')).toHaveTextContent('74/100');
    expect(screen.getByTestId('week-domain-work')).not.toHaveTextContent('Работа и деньги: 74/100');

    fireEvent.click(screen.getByRole('button', { name: 'Что повлияло' }));
    expect(screen.getByTestId('week-domain-explainability-work-factors')).toHaveTextContent('Солнце');
    expect(screen.getByTestId('week-domain-explainability-work')).toHaveTextContent('Неделя лучше работает через один главный фокус.');
  });

  it('maps astro explanations into domain disclosure factors', () => {
    const week = {
      ...baseWeek,
      detailLayers: [{
        ...baseWeek.detailLayers[0],
        factors: [{
          id: 'work-factor-astro',
          label: 'Солнце в 10 доме',
          explanationHuman: 'Солнце в 10 доме — усиливает видимость и рабочий фокус',
          explanationAstro: null,
          value: '74/100',
          impact: null,
          source: 'week_supporting_factor',
          relatedKey: 'work',
        }],
      }],
    };

    render(<WeekDomainPanel week={week} />);
    fireEvent.click(screen.getByRole('button', { name: 'Что повлияло' }));
    expect(screen.getByTestId('week-domain-explainability-work-factors')).toHaveTextContent('Солнце в 10 доме');
    expect(screen.getByTestId('week-domain-explainability-work-factors')).toHaveTextContent('усиливает видимость и рабочий фокус');
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

  it('does not inject arbitrary week factors into actions without exact match', () => {
    const week = {
      ...baseWeek,
      actions: [{ id: 'action-x', text: 'Сузить план', factor_id: 'missing-factor', impact: 'green', timeframe: 'week:green' }],
      risks: [],
    };

    render(<WeekActionsPanel week={week} />);
    expect(screen.queryByRole('button', { name: 'Почему это в фокусе' })).toBeNull();
    expect(screen.getByTestId('week-actions-list')).not.toHaveTextContent(/green|week:green/i);
  });

  it('filters all_week tagged global action and risk cards', () => {
    const week = {
      ...baseWeek,
      actions: [
        ...baseWeek.actions,
        { id: 'action-hidden', text: 'Скрытый глобальный action', tag: 'all_week' },
      ],
      risks: [
        ...baseWeek.risks,
        { id: 'risk-hidden', text: 'Скрытый глобальный risk', tag: 'all_week' },
      ],
    };

    render(<WeekActionsPanel week={week} />);
    expect(screen.getByTestId('week-actions-list')).not.toHaveTextContent('Скрытый глобальный action');
    expect(screen.getByTestId('week-risks-list')).not.toHaveTextContent('Скрытый глобальный risk');
  });

  it('caps actions and risks to a compact weekly set', () => {
    const week = {
      ...baseWeek,
      actions: [
        ...baseWeek.actions,
        { id: 'action-2', text: 'Сузить встречи' },
        { id: 'action-3', text: 'Не должен попасть в компактный блок' },
      ],
      risks: [
        ...baseWeek.risks,
        { id: 'risk-2', text: 'Не дробить внимание' },
        { id: 'risk-3', text: 'Лишний риск вне лимита' },
      ],
    };

    render(<WeekActionsPanel week={week} />);
    expect(screen.getByTestId('week-actions-list')).toHaveTextContent('Закрыть один глубокий рабочий цикл');
    expect(screen.getByTestId('week-actions-list')).toHaveTextContent('Сузить встречи');
    expect(screen.getByTestId('week-actions-list')).not.toHaveTextContent('Не должен попасть в компактный блок');
    expect(screen.getByTestId('week-risks-list')).toHaveTextContent('Не обещать больше, чем удержите');
    expect(screen.getByTestId('week-risks-list')).toHaveTextContent('Не дробить внимание');
    expect(screen.getByTestId('week-risks-list')).not.toHaveTextContent('Лишний риск вне лимита');
  });

  it('keeps weekly domain disclosure available even without exact factor match', () => {
    const week = {
      ...baseWeek,
      domains: [{
        key: 'focus',
        title: 'Фокус',
        status: 'green',
        value: 74,
        headline: 'Один приоритет держит неделю',
        advice: 'Сужайте контекст.',
        why_text: null,
        supporting_factors: [],
      }],
      factors: [{ id: 'factor-z', label: 'money:green', impact: 'high', category: 'other', explanation_human: null, explanation_astro: null, source_models: [], weight: 0.1 }],
    };

    render(<WeekDomainPanel week={week} />);
    expect(screen.getByRole('button', { name: 'Что повлияло' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Что повлияло' }));
    expect(screen.getByTestId('week-domain-explainability-focus')).toHaveTextContent('Неделя лучше всего складывается через один главный приоритет');
  });

  it('renders weekly day cards with user-facing semantics instead of raw enum-like status', () => {
    const onDayClick = jest.fn();
    const week: WeekSurfaceModel = {
      ...baseWeek,
      dayCards: [
        {
          date: '2026-04-01',
          weekday: 'wed',
          mode: 'green',
          score: 88,
          headline: 'Фокус на главном',
          peak_window_label: 'Утро',
          best_for: ['Стратегия'],
          avoid: ['Перегруз'],
        },
      ],
    };

    render(<WeekDayGrid week={week} onDayClick={onDayClick} />);

    const card = screen.getByTestId('week-day-card-1');
    expect(card).toHaveTextContent('Ср');
    expect(card).toHaveTextContent('88/100');
    expect(card).toHaveTextContent('Фокус на главном');
    expect(card).toHaveTextContent('Утро');
    expect(card).toHaveTextContent('Избегать: Перегруз');
    expect(card).not.toHaveTextContent(/green|yellow|red/i);

    fireEvent.click(card.querySelector('button') as HTMLElement);
    expect(onDayClick).toHaveBeenCalledWith('2026-04-01');
  });
});


describe('Week day card detail layer', () => {
  it('renders compact day drawer for canonical drill-down', () => {
    render(
      <WeekDayDrawer
        surfaceMode="canonical"
        card={{
          date: '2026-04-01',
          weekday: 'СР, 1 апр',
          mode: 'green',
          score: 88,
          headline: 'Фокус на главном',
          lead: 'День лучше держать через один главный приоритет.',
          practical: [],
          supporting_factors: [],
          details: { why_text: 'День лучше держать через один главный приоритет.', why_title: null, supporting_factors: [] },
          factor_ids: [],
          best_for: ['Стратегия'],
          avoid: ['Суета'],
          peak_window_label: 'Утро',
        }}
      />,
    );

    expect(screen.getByTestId('week-day-drawer')).toHaveTextContent('СР, 1 апр');
    expect(screen.getByTestId('week-day-drawer')).toHaveTextContent('Фокус на главном');
    expect(screen.getByTestId('week-day-drawer-best-for')).toHaveTextContent('Стратегия');
    expect(screen.getByTestId('week-day-drawer-avoid')).toHaveTextContent('Суета');
    expect(screen.getByTestId('week-day-drawer-detail')).toHaveTextContent('День лучше держать через один главный приоритет.');
  });

  it('renders day detail disclosure with practical and supporting factors', () => {
    const { WeekDayGrid } = require('../../../components/week/week-day-grid');
    const week = {
      ...baseWeek,
      dayCards: [{
        date: '2026-04-01',
        weekday: 'wed',
        mode: 'green',
        score: 88,
        headline: 'Фокус на главном',
        lead: 'День лучше держать через один главный приоритет.',
        practical: ['Закрыть одно главное дело', 'Проверить дедлайны'],
        supporting_factors: [{ label: 'Марс', explanation_human: 'Помогает дожимать задачи', value: '88/100' }],
        details: { why_text: 'День лучше держать через один главный приоритет.', why_title: 'Почему день так звучит', supporting_factors: [{ label: 'Марс', explanation_human: 'Помогает дожимать задачи', value: '88/100' }] },
        factor_ids: ['week:theme_anchor'],
        best_for: ['Стратегия'],
        avoid: ['Суета'],
        peak_window_label: 'Утро',
      }],
    };
    render(<WeekDayGrid week={week} onDayClick={() => {}} />);
    expect(screen.getByTestId('week-day-card-1')).toHaveTextContent('Фокус на главном');
    expect(screen.getByTestId('week-day-card-1')).toHaveTextContent('Закрыть одно главное дело');
    fireEvent.click(screen.getByRole('button', { name: 'Детали дня' }));
    expect(screen.getByTestId('week-day-detail-1-factors')).toHaveTextContent('Марс');
    expect(screen.getByTestId('week-day-detail-1')).toHaveTextContent('День лучше держать через один главный приоритет.');
    expect(screen.getByTestId('week-day-card-1')).toHaveTextContent('Лучше: Закрыть одно главное дело · Проверить дедлайны');
  });
});
