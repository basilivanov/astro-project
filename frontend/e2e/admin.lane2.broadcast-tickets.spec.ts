import { expect, test } from '@playwright/test';
import {
  attachConsoleAndPageErrors,
  bootstrapMockTelegram,
  expectNoCrash,
  expectNoRouteHygieneIssues,
} from './utils';

test.describe('Admin Lane 2 reliability', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMockTelegram(page);
  });

  test('/admin/broadcast loads cleanly, validates required text, and submits successfully', async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

    await page.goto('/admin/broadcast');
    await expectNoCrash(page);

    await expect(page.getByRole('heading', { name: 'Рассылка' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Отправить всем/i })).toBeVisible();
    await expect(page.getByText(/Внимание! Сообщение будет отправлено/i)).toBeVisible();

    const messageField = page.locator('textarea[name="text"]');
    await page.getByRole('button', { name: /Отправить всем/i }).click();
    await expect(messageField).toBeFocused();
    await expect(page).toHaveURL(/\/admin\/broadcast$/);

    await messageField.fill('Lane 2 broadcast check');
    await page.locator('input[name="image_url"]').fill('https://example.com/banner.png');
    await page.getByRole('button', { name: /Отправить всем/i }).click();

    await expect(messageField).toHaveValue('Lane 2 broadcast check');
    await expect(page.locator('input[name="image_url"]')).toHaveValue('https://example.com/banner.png');
    await expect(page.getByRole('button', { name: /Отправить всем/i })).toBeVisible();

    hygiene.dispose();
    await expectNoRouteHygieneIssues('/admin/broadcast', hygiene);
  });

  test('/admin/tickets loads cleanly into a controlled operator state', async ({ page }) => {
    const hygiene = attachConsoleAndPageErrors(page);

    await page.goto('/admin/tickets');
    await expectNoCrash(page);

    await expect(page.getByRole('heading', { name: 'Тикеты поддержки' })).toBeVisible();
    await expect(page.getByText(/^Обращения пользователей \(\d+\)$/)).toBeVisible();
    await expect(page.getByText('Нет активных обращений.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Ответить в Telegram' })).toHaveCount(0);

    hygiene.dispose();
    await expectNoRouteHygieneIssues('/admin/tickets', hygiene);
  });

  test('/admin/tickets renders a controlled empty state when the backend returns no active tickets', async ({ page }) => {
    await page.route('**/api/admin/tickets?limit=50', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'mock failure for empty fallback' }),
      });
    });
    const hygiene = attachConsoleAndPageErrors(page);

    await page.goto('/admin/tickets');
    await expectNoCrash(page);

    await expect(page.getByRole('heading', { name: 'Тикеты поддержки' })).toBeVisible();
    await expect(page.getByText('Обращения пользователей (0)')).toBeVisible();
    await expect(page.getByText('Нет активных обращений.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Ответить в Telegram' })).toHaveCount(0);

    hygiene.dispose();
    await expectNoRouteHygieneIssues('/admin/tickets', hygiene);
  });
});
