import {
  extractReportFallbackText,
  hasReportContent,
  parseReportBlocks,
  type ReportBlock,
} from "../../../components/blocks/report-renderer";
import {
  buildSectionAnchorId,
  estimateReadingMinutes,
  extractSectionPreview,
  formatSectionTitle,
} from "../../../lib/forecast-ui";

export type ReportChunk = {
  id?: string;
  section?: string;
  title?: string | null;
  content?: unknown;
};

export type RenderableSection = {
  id: string;
  anchorId: string;
  section: string;
  title: string;
  blocks: ReportBlock[];
  fallbackText: string | null;
  preview: string | null;
  readingMinutes: number;
};

export type ReadFailureContextInput = {
  reportId: string;
  reportType?: string | null;
  status?: string | null;
  hasCheckoutToken: boolean;
  readEntryPoint: string;
  directEntryPoint: string;
  failureSurface: string;
  failureFlowId: string;
};

export type ReadFailureContext = {
  report_id: string;
  report_type: string;
  status: string;
  entry_point: string;
  retry_cta_id: string;
  support_cta_id: string;
  surface: string;
  flow_id: string;
};

export type ReadContinuityFacts = {
  fixtureId: string | null;
  scenarioLabel: string | null;
  manifestId: string | null;
  clientName: string | null;
  birthDateLocal: string | null;
  birthTimezone: string | null;
  birthTimeKnown: boolean | null;
};

export const SECTION_FALLBACK_MESSAGE =
  "Исходный формат секции не удалось разобрать полностью. Показываем безопасную текстовую версию, чтобы содержание не потерялось.";

export const buildExpandedSections = (sections: RenderableSection[]) =>
  sections.slice(0, 2).reduce<Record<string, boolean>>((acc, section) => {
    acc[section.id] = true;
    return acc;
  }, {});

export const buildSectionToggleState = (
  sections: RenderableSection[],
  nextExpandedValue: boolean,
) =>
  sections.reduce<Record<string, boolean>>((acc, section) => {
    acc[section.id] = nextExpandedValue;
    return acc;
  }, {});

export const prepareRenderableSections = (chunks: unknown): RenderableSection[] => {
  if (!Array.isArray(chunks)) {
    return [];
  }

  return chunks.flatMap((chunk, index) => {
    const section =
      typeof chunk?.section === "string" && chunk.section.trim().length > 0
        ? chunk.section
        : `section_${index + 1}`;
    const blocks = parseReportBlocks(chunk?.content);
    const fallbackText =
      blocks.length === 0
        ? extractReportFallbackText(chunk?.content) ??
          (hasReportContent(chunk?.content) ? SECTION_FALLBACK_MESSAGE : null)
        : null;

    if (blocks.length === 0 && !fallbackText) {
      return [];
    }

    return [
      {
        id:
          typeof chunk?.id === "string" && chunk.id.trim().length > 0
            ? chunk.id
            : section,
        anchorId: buildSectionAnchorId(
          typeof chunk?.id === "string" && chunk.id.trim().length > 0 ? chunk.id : section,
          "read",
        ),
        section,
        title:
          typeof chunk?.title === "string" && chunk.title.trim().length > 0
            ? chunk.title.trim()
            : formatSectionTitle(section),
        blocks,
        fallbackText,
        preview: extractSectionPreview({ blocks, fallbackText }),
        readingMinutes: estimateReadingMinutes({ blocks, fallbackText }),
      },
    ];
  });
};

export const buildReadDescription = (status: string, clientName: string, sectionCount: number) => {
  if (status === "completed") {
    return `Разбор уже собран для ${clientName} и разбит на ${sectionCount} секций. Сначала просмотрите превью, затем раскрывайте только те части, где нужен более детальный ориентир.`;
  }

  if (status === "in_progress" || status === "pending") {
    return `Отчет для ${clientName} еще в работе. Как только секции будут готовы, экран останется в том же сценарии и покажет структуру чтения.`;
  }

  if (sectionCount === 0) {
    return `Разбор для ${clientName} пока не содержит доступных блоков. Можно вернуться позже или запустить повторную сборку.`;
  }

  return `Разбор для ${clientName} доступен в секциях: сначала главная канва, затем детальные блоки по темам.`;
};

export const formatAccessSource = (accessSource: string) => {
  if (accessSource === "report_entitlement") {
    return "Разовый unlock";
  }
  if (accessSource === "subscription") {
    return "Подписка";
  }
  if (accessSource === "credits") {
    return "Пакет вопросов";
  }
  if (accessSource === "trial") {
    return "Пробный доступ";
  }
  if (accessSource === "bypass") {
    return "Внутренний доступ";
  }
  return accessSource;
};

