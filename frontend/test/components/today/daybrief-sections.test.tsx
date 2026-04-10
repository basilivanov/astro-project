import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import {
  TodayCtaPanel,
  TodayScores,
  TodayVerdict,
} from '../../../components/today/daybrief-sections';
import type { DayBriefDto } from '../../../lib/day-brief';

jest.mock('next/link', () => {
  return ({ children, href, onClick, ...props }: any) => React.createElement('a', { href, onClick, ...props }, children);
});

const buildBrief = (): DayBriefDto => ({
  version: 'day_brief_canon_v1',
  status: 'complete',
  date: '2026-04-10',
  personalization_level: 'personalized_v2',
  hero: {
    title: 'Собранный день',
    subtitle: 'Четыре ключевые сферы на сегодня.',
    day_type: 'deep_focus',
    tone: 'calm',
  },
  domains: {
    energy: {
      key: 'energy',
      title: 'Энергия',
      score_status: 'complete',
      score: 82,
      status: 'green',
      description_status: 'complete',
      description: 'Ресурс держится ровно. Лучше работать в устойчивом темпе без резких рывков.',
      why_status: 'complete',
      why_astro_text: 'Твой Марс сегодня включён мягче обычного, поэтому энергия лучше собирается в последовательное действие. Лунный фон поддерживает телесный ритм и не любит перегрузку.',
      evidence_refs: [],
    },
    money: {
      key: 'money',
      title: 'Деньги',
      score_status: 'complete',
      score: 68,
      status: 'yellow',
      description_status: 'complete',
      description: 'Рабочие и денежные вопросы лучше вести через один главный приоритет. Цифры и договорённости сегодня требуют внимательной фиксации.',
      why_status: 'complete',
      why_astro_text: 'Твой 2-й дом денег и личной цены вопроса сейчас звучит через проверку условий, а не через быстрый разгон. Меркурий усиливает тему формулировок и точных цифр.',
      evidence_refs: [],
    },
    love: {
      key: 'love',
      title: 'Любовь',
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
    subscription_active_until: null,
    days_left: null,
    show_upgrade_cta: true,
    show_resume_banner: false,
  },
  cta: {
    primary: { type: 'ask_question', label: 'Спросить совет', href: '/question' },
    secondary: { type: 'open_premium', label: 'Открыть premium', href: '/reports' },
  },
});

describe('daybrief sections', () => {
  it('renders verdict from strict day hero', () => {
    render(React.createElement(TodayVerdict, { brief: buildBrief() }));

    expect(screen.getByTestId('today-verdict')).toBeInTheDocument();
    expect(screen.getByText('Собранный день')).toBeInTheDocument();
    expect(screen.getByText('Четыре ключевые сферы на сегодня.')).toBeInTheDocument();
    expect(screen.getByText('Глубокий фокус')).toBeInTheDocument();
  });

  it('renders only four canonical domain cards with a single why text block', () => {
    const onScoreTap = jest.fn();
    render(React.createElement(TodayScores, { brief: buildBrief(), onScoreTap }));

    expect(screen.getByTestId('today-scores')).toBeInTheDocument();
    expect(screen.getByTestId('today-score-energy')).toBeInTheDocument();
    expect(screen.getByTestId('today-score-money')).toBeInTheDocument();
    expect(screen.getByTestId('today-score-love')).toBeInTheDocument();
    expect(screen.getByTestId('today-score-focus')).toBeInTheDocument();
    expect(screen.queryByText('Лучше использовать')).not.toBeInTheDocument();
    expect(screen.queryByText('Риски дня')).not.toBeInTheDocument();
    expect(screen.queryByText('Временные окна')).not.toBeInTheDocument();
    expect(screen.queryByText(/Сильный сигнал|Фоновый сигнал|Умеренный сигнал/i)).not.toBeInTheDocument();

    const energyWhy = screen.getByTestId('today-score-details-energy');
    expect(energyWhy).toHaveTextContent('Что повлияло');
    expect(energyWhy).toHaveTextContent('Твой Марс сегодня включён мягче обычного');
    expect(energyWhy.querySelectorAll('li')).toHaveLength(0);
  });

  it('renders honest no-data and error states inside domain cards', () => {
    render(React.createElement(TodayScores, { brief: buildBrief(), onScoreTap: jest.fn() }));

    expect(screen.getByTestId('today-score-love')).toHaveTextContent('Нет данных');
    expect(screen.getByTestId('today-score-love')).toHaveTextContent('Нет данных по этой сфере.');
    expect(screen.getByTestId('today-score-love')).toHaveTextContent('Для этой сферы пока нет персонального астрологического объяснения.');

    expect(screen.getByTestId('today-score-focus')).toHaveTextContent('Ошибка');
    expect(screen.getByTestId('today-score-focus')).toHaveTextContent('Ошибка расчёта этой сферы.');
    expect(screen.getByTestId('today-score-focus')).toHaveTextContent('Причина для этой сферы не рассчитана.');
  });

  it('keeps score tap only for complete domains', () => {
    const onScoreTap = jest.fn();
    render(React.createElement(TodayScores, { brief: buildBrief(), onScoreTap }));

    fireEvent.click(screen.getByLabelText('Энергия: 82'));
    expect(onScoreTap).toHaveBeenCalledWith('energy', 82);
    expect(screen.queryByLabelText('Любовь: 0')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Фокус: 0')).not.toBeInTheDocument();
  });

  it('renders CTA panel without day fallback copy', () => {
    const onCta = jest.fn();
    render(React.createElement(TodayCtaPanel, { brief: buildBrief(), onCta }));

    expect(screen.getByText('Перейдите в недельную карту или откройте историю разборов.')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('today-cta-week'));
    fireEvent.click(screen.getByTestId('today-cta-premium'));
    expect(onCta).toHaveBeenNthCalledWith(1, 'ask_question', '/question', 'daybrief_primary', 'CTA_PRIMARY');
    expect(onCta).toHaveBeenNthCalledWith(2, 'open_premium', '/reports', 'daybrief_secondary', 'CTA_SECONDARY');
  });
});
