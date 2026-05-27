import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { EmptyState, ErrorState, LoadingState } from '../../components/ui-states';

describe('ui states', () => {
  it('renders loading state message', () => {
    render(React.createElement(LoadingState, { message: 'Загрузка', compact: true }));
    expect(screen.getByText('Загрузка')).toBeInTheDocument();
  });

  it('renders error state and calls retry', () => {
    const onRetry = jest.fn();
    render(React.createElement(ErrorState, { error: 'Ошибка сети', onRetry }));
    fireEvent.click(screen.getByRole('button', { name: 'Попробовать снова' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders empty state link action', () => {
    render(
      React.createElement(EmptyState, {
        message: 'Пока пусто',
        actionLabel: 'Перейти',
        actionHref: '/reports',
        actionTestId: 'empty-link',
      }),
    );
    const link = screen.getByTestId('empty-link');
    expect(link).toHaveAttribute('href', '/reports');
    expect(screen.getByText('Пока пусто')).toBeInTheDocument();
  });
});
