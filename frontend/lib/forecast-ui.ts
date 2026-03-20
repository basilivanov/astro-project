import type { ReportBlock } from "../components/blocks/report-renderer";

const SECTION_TITLE_MAP: Record<string, string> = {
  executive_summary: "Главное",
  input_frame: "Данные рождения",
  technical_appendix: "Технические детали",
  horary_00_passport: "Паспорт вопроса",
  horary_00_technical: "Данные карты",
  horary_01_verdict: "Вердикт",
  horary_02_radicality: "Радикальность",
  horary_03_significators: "Главные герои",
  horary_04_state: "Состояние сторон",
  horary_05_mechanics: "Механика события",
  horary_06_moon: "Луна как сценарист",
  horary_07_timing: "Тайминг",
  horary_08_conditions: "Условия успеха",
  horary_09_risks: "Риски",
  horary_10_alternatives: "Альтернативы",
  horary_11_summary: "Итог",
  synthesis: "Синтез ядра",
  framework_elements_modes: "Баланс стихий",
  axes_truths: "Оси развития",
  aspects_beginner: "Аспекты планет",
  configurations_geometry: "Фигуры карты",
  dispositor_office: "Цепочки управления",
  core_triad: "Личное ядро (Sol/Lun/Asc)",
  mercury_mind: "Мышление и коммуникация",
  shadow_trauma: "Тень и Травма",
  nodes_growth: "Вектор развития (Узлы)",
  vertex_fate: "Судьбоносные встречи",
  balance_wheel_1_6: "Сферы жизни (Личность)",
  balance_wheel_7_12: "Сферы жизни (Социум)",
  love_intimacy: "Любовь и Близость",
  money_realization: "Деньги и Реализация",
  stars_transuranus: "Высшие смыслы",
  time_cycles: "Текущий период",
  final_synthesis: "Финальная сборка",
  week_strategy: "Стратегия недели",
  month_full_forecast: "Прогноз на месяц",
  month_theme: "Тема месяца",
  decade_overview: "Обзор 10 лет",
  decade_timeline: "Хронология (10 лет)",
  decade_storylines: "Сюжетные линии",
  synastry_overview: "Обзор совместимости",
  synastry_categories: "Анализ по сферам",
  synastry_advice: "Советы",
  solar_theme: "Главная тема года",
  solar_money: "Финансы года",
  solar_love: "Отношения года",
  solar_strategy: "Стратегия года",
};

const REPORT_TYPE_MAP: Record<string, string> = {
  natal_master: "Натальная карта",
  year_forecast: "Альманах 2026",
  month_forecast: "Прогноз на месяц",
  week_forecast: "Стратегия недели",
  ten_year_forecast: "Прогноз на 10 лет",
  horary_answer: "Ответ на вопрос",
  synastry: "Совместимость",
  solar_return: "Соляр",
};

const MAX_PREVIEW_LENGTH = 160;
const READING_WORDS_PER_MINUTE = 120;

const hasText = (value: unknown): value is string =>
  typeof value === "string" && value.trim().length > 0;

const normalizeText = (value: unknown) =>
  hasText(value) ? value.replace(/\s+/g, " ").trim() : null;

