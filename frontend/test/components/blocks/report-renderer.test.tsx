import React from 'react';
import { render, screen } from '@testing-library/react';
import {
  ReportRenderer,
  extractReportFallbackText,
  hasReportContent,
  parseReportBlocks,
  sanitizeReportBlocks,
} from '../../../components/blocks/report-renderer';

describe('report-renderer normalization and fallback', () => {
  it('sanitizes mixed block payloads into deterministic supported blocks', () => {
    const blocks = sanitizeReportBlocks([
      {
        type: 'header',
        text: '  Overview  ',
        level: 9,
      },
      {
        type: 'callout',
        variant: 'LOUD',
        title: 'Heads up',
        text: '  Important note  ',
      },
      {
        type: 'list',
        items: [' Alpha ', { text: 'Beta' }, { content: 'Alpha' }, null],
        ordered: 'yes',
      },
      {
        type: 'key_value',
        items: [
          [' Mood ', ' Stable '],
          { label: 'Risk', value: 'Low' },
          { key: 'Empty', value: '   ' },
        ],
      },
      {
        type: 'table',
        columns: [' Name ', { header: 'Score', align: 'sideways' }, { text: 'Status', nowrap: 1 }],
        rows: [
          [' Alice ', 7, { text: 'Ready' }],
          [{ value: 'Bob' }, false, { label: 'Waiting' }],
          [null, undefined, '   '],
        ],
      },
      {
        type: 'rating',
        value: '4',
        max: 0,
        label: 'Confidence',
      },
      {
        type: 'traffic_lights',
        items: { health: 'green', money: 'yellow', love: 'blue' },
      },
      {
        type: 'markdown',
        content: '```markdown\n**Hello**\n```',
      },
      {
        type: 'unknown',
        text: 'skip',
      },
    ]);

    expect(blocks).toEqual([
      { type: 'header', text: 'Overview', level: 2 },
      { type: 'callout', variant: 'neutral', title: 'Heads up', content: 'Important note' },
      { type: 'list', items: ['Alpha', 'Beta', 'Alpha'], ordered: true },
      {
        type: 'key_value',
        items: [
          { key: 'Mood', value: 'Stable' },
          { key: 'Risk', value: 'Low' },
        ],
      },
      {
        type: 'table',
        columns: [
          { header: 'Name' },
          { header: 'Score', accessorKey: undefined, width: undefined, align: undefined, nowrap: false },
          { header: 'Status', accessorKey: undefined, width: undefined, align: undefined, nowrap: true },
        ],
        rows: [
          ['Alice', '7', 'Ready'],
          ['Bob', 'false', 'Waiting'],
        ],
      },
      { type: 'rating', value: 4, max: undefined, label: 'Confidence' },
      { type: 'traffic_lights', items: { health: 'green', money: 'yellow', love: 'gray' } },
      { type: 'markdown', content: '**Hello**' },
      { type: 'paragraph', text: 'skip' },
    ]);
  });

  it('parses nested report payloads and detects structured content', () => {
    const content = {
      blocks: [
        {
          type: 'paragraph',
          content: '```txt\nStructured text lives here.\n```',
        },
      ],
    };

    expect(parseReportBlocks(content)).toEqual([
      { type: 'paragraph', text: 'Structured text lives here.' },
    ]);
    expect(hasReportContent(content)).toBe(true);
    expect(hasReportContent({ answer: { blocks: [{ type: 'divider' }] } })).toBe(true);
    expect(hasReportContent({ answer: { text: 'tiny' } })).toBe(true);
    expect(parseReportBlocks('```json\n{"blocks":[{"type":"divider"}]}\n```')).toEqual([{ type: 'divider' }]);
  });

  it('extracts readable fallback text and deduplicates direct string fragments', () => {
    const fallback = extractReportFallbackText({
      title: 'Detailed forecast outlook for the next week.',
      summary: 'Detailed forecast outlook for the next week.',
      items: [
        'Mercury retrograde needs careful planning.',
        'Mercury retrograde needs careful planning.',
        'Expect delays, but good results after revision.',
      ],
    });

    expect(fallback).toBe('Detailed forecast outlook for the next week.');

    expect(extractReportFallbackText('short text')).toBeNull();
    expect(extractReportFallbackText('```txt\nReadable fallback sentence, with punctuation.\n```')).toBe(
      'Readable fallback sentence, with punctuation.',
    );
  });

  it('renders fallback card when blocks sanitize to empty', () => {
    render(
      <ReportRenderer
        blocks={[{ type: 'list', items: [null, '   '] }]}
        fallbackTitle="Text fallback title"
        fallbackText="Normalized fallback text that is readable."
      />,
    );

    expect(screen.getByTestId('report-fallback-card')).toBeInTheDocument();
    expect(screen.getByText('Text fallback title')).toBeInTheDocument();
    expect(screen.getByText('Normalized fallback text that is readable.')).toBeInTheDocument();
  });

  it('renders normalized supported blocks without using fallback', () => {
    render(
      <ReportRenderer
        blocks={[
          { type: 'header', text: 'Renderer heading', level: 2 },
          { type: 'paragraph', content: 'Primary paragraph content for users.' },
          { type: 'markdown', content: '```md\n*Bullet-like markdown*\n```' },
        ]}
        fallbackText="Should stay hidden"
      />,
    );

    expect(screen.getByText('Renderer heading')).toBeInTheDocument();
    expect(screen.getByText('Primary paragraph content for users.')).toBeInTheDocument();
    expect(screen.getByText('*Bullet-like markdown*')).toBeInTheDocument();
    expect(screen.queryByTestId('report-fallback-card')).not.toBeInTheDocument();
  });
});
