import React from 'react';
import { render, screen } from '@testing-library/react';
import { DetailDisclosureCard } from '../../../components/detail/detail-disclosure-card';
import { DetailEvidenceChips } from '../../../components/detail/detail-evidence-chips';

describe('detail primitives', () => {
  it('renders disclosure body and normalized factors', () => {
    render(
      React.createElement(DetailDisclosureCard, {
        testId: 'detail-card',
        title: 'Почему так',
        body: 'Потому что сигнал сильнее обычного',
        factors: [{
          id: 'f-1',
          label: 'Меркурий',
          explanationHuman: 'Собирает внимание',
          explanationAstro: 'В сильной позиции',
          value: 'Сильный сигнал',
          impact: null,
          source: 'today_supporting_factor',
          relatedKey: 'focus',
        }],
        isOpen: true,
      }),
    );

    expect(screen.getByTestId('detail-card')).toHaveTextContent('Почему так');
    expect(screen.getByTestId('detail-card')).toHaveTextContent('Потому что сигнал сильнее обычного');
    expect(screen.getByTestId('detail-card-factors')).toHaveTextContent('Меркурий');
    expect(screen.getByTestId('detail-card-factors')).toHaveTextContent('Сильный сигнал');
  });

  it('renders evidence chips from timeframe', () => {
    render(React.createElement(DetailEvidenceChips, { timeframe: 'Утро' }));
    expect(screen.getByTestId('detail-evidence-chips')).toHaveTextContent('Утро');
  });

  it('does not render raw status-like evidence chips', () => {
    render(React.createElement(DetailEvidenceChips, { timeframe: 'week:green', values: ['green', 'all_day', 'Проверить план'] }));
    expect(screen.getByTestId('detail-evidence-chips')).toHaveTextContent('Проверить план');
    expect(screen.getByTestId('detail-evidence-chips')).not.toHaveTextContent(/week:green|green|all_day/i);
  });
});
