import {
  deriveCreatePageState,
  getCheckoutStatusTone,
  getSolarFallbackLabel,
} from '../../app/create/create-page-helpers';
import type { CheckoutSessionState, CreateProfile } from '../../components/catalog/create-shared';

describe('create-page-helpers', () => {
  const checkoutState = (status: CheckoutSessionState['status']): CheckoutSessionState => ({ status, message: null });

  const baseProfile: CreateProfile = {
    id: 1,
    full_name: 'Test User',
    birth_date: '1990-01-01',
    birth_time: '12:00',
    birth_place: 'Moscow',
    current_location: 'Tbilisi',
    can_access_premium: false,
    can_ask_horary: false,
    feature_flags: { enable_one_off_entitlements_runtime: true, enable_persistent_checkout_sessions: true },
    report_access: {
      solar_return: { allowed: false, remaining_unlocks: 0 },
    },
    report_unlocks: {
      solar_return: 0,
    },
  } as CreateProfile;

  it('derives one-off paywall state for locked premium report', () => {
    const result = deriveCreatePageState({
      type: 'solar_return',
      isHorary: false,
      isSubscriptionProduct: false,
      checkoutToken: null,
      mockQueryEnabled: false,
      profile: baseProfile,
      shouldUseMockProfile: false,
      checkoutState: checkoutState('idle'),
    });

    expect(result.shouldShowOneOffReportUnlockPaywall).toBe(true);
    expect(result.hasOneOffUnlock).toBe(false);
    expect(result.canGeneratePremium).toBe(false);
    expect(result.checkoutBusy).toBe(false);
    expect(result.checkoutMode).toBe('report_unlock');
    expect(result.analyticsFlags).toEqual({
      has_subscription_access: false,
      has_one_off_unlock: false,
      report_unlock_bridge: true,
      should_show_one_off_paywall: true,
    });
  });

  it('derives unlocked premium state when unlock balance exists', () => {
    const result = deriveCreatePageState({
      type: 'solar_return',
      isHorary: false,
      isSubscriptionProduct: false,
      checkoutToken: 'tok_123',
      mockQueryEnabled: false,
      profile: {
        ...baseProfile,
        report_access: { solar_return: { allowed: false, remaining_unlocks: 2 } },
      } as CreateProfile,
      shouldUseMockProfile: false,
      checkoutState: checkoutState('pending'),
    });

    expect(result.availableUnlocks).toBe(2);
    expect(result.hasOneOffUnlock).toBe(true);
    expect(result.canGeneratePremium).toBe(true);
    expect(result.shouldShowOneOffReportUnlockPaywall).toBe(false);
    expect(result.checkoutBusy).toBe(true);
  });

  it('derives free horary access without premium generation', () => {
    const result = deriveCreatePageState({
      type: 'horary',
      isHorary: true,
      isSubscriptionProduct: false,
      checkoutToken: null,
      mockQueryEnabled: false,
      profile: {
        ...baseProfile,
        can_ask_horary: true,
      } as CreateProfile,
      shouldUseMockProfile: false,
      checkoutState: checkoutState('idle'),
    });

    expect(result.canAskFree).toBe(true);
    expect(result.canGeneratePremium).toBe(false);
    expect(result.shouldShowOneOffReportUnlockPaywall).toBe(false);
    expect(result.checkoutMode).toBe('horary');
  });

  it('returns stable solar fallback label priority', () => {
    expect(getSolarFallbackLabel(baseProfile)).toBe('Tbilisi');
    expect(getSolarFallbackLabel({ ...baseProfile, current_location: '', birth_place: 'Paris' } as CreateProfile)).toBe('Paris');
    expect(getSolarFallbackLabel({ ...baseProfile, current_location: '', birth_place: '' } as CreateProfile)).toBe('текущую локацию из профиля');
  });

  it('returns checkout status tone by state', () => {
    expect(getCheckoutStatusTone('failed')).toBe('border-rose-100 bg-rose-50 text-rose-700');
    expect(getCheckoutStatusTone('canceled')).toBe('border-rose-100 bg-rose-50 text-rose-700');
    expect(getCheckoutStatusTone('pending')).toBe('border-emerald-100 bg-emerald-50 text-emerald-700');
  });
});
