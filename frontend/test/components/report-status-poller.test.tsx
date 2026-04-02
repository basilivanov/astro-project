import React from 'react';
import { render, screen } from '@testing-library/react';

import ReportStatusPoller from '../../components/report-status-poller';

const refreshMock = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    refresh: refreshMock,
  }),
}));

describe('ReportStatusPoller', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders active copy and refreshes on the default interval for in-progress reports', () => {
    render(<ReportStatusPoller reportId="report-42" status="in_progress" />);

    expect(screen.getByText('Собираем неделю… обновляем каждые 5 с.')).toBeInTheDocument();
    expect(refreshMock).not.toHaveBeenCalled();

    jest.advanceTimersByTime(5000);
    expect(refreshMock).toHaveBeenCalledTimes(1);

    jest.advanceTimersByTime(10000);
    expect(refreshMock).toHaveBeenCalledTimes(3);
  });

  it('rounds sub-second intervals up in the UI and uses the provided polling interval', () => {
    render(<ReportStatusPoller reportId="report-42" status="pending" intervalMs={1200} />);

    expect(screen.getByText('Собираем неделю… обновляем каждые 1 с.')).toBeInTheDocument();

    jest.advanceTimersByTime(1199);
    expect(refreshMock).not.toHaveBeenCalled();

    jest.advanceTimersByTime(1);
    expect(refreshMock).toHaveBeenCalledTimes(1);
  });

  it('does not render or schedule polling for terminal statuses', () => {
    render(<ReportStatusPoller reportId="report-42" status="completed" />);

    expect(screen.queryByText(/Собираем неделю/i)).not.toBeInTheDocument();

    jest.advanceTimersByTime(15000);
    expect(refreshMock).not.toHaveBeenCalled();
  });

  it('does not schedule polling when report id is missing', () => {
    render(<ReportStatusPoller reportId="" status="in_progress" />);

    expect(screen.getByText('Собираем неделю… обновляем каждые 5 с.')).toBeInTheDocument();

    jest.advanceTimersByTime(15000);
    expect(refreshMock).not.toHaveBeenCalled();
  });

  it('cleans up the interval when the component unmounts', () => {
    const clearIntervalSpy = jest.spyOn(window, 'clearInterval');
    const { unmount } = render(<ReportStatusPoller reportId="report-42" status="in_progress" intervalMs={3000} />);

    jest.advanceTimersByTime(3000);
    expect(refreshMock).toHaveBeenCalledTimes(1);

    unmount();
    expect(clearIntervalSpy).toHaveBeenCalledTimes(1);

    jest.advanceTimersByTime(9000);
    expect(refreshMock).toHaveBeenCalledTimes(1);
  });
});
