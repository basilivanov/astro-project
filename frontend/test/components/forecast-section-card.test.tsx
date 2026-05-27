import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { ForecastSectionCard } from '../../components/forecast-section-card';

describe('ForecastSectionCard', () => {
  it('renders collapsed state with fallback meta and no optional fields', () => {
    const onToggle = jest.fn();

    render(
      <ForecastSectionCard
        index={3}
        title="Прогноз на неделю"
        expanded={false}
        onToggle={onToggle}
      >
        <div>Содержимое секции</div>
      </ForecastSectionCard>,
    );

    expect(screen.getByRole('button', { name: /прогноз на неделю/i })).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('03')).toBeInTheDocument();
    expect(screen.getByText('Секция 03')).toBeInTheDocument();
    expect(screen.getByText('Открыть')).toBeInTheDocument();
    expect(screen.queryByText('Содержимое секции')).not.toBeInTheDocument();
    expect(screen.queryByText('Preview text')).not.toBeInTheDocument();
  });

  it('renders expanded state with optional props and section content', () => {
    render(
      <ForecastSectionCard
        index={12}
        title="Детальный разбор"
        preview="Краткое описание раздела"
        anchorId="forecast-section"
        expanded
        onToggle={() => {}}
        badge="Важно"
        meta="Персональный блок"
        className="extra-class"
      >
        <div>Детали прогноза</div>
      </ForecastSectionCard>,
    );

    const section = document.getElementById('forecast-section');
    expect(section).toHaveClass('extra-class');
    expect(screen.getByRole('button', { name: /детальный разбор/i })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Персональный блок')).toBeInTheDocument();
    expect(screen.getByText('Важно')).toBeInTheDocument();
    expect(screen.getByText('Краткое описание раздела')).toBeInTheDocument();
    expect(screen.getByText('Свернуть')).toBeInTheDocument();
    expect(screen.getByText('Детали прогноза')).toBeInTheDocument();
  });

  it('calls onToggle when header button is clicked', () => {
    const onToggle = jest.fn();

    render(
      <ForecastSectionCard
        index={1}
        title="Ещё секция"
        expanded={false}
        onToggle={onToggle}
      >
        <div>Child</div>
      </ForecastSectionCard>,
    );

    fireEvent.click(screen.getByRole('button', { name: /ещё секция/i }));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });
});
