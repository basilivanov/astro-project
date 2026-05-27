export type CreateProductInputContext = {
  type?: string | null;
  isHorary: boolean;
  isSynastry: boolean;
  isSolarReturn: boolean;
  mode?: string | null;
  mockQueryEnabled: boolean;
};

export type ProductInputDraft = {
  partnerName: string;
  partnerBirthDate: string;
  partnerBirthLocation: string;
  solarCurrentLocation: string;
};

export function appendQueryParam(path: string, key: string, value: string): string {
  const glue = path.includes("?") ? "&" : "?";
  return `${path}${glue}${key}=${encodeURIComponent(value)}`;
}

export function buildCheckoutReturnPath({
  type,
  mode,
  mockQueryEnabled,
}: Pick<CreateProductInputContext, "type" | "mode" | "mockQueryEnabled">): string {
  if (!type) {
    return "/reports";
  }

  let returnPath = `/create?type=${type}`;
  if (mode === "mock" || mockQueryEnabled) {
    returnPath = appendQueryParam(returnPath, "mock", "1");
    returnPath = appendQueryParam(returnPath, "runtime", "1");
  }
  return returnPath;
}

export function validateCreateInputs(
  context: CreateProductInputContext,
  draft: ProductInputDraft,
  question: string,
  payloadOverride?: Record<string, string | undefined>,
): string | null {
  if (context.isHorary && !question.trim()) {
    return "Пожалуйста, введите вопрос.";
  }

  const partnerBirthDateValue = payloadOverride?.partner_birth_date ?? draft.partnerBirthDate;
  const partnerBirthLocationValue = payloadOverride?.partner_birth_location ?? draft.partnerBirthLocation;

  if (
    context.isSynastry &&
    (!(partnerBirthDateValue || "").trim() || !(partnerBirthLocationValue || "").trim())
  ) {
    return "Для совместимости нужны дата/время и место рождения партнёра.";
  }

  return null;
}

export function buildCreatePayload(
  context: CreateProductInputContext,
  draft: ProductInputDraft,
  question: string,
): Record<string, string | undefined> {
  const payload: Record<string, string | undefined> = {
    report_type: context.type || undefined,
    question: context.isHorary ? question : undefined,
  };

  if (context.isSynastry) {
    payload.partner_name = draft.partnerName.trim() || undefined;
    payload.partner_birth_date = draft.partnerBirthDate.trim() || undefined;
    payload.partner_birth_location = draft.partnerBirthLocation.trim() || undefined;
  }

  if (context.isSolarReturn) {
    payload.solar_current_location = draft.solarCurrentLocation.trim() || undefined;
  }

  return payload;
}

export function restoreProductDraft(
  context: Pick<CreateProductInputContext, "type" | "isSynastry" | "isSolarReturn">,
  currentDraft: ProductInputDraft,
  draftOverride?: Record<string, string | undefined> | null,
): ProductInputDraft {
  if (!context.type || (!context.isSynastry && !context.isSolarReturn) || !draftOverride) {
    return currentDraft;
  }

  const nextDraft: ProductInputDraft = {
    ...currentDraft,
  };

  if (context.isSynastry) {
    if (typeof draftOverride.partner_name === "string") {
      nextDraft.partnerName = draftOverride.partner_name;
    }
    if (typeof draftOverride.partner_birth_date === "string") {
      nextDraft.partnerBirthDate = draftOverride.partner_birth_date;
    }
    if (typeof draftOverride.partner_birth_location === "string") {
      nextDraft.partnerBirthLocation = draftOverride.partner_birth_location;
    }
  }

  if (context.isSolarReturn && typeof draftOverride.solar_current_location === "string") {
    nextDraft.solarCurrentLocation = draftOverride.solar_current_location;
  }

  return nextDraft;
}

export function didProductDraftChange(previousDraft: ProductInputDraft, nextDraft: ProductInputDraft): boolean {
  return (
    nextDraft.partnerName !== previousDraft.partnerName ||
    nextDraft.partnerBirthDate !== previousDraft.partnerBirthDate ||
    nextDraft.partnerBirthLocation !== previousDraft.partnerBirthLocation ||
    nextDraft.solarCurrentLocation !== previousDraft.solarCurrentLocation
  );
}
