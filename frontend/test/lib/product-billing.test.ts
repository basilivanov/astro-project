import {
  getReportUnlockPriceLabel,
  getReportUnlockPriceValue,
  getRuntimeAccessBadge,
  getRuntimePriceLabel,
  getRuntimePriceValue,
  HORARY_PRICE_LABEL,
  HORARY_PRICE_RUB,
  isHoraryProductType,
  isReportUnlockBridgeEnabled,
  isSubscriptionProductType,
  SUBSCRIPTION_PRICE_LABEL,
  SUBSCRIPTION_PRICE_RUB,
} from '../../lib/product-billing';

describe('product-billing helpers', () => {
  it('detects subscription and horary types', () => {
    expect(isSubscriptionProductType('natal_master')).toBe(true);
    expect(isSubscriptionProductType('horary')).toBe(false);
    expect(isHoraryProductType('horary_answer')).toBe(true);
    expect(isHoraryProductType('year_forecast')).toBe(false);
  });

  it('returns runtime labels and values', () => {
    expect(getRuntimePriceLabel('week_forecast')).toBe(SUBSCRIPTION_PRICE_LABEL);
    expect(getRuntimePriceValue('week_forecast')).toBe(SUBSCRIPTION_PRICE_RUB);
    expect(getRuntimePriceLabel('horary')).toBe(HORARY_PRICE_LABEL);
    expect(getRuntimePriceValue('horary')).toBe(HORARY_PRICE_RUB);
  });

  it('returns access badges by product class', () => {
    expect(getRuntimeAccessBadge('week_forecast')).toBe('Разовый доступ');
    expect(getRuntimeAccessBadge('horary')).toBe('Разовый вопрос');
    expect(getRuntimeAccessBadge('unknown')).toBe('Каталог');
  });

  it('enables unlock bridge only for supported products with both flags', () => {
    expect(
      isReportUnlockBridgeEnabled('natal_master', {
        enable_one_off_entitlements_runtime: true,
        enable_persistent_checkout_sessions: true,
      }),
    ).toBe(true);
    expect(
      isReportUnlockBridgeEnabled('week_forecast', {
        enable_one_off_entitlements_runtime: true,
        enable_persistent_checkout_sessions: true,
      }),
    ).toBe(false);
  });

  it('resolves unlock prices with fallback', () => {
    expect(getReportUnlockPriceValue('year_forecast')).toBe(499);
    expect(getReportUnlockPriceValue('missing')).toBe(HORARY_PRICE_RUB);
    expect(getReportUnlockPriceLabel('solar_return')).toBe('199₽');
  });
});
