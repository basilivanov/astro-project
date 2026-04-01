import nextJest from 'next/jest.js';
import type { Config } from 'jest';

const createJestConfig = nextJest({
  dir: './',
});

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/test/setup.ts'],
  testMatch: ['<rootDir>/test/**/*.test.{ts,tsx}'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!e2e/**',
    '!**/*.d.ts',
    '!**/*.spec.*',
    '!**/*.test.*',
    '!**/__tests__/**',
    '!**/__mocks__/**',
    '!**/__snapshots__/**',
    '!**/*.snap',
    '!.next/**',
    '!.next_*/**',
    '!coverage/**',
    '!node_modules/**',
  ],
  coveragePathIgnorePatterns: [
    '/e2e/',
    '/__tests__/',
    '/__mocks__/',
    '/__snapshots__/',
    '/node_modules/',
    '/coverage/',
    '/\\.next/',
  ],
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['text', 'json-summary', 'html'],
  coverageProvider: 'v8',
  coverageThreshold: {
    global: {
      lines: 95,
    },
  },
};

export default createJestConfig(config);
