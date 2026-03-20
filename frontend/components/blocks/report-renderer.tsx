import React from "react";
import { AlertCircle } from "lucide-react";
import { HeaderBlock } from "./header-block";
import { CalloutBlock, CalloutType } from "./callout-block";
import { BulletsBlock } from "./bullets-block";
import { KeyValueBlock, KeyValueItem } from "./key-value-block";
import { TableBlock } from "./table-block";
import { RatingBlock } from "./rating-block";
import { DividerBlock } from "./divider-block";
import { TrafficLights } from "../TrafficLights";

// START_BLOCK_REPORT_RENDERER
// --- Types Definition ---

export type BlockType = 
  | "header" 
  | "paragraph" 
  | "callout" 
  | "list" 
  | "key_value" 
  | "table" 
  | "rating"
  | "divider"
  | "traffic_lights"
  // Legacy/Fallback types
  | "text" 
  | "markdown"; 

export interface ReportBlock {
  type: BlockType;
  [key: string]: any;
}

interface ReportRendererProps {
  blocks: ReportBlock[];
  fallbackText?: string | null;
  fallbackTitle?: string;
}

const SUPPORTED_BLOCK_TYPES = new Set<BlockType>([
  "header",
  "paragraph",
  "callout",
  "list",
  "key_value",
  "table",
  "rating",
  "divider",
  "traffic_lights",
  "text",
  "markdown",
]);

const SUPPORTED_CALLOUT_TYPES = new Set<CalloutType>([
  "info",
  "success",
  "warning",
  "error",
  "neutral",
]);

const hasText = (value: unknown): value is string =>
  typeof value === "string" && value.trim().length > 0;

const isPlainObject = (value: unknown): value is Record<string, any> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const isSupportedBlockType = (value: unknown): value is BlockType =>
  typeof value === "string" && SUPPORTED_BLOCK_TYPES.has(value as BlockType);

const stripCodeFence = (value: string) => {
  const trimmed = value.trim();
  const match = trimmed.match(/^```(?:json|markdown|md|txt)?\s*([\s\S]*?)\s*```$/i);
  return match ? match[1].trim() : trimmed;
};

const normalizeText = (value: unknown): string | null => {
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (!hasText(value)) {
    return null;
  }

  return stripCodeFence(value).trim() || null;
};

const getFirstText = (
  value: Record<string, any>,
  keys: string[] = ["text", "content", "body", "summary", "description", "message", "markdown"],
): string | null => {
  for (const key of keys) {
    const text = normalizeText(value[key]);
    if (text) {
      return text;
    }
  }

  return null;
};

const dedupeTextFragments = (fragments: string[]) => {
  const seen = new Set<string>();

  return fragments.filter((fragment) => {
    const key = fragment.replace(/\s+/g, " ").trim().toLowerCase();
    if (!key || seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};

const normalizeTextArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    const text = normalizeText(item);
    if (text) {
      return [text];
    }

    if (!isPlainObject(item)) {
      return [];
    }

    const nestedText = getFirstText(item, ["text", "content", "value", "label", "name", "title"]);
    return nestedText ? [nestedText] : [];
  });
};

const normalizeKeyValueItems = (value: unknown): KeyValueItem[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (Array.isArray(item)) {
      const key = normalizeText(item[0]);
      const itemValue = normalizeText(item[1]);
      return key && itemValue ? [{ key, value: itemValue }] : [];
    }

    if (!isPlainObject(item)) {
      return [];
    }

    const key = getFirstText(item, ["key", "label", "name", "title"]);
    const itemValue = getFirstText(item, ["value", "text", "content", "description"]);
    return key && itemValue ? [{ key, value: itemValue }] : [];
  });
};

const normalizeTableColumns = (value: unknown) => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((column) => {
    if (hasText(column)) {
      return [{ header: column.trim() }];
    }

    if (!isPlainObject(column)) {
      return [];
    }

    const header = getFirstText(column, ["header", "label", "title", "name", "text"]);
    if (!header) {
      return [];
    }

    return [{
      header,
      accessorKey: typeof column.accessorKey === "string" ? column.accessorKey : undefined,
      width: typeof column.width === "string" ? column.width : undefined,
      align: column.align === "left" || column.align === "center" || column.align === "right" ? column.align : undefined,
      nowrap: Boolean(column.nowrap),
    }];
  });
};

const normalizeTableCell = (value: unknown): string | null => {
  const text = normalizeText(value);
  if (text) {
    return text;
  }

  if (!isPlainObject(value)) {
    return null;
  }

  return getFirstText(value, ["text", "value", "content", "label", "name"]);
};

const normalizeTableRows = (value: unknown): string[][] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((row) => {
    if (!Array.isArray(row)) {
      return [];
    }

    const cells = row.map(normalizeTableCell);
    if (cells.every((cell) => cell === null)) {
      return [];
    }

    return [cells.map((cell) => cell ?? "")];
  });
};

const toFiniteNumber = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
};