export const READ_STATUS_META: Record<
  string,
  { label: string; description: string; tone: "emerald" | "indigo" | "amber" | "rose" | "slate"; metaValue: string }
> = {
  completed: {
    label: "Готов к чтению",
    description: "Структура уже собрана по секциям",
    tone: "emerald",
    metaValue: "Готово",
  },
  in_progress: {
    label: "В обработке",
    description: "Секции еще собираются",
    tone: "indigo",
    metaValue: "В работе",
  },
  pending: {
    label: "Ожидает сборку",
    description: "Сценарий еще не завершен",
    tone: "amber",
    metaValue: "Ожидание",
  },
  failed: {
    label: "Ошибка сборки",
    description: "Нужен повторный запуск",
    tone: "rose",
    metaValue: "Сбой",
  },
};

export const toErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
};

export const buildReadFailureContext = ({
  reportId,
  reportType,
  status,
  hasCheckoutToken,
  readEntryPoint,
  directEntryPoint,
  failureSurface,
  failureFlowId,
}: ReadFailureContextInput): ReadFailureContext => ({
  report_id: reportId,
  report_type: reportType || "unknown",
  status: status || "failed",
  entry_point: hasCheckoutToken ? readEntryPoint : directEntryPoint,
  retry_cta_id: "read-regenerate-button",
  support_cta_id: "read-failure-history-link",
  surface: failureSurface,
  flow_id: failureFlowId,
});

const readText = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

const readBoolean = (value: unknown): boolean | null => {
  if (typeof value === "boolean") {
    return value;
  }
  return null;
};

const isObject = (value: unknown): value is Record<string, unknown> =>
  Boolean(value) && typeof value === "object" && !Array.isArray(value);

export const extractReadContinuityFacts = (payload: unknown): ReadContinuityFacts => {
  const report = isObject(payload) && isObject(payload.report) ? payload.report : null;
  const personaPack = isObject(payload) && isObject(payload.persona_pack) ? payload.persona_pack : null;
  const fixture = isObject(payload) && isObject(payload.fixture) ? payload.fixture : null;
  const profile = isObject(payload) && isObject(payload.profile) ? payload.profile : null;

  return {
    fixtureId:
      readText(personaPack?.fixture_id) ??
      readText(fixture?.id) ??
      readText(report?.fixture_id),
    scenarioLabel:
      readText(personaPack?.scenario_label) ??
      readText(fixture?.scenario_label) ??
      readText(report?.scenario_label),
    manifestId:
      readText(personaPack?.manifest_id) ??
      readText(fixture?.manifest_id) ??
      readText(report?.fixture_manifest_id),
    clientName:
      readText(profile?.client_name) ??
      readText(fixture?.client_name) ??
      readText(report?.client_name),
    birthDateLocal:
      readText(profile?.birth_date_local) ??
      readText(fixture?.birth_date_local) ??
      readText(report?.birth_date_local),
    birthTimezone:
      readText(profile?.birth_timezone) ??
      readText(fixture?.birth_timezone) ??
      readText(report?.birth_timezone),
    birthTimeKnown:
      readBoolean(profile?.birth_time_known) ??
      readBoolean(fixture?.birth_time_known) ??
      readBoolean(report?.birth_time_known),
  };
};

const isWholeSignEdgeScenario = (facts: ReadContinuityFacts) => facts.scenarioLabel === "whole-sign-edge";

export const buildReadContinuitySummary = (facts: ReadContinuityFacts) => {
  if (facts.birthTimeKnown !== true && !isWholeSignEdgeScenario(facts)) {
    return null;
  }

  const detailParts = [facts.birthDateLocal, facts.birthTimezone].filter((value): value is string => Boolean(value));
  const detail = detailParts.join(" • ");

  return {
    label: isWholeSignEdgeScenario(facts) ? "Safe mode домов сохранён" : "Точное время сохранено",
    value: detail.length > 0 ? detail : "Канонический known-time сценарий",
  };
};

export const buildReadContinuityEvidence = (facts: ReadContinuityFacts) => {
  const items = [
    facts.fixtureId ? `Фикстура: ${facts.fixtureId}` : null,
    facts.scenarioLabel ? `Сценарий: ${facts.scenarioLabel}` : null,
    facts.manifestId ? `Manifest: ${facts.manifestId}` : null,
    isWholeSignEdgeScenario(facts) ? "Safe mode: Whole Sign" : null,
  ].filter((value): value is string => Boolean(value));

  return items;
};
