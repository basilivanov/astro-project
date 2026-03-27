import { expect, test } from '@playwright/test';
import { bootstrapMockTelegram, expectNoCrash } from './utils';

test.use({ trace: 'off' });

test.describe('Localization Checks', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test('keeps plural forms and fallback copy stable on week surface', async ({ page }) => {
    await page.addInitScript(() => {
      (window as Window & typeof globalThis & { MOCK_WEEK_REPORT_OVERRIDE?: unknown }).MOCK_WEEK_REPORT_OVERRIDE = {
        report: { id: 'week-localization-report', report_type: 'week_forecast', status: 'completed' },
        chunks: [
          {
            id: 'week-chunk-1',
            section: 'focus',
            title: 'Главный фокус недели',
            content: JSON.stringify([{ type: 'paragraph', text: 'Неделя помогает держать ритм.' }]),
          },
          {
            id: 'week-chunk-2',
            section: 'timing',
            title: 'Лучшее время',
            content: JSON.stringify([{ type: 'paragraph', text: 'Вторая половина недели подходит для встреч.' }]),
          },
          {
            id: 'week-chunk-3',
            section: 'week_strategy',
            title: 'Стратегия недели',
            content: 'Даже при частичном ответе пользователь видит безопасный fallback-текст без технических ключей.',
          },
        ],
      };
    });

    await page.goto('/week?mock=1');

    await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
    await expect(page.getByTestId('week-page')).toBeVisible();
    await expect(page.getByTestId('week-overview-panel')).toBeVisible();
    await expect(page.getByText('Главный фокус недели').first()).toBeVisible();
    await expect(page.getByText('Лучшее время').first()).toBeVisible();
    await expect(page.getByText('Даже при частичном ответе пользователь видит безопасный fallback-текст без технических ключей.').first()).toBeVisible();
    await expect(page.getByText('week_strategy')).toHaveCount(0);
    await expectNoCrash(page);
  });

  test('respects Telegram language switch and keeps Russian copy as fallback', async ({ page }) => {
    await page.addInitScript(() => {
      (window as Window & typeof globalThis & { MOCK_USER_OVERRIDE?: unknown }).MOCK_USER_OVERRIDE = {
        id: 123456789,
        first_name: 'Lang',
        last_name: 'Switch',
        language_code: 'en',
      };
    });

    await page.goto('/profile?mock=1');

    await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
    await expect(page.getByTestId('profile-content')).toBeVisible();
    await expect(page.getByRole('main').last()).toBeVisible();
    await expect(page.getByLabel('Профиль пользователя')).toBeVisible();
    await expect(page.getByLabel('Статус подписки')).toBeVisible();
    await expect(page.getByLabel('Реферальная программа')).toBeVisible();
    await expect(page.getByLabel('Разделы профиля')).toBeVisible();
    await expect(page.getByText('Debug User')).toBeVisible();
    await expect(page.getByText('Profile')).toHaveCount(0);
    await expectNoCrash(page);
  });

  test('exposes accessible landmarks and aria labels on consumer shell smoke', async ({ page }) => {
    await page.goto('/profile?mock=1');

    await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Разделы профиля' })).toBeVisible();
    await expect(page.getByLabel('Профиль пользователя')).toBeVisible();
    await expect(page.getByLabel('Статус подписки')).toBeVisible();
    await expect(page.getByLabel('Реферальная программа')).toBeVisible();
    await expectNoCrash(page);
  });
});