const normalizeCalloutType = (value: unknown): CalloutType =>
  typeof value === "string" && SUPPORTED_CALLOUT_TYPES.has(value as CalloutType)
    ? (value as CalloutType)
    : "neutral";

const normalizeLight = (value: unknown) =>
  value === "green" || value === "yellow" || value === "red" || value === "gray"
    ? value
    : "gray";

const normalizeTrafficLights = (value: unknown) => {
  if (!isPlainObject(value)) {
    return null;
  }

  return {
    health: normalizeLight(value.health),
    money: normalizeLight(value.money),
    love: normalizeLight(value.love),
  };
};

const normalizeBlock = (value: unknown): ReportBlock | null => {
  const primitiveText = normalizeText(value);
  if (primitiveText) {
    return { type: "paragraph", text: primitiveText };
  }

  if (!isPlainObject(value)) {
    return null;
  }

  const type = isSupportedBlockType(value.type) ? value.type : null;

  if (!type) {
    const listItems = normalizeTextArray(value.items);
    if (listItems.length > 0) {
      return { type: "list", items: listItems, ordered: Boolean(value.ordered) };
    }

    const text = getFirstText(value);
    return text ? { type: "paragraph", text } : null;
  }

  switch (type) {
    case "header": {
      const text = getFirstText(value, ["text", "content", "title"]);
      if (!text) {
        return null;
      }

      const level = toFiniteNumber(value.level);
      return {
        type: "header",
        text,
        level: level && level >= 1 && level <= 6 ? level : 2,
      };
    }

    case "paragraph":
    case "text": {
      const text = getFirstText(value, ["text", "content", "body", "markdown"]);
      return text ? { type, text } : null;
    }

    case "markdown": {
      const content = getFirstText(value, ["content", "text", "markdown", "body"]);
      return content ? { type: "markdown", content } : null;
    }

    case "callout": {
      const title = getFirstText(value, ["title", "label", "heading"]);
      const content = getFirstText(value, ["content", "text", "body", "description"]);

      if (!title && !content) {
        return null;
      }

      return {
        type: "callout",
        variant: normalizeCalloutType(value.variant ?? value.tone),
        title: title ?? undefined,
        content: content ?? title,
      };
    }

    case "list": {
      const items = normalizeTextArray(value.items ?? value.content ?? value.rows);
      return items.length > 0
        ? { type: "list", items, ordered: Boolean(value.ordered) }
        : null;
    }

    case "key_value": {
      const items = normalizeKeyValueItems(value.items);
      return items.length > 0 ? { type: "key_value", items } : null;
    }

    case "table": {
      const columns = normalizeTableColumns(value.columns ?? value.headers);
      const rows = normalizeTableRows(value.rows);

      return columns.length > 0 && rows.length > 0
        ? { type: "table", columns, rows }
        : null;
    }

    case "rating": {
      const ratingValue = toFiniteNumber(value.value ?? value.rating);
      if (ratingValue === null) {
        return null;
      }

      const max = toFiniteNumber(value.max);
      const label = getFirstText(value, ["label", "title", "name"]);

      return {
        type: "rating",
        value: ratingValue,
        max: max && max > 0 ? max : undefined,
        label: label ?? undefined,
      };
    }

    case "divider":
      return { type: "divider" };

    case "traffic_lights": {
      const items = normalizeTrafficLights(value.items ?? value.lights ?? value.content);
      return items ? { type: "traffic_lights", items } : null;
    }

    default:
      return null;
  }
};

const resolveReportContent = (content: unknown): unknown => {
  if (typeof content !== "string") {
    return content;
  }

  const normalized = normalizeText(content);
  if (!normalized) {
    return "";
  }

  try {
    return JSON.parse(normalized);
  } catch {
    return normalized;
  }
};

const hasStructuredContent = (value: unknown, depth = 0): boolean => {
  if (depth > 5 || value == null) {
    return false;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return true;
  }

  if (typeof value === "string") {
    return normalizeText(value) !== null;
  }

  if (Array.isArray(value)) {
    return value.some((item) => hasStructuredContent(item, depth + 1));
  }

  if (!isPlainObject(value)) {
    return false;
  }

  if (Array.isArray(value.blocks)) {
    return hasStructuredContent(value.blocks, depth + 1);
  }

  return Object.values(value).some((item) => hasStructuredContent(item, depth + 1));
};

const collectStructuredText = (value: unknown, depth = 0): string[] => {
  if (depth > 5 || value == null) {
    return [];
  }

  const directText = normalizeText(value);
  if (directText) {
    return [directText];
  }

  if (Array.isArray(value)) {
    return value.flatMap((item) => collectStructuredText(item, depth + 1));
  }

  if (!isPlainObject(value)) {
    return [];
  }

  if (Array.isArray(value.blocks)) {
    return collectStructuredText(value.blocks, depth + 1);
  }

  const preferredKeys = ["title", "text", "content", "body", "summary", "description", "message", "markdown", "value", "label"];
  const preferredFragments = preferredKeys.flatMap((key) => collectStructuredText(value[key], depth + 1));
  if (preferredFragments.length > 0) {
    return preferredFragments;
  }

  if (Array.isArray(value.items)) {
    return collectStructuredText(value.items, depth + 1);
  }

  return Object.values(value).flatMap((item) => collectStructuredText(item, depth + 1));
};

