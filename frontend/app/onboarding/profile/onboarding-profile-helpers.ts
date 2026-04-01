export type OnboardingProfileForm = {
  full_name: string;
  birth_date: string;
  birth_time: string;
  birth_time_known: boolean;
  birth_place: string;
  birth_lat: number;
  birth_lon: number;
  birth_timezone: string;
};

export type OnboardingKnownTimeContinuity = {
  label: string;
  value: string;
  evidence: string[];
};

export function createInitialOnboardingProfileForm(): OnboardingProfileForm {
  return {
    full_name: "",
    birth_date: "",
    birth_time: "12:00",
    birth_time_known: true,
    birth_place: "",
    birth_lat: 0,
    birth_lon: 0,
    birth_timezone: "",
  };
}

export function isOnboardingProfileStepValid(step: number, form: OnboardingProfileForm): boolean {
  if (step === 0) return true;
  if (step === 1) return form.full_name.trim().length > 1 && form.birth_date.length > 0;
  if (step === 2) return !form.birth_time_known || form.birth_time.length > 0;
  if (step === 3) return form.birth_place.trim().length > 0 && form.birth_timezone.trim().length > 0;
  return false;
}

export function buildKnownTimeOnboardingContinuity(form: OnboardingProfileForm): OnboardingKnownTimeContinuity | null {
  if (!form.birth_time_known) {
    return null;
  }

  const birthDate = form.birth_date.trim();
  const birthTime = form.birth_time.trim();
  const birthTimezone = form.birth_timezone.trim();

  if (!birthDate || !birthTime || !birthTimezone) {
    return null;
  }

  return {
    label: "Точное время будет сохранено",
    value: `${birthDate} ${birthTime} • ${birthTimezone}`,
    evidence: [
      `Дата: ${birthDate}`,
      `Время: ${birthTime}`,
      `Часовой пояс: ${birthTimezone}`,
    ],
  };
}