const uniq = (fragments: string[]) => {
  const seen = new Set<string>();

  return fragments.filter((fragment) => {
    const key = fragment.toLowerCase();
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};

const truncateText = (value: string, maxLength: number) => {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 1).trimEnd()}…`;
};

const getBlockPreviewFragments = (block: ReportBlock): string[] => {
  switch (block.type) {
    case "paragraph":
    case "text":
      return [normalizeText(block.text ?? block.content)].filter(Boolean) as string[];
    case "header":
      return block.level && block.level <= 2
        ? []
        : [normalizeText(block.text)].filter(Boolean) as string[];
    case "callout":
      return [normalizeText(block.title), normalizeText(block.content ?? block.text)].filter(Boolean) as string[];
    case "list":
      return Array.isArray(block.items)
        ? block.items
            .map((item) => normalizeText(item))
            .filter(Boolean)
            .slice(0, 2) as string[]
        : [];
    case "key_value":
      return Array.isArray(block.items)
        ? block.items
            .map((item) => {
              const key = normalizeText(item?.key);
              const value = normalizeText(item?.value);
              return key && value ? `${key}: ${value}` : value;
            })
            .filter(Boolean)
            .slice(0, 2) as string[]
        : [];
    case "rating": {
      const label = normalizeText(block.label);
      const value = typeof block.value === "number" ? block.value : normalizeText(block.value);
      const max = typeof block.max === "number" ? block.max : normalizeText(block.max);
      if (!value) {
        return [];
      }
      return [label ? `${label}: ${value}${max ? `/${max}` : ""}` : `Оценка ${value}${max ? `/${max}` : ""}`];
    }
    case "traffic_lights":
      return ["Подсветка недели по ключевым сферам: тонус, деньги и чувства."];
    default:
      return [];
  }
};

const getBlockReadingFragments = (block: ReportBlock): string[] => {
  switch (block.type) {
    case "paragraph":
    case "text":
      return [normalizeText(block.text ?? block.content)].filter(Boolean) as string[];
    case "header":
      return [normalizeText(block.text)].filter(Boolean) as string[];
    case "markdown":
      return [normalizeText(block.content)].filter(Boolean) as string[];
    case "callout":
      return [normalizeText(block.title), normalizeText(block.content ?? block.text)].filter(Boolean) as string[];
    case "list":
      return Array.isArray(block.items)
        ? block.items.map((item) => normalizeText(item)).filter(Boolean) as string[]
        : [];
    case "key_value":
      return Array.isArray(block.items)
        ? block.items
            .map((item) => {
              const key = normalizeText(item?.key);
              const value = normalizeText(item?.value);
              return key && value ? `${key} ${value}` : value;
            })
            .filter(Boolean) as string[]
        : [];
    case "table":
      return [
        ...(Array.isArray(block.columns)
          ? block.columns
              .map((column) =>
                typeof column?.header === "string" ? normalizeText(column.header) : null,
              )
              .filter(Boolean)
          : []),
        ...(Array.isArray(block.rows)
          ? block.rows.flatMap((row) =>
              Array.isArray(row)
                ? row.map((cell) => normalizeText(cell)).filter(Boolean)
                : [],
            )
          : []),
      ] as string[];
    case "rating": {
      const label = normalizeText(block.label);
      const value = typeof block.value === "number" ? String(block.value) : normalizeText(block.value);
      const max = typeof block.max === "number" ? String(block.max) : normalizeText(block.max);
      if (!value) {
        return [];
      }
      return [label ? `${label} ${value}${max ? ` из ${max}` : ""}` : `Оценка ${value}${max ? ` из ${max}` : ""}`];
    }
    case "traffic_lights":
      return ["Светофор сфер: тонус, деньги, чувства."];
    default:
      return [];
  }
};

const countWords = (value: string) => value.split(/\s+/).filter(Boolean).length;

export const formatSectionTitle = (id: string) =>
  SECTION_TITLE_MAP[id] || id.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

export const formatReportType = (value: string) => REPORT_TYPE_MAP[value] || value.replace(/_/g, " ");

export const formatReadingTime = (minutes: number) => `${Math.max(1, minutes)} мин`;

export const buildSectionAnchorId = (value: string, prefix = "section") => {
  const normalized = value
    .toLowerCase()
    .replace(/[^a-z0-9а-яё_-]+/gi, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^-|-$/g, "");

  return `${prefix}-${normalized || "item"}`;
};

export const estimateReadingMinutes = ({
  blocks,
  fallbackText,
  minimum = 1,
}: {
  blocks: ReportBlock[];
  fallbackText?: string | null;
  minimum?: number;
}) => {
  const fragments = uniq(
    [
      ...blocks.flatMap((block) => getBlockReadingFragments(block)),
      normalizeText(fallbackText),
    ].filter((fragment): fragment is string => Boolean(fragment)),
  );

  const wordCount = fragments.reduce((sum, fragment) => sum + countWords(fragment), 0);
  if (wordCount === 0) {
    return minimum;
  }

  return Math.max(minimum, Math.ceil(wordCount / READING_WORDS_PER_MINUTE));
};

export const extractSectionPreview = ({
  blocks,
  fallbackText,
  maxLength = MAX_PREVIEW_LENGTH,
}: {
  blocks: ReportBlock[];
  fallbackText?: string | null;
  maxLength?: number;
}) => {
  const fragments = uniq(
    blocks
      .flatMap((block) => getBlockPreviewFragments(block))
      .filter((fragment): fragment is string => Boolean(fragment)),
  );

  const primaryPreview = fragments.slice(0, 2).join(" ");
  if (primaryPreview) {
    return truncateText(primaryPreview, maxLength);
  }

  const fallbackPreview = normalizeText(fallbackText);
  return fallbackPreview ? truncateText(fallbackPreview, maxLength) : null;
};