const looksReadableText = (value: string) => {
  const normalized = value.replace(/\s+/g, " ").trim();

  if (normalized.length >= 28) {
    return true;
  }

  if (/\s/.test(normalized) && normalized.length >= 12) {
    return true;
  }

  return /[.!?,:;]/.test(normalized) && normalized.length >= 10;
};

export const sanitizeReportBlocks = (blocks: unknown): ReportBlock[] => {
  if (!Array.isArray(blocks)) {
    return [];
  }

  return blocks.flatMap((block) => {
    const normalized = normalizeBlock(block);
    return normalized ? [normalized] : [];
  });
};

export const parseReportBlocks = (content: unknown): ReportBlock[] => {
  const resolvedContent = resolveReportContent(content);

  if (Array.isArray(resolvedContent)) {
    return sanitizeReportBlocks(resolvedContent);
  }

  if (isPlainObject(resolvedContent)) {
    if (Array.isArray(resolvedContent.blocks)) {
      return sanitizeReportBlocks(resolvedContent.blocks);
    }

    const singleBlock = normalizeBlock(resolvedContent);
    return singleBlock ? [singleBlock] : [];
  }

  return [];
};

export const hasReportContent = (content: unknown): boolean =>
  hasStructuredContent(resolveReportContent(content));

export const extractReportFallbackText = (content: unknown): string | null => {
  const resolvedContent = resolveReportContent(content);

  if (typeof resolvedContent === "string") {
    const text = normalizeText(resolvedContent);
    return text && looksReadableText(text) ? text : null;
  }

  const fragments = dedupeTextFragments(collectStructuredText(resolvedContent));
  if (fragments.length === 0) {
    return null;
  }

  return fragments.join("\n\n");
};

export const ReportRenderer: React.FC<ReportRendererProps> = ({
  blocks,
  fallbackText,
  fallbackTitle = "Секция доступна в текстовом виде",
}) => {
  const safeBlocks = sanitizeReportBlocks(blocks);

  if (safeBlocks.length === 0) {
    return hasText(fallbackText) ? (
      <FallbackTextCard title={fallbackTitle} text={fallbackText} />
    ) : null;
  }

  return (
    <div className="report-content-blocks space-y-4 pb-2">
      {safeBlocks.map((block, index) => (
        <BlockDispatcher key={index} block={block} />
      ))}
    </div>
  );
};

const FallbackTextCard: React.FC<{ title: string; text: string }> = ({ title, text }) => (
  <div
    data-testid="report-fallback-card"
    className="rounded-2xl border border-amber-200 bg-amber-50/90 p-4 shadow-sm"
  >
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white text-amber-500 shadow-sm">
        <AlertCircle className="h-5 w-5" />
      </div>
      <div className="min-w-0 space-y-3">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-amber-700">
            Текстовый fallback
          </p>
          <h4 className="mt-1 text-sm font-bold text-amber-950">{title}</h4>
        </div>
        <div className="rounded-xl border border-white/80 bg-white/90 p-3 text-sm leading-relaxed text-slate-700 whitespace-pre-wrap overflow-wrap-anywhere">
          {text}
        </div>
      </div>
    </div>
  </div>
);

const BlockDispatcher: React.FC<{ block: ReportBlock }> = ({ block }) => {
  switch (block.type) {
    case "header":
      return <HeaderBlock level={block.level || 2} text={block.text} />;
    
    case "paragraph":
    case "text":
      return <p className="text-slate-700 leading-relaxed overflow-wrap-anywhere">{block.text || block.content}</p>;

    case "callout":
      return (
        <CalloutBlock type={block.variant as CalloutType} title={block.title}>
          {block.content || block.text}
        </CalloutBlock>
      );

    case "list":
      return <BulletsBlock items={block.items} ordered={block.ordered} />;

    case "key_value":
      return <KeyValueBlock items={block.items as KeyValueItem[]} />;

    case "table":
      return <TableBlock columns={block.columns} rows={block.rows} />;

    case "rating":
      return <RatingBlock value={block.value} max={block.max} label={block.label} />;

    case "divider":
      return <DividerBlock />;

    case "traffic_lights":
      return <TrafficLights lights={block.items} />;

    case "markdown":
      // Fallback for raw markdown if needed, currently just rendering text
      return (
        <div className="prose max-w-none text-slate-700">
           {/* Ideally use a markdown parser here if we support mixed content */}
           <pre className="whitespace-pre-wrap text-xs bg-slate-50 p-2 rounded border">{block.content}</pre>
        </div>
      );

    default:
      return null;
  }
};
// END_BLOCK_REPORT_RENDERER
