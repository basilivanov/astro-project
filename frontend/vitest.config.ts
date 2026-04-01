import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  esbuild: {
    jsx: 'automatic',
    jsxImportSource: 'react',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    globals: true,
    include: ['test/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      reportsDirectory: './coverage',
      include: ['app/**/*.{ts,tsx}', 'components/**/*.{ts,tsx}', 'lib/**/*.{ts,tsx}'],
      exclude: [
        'e2e/**',
        '**/*.d.ts',
        '**/*.spec.*',
        '**/*.test.*',
        '**/__tests__/**',
        '**/__mocks__/**',
        '**/__snapshots__/**',
        '**/*.snap',
        '.next/**',
        '.next_*/*',
        'coverage/**',
        'node_modules/**',
      ],
      thresholds: {
        lines: 95,
      },
    },
  },
});
