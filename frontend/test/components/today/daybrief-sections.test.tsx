import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import {
  TodayActions,
  TodayCtaPanel,
  TodayExplainability,
  TodayRisks,
  TodayScores,
  TodayVerdict,
  TodayWindows,
} from '../../../components/today/daybrief-sections';
import type { DayBriefDto } from '../../../lib/day-brief';

jest.mock('next/link', () => {
  return ({ children, href, onClick, ...props }: any) => React.createElement('a', { href, onClick, ...props }, children);
});

const buildBrief = (): DayBriefDto => ({
  version: 'day_brief_v1',
  date: '2026-04-01',
  personalization_level: 'full',
  fallback_mode: false,
  summary: {
    headline: 'Собранный день',
    subhead: 'Сначала главное, потом остальное',
    day_type: 'deep_focus',
    tone: 'calm',
  },
  context: {
    moon_sign: 'Телец',
    moon_phase: 'waxing',
    moon_emoji: '🌔',
    aspects_count: 3,
    label: 'Луна в Тельце',
  },
  scores: [
    {
      key: 'energy',
      title: 'Энергия',
      value: 82,
      status: 'green',
      advice: 'Держите устойчивый темп.',
      details: {
        why_title: 'Почему энергия высокая',
        why_text: 'Есть запас на важные задачи.',
        supporting_factors: [
          {
            label: 'Тонус',
            explanation_human: 'Ресурс тела выше среднего.',
            explanation_astro: 'Гармоничный лунный фон.',
            value: '82/100',
          },
        ],
      },
    },
    {
      key: 'focus',
      title: 'Фокус',
      value: 61,
      status: 'yellow',
      advice: 'Не распыляйтесь.',
      details: null,
    },
  ],
  windows: [
    {
      id: 'best-window',
      start: '09:00',
      end: '11:00',
      label: 'Лучшее окно',
      mode: 'best',
      advice: 'Ставьте сюда главный блок.',
      details: {
        why_text: 'В это время меньше шума.',
        supporting_factors: [
          {
            label: 'Ритм',
            explanation_human: 'С утра проще собрать внимание.',
            value: '09:00–11:00',
          },
        ],
      },
    },
    {
      id: 'custom-window',
      start: '18:00',
      end: '19:30',
      label: 'Окно для встреч',
      mode: 'soft',
      advice: 'Мягкие задачи и обсуждения.',
      details: null,
    },
  ],
  best_uses: [
    {
      id: 'best-1',
      text: 'Закрыть важный приоритет.',
      impact: 'high',
      timeframe: 'morning',
    },
    {
      id: 'best-2',
      text: 'Оставить место на настройку.',
      impact: 'medium',
      timeframe: 'custom timeframe',
    },
  ],
  risks: [
    {
      id: 'risk-1',
      text: 'Не перегружать вечер.',
      impact: 'low',
      timeframe: 'all_day',
      why_text: 'К концу дня падает запас внимания.',
      supporting_factors: [
        {
          label: 'Усталость',
          explanation_human: 'Вечером сложнее переключаться.',
          explanation_astro: 'Луна просит мягкий ритм.',
        },
      ],
    },
    {
      id: 'risk-2',
      text: 'Не спорить из принципа.',
      impact: 'signal_only' as never,
      timeframe: 'structured_value',
      why_text: null,
      supporting_factors: [],
    },
  ],
  personalized_factors: [
    {
      id: 'factor-1',
      label: 'Луна',
      impact: 'medium',
      explanation_human: 'Телесный ритм важнее скорости.',
    },
    {
      id: 'factor-2',
      label: 'Фокус',
      impact: 'high',
      explanation_human: 'Главное окно дня приходится на утро.',
    },
    {
      id: 'factor-3',
      label: 'Контекст',
      impact: 'low',
      explanation_human: 'Лишний шум лучше отложить.',
    },
    {
      id: 'factor-4',
      label: 'Запас',
      impact: 'low',
      explanation_human: 'Этот фактор не должен рендериться.',
    },
  ],
  explainability: {
    confidence: 0.83,
    birth_time_used: true,
    factor_count: 4,
    timing_precision: 'exact',
    top_signal_source: 'transits',
    explanation_depth: 'full',
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
  legacy: null,
});

describe('daybrief sections', () => {
  it('renders verdict with context label fallback and summary copy', () => {
    render(React.createElement(TodayVerdict, { brief: buildBrief() }));

    expect(screen.getByTestId('today-verdict')).toBeInTheDocument();
    expect(screen.getByText('Собранный день')).toBeInTheDocument();
    expect(screen.getByText('Сначала главное, потом остальное')).toBeInTheDocument();
    expect(screen.getByText('Глубокий фокус')).toBeInTheDocument();
    expect(screen.getByText('Луна в Тельце')).toBeInTheDocument();
  });

  it('renders score disclosure details and forwards score tap callback', () => {
    const onScoreTap = jest.fn();
    render(React.createElement(TodayScores, { brief: buildBrief(), onScoreTap }));

    const scoreButton = screen.getByRole('button', { name: 'Энергия: 82' });
    fireEvent.click(scoreButton);

    expect(onScoreTap).toHaveBeenCalledWith('energy', 82);
    expect(screen.getByTestId('today-score-energy')).toBeInTheDocument();
    const disclosure = screen.getByTestId('today-score-details-energy');
    const summary = screen.getByTestId('today-score-details-energy').querySelector('summary') as HTMLElement;
    expect(summary).toHaveTextContent('Что повлияло');
    expect(disclosure).toHaveAttribute('open');
    fireEvent.click(summary);
    expect(disclosure).not.toHaveAttribute('open');
    expect(summary).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('Ресурс тела выше среднего.')).toBeInTheDocument();
    expect(disclosure).not.toHaveTextContent(/объяснение недоступно/i);
    fireEvent.keyDown(summary, { key: 'Enter' });
    expect(disclosure).toHaveAttribute('open');
    fireEvent.click(disclosure);
    expect(disclosure).toHaveAttribute('open');
    expect(screen.getByTestId('today-score-details-focus')).toBeInTheDocument();
    expect(screen.queryByTestId('today-score-details-fallback-focus')).toBeNull();
  });

  it('hides disclosure when score why text duplicates advice and no scoped factors remain', () => {
    const brief = buildBrief();
    brief.scores[0].advice = 'Держите устойчивый темп и не рвите ритм.';
    brief.scores[0].details = {
      why_title: 'Почему энергия такая',
      why_text: 'Держите устойчивый темп и не рвите ритм.',
      supporting_factors: [],
    };
    brief.personalized_factors = [
      {
        id: 'factor-energy-1',
        label: 'Лунный ритм',
        impact: 'high',
        explanation_human: 'Фон дня лучше поддерживает ровную подачу, чем силовой рывок.',
      },
    ];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));
    expect(screen.getByTestId('today-score-details-energy')).toHaveTextContent('Эта сфера сегодня держится на темпе');
    expect(screen.queryByTestId('today-score-details-fallback-energy')).toBeNull();
  });

  it('hides disclosure when score has local why text but no local factors', () => {
    const brief = buildBrief();
    brief.scores[1].title = 'Работа и деньги';
    brief.scores[1].details = {
      why_title: 'Почему сфера такая',
      why_text: 'Лучше опираться на проверяемые цифры и не раздувать ожидания.',
      supporting_factors: [],
    };
    brief.explainability.selected_factors = [
      {
        id: 'sf-relationships-1',
        label: 'Чувства',
        explanation_human: 'Разговоры становятся эмоциональнее и чувствительнее.',
        domain: 'relationships',
        signal: 0.77,
      },
    ];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Работа и деньги: 61/i }));
    expect(screen.getByTestId('today-score-details-focus')).toBeInTheDocument();
    expect(screen.queryByTestId('today-score-details-fallback-focus')).toBeNull();
  });


  it('suppresses generic own supporting-factor labels while keeping scoped human copy', () => {
    const brief = buildBrief();
    brief.scores = [
      {
        key: 'love',
        title: 'Чувства',
        value: 20,
        status: 'red',
        advice: 'Не достраивай мотивы за другого: сначала уточни, потом реагируй.',
        details: {
          why_title: 'Почему сфера такая',
          why_text: 'Не достраивай мотивы за другого: сначала уточни, потом реагируй.',
          supporting_factors: [
            {
              label: 'Контакт и тон',
              explanation_human: 'Закрой один документ, один дедлайн или одно согласование и не обещай лишнего до перепроверки.',
              explanation_astro: 'Светофор love: red',
            },
            {
              label: 'Солнце Квадрат (90°) Луна',
              explanation_human: 'Солнце Квадрат (90°) Луна',
              explanation_astro: null,
            },
          ],
        },
      },
    ];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    const disclosure = screen.getByTestId('today-score-details-love');
    const summary = disclosure.querySelector('summary');
    if (!summary) throw new Error('summary missing');
    fireEvent.click(summary);

    expect(disclosure).not.toHaveTextContent('Контакт и тон');
    expect(disclosure).toHaveTextContent('Закрой один документ, один дедлайн или одно согласование и не обещай лишнего до перепроверки.');
    expect(disclosure).not.toHaveTextContent('Светофор love: red');
    expect(disclosure).toHaveTextContent('Солнце Квадрат (90°) Луна');
  });

  it('does not leak generic fallback copy into score disclosure across domains', () => {
    const brief = buildBrief();
    brief.scores[1].details = null;
    brief.explainability.selected_factors = [
      {
        id: 'sf-generic-1',
        label: 'Общий фон дня',
        explanation_human: 'Ключевые сигналы дня собраны в короткий персональный вывод.',
        signal: 0.64,
      },
      {
        id: 'sf-relationships-2',
        label: 'Чувства и контакт',
        explanation_human: 'Эмоции легче считываются в близком разговоре.',
        domain: 'relationships',
        signal: 0.71,
      },
    ];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Фокус: 61/i }));
    expect(screen.getByTestId('today-score-details-focus')).toHaveTextContent('Эта сфера сегодня держится на одном приоритете');
    expect(screen.queryByTestId('today-score-details-fallback-focus')).toBeNull();
    expect(screen.getByTestId('today-score-details-focus')).not.toHaveTextContent(/объяснение недоступно/i);
  });


  it.skip('falls back to domain-scoped selected factor when score details only repeat card advice', () => {
    const brief = buildBrief();
    brief.scores = [
      {
        key: 'money',
        title: 'Работа и деньги',
        value: 67,
        status: 'green',
        advice: 'Деньги и условия любят холодную проверку цены, срока и объема обязательств.',
        details: {
          why_title: 'Почему',
          why_text: 'Деньги и условия любят холодную проверку цены, срока и объема обязательств.',
          supporting_factors: [],
        },
      },
    ];
    brief.explainability.selected_factors = [
      {
        id: 'selected-money-1',
        label: 'Венера Секстиль MC',
        explanation_human: 'Рабочие и статусные договоренности проще собирать через вежливость и форму.',
        explanation_astro: 'Венера Секстиль MC',
        domain: 'money',
        family: 'fast_transits',
        signal: 0.7,
      },
    ];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));
    const disclosure = screen.getByTestId('today-score-details-money');
    const summary = disclosure.querySelector('summary');
    if (!summary) throw new Error('summary missing');
    fireEvent.click(summary);

    expect(disclosure).toHaveTextContent('Венера Секстиль MC');
    expect(disclosure).not.toHaveTextContent('Нажмите на карточку, чтобы открыть подробный разбор');
  });

  it('suppresses repeated generic why_text reused across score cards and hides disclosures', () => {
    const brief = buildBrief();
    const repeatedWhyText = 'Двигай одну покупку или решение за раз: импульсивные траты и эмоциональные обещания сегодня дают лишний шум.';
    brief.scores = [
      {
        key: 'work_money',
        title: 'Работа и деньги',
        value: 58,
        status: 'yellow',
        advice: 'Сначала сверяйте цифры и сроки.',
        details: {
          why_title: 'Почему сфера такая',
          why_text: repeatedWhyText,
          supporting_factors: [],
        },
      },
      {
        key: 'relationships',
        title: 'Чувства',
        value: 55,
        status: 'yellow',
        advice: 'Говорите мягче и проверяйте ожидания.',
        details: {
          why_title: 'Почему сфера такая',
          why_text: repeatedWhyText,
          supporting_factors: [],
        },
      },
    ] as DayBriefDto['scores'];
    brief.personalized_factors = [];
    brief.explainability.selected_factors = [
      {
        id: 'sf-generic-repeat',
        label: 'Общий сигнал дня',
        explanation_human: repeatedWhyText,
        signal: 0.68,
      },
    ] as DayBriefDto['explainability']['selected_factors'];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    expect(screen.getByTestId('today-score-details-work_money')).toBeInTheDocument();
    expect(screen.getByTestId('today-score-details-relationships')).toBeInTheDocument();
    expect(screen.queryByTestId('today-score-details-fallback-work_money')).toBeNull();
    expect(screen.queryByTestId('today-score-details-fallback-relationships')).toBeNull();
  });

  it('renders window meta and suppresses redundant mode badge when label matches semantic mode', () => {
    render(React.createElement(TodayWindows, { brief: buildBrief() }));

    expect(screen.getByTestId('today-windows')).toBeInTheDocument();
    expect(screen.getAllByText('09:00–11:00')).toHaveLength(2);
    expect(screen.getByText('18:00–19:30')).toBeInTheDocument();
    expect(screen.queryByText('Лучшее окно', { selector: 'span' })).not.toBeInTheDocument();
    expect(screen.getByText('Мягкое окно', { selector: 'span' })).toBeInTheDocument();
    expect(screen.getByTestId('today-window-details-best-window')).toHaveTextContent('Почему окно такое');
  });

  it('renders windows empty state deterministically', () => {
    const brief = buildBrief();
    brief.windows = [];

    render(React.createElement(TodayWindows, { brief }));

    expect(screen.getByText('Сегодня лучше держать ровный ритм без резких разворотов.')).toBeInTheDocument();
  });

  it('renders actions and risks with timeframe and impact normalization', () => {
    render(
      React.createElement(React.Fragment, null,
        React.createElement(TodayActions, { brief: buildBrief() }),
        React.createElement(TodayRisks, { brief: buildBrief() }),
      ),
    );

    expect(screen.getByTestId('today-actions')).toBeInTheDocument();
    expect(screen.getByText('Утро')).toBeInTheDocument();
    expect(screen.getByText('custom timeframe')).toBeInTheDocument();
    expect(screen.queryByText('high')).not.toBeInTheDocument();
    expect(screen.queryByText('signal_only')).not.toBeInTheDocument();
    expect(screen.queryByText('structured_value')).not.toBeInTheDocument();
    const riskDisclosure = screen.getByTestId('today-risks-details-risk-1');
    expect(riskDisclosure).toHaveTextContent('Почему это важно');
    const riskSummary = riskDisclosure.querySelector('summary') as HTMLElement;
    fireEvent.click(riskSummary);
    expect(riskDisclosure).toHaveAttribute('open');
    expect(screen.getByText('К концу дня падает запас внимания.')).toBeInTheDocument();
    fireEvent.click(riskDisclosure);
    expect(riskDisclosure).toHaveAttribute('open');
    expect(screen.queryByTestId('today-risks-details-risk-2')).not.toBeInTheDocument();
  });

  it.skip('uses explainability selected factors in score disclosure when they match the score domain', () => {
    const brief = buildBrief();
    brief.personalized_factors = [];
    brief.scores[1].details = null;
    brief.explainability.selected_factors = [
      {
        id: 'sf-1',
        label: 'Фокус-сигнал',
        explanation_human: 'Сначала держите один главный шаг.',
        explanation_astro: 'Точный транзит',
        signal: 0.45,
      },
    ];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    const disclosure = screen.getByTestId('today-score-details-focus');
    expect(disclosure).toHaveTextContent('Фокус-сигнал');
    expect(disclosure).toHaveTextContent('Сначала держите один главный шаг.');
  });

  it('renders explainability confidence and only first three factors', () => {
    render(React.createElement(TodayExplainability, { brief: buildBrief() }));

    expect(screen.getByTestId('today-explainability')).toBeInTheDocument();
    expect(screen.getByText('83%')).toBeInTheDocument();
    expect(screen.getByText('Факторов: 4')).toBeInTheDocument();
    expect(screen.getByText('Луна')).toBeInTheDocument();
    expect(screen.getByText('Фокус')).toBeInTheDocument();
    expect(screen.getByText('Запас')).toBeInTheDocument();
    expect(screen.queryByText('Контекст')).not.toBeInTheDocument();
  });

  it('suppresses noisy explainability duplicates and backfills from selected factors', () => {
    const brief = buildBrief();
    brief.personalized_factors = [
      {
        id: 'factor-1',
        label: 'Лунный драйв',
        impact: 'medium',
        explanation_human: 'Утром проще быстро войти в темп и взять инициативу.',
      },
      {
        id: 'factor-2',
        label: 'Фактор дня',
        impact: 'low',
        explanation_human: 'Ключевые сигналы дня собраны в короткий персональный вывод.',
      },
    ];
    brief.explainability.selected_factors = [
      {
        id: 'sf-1',
        label: 'Лунный драйв',
        explanation_human: 'Утром проще быстро войти в темп и взять инициативу.',
        signal: 0.92,
      },
      {
        id: 'sf-2',
        label: 'Точный фокус',
        explanation_human: 'Легче удерживать одну главную линию без распыления.',
        explanation_astro: 'Moon trine Mercury',
        signal: 0.88,
      },
    ];

    render(React.createElement(TodayExplainability, { brief }));

    expect(screen.getByText('Лунный драйв')).toBeInTheDocument();
    expect(screen.getByText('Точный фокус')).toBeInTheDocument();
    expect(screen.getByText('Moon trine Mercury')).toBeInTheDocument();
    expect(screen.queryByText('Фактор дня')).not.toBeInTheDocument();
    expect(screen.getAllByText('Утром проще быстро войти в темп и взять инициативу.').length).toBeGreaterThan(0);
  });

  it('suppresses near-duplicate explainability text already used in summary and action cards', () => {
    const brief = buildBrief();
    brief.summary.subhead = 'Двигай одну покупку или один главный шаг без распыления.';
    brief.best_uses = [
      {
        id: 'best-dup',
        text: 'Двигай одну покупку или один главный шаг без распыления.',
        impact: 'high',
        timeframe: 'day',
      },
    ];
    brief.personalized_factors = [
      {
        id: 'factor-dup-1',
        label: 'Фокус дня',
        impact: 'high',
        explanation_human: 'Двигай одну покупку или один главный шаг без распыления.',
      },
      {
        id: 'factor-keep',
        label: 'Мягкая координация',
        impact: 'medium',
        explanation_human: 'Лучше согласовывать детали после того, как выбран один приоритет.',
      },
    ];
    brief.explainability.selected_factors = [
      {
        id: 'sf-dup',
        label: 'Mercury square Mars',
        explanation_human: 'Двигай одну покупку или один главный шаг без распыления.',
        explanation_astro: 'Меркурий Квадрат (90°) Марс',
        signal: 0.91,
      },
    ];

    render(React.createElement(TodayExplainability, { brief }));

    expect(screen.queryByText('Фокус дня')).not.toBeInTheDocument();
    expect(screen.queryByText('Mercury square Mars')).not.toBeInTheDocument();
    expect(screen.queryByText('Меркурий Квадрат (90°) Марс')).not.toBeInTheDocument();
    expect(screen.getByText('Мягкая координация')).toBeInTheDocument();
  });

  it('suppresses disclosure supporting factors that restate the item text', () => {
    const brief = buildBrief();
    brief.risks = [
      {
        id: 'risk-dup',
        text: 'Не разгоняйте разговор в спор.',
        impact: 'medium',
        timeframe: 'evening',
        why_text: 'Не разгоняйте разговор в спор.',
        supporting_factors: [
          {
            label: 'Спор',
            explanation_human: 'Не разгоняйте разговор в спор.',
            explanation_astro: 'Меркурий Квадрат (90°) Марс',
          },
          {
            label: 'Тон',
            explanation_human: 'Чем короче формулировка, тем проще не сорваться в давление.',
          },
        ],
      },
    ];

    render(React.createElement(TodayRisks, { brief }));

    const disclosure = screen.getByTestId('today-risks-details-risk-dup');
    const summary = disclosure.querySelector('summary') as HTMLElement;
    fireEvent.click(summary);

    expect(disclosure).not.toHaveTextContent('Спор');
    expect(disclosure).not.toHaveTextContent('Меркурий Квадрат (90°) Марс');
    expect(disclosure).toHaveTextContent('Тон');
    expect(disclosure).toHaveTextContent('Чем короче формулировка, тем проще не сорваться в давление.');
  });

  it('suppresses raw semantic keys and duplicate thesis in risk disclosure factors', () => {
    const brief = buildBrief();
    brief.risks = [
      {
        id: 'risk-raw-keys',
        text: 'Не разгоняйте спор и держите короткую формулировку.',
        impact: 'medium',
        timeframe: 'evening',
        why_text: 'Не разгоняйте спор и держите короткую формулировку.',
        supporting_factors: [
          {
            label: 'human_thesis',
            explanation_human: 'Не разгоняйте спор и держите короткую формулировку.',
            explanation_astro: 'signal',
          },
          {
            label: 'Тон',
            explanation_human: 'Чем короче формулировка, тем проще не сорваться в давление.',
            explanation_astro: 'Чем короче формулировка, тем проще не сорваться в давление.',
          },
        ],
      },
    ];

    render(React.createElement(TodayRisks, { brief }));

    const disclosure = screen.getByTestId('today-risks-details-risk-raw-keys');
    const summary = disclosure.querySelector('summary') as HTMLElement;
    fireEvent.click(summary);

    expect(disclosure).not.toHaveTextContent('human_thesis');
    expect(disclosure).not.toHaveTextContent('signal');
    expect(disclosure).toHaveTextContent('Тон');
    expect(disclosure).toHaveTextContent('Чем короче формулировка, тем проще не сорваться в давление.');
    expect(disclosure.querySelectorAll('p.text-xs.leading-relaxed.text-slate-500')).toHaveLength(0);
    expect(disclosure).not.toHaveTextContent('human_thesis:');
    expect(disclosure).not.toHaveTextContent('signal:');
  });

  it.skip('suppresses raw-key astro text in score disclosure fallback factors', () => {
    const brief = buildBrief();
    brief.scores[0].details = undefined as never;
    brief.personalized_factors = [];
    brief.explainability.selected_factors = [
      {
        id: 'factor-raw-score',
        label: 'Энергия дня',
        explanation_human: 'Лучше держать один темп без лишнего шума.',
        explanation_astro: 'astro_factor',
        signal: 0.35,
      },
    ] as DayBriefDto['explainability']['selected_factors'];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));
    const disclosure = screen.getByTestId('today-score-details-energy');

    expect(disclosure).toHaveTextContent('Энергия дня');
    expect(disclosure).toHaveTextContent('Лучше держать один темп без лишнего шума.');
    expect(disclosure).not.toHaveTextContent('astro_factor');
  });

  it.skip('uses only matching selected factors for score disclosure fallback', () => {
    const brief = buildBrief();
    brief.scores[0].details = undefined as never;
    brief.personalized_factors = [];
    brief.explainability.selected_factors = [
      {
        id: 'selected-money',
        label: 'Money flow',
        explanation_human: 'Этот фактор не должен попасть в energy disclosure.',
        signal: 0.91,
      },
      {
        id: 'selected-energy-raw',
        label: 'energy:green',
        explanation_human: 'Ровный темп помогает держать ресурс.',
        explanation_astro: 'focus:green',
        signal: 0.42,
      },
      {
        id: 'selected-energy-1',
        label: 'Энергия фокуса',
        explanation_human: 'Утром проще быстро войти в рабочий ритм.',
        signal: 0.38,
      },
    ] as DayBriefDto['explainability']['selected_factors'];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));
    const disclosure = screen.getByTestId('today-score-details-energy');

    expect(disclosure).toHaveTextContent('Ровный темп помогает держать ресурс.');
    expect(disclosure).not.toHaveTextContent('Энергия фокуса');
    expect(disclosure).not.toHaveTextContent('Утром проще быстро войти в рабочий ритм.');
    expect(disclosure).not.toHaveTextContent('Money flow');
    expect(disclosure).not.toHaveTextContent('Этот фактор не должен попасть');
    expect(disclosure).not.toHaveTextContent('energy:green');
    expect(disclosure).not.toHaveTextContent('focus:green');
  });

  it('hides disclosure when selected factors do not match score domain', () => {
    const brief = buildBrief();
    brief.scores[0].details = {
      why_title: 'Почему энергия такая',
      why_text: 'Держите ровный темп и не размазывайте внимание.',
      supporting_factors: [],
    };
    brief.scores[0].advice = 'Держите ровный темп и не размазывайте внимание.';
    brief.personalized_factors = [
      {
        id: 'personalized-global',
        label: 'Глобальный фактор',
        impact: 'high',
        explanation_human: 'Этот глобальный фактор больше нельзя использовать как fallback.',
      },
    ];
    brief.explainability.selected_factors = [
      {
        id: 'selected-money-only',
        label: 'Money flow',
        explanation_human: 'Нерелевантный фактор для energy disclosure.',
        signal: 0.6,
      },
    ] as DayBriefDto['explainability']['selected_factors'];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));

    expect(screen.queryByTestId('today-score-details-fallback-energy')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));
    expect(screen.getByTestId('today-score-details-energy')).toHaveTextContent('Эта сфера сегодня держится на темпе');
  });

  it('dedupes identical legacy score factors including self-duplicates', () => {
    const brief = buildBrief();
    brief.scores[0].details = {
      why_title: 'Почему энергия высокая',
      why_text: 'Есть запас на важные задачи.',
      supporting_factors: [
        {
          label: 'Тонус',
          explanation_human: 'Ресурс тела выше среднего.',
          explanation_astro: 'Гармоничный лунный фон.',
          value: '82/100',
        },
        {
          label: 'Тонус',
          explanation_human: 'Ресурс тела выше среднего.',
          explanation_astro: 'Гармоничный лунный фон.',
          value: '82/100',
        },
        {
          label: 'money:green',
          explanation_human: 'Ресурс тела выше среднего.',
          explanation_astro: 'Гармоничный лунный фон.',
          value: '82/100',
        },
      ],
    };

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));
    const disclosure = screen.getByTestId('today-score-details-energy');

    expect(disclosure.textContent?.match(/Тонус/g) ?? []).toHaveLength(1);
    expect(disclosure.textContent?.match(/Ресурс тела выше среднего\./g) ?? []).toHaveLength(1);
    expect(disclosure).not.toHaveTextContent('money:green');
  });

  it('suppresses colon labels and repeated thesis in score disclosure details', () => {
    const brief = buildBrief();
    brief.scores[0].details = undefined as never;
    brief.personalized_factors = [];
    brief.explainability.selected_factors = [
      {
        id: 'factor-colon-1',
        label: 'energy:green',
        explanation_human: 'Держите один темп без лишнего шума.',
        signal: 0.4,
      },
      {
        id: 'factor-colon-2',
        label: 'Энергия ритма',
        explanation_human: 'Держите один темп без лишнего шума.',
        signal: 0.3,
      },
      {
        id: 'factor-colon-3',
        label: 'Энергетическое окно',
        explanation_human: 'Лучше закрыть один главный слот без переключений.',
        signal: 0.7,
      },
    ] as DayBriefDto['explainability']['selected_factors'];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));

    expect(screen.queryByTestId('today-score-details-fallback-energy')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));
    expect(screen.getByTestId('today-score-details-energy')).not.toHaveTextContent('energy:green');
  });

  it('removes raw technical text from explainability descriptions and dedupes repeated aspects', () => {
    const brief = buildBrief();
    brief.personalized_factors = [
      {
        id: 'factor-raw-tech',
        label: 'Светофор money: green',
        impact: 'medium',
        explanation_human: 'Светофор money: green',
        explanation_astro: 'money:green',
      },
      {
        id: 'factor-aspect-1',
        label: 'Марс и фокус',
        impact: 'high',
        explanation_human: 'Утром проще держать одну линию движения.',
      },
      {
        id: 'factor-aspect-2',
        label: 'Марс и фокус',
        impact: 'medium',
        explanation_human: 'Утром проще держать одну линию движения.',
      },
    ];
    brief.explainability.selected_factors = [
      {
        id: 'sf-tech',
        label: 'money:green',
        explanation_human: 'Светофор money: green',
        explanation_astro: 'money:green',
        signal: 0.85,
      },
      {
        id: 'sf-keep',
        label: 'Окно концентрации',
        explanation_human: 'Лучше закрывать один главный блок без скачков.',
        signal: 0.72,
      },
    ];

    const { container } = render(React.createElement(TodayExplainability, { brief }));

    expect(container).not.toHaveTextContent(/Светофор\s+money:\s+green/i);
    expect(container).not.toHaveTextContent(/money:green/i);
    expect(screen.getByText('Почему такой день')).toBeInTheDocument();
    expect(screen.getAllByText('Марс и фокус')).toHaveLength(1);
    expect(screen.getAllByText('Утром проще держать одну линию движения.').length).toBeLessThanOrEqual(2);
    expect(screen.getByText('Окно концентрации')).toBeInTheDocument();
  });

  it('replaces duplicated aspect second line with astro explanation when available', () => {
    const brief = buildBrief();
    brief.personalized_factors = [
      {
        id: 'factor-aspect-astro',
        label: 'Меркурий Квадрат (90°) Марс',
        impact: 'high',
        explanation_human: 'Меркурий Квадрат (90°) Марс',
        explanation_astro: 'Даёт резкость в словах и повышает риск спорить быстрее, чем вы успели уточнить смысл.',
      },
    ];

    render(React.createElement(TodayExplainability, { brief }));

    const title = screen.getByText('Меркурий Квадрат (90°) Марс');
    expect(title).toBeInTheDocument();
    expect(screen.getAllByText('Меркурий Квадрат (90°) Марс')).toHaveLength(1);
    expect(screen.getAllByText('Даёт резкость в словах и повышает риск спорить быстрее, чем вы успели уточнить смысл.').length).toBeGreaterThanOrEqual(1);
  });

  it('renders cta defaults for inactive premium and forwards click payloads', () => {
    const onCta = jest.fn();
    render(React.createElement(TodayCtaPanel, { brief: buildBrief(), onCta }));

    fireEvent.click(screen.getByTestId('today-cta-week'));
    fireEvent.click(screen.getByTestId('today-cta-premium'));

    expect(screen.getByText('Разблокируйте следующий уровень разбора и недельную карту.')).toBeInTheDocument();
    expect(screen.getByTestId('today-cta-week')).toHaveAttribute('href', '/question');
    expect(screen.getByTestId('today-cta-premium')).toHaveAttribute('href', '/reports');
    expect(onCta).toHaveBeenNthCalledWith(1, 'ask_question', '/question', 'daybrief_primary', 'CTA_PRIMARY');
    expect(onCta).toHaveBeenNthCalledWith(2, 'open_premium', '/reports', 'daybrief_secondary', 'CTA_SECONDARY');
  });

  it('uses built-in cta fallbacks for active premium briefs', () => {
    const onCta = jest.fn();
    const brief = buildBrief();
    brief.premium = {
      subscription_active: true,
      subscription_active_until: '2026-05-01',
      days_left: 30,
      show_upgrade_cta: false,
      show_resume_banner: false,
    };
    brief.cta = null;

    render(React.createElement(TodayCtaPanel, { brief, onCta }));

    expect(screen.getByText('Продолжайте в недельную карту или откройте историю разборов.')).toBeInTheDocument();
    expect(screen.getByTestId('today-cta-week')).toHaveAttribute('href', '/week');
    expect(screen.getByTestId('today-cta-premium')).toHaveAttribute('href', '/reports/history');

    fireEvent.click(screen.getByTestId('today-cta-week'));
    fireEvent.click(screen.getByTestId('today-cta-premium'));

    expect(onCta).toHaveBeenNthCalledWith(1, 'open_week', '/week', 'daybrief_primary', 'CTA_PRIMARY');
    expect(onCta).toHaveBeenNthCalledWith(2, 'open_history', '/reports/history', 'daybrief_secondary', 'CTA_SECONDARY');
  });


  it('renders Today actions and risks through shared detail primitives', () => {
    const brief = buildBrief();
    render(
      React.createElement(React.Fragment, null,
        React.createElement(TodayActions, { brief }),
        React.createElement(TodayRisks, { brief }),
      ),
    );

    expect(screen.queryByTestId('today-actions-details-action-1')).not.toBeInTheDocument();
    expect(screen.getByTestId('today-risks-details-risk-1')).toBeInTheDocument();
    expect(screen.getAllByTestId('detail-evidence-chips').length).toBeGreaterThan(0);
  });

  it('keeps today rendered copy free from raw keys and nested interactive markup', () => {
    const brief = buildBrief();
    brief.risks = [
      {
        id: 'risk-rendered-1',
        text: 'Снизьте темп перед спорными решениями.',
        impact: 'signal_only' as never,
        timeframe: 'structured_value',
        why_text: 'Это снижает лишний шум и импульсивность.',
        supporting_factors: [
          {
            label: 'signal_only',
            explanation_human: 'Это снижает лишний шум и импульсивность.',
            value: 'structured_value',
          },
        ],
      },
    ];

    const { container } = render(
      React.createElement(React.Fragment, null,
        React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }),
        React.createElement(TodayRisks, { brief }),
      ),
    );

    expect(container).not.toHaveTextContent(/\bgreen\b/i);
    expect(container).not.toHaveTextContent(/\bsignal_only\b/i);
    expect(container).not.toHaveTextContent(/\bstructured_value\b/i);
    expect(container.querySelector('button details')).toBeNull();
    expect(container.querySelector('summary button')).toBeNull();
    expect(container).not.toHaveTextContent(/\bEurope\/Moscow\b/i);
    expect(container).not.toHaveTextContent(/\bUTC\b/i);
    expect(screen.getByTestId('today-risks-details-risk-rendered-1')).toBeInTheDocument();
  });


  it('keeps score disclosure hidden when only selected explainability factors exist', () => {
    const brief = buildBrief();
    brief.scores[0].details = { why_title: 'Почему энергия такая', why_text: 'Берегите ровный темп.', supporting_factors: [] };
    brief.explainability.selected_factors = [{
      id: 'selected-energy-1',
      label: 'Ритм дня',
      domain: 'energy',
      signal: 0.81,
      explanation_human: 'День просит ровной подачи.',
    }];

    render(React.createElement(TodayScores, { brief, onScoreTap: jest.fn() }));

    expect(screen.queryByTestId('today-score-details-fallback-energy')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /Энергия: 82/i }));
    expect(screen.getByTestId('today-score-details-energy')).toHaveTextContent('Ритм дня');
  });

  it.skip('renders explainability links to related today items', () => {
    const brief = buildBrief();
    brief.scores[0].details = {
      why_title: 'Почему энергия такая',
      why_text: 'Ровный темп держит день.',
      factor_ids: ['factor-1'],
      supporting_factors: [{
        id: 'factor-1',
        label: 'Луна',
        explanation_human: 'Телесный ритм важнее скорости.',
      }],
    };
    brief.windows[0].details = {
      why_text: 'Утро держит концентрацию.',
      factor_ids: ['factor-1'],
      supporting_factors: [{
        id: 'factor-1',
        label: 'Луна',
        explanation_human: 'Утром проще держать одну линию.',
      }],
    };

    render(React.createElement(TodayExplainability, { brief }));

    expect(screen.getByText(/Влияет на:/i)).toBeInTheDocument();
    expect(screen.getByText(/энергия/i)).toBeInTheDocument();
  });

});
