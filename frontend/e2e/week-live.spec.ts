import { test, expect } from '@playwright/test';

test.describe('Week Tab Live States', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      (window as any).Telegram = {
        WebApp: {
          initData: '123456789',
          ready: () => {},
          expand: () => {},
          close: () => {},
          initDataUnsafe: { user: { id: 123456789, first_name: 'Debug', last_name: 'User' } }
        }
      };
    });
  });

  test('should show generate action for empty state', async ({ page }) => {
    await page.goto('/week');
    await expect(page.getByRole('heading', { name: 'Навигатор недели' })).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('week-ready-state')).toBeVisible();
    await expect(page.getByTestId('week-generate-action')).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('week-generate-action')).toHaveAttribute('data-semantic-block', 'GENERATE_ACTION');
  });

  test('should show valid ready-state content', async ({ page }) => {
    await page.goto('/week');
    const generateAction = page.getByTestId('week-generate-action');
    const overviewPanel = page.getByTestId('week-overview-panel');
    const primaryCta = page.getByTestId('week-primary-cta');

    await expect(page.getByText('Навигатор недели')).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('week-ready-state')).toBeVisible();
    await expect(generateAction.or(overviewPanel).or(primaryCta)).toBeVisible();
  });
});
