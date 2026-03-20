import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_MONTH_FORECAST_BRIDGE_STOREFRONT
// ROLE: Verify month_forecast keeps subscription storefront when bridge flags are off.
// ############################################################################

test.describe('Month forecast storefront alignment', () => {
  test('catalog still presents month forecast as subscription', async ({ page }) => {
    await page.goto('/reports');

    await expect(page.locator('a[href="/create?type=month_forecast"]')).toContainText('299₽/мес');
  });

  test('create keeps month forecast on subscription paywall when runtime bridge flags are off', async ({
    page,
  }) => {
    await page.addInitScript(() => {
      window.sessionStorage.setItem('mock_telegram_user', '1');
      Object.assign(window, {
        MOCK_INIT_DATA_OVERRIDE: 'month-forecast-storefront',
        MOCK_USER_OVERRIDE: { id: 990101, first_name: 'Month', last_name: 'Storefront' },
      });
    });

    await page.route('**/api/users/me', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          full_name: 'Month Storefront',
          can_ask_horary: false,
          can_access_premium: false,
          horary_balance: 0,
          report_unlocks: {
            natal_master: 0,
            month_forecast: 0,
            year_forecast: 0,
            solar_return: 0,
            synastry: 0,
          },
          feature_flags: {
            enable_one_off_entitlements_runtime: false,
            enable_persistent_checkout_sessions: false,
            legacy_premium_subscription_access: true,
          },
        }),
      });
    });

    await page.goto('/create?type=month_forecast&mock=1&runtime=1');

    await expect(page.getByTestId('create-subscription-note')).toContainText('через подписку');
    await expect(page.getByRole('button', { name: /Оформить подписку 299₽\/мес/i })).toBeVisible();
  });
});
