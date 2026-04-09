import { fireEvent, render, screen } from '@testing-library/react';

import { WeekDayStrip } from '../../../components/week/week-day-strip';
import { type WeekSurfaceModel } from '../../../lib/week-brief';

const week: WeekSurfaceModel = {
  headline: 'Неделя фокуса',
  subhead: 'Краткий ритм',
  theme: 'Тест',
  weekType: 'balance',
  status: 'ready',
  weekStart: '2026-04-01',
  weekEnd: '2026-04-07',
  timezone: null,
  location: null,
  personalizationLevel: 'full',
  fallbackMode: false,
  reportId: 'rep-1',
  dayCards: [],
  dayStrip: [
    {
      date: '2026-04-01',
      weekday: 'СР, 1 апр',
      mode: 'green',
      score: 88,
      headline: 'Фокус на главном',
      lead: null,
      practical: [],
      supporting_factors: [],
      details: { why_text: 'День лучше держать через один ритм.', why_title: 'Почему день так звучит', supporting_factors: [{ label: 'Солнце', explanation_human: 'Собирает фокус' }] },
      factor_ids: ['week:theme_anchor'],
      best_for: ['Стратегия'],
      avoid: ['Суета'],
      peak_window_label: 'Утро',
    },
  ],
  domains: [],
  actions: [],
  risks: [],
  factors: [],
  deepSections: [],
  explainabilitySummary: 'Высокая опора.',
  explainabilityDetailItems: [],
  explainability: { confidence: 0.8, birth_time_used: true, factor_count: 1, timing_precision: null, top_signal_source: null, explanation_depth: null },
  confidenceLabel: 'Высокая опора на текущие данные',
  confidenceShortLabel: 'высокая',
  birthTimeLabel: 'учтено точное время рождения',
  topSignalLabel: null,
  cta: { primary: null, secondary: null },
  sectionsCount: 0,
  waitMessage: null,
};

describe('WeekDayStrip', () => {
  it('renders compact overview cards without detail disclosure', () => {
    const onDayClick = jest.fn();
    render(<WeekDayStrip week={week} onDayClick={onDayClick} />);

    const card = screen.getByTestId('week-day-strip-card-1');
    expect(screen.getByTestId('week-day-strip-section')).toHaveTextContent('Окно и фокус — в одной строке');
    expect(card).toHaveTextContent('СР, 1 апр');
    expect(card).toHaveTextContent('88/100');
    expect(card).toHaveTextContent('Фокус на главном');
    expect(card).toHaveTextContent('Окно Утро · Фокус Стратегия');
    expect(card).toHaveTextContent('День лучше держать через один ритм.');
    expect(card).toHaveTextContent('Солнце');
    expect(card).not.toHaveTextContent('Детали дня');

    fireEvent.click(card.querySelector('button') as HTMLElement);
    expect(onDayClick).toHaveBeenCalledWith('2026-04-01');
  });
});
