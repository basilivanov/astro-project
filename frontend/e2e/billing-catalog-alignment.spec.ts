import { test, expect } from '@playwright/test';

// ############################################################################
// AI_HEADER: E2E_BILLING_CATALOG_ALIGNMENT
// ROLE: Verify storefront pricing matches current billing runtime.
// ############################################################################

test.describe('Billing/Catalog alignment', () => {
  test('catalog presents non-horary as subscription and horary as one-off', async ({ page }) => {
    await page.goto('/reports');

    await expect(page.getByTestId('catalog-billing-note')).toContainText('299₽/мес');
    await expect(page.locator('a[href="/create?type=natal_master"]')).toContainText('299₽/мес');
    await expect(page.locator('a[href="/create?type=year_forecast"]')).toContainText('299₽/мес');
    await expect(page.locator('a[href="/create?type=horary"]')).toContainText('199₽');
  });

  test('create paywall explains subscription access for non-horary products', async ({ page }) => {
    await page.goto('/create?type=natal_master&guest=1');

    await expect(page.getByTestId('create-subscription-note')).toContainText('через подписку');
    await expect(page.getByRole('button', { name: /Оформить подписку 299₽\/мес/i })).toBeVisible();
  });

  test('create paywall keeps horary as one-off purchase', async ({ page }) => {
    await page.goto('/create?type=horary&guest=1');

    await expect(page.getByRole('button', { name: /Оплатить 199₽/i })).toBeVisible();
  });
});
