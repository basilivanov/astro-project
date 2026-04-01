import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import ReportSectionAccordion from '../../components/report-section-accordion';

jest.mock('../../components/copy-button', () => ({
  __esModule: true,
  default: ({ text, disabled }: { text: string; disabled?: boolean }) => (
    <button data-testid="copy-button" data-text={text} disabled={disabled ?? false}>
      copy
    </button>
  ),
}));

jest.mock('../../components/blocks/report-renderer', () => ({
  __esModule: true,
  ReportRenderer: ({ blocks, fallbackText }: { blocks: unknown; fallbackText?: string }) => (
    <div data-testid="report-renderer" data-blocks={JSON.stringify(blocks)} data-fallback={fallbackText ?? ''}>
      renderer
    </div>
  ),
}));

type ChunkStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

type Chunk = {
  section: string;
  title?: string | null;
  status: ChunkStatus;
  content?: string | null;
  error_message?: string | null;
};

const makeChunk = (overrides: Partial<Chunk> = {}): Chunk => ({
  section: 'summary',
  title: 'Summary',
  status: 'completed',
  content: null,
  error_message: null,
  ...overrides,
});

const renderAccordion = (chunk: Chunk, props: Partial<React.ComponentProps<typeof ReportSectionAccordion>> = {}) =>
  render(
    <ReportSectionAccordion
      reportId="report-1"
      chunk={chunk as React.ComponentProps<typeof ReportSectionAccordion>['chunk']}
      meta="meta"
      badgeClassName="badge"
      errorAtLabel="12:00"
      {...props}
    />,
  );

describe('ReportSectionAccordion', () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    global.fetch = jest.fn() as typeof fetch;
  });

  it('renders fetched blocks when opened with completed section and no inline content', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      new Response(JSON.stringify({ content: JSON.stringify([{ type: 'paragraph', text: 'Loaded text' }]) }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    renderAccordion(makeChunk(), { initiallyOpen: true });

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('/api/admin/reports/report-1/sections/summary'));
    expect(await screen.findByTestId('report-renderer')).toBeInTheDocument();
    expect(screen.getByTestId('report-renderer')).toHaveAttribute(
      'data-blocks',
      JSON.stringify([{ type: 'paragraph', text: 'Loaded text' }]),
    );
    expect(screen.queryByText('Загружаю блоки...')).not.toBeInTheDocument();
  });

  it('does not fetch when initially closed, but fetches after opening', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      new Response(JSON.stringify({ content: JSON.stringify([{ type: 'paragraph', text: 'Deferred load' }]) }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const { container } = renderAccordion(makeChunk(), { initiallyOpen: false });

    expect(global.fetch).not.toHaveBeenCalled();

    const details = container.querySelector('details');
    expect(details).not.toBeNull();
    details!.open = true;
    fireEvent(details!, new Event('toggle'));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    expect(await screen.findByTestId('report-renderer')).toBeInTheDocument();
  });



  it('prefers parsed blocks over fallback card when completed content is valid json', () => {
    renderAccordion(
      makeChunk({ content: JSON.stringify([{ type: 'paragraph', text: 'Inline block' }]) }),
      { initiallyOpen: true },
    );

    expect(screen.getByTestId('report-renderer')).toBeInTheDocument();
    expect(screen.queryByTestId('report-fallback-card')).not.toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('renders fallback card when completed content is plain text', () => {
    renderAccordion(makeChunk({ content: 'Plain text body' }), { initiallyOpen: true });

    expect(screen.getByTestId('report-fallback-card')).toHaveTextContent('Plain text body');
    expect(screen.queryByTestId('report-renderer')).not.toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('shows progress state and placeholder without fetching for in-progress sections', () => {
    renderAccordion(makeChunk({ status: 'in_progress' }), { initiallyOpen: true });

    expect(screen.getByText('Секция сейчас в работе. После ответа модели блоки появятся здесь автоматически.')).toBeInTheDocument();
    expect(screen.getByText('Мини-лог: контент появится после генерации секции.')).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('surfaces action error when regenerate request fails', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(new Response('boom', { status: 500 }));

    renderAccordion(makeChunk({ content: 'Existing content' }), { initiallyOpen: true });

    fireEvent.click(screen.getByRole('button', { name: 'Перегенерировать' }));

    expect(await screen.findByText('Команду не удалось отправить. Повторите попытку.')).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith('/api/admin/reports/report-1/sections/summary/regenerate/async', { method: 'POST' });
  });
});
