import {
  buildSectionAnchorId,
  estimateReadingMinutes,
  extractSectionPreview,
  formatReadingTime,
  formatReportType,
  formatSectionTitle,
} from '../../lib/forecast-ui';

describe('forecast-ui helpers', () => {
  it('formats known and fallback labels', () => {
    expect(formatSectionTitle('week_strategy')).toBe('Стратегия недели');
    expect(formatSectionTitle('custom_section_name')).toBe('Custom Section Name');
    expect(formatReportType('year_forecast')).toBe('Альманах 2026');
    expect(formatReportType('custom_report')).toBe('custom report');
    expect(formatReadingTime(0)).toBe('1 мин');
    expect(formatReadingTime(7)).toBe('7 мин');
  });

  it('builds stable anchor ids from mixed alphabets and punctuation', () => {
    expect(buildSectionAnchorId(' Секция дня / Focus! ')).toBe('section-секция-дня-focus');
    expect(buildSectionAnchorId('***', 'report')).toBe('report-item');
    expect(buildSectionAnchorId('A__B---C')).toBe('section-a__b-c');
  });

  it('estimates reading minutes from normalized unique block fragments', () => {
    const minutes = estimateReadingMinutes({
      blocks: [
        { type: 'paragraph', text: 'alpha beta gamma' },
        { type: 'header', text: 'Summary' },
        { type: 'markdown', content: 'delta epsilon' },
        { type: 'callout', title: 'Heads up', content: 'zeta eta' },
        { type: 'list', items: ['theta iota', 'theta iota', 'kappa lambda'] },
        { type: 'key_value', items: [{ key: 'Mu', value: 'Nu' }] },
        { type: 'table', columns: [{ header: 'Xi' }], rows: [['omicron', 'pi']] },
        { type: 'rating', label: 'Score', value: 4, max: 5 },
        { type: 'traffic_lights' },
      ],
      fallbackText: 'alpha beta gamma',
      minimum: 2,
    });

    expect(minutes).toBe(2);
  });

  it('returns minimum reading time when there is no readable content', () => {
    expect(estimateReadingMinutes({ blocks: [], fallbackText: '   ', minimum: 3 })).toBe(3);
  });

  it('extracts previews from prioritized fragments and falls back to fallback text', () => {
    expect(extractSectionPreview({
      blocks: [
        { type: 'header', level: 1, text: 'Ignored big header' },
        { type: 'paragraph', text: '  Main insight appears here.  ' },
        { type: 'list', items: ['First point', 'Second point', 'Third point'] },
        { type: 'key_value', items: [{ key: 'Mood', value: 'Stable' }, { key: 'Focus', value: 'High' }] },
      ],
      fallbackText: 'Unused fallback',
      maxLength: 80,
    })).toBe('Main insight appears here. First point');

    expect(extractSectionPreview({
      blocks: [{ type: 'header', level: 2, text: 'Skip me too' }],
      fallbackText: '  fallback text that will be truncated neatly  ',
      maxLength: 20,
    })).toBe('fallback text that…');

    expect(extractSectionPreview({
      blocks: [
        { type: 'rating', label: 'Оценка', value: 8, max: 10 },
        { type: 'traffic_lights' },
      ],
      maxLength: 120,
    })).toBe('Оценка: 8/10 Подсветка недели по ключевым сферам: тонус, деньги и чувства.');

    expect(extractSectionPreview({ blocks: [], fallbackText: null })).toBeNull();
  });

  it('normalizes preview fragments across text, callout, key-value, and rating fallbacks', () => {
    expect(extractSectionPreview({
      blocks: [
        { type: 'text', content: '  Shared fragment  ' },
        { type: 'paragraph', text: 'shared fragment' },
        { type: 'callout', text: '  Callout body  ' },
        { type: 'key_value', items: [{ key: 'Only key' }, { value: 'Solo value' }] },
        { type: 'rating', value: '7' },
      ],
      maxLength: 120,
    })).toBe('Shared fragment Callout body');

    expect(extractSectionPreview({
      blocks: [
        { type: 'key_value', items: [{ key: 'Only key' }, { value: 'Solo value' }] },
        { type: 'rating', value: '7' },
      ],
      maxLength: 120,
    })).toBe('Solo value Оценка 7');
  });

  it('estimates reading minutes for text-only fragments, sparse data, and deduped fallback text', () => {
    expect(estimateReadingMinutes({
      blocks: [
        { type: 'text', content: '  Shared fragment  ' },
        { type: 'paragraph', text: 'shared fragment' },
        { type: 'header', text: '  Reading heading  ' },
        { type: 'callout', text: '  Callout body  ' },
        { type: 'key_value', items: [{ key: 'Only key' }, { value: 'Solo value' }] },
        { type: 'table', columns: [{ header: 42 as never }], rows: [[' Cell value '], 'bad-row' as never] },
        { type: 'rating', value: '7' },
      ],
      fallbackText: 'shared fragment',
    })).toBe(1);

    expect(estimateReadingMinutes({
      blocks: [
        { type: 'rating', label: 'Score', value: 0 },
        { type: 'rating', label: 'Score', value: '0', max: '10' },
      ],
      minimum: 2,
    })).toBe(2);
  });

  it('truncates long previews sourced from primary fragments', () => {
    expect(extractSectionPreview({
      blocks: [
        { type: 'paragraph', text: '12345 67890' },
        { type: 'list', items: ['ABCDE FGHIJ'] },
      ],
      maxLength: 12,
    })).toBe('12345 67890…');
  });
});
