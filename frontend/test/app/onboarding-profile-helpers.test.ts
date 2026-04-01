import {
  buildKnownTimeOnboardingContinuity,
  createInitialOnboardingProfileForm,
  isOnboardingProfileStepValid,
} from '../../app/onboarding/profile/onboarding-profile-helpers';

describe('onboarding profile helpers', () => {
  it('keeps the canonical known-time majority path valid across steps', () => {
    const form = {
      ...createInitialOnboardingProfileForm(),
      full_name: 'Ava Meridian',
      birth_date: '1992-08-14',
      birth_time: '06:32',
      birth_place: 'London, UK',
      birth_timezone: 'Europe/London',
    };

    expect(isOnboardingProfileStepValid(1, form)).toBe(true);
    expect(isOnboardingProfileStepValid(2, form)).toBe(true);
    expect(isOnboardingProfileStepValid(3, form)).toBe(true);
  });

  it('requires timezone-backed location evidence before final known-time submit', () => {
    const form = {
      ...createInitialOnboardingProfileForm(),
      full_name: 'Ava Meridian',
      birth_date: '1992-08-14',
      birth_time: '06:32',
      birth_place: 'London, UK',
      birth_timezone: '',
    };

    expect(isOnboardingProfileStepValid(3, form)).toBe(false);
  });

  it('builds continuity evidence only for known-time majority-path payloads', () => {
    expect(
      buildKnownTimeOnboardingContinuity({
        ...createInitialOnboardingProfileForm(),
        full_name: 'Ava Meridian',
        birth_date: '1992-08-14',
        birth_time: '06:32',
        birth_place: 'London, UK',
        birth_timezone: 'Europe/London',
      }),
    ).toEqual({
      label: 'Точное время будет сохранено',
      value: '1992-08-14 06:32 • Europe/London',
      evidence: ['Дата: 1992-08-14', 'Время: 06:32', 'Часовой пояс: Europe/London'],
    });

    expect(
      buildKnownTimeOnboardingContinuity({
        ...createInitialOnboardingProfileForm(),
        birth_date: '1990-01-01',
        birth_time: '12:00',
        birth_timezone: 'Europe/Moscow',
        birth_time_known: false,
      }),
    ).toBeNull();
  });
});
