import { cn } from '../../lib/utils';

describe('cn', () => {
  it('merges conditional classes', () => {
    expect(cn('px-2', false && 'hidden', 'py-1')).toBe('px-2 py-1');
  });

  it('deduplicates tailwind conflicts', () => {
    expect(cn('px-2', 'px-4', 'text-sm', 'text-lg')).toBe('px-4 text-lg');
  });
});
