"""LLM response parsing, block normalization, and section validation."""
# ############################################################################
# AI_HEADER: MODULE_LLM_PARSE_VALIDATE
# ROLE: Normalize LLM JSON blocks and validate report section content contracts.
# DEPENDENCIES: json, re, structlog, backend.app.llm.orchestrator models.
# GRACE_ANCHORS: [LLM_PARSE_VALIDATE]
# ############################################################################
# START_MODULE_CONTRACT: M-LLM-PARSE-VALIDATE
# purpose: Preserve LLM response parsing, block normalization, repair, and validation semantics outside the compatibility facade.
# owns:
#   - backend/app/llm/orchestrator_parse.py
# inputs:
#   - raw LLM text, SectionSpec, and normalized JSON block payloads
# outputs:
#   - SectionResult objects or validation errors used by retry/fallback orchestration
# invariants:
#   - JSON block contract, natal coverage rules, and fallback repair behavior remain unchanged
#   - public imports remain available from backend.app.llm.orchestrator
# non_goals:
#   - changing model routing, prompt text, or provider execution
# END_MODULE_CONTRACT: M-LLM-PARSE-VALIDATE
# START_MODULE_MAP: M-LLM-PARSE-VALIDATE
# public_entrypoints:
#   - validate_section_content -> content contract guard used by LLMOrchestrator
# internal_entrypoints:
#   - _parse_section_result -> raw model response to SectionResult adapter
#   - _repair_section_content -> deterministic repair helper for weak content
# semantic_blocks:
#   - LLM_PARSE_VALIDATE: JSON extraction, block normalization, validation, repair, and parsing
# owned_tests:
#   - tests/test_llm_cli_parsing.py
#   - tests/test_llm_fallback_chain.py
# adjacent_modules:
#   - backend/app/llm/orchestrator.py
# END_MODULE_MAP: M-LLM-PARSE-VALIDATE
from __future__ import annotations
import json
import re
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
import structlog
from .orchestrator_contracts import (
    LLMBlockContractError,
    LLMContentValidationError,
    NATAL_SECTION_IDS,
    SectionResult,
    SectionSpec,
    _contains_any,
)
logger = structlog.get_logger()
# START_BLOCK: LLM_PARSE_VALIDATE
def _strip_code_fences(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            if lines[-1].strip().startswith("```"):
                return "\n".join(lines[1:-1]).strip()
    return text
def _extract_json_text(text: str) -> str:
    # Try array first
    start_arr = text.find("[")
    end_arr = text.rfind("]")
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        return text[start_arr : end_arr + 1].strip()
    # Try object
    start_obj = text.find("{")
    end_obj = text.rfind("}")
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        return text[start_obj : end_obj + 1].strip()
    return text
def _try_parse_blocks(text: str) -> Optional[List[Dict[str, Any]]]:
    if not text:
        return None
    # 1. Strip fences and basic cleaning
    candidate = _strip_code_fences(text.strip())
    # 2. Extract JSON part (strips leading/trailing junk)
    candidate = _extract_json_text(candidate)
    # 3. Structural repairs for common small model errors
    # Fix doubled braces like }} that should be }
    # Only if it looks like structural (followed by , or ])
    candidate = re.sub(r'\}\s*\}\s*([,\]])', r'}\1', candidate)
    # Fix trailing garbage after array close
    if candidate.endswith(']]'): candidate = candidate[:-1] # common error in some models
    # 4. Auto-repair for truncation (incomplete array)
    if candidate.startswith("[") and not candidate.endswith("]"):
        last_brace = candidate.rfind("}")
        if last_brace != -1:
            candidate = candidate[:last_brace+1] + "]"
    if not candidate.startswith("[") or not candidate.endswith("]"):
        return None
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        # Try one last aggressive repair: strip everything after last ]
        # already handled by _extract_json_text but if it failed above...
        try:
            end_idx = candidate.rfind("]")
            if end_idx != -1:
                data = json.loads(candidate[:end_idx+1])
            else:
                return None
        except json.JSONDecodeError:
            return None
    if isinstance(data, list):
        return data
    return None
def _extract_text_from_blocks(blocks: List[Dict[str, Any]]) -> str:
    texts = []
    for block in blocks:
        if isinstance(block, dict):
            if "text" in block and isinstance(block["text"], str):
                texts.append(block["text"])
            if "content" in block and isinstance(block["content"], str):
                texts.append(block["content"])
            if "items" in block and isinstance(block["items"], list):
                for item in block["items"]:
                    if isinstance(item, str):
                        texts.append(item)
                    elif isinstance(item, dict):
                        texts.append(str(item.get("key", "")))
                        texts.append(str(item.get("value", "")))
                        texts.append(str(item.get("text", "")))
            if "rows" in block and isinstance(block["rows"], list):
                for row in block["rows"]:
                    if isinstance(row, list):
                        for cell in row:
                            texts.append(str(cell))
    return " ".join(texts)
_CALLOUT_VARIANTS = {"info", "warning", "error", "success", "quote", "neutral"}
_TRAFFIC_LIGHT_VALUES = {"red", "yellow", "green"}
_CALLOUT_VARIANT_ALIASES = {
    "red": "error",
    "yellow": "warning",
    "green": "success",
}
_HOUSE_AFTER_WORD_RE = re.compile(r"\bдом(?:а|е)?\s*(\d{1,2})(?!\s*-)", re.IGNORECASE)
_HOUSE_BEFORE_WORD_RE = re.compile(r"\b(\d{1,2})\s*дом(?:а|е)?\b", re.IGNORECASE)
def _extract_house_numbers(text: str) -> set[int]:
    houses: set[int] = set()
    for pattern in (_HOUSE_AFTER_WORD_RE, _HOUSE_BEFORE_WORD_RE):
        for match in pattern.finditer(text or ""):
            try:
                house = int(match.group(1))
            except (TypeError, ValueError):
                continue
            if 1 <= house <= 12:
                houses.add(house)
    return houses
def _ensure_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LLMBlockContractError(f"missing or invalid {field_name}")
    return value.strip()
def _normalize_callout_variant(value: Any) -> str:
    variant = _ensure_string(value, field_name="callout.variant").lower()
    return _CALLOUT_VARIANT_ALIASES.get(variant, variant)
def _normalize_table_columns(columns: Any) -> List[Dict[str, Any]]:
    if not isinstance(columns, list) or not columns:
        raise LLMBlockContractError("table.columns must be a non-empty list")
    normalized: List[Dict[str, Any]] = []
    for index, column in enumerate(columns):
        if isinstance(column, str):
            column = {"header": column, "width": "auto"}
        if not isinstance(column, dict):
            raise LLMBlockContractError(f"table.columns[{index}] must be an object")
        header = _ensure_string(column.get("header"), field_name=f"table.columns[{index}].header")
        item: Dict[str, Any] = {"header": header}
        if column.get("width") is not None:
            item["width"] = str(column.get("width"))
        if column.get("align") is not None:
            item["align"] = str(column.get("align"))
        if column.get("nowrap") is not None:
            item["nowrap"] = bool(column.get("nowrap"))
        normalized.append(item)
    return normalized
def _normalize_key_value_items(items: Any) -> List[Dict[str, str]]:
    if not isinstance(items, list) or not items:
        raise LLMBlockContractError("key_value.items must be a non-empty list")
    normalized: List[Dict[str, str]] = []
    for index, item in enumerate(items):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            item = {"key": item[0], "value": item[1]}
        if not isinstance(item, dict):
            raise LLMBlockContractError(f"key_value.items[{index}] must be an object")
        normalized.append(
            {
                "key": _ensure_string(item.get("key"), field_name=f"key_value.items[{index}].key"),
                "value": _ensure_string(item.get("value"), field_name=f"key_value.items[{index}].value"),
            }
        )
    return normalized
def _normalize_block(block: Any, index: int) -> Dict[str, Any]:
    if not isinstance(block, dict):
        raise LLMBlockContractError(f"block[{index}] must be an object")
    block_type = block.get("type")
    if block_type not in {"header", "paragraph", "list", "table", "key_value", "callout", "rating", "divider", "traffic_lights"}:
        raise LLMBlockContractError(f"invalid block type: {block_type}")
    if block_type == "header":
        level = block.get("level")
        if not isinstance(level, int):
            raise LLMBlockContractError("header.level must be an integer")
        return {"type": "header", "level": level, "text": _ensure_string(block.get("text"), field_name="header.text")}
    if block_type == "paragraph":
        text = block.get("text")
        if text is None and isinstance(block.get("content"), str):
            text = block.get("content")
        return {"type": "paragraph", "text": _ensure_string(text, field_name="paragraph.text")}
    if block_type == "list":
        items = block.get("items")
        if not isinstance(items, list) or not items:
            raise LLMBlockContractError("list.items must be a non-empty list")
        normalized_items: List[str] = []
        for item_index, item in enumerate(items):
            if isinstance(item, dict):
                if "text" in item:
                    item = item.get("text")
                elif "value" in item:
                    item = item.get("value")
            normalized_items.append(_ensure_string(item, field_name=f"list.items[{item_index}]"))
        result: Dict[str, Any] = {
            "type": "list",
            "items": normalized_items,
            "ordered": bool(block.get("ordered", False)),
        }
        if block.get("style") is not None:
            result["style"] = str(block.get("style"))
        return result
    if block_type == "table":
        rows = block.get("rows")
        if not isinstance(rows, list) or not rows:
            raise LLMBlockContractError("table.rows must be a non-empty list")
        normalized_rows: List[List[str]] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, list):
                raise LLMBlockContractError(f"table.rows[{row_index}] must be a list")
            normalized_rows.append([str(cell) for cell in row])
        return {
            "type": "table",
            "columns": _normalize_table_columns(block.get("columns")),
            "rows": normalized_rows,
        }
    if block_type == "key_value":
        return {
            "type": "key_value",
            "items": _normalize_key_value_items(block.get("items")),
        }
    if block_type == "callout":
        content = block.get("content")
        if content is None and isinstance(block.get("text"), str):
            content = block.get("text")
        variant = _normalize_callout_variant(block.get("variant"))
        if variant not in _CALLOUT_VARIANTS:
            raise LLMBlockContractError(f"invalid callout.variant: {variant}")
        return {
            "type": "callout",
            "variant": variant,
            "title": _ensure_string(block.get("title"), field_name="callout.title"),
            "content": _ensure_string(content, field_name="callout.content"),
        }
    if block_type == "rating":
        value = block.get("value")
        label = _ensure_string(block.get("label"), field_name="rating.label")
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise LLMBlockContractError("rating.value must be numeric") from None
        try:
            numeric_max = float(block.get("max", 10))
        except (TypeError, ValueError):
            raise LLMBlockContractError("rating.max must be numeric") from None
        return {
            "type": "rating",
            "value": numeric_value,
            "max": numeric_max,
            "label": label,
        }
    if block_type == "divider":
        return {"type": "divider"}
    items = block.get("items")
    if not isinstance(items, dict):
        raise LLMBlockContractError("traffic_lights.items must be an object")
    normalized_lights: Dict[str, str] = {}
    for key in ("health", "money", "love"):
        value = _ensure_string(items.get(key), field_name=f"traffic_lights.items.{key}").lower()
        if value not in _TRAFFIC_LIGHT_VALUES:
            raise LLMBlockContractError(f"invalid traffic_lights.items.{key}: {value}")
        normalized_lights[key] = value
    return {"type": "traffic_lights", "items": normalized_lights}
def _normalize_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(blocks, list) or not blocks:
        raise LLMBlockContractError("empty blocks")
    return [_normalize_block(block, index) for index, block in enumerate(blocks)]
def _has_quote_callout(blocks: List[Dict[str, Any]]) -> bool:
    return any(
        block.get("type") == "callout"
        and block.get("variant") == "quote"
        and (block.get("title") or block.get("content"))
        for block in blocks
    )
def _fallback_section_result(raw: str, section: SectionSpec) -> SectionResult:
    # Previously returned raw text. Now we strictly fail on invalid JSON.
    # The caller (orchestrator) will catch this and retry.
    snippet = raw[:200].replace("\n", " ").strip()
    logger.warning(
        "llm.invalid_json.fail",
        block_id="LLM_PARSE",
        section_id=section.section_id,
        snippet=snippet,
    )
    raise LLMBlockContractError(f"Invalid JSON in section {section.section_id}")
def validate_natal_section_content(
    section: SectionSpec,
    text: str,
    blocks: Optional[List[Dict[str, Any]]] = None,
) -> None:
    lower = text.lower()
    if section.section_id == "executive_summary":
        strength_tokens = [
            "силь",
            "суперсил",
            "опор",
            "ресурс",
            "талант",
            "стандарт",
            "каркас",
            "собран",
            "уме",
            "чувствитель",
            "интуиц",
            "надежн",
            "выдерж",
            "структур",
            "самостоятельн",
            "нюанс",
        ]
        risk_tokens = [
            "риск",
            "ловуш",
            "перегиб",
            "тенев",
            "самосабот",
            "перегруз",
            "стресс",
            "давлен",
            "идеализац",
            "дистанци",
            "избег",
            "затуман",
            "туман",
            "напряжен",
            "крайност",
            "уход",
        ]
        relationship_tokens = [
            "отнош",
            "партнер",
            "любов",
            "близост",
            "союз",
            "довер",
            "границ",
            "разговор",
            "диалог",
            "связ",
            "контакт",
        ]
        money_tokens = [
            "деньг",
            "работ",
            "карьер",
            "реализац",
            "финанс",
            "доход",
            "репутац",
            "зараб",
            "професс",
        ]
        development_tokens = [
            "фокус",
            "развит",
            "рост",
            "вектор",
            "зрел",
            "режим",
            "стратег",
            "избег",
            "делать",
            "действ",
            "ритм",
            "курс",
            "границ",
            "пауза",
            "проверя",
            "начни",
            "осознан",
            "шаг",
        ]
        if not _contains_any(lower, strength_tokens):
            raise LLMContentValidationError("natal executive missing strengths_or_risks")
        if not _contains_any(lower, risk_tokens):
            raise LLMContentValidationError("natal executive missing strengths_or_risks")
        if not _contains_any(lower, relationship_tokens):
            raise LLMContentValidationError("natal executive missing relationship")
        if not _contains_any(lower, money_tokens):
            raise LLMContentValidationError("natal executive missing money")
        if not _contains_any(lower, development_tokens):
            raise LLMContentValidationError("natal executive missing development")
        return
    if section.section_id == "input_frame":
        # Keep this one relatively strict as it's critical and generated by code mostly
        if not re.search(r"\bкверент\b|\bклиент\b", lower):
            raise LLMContentValidationError("natal input missing client")
        return
    if section.section_id == "synthesis":
        if blocks and _has_quote_callout(blocks):
            return
        if not _contains_any(lower, ["метафор", "образ", "сцена"]):
            raise LLMContentValidationError("natal synthesis missing metaphor")
        return
    if section.section_id == "framework_elements_modes":
        if not any(token in lower for token in ["стих", "элемент", "огон", "зем", "возду", "вод"]):
            raise LLMContentValidationError("natal framework missing element balance")
        if "доминант" not in lower:
            raise LLMContentValidationError("natal framework missing dominants")
        if "дефиц" not in lower:
            raise LLMContentValidationError("natal framework missing deficit")
        if "стиль жизни" not in lower and "формула баланса" not in lower:
            raise LLMContentValidationError("natal framework missing lifestyle")
        return
    if section.section_id == "axes_truths":
        if not any(token in lower for token in ["asc", "dsc", "ic", "mc", "асц", "дсц"]):
            raise LLMContentValidationError("natal axes missing tokens")
        return
    if section.section_id == "aspects_beginner":
        return # Content length check is enough
    if section.section_id == "configurations_geometry":
        return # Content length check is enough
    if section.section_id == "dispositor_office":
        if "офис" not in lower and "босс" not in lower and "иерарх" not in lower:
            raise LLMContentValidationError("natal dispositor missing office")
        return
    if section.section_id == "core_triad":
        if not any(token in lower for token in ["солнц", "лун", "sun", "moon"]):
            raise LLMContentValidationError("natal core missing triad")
        return
    if section.section_id == "mercury_mind":
        if "меркури" not in lower and "мышлени" not in lower:
            raise LLMContentValidationError("natal mercury missing sections")
        return
    if section.section_id == "shadow_trauma":
        if "хирон" not in lower and "лилит" not in lower:
            raise LLMContentValidationError("natal shadow missing points")
        return
    if section.section_id == "nodes_growth":
        if "узел" not in lower and "узла" not in lower:
            raise LLMContentValidationError("natal nodes missing nodes")
        return
    if section.section_id == "vertex_fate":
        if "вертекс" not in lower and "vertex" not in lower and "судьб" not in lower:
            raise LLMContentValidationError("natal vertex missing name")
        return
    if section.section_id in ["balance_wheel_1_6", "balance_wheel_7_12"]:
        # Live outputs often alternate between "1 Дом" and "Дом 8" phrasing.
        # Count both to avoid false retries/fallbacks on otherwise valid sections.
        expected = {1, 2, 3, 4, 5, 6} if section.section_id == "balance_wheel_1_6" else {7, 8, 9, 10, 11, 12}
        found_houses = _extract_house_numbers(text)
        if len(found_houses & expected) < 2:
            raise LLMContentValidationError(f"natal balance wheel ({section.section_id}) too few houses")
        return
    if section.section_id == "time_cycles":
        return
    if section.section_id == "final_synthesis":
        success_callouts = [
            block
            for block in (blocks or [])
            if isinstance(block, dict)
            and block.get("type") == "callout"
            and block.get("variant") == "success"
        ]
        if len(success_callouts) != 1 or len(blocks or []) != 1:
            raise LLMContentValidationError("natal final invalid format")
        callout_text = " ".join(
            str(success_callouts[0].get(key, ""))
            for key in ("title", "content")
        ).lower()
        if "девиз" not in callout_text:
            raise LLMContentValidationError("natal final missing motto")
        if "совет" not in callout_text:
            raise LLMContentValidationError("natal final missing advice")
        return
def validate_section_content(section: SectionSpec, content: str) -> None:
    """
    # PURPOSE: Enforce minimum structure for section content.
    # INPUT: section spec and JSON content.
    # OUTPUT: None (raises on invalid structure).
    # CONTEXT: Used to trigger retries/fallbacks for weak LLM output.
    """
    text = (content or "").strip()
    blocks = _try_parse_blocks(text)
    if blocks is None:
        raise LLMBlockContractError("content is not a valid JSON array of blocks")
    blocks = _normalize_blocks(blocks)
    # Extract text for validation
    full_text = _extract_text_from_blocks(blocks)
    lower = full_text.lower()
    min_length_map = {
        "executive_summary": 120,
        "input_frame": 100,
        "month_full_forecast": 260,
        "synthesis": 150,
        "framework_elements_modes": 150,
        "axes_truths": 150,
        "aspects_beginner": 150,
        "configurations_geometry": 150,
        "dispositor_office": 150,
        "core_triad": 150,
        "mercury_mind": 150,
        "shadow_trauma": 150,
        "nodes_growth": 150,
        "vertex_fate": 150,
        "balance_wheel": 500,
        "love_intimacy": 150,
        "money_realization": 150,
        "stars_transuranus": 150,
        "time_cycles": 150,
        "final_synthesis": 100,
    }
    min_length = min_length_map.get(
        section.section_id, 50 if section.section_id in NATAL_SECTION_IDS else 30
    )
    if len(full_text) < min_length:
        raise LLMContentValidationError("content too short")
    if section.section_id in NATAL_SECTION_IDS:
        validate_natal_section_content(section, full_text, blocks=blocks)
        return
    is_horary = section.section_id.startswith("horary_")
    if is_horary and re.search(r"[a-z]", full_text):
        # Allow some latin for technical terms but warn? 
        # Strict latin check might fail on IDs or keys. 
        # Only check if it looks like English text.
        # Simple heuristic: if > 20% latin chars?
        pass
    if section.section_id == "synthesis":
        required = ["метафора", "тезис", "ресурс", "узел", "ключ"]
        for req in required:
             if req not in lower:
                 raise LLMContentValidationError(f"synthesis missing {req}")
    if section.section_id == "input_frame":
        if "дата" not in lower:
            raise LLMContentValidationError("input frame missing date")
    if section.section_id == "executive_summary":
        if "силь" not in lower or "риск" not in lower:
            raise LLMContentValidationError("natal executive missing strengths_or_risks")
        if "отнош" not in lower and "партнер" not in lower:
            raise LLMContentValidationError("natal executive missing relationship")
        if "деньг" not in lower and "работ" not in lower:
            raise LLMContentValidationError("natal executive missing money")
        if "фокус" not in lower and "развит" not in lower:
            raise LLMContentValidationError("natal executive missing development")
    if section.section_id == "framework_elements_modes":
        # Relaxed: require at least 2 of 4 elements (allows creative phrasing)
        element_tokens = ["огон", "зем", "возду", "вод"]
        element_count = sum(1 for token in element_tokens if token in lower)
        if element_count < 2:
            raise LLMContentValidationError(f"missing element balance (found {element_count}/4)")
        # Relaxed: require at least 2 of 3 modes
        mode_tokens = ["кардин", "фикс", "мутаб"]
        mode_count = sum(1 for token in mode_tokens if token in lower)
        if mode_count < 2:
            raise LLMContentValidationError(f"missing mode balance (found {mode_count}/3)")
        if "доминант" not in lower:
            raise LLMContentValidationError("natal framework missing dominants")
        if "дефиц" not in lower:
            raise LLMContentValidationError("natal framework missing deficit")
        if "стиль жизни" not in lower and "формула баланса" not in lower:
            raise LLMContentValidationError("natal framework missing lifestyle")
    if section.section_id == "month_theme":
        required_blocks = [
            "статус месяца",
            "центральная нить смысла",
            "главные активаторы",
            "карта сфер",
        ]
        if not all(token in lower for token in required_blocks):
            raise LLMContentValidationError("missing month forecast blocks")
        if not any(indicator in full_text for indicator in ["🟢", "🟡", "🔴"]):
            raise LLMContentValidationError("missing status indicators")
    if section.section_id == "month_overview":
        required = [
            "статус месяца",
            "метафора месяца",
            "цена ошибок",
            "центральная нить",
        ]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("missing month overview blocks")
        if "совет-формула" not in lower and "совет формула" not in lower:
            raise LLMContentValidationError("missing month overview blocks")
    if section.section_id.startswith("week_") and section.section_id != "week_strategy":
        required = [
            "статус",
            "главная тема",
            "подневная стратегия",
        ]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("missing month week blocks")
    if section.section_id.startswith("month_") and section.section_id.endswith("_forecast") and section.section_id != "month_full_forecast":
        required = [
            "статус месяца",
            "центральная нить",
            "главные активаторы",
        ]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("missing year month blocks")
    if section.section_id == "axes_truths":
        # Relaxed: require at least 2 axes mentioned instead of ALL 4
        # This prevents false negatives while maintaining structural validation
        axis_tokens = ["ASC", "DSC", "IC", "MC", "асц", "дсц"]
        found_axes = sum(1 for token in axis_tokens if token in full_text)
        if found_axes < 2:
            raise LLMContentValidationError("missing axis tokens (need at least 2)")
        # Allow variations of "two truths" phrasing
        truth_phrases = ["твоя правда", "твоя правд", "две правд", "два правд", "правда партн", "партнера правда"]
        if not any(phrase in lower for phrase in truth_phrases):
            raise LLMContentValidationError("missing two truths phrasing")
    if section.section_id == "aspects_beginner":
        # Relaxed: metaphors are nice but not strictly required if content is substantial
        metaphors = ["мотор", "качел", "пружин", "магнит", "механизм", "связ"]
        # Only enforce if content is very short (less than 200 chars)
        if len(full_text) < 200 and not any(word in lower for word in metaphors):
            raise LLMContentValidationError("content too short without beginner metaphors")
    if section.section_id == "configurations_geometry":
        # Relaxed: require at least 3 of 4 key fields
        key_fields = ["дар", "риск", "ключ", "вопрос"]
        found_count = sum(1 for field in key_fields if field in lower)
        if found_count < 3:
            raise LLMContentValidationError(f"missing configuration fields (found {found_count}/4)")
    if section.section_id == "dispositor_office":
        # Relaxed: allow any office-like metaphor (офис/босс/иерарх/управление)
        office_found = any(token in lower for token in ["офис", "босс", "иерарх", "управлен", "конверт"])
        if not office_found:
            raise LLMContentValidationError("missing office metaphor")
    if section.section_id == "core_triad":
        # Relaxed: allow emoji variants, require at least 2 of 3 triad elements
        asc_found = any(token in full_text for token in ["ASC", "асц", "⬆️"])
        sun_found = any(token in full_text for token in ["Солнце", "солнц", "☀️"])
        moon_found = any(token in full_text for token in ["Луна", "лун", "🌙"])
        triad_count = sum(1 for found in [asc_found, sun_found, moon_found] if found)
        if triad_count < 2:
            raise LLMContentValidationError("missing core triad (need at least 2 of 3)")
    if section.section_id == "mercury_mind":
        # Relaxed: allow "меркури" or "мышление"
        mercury_found = any(token in full_text for token in ["Меркурий", "меркури", "☿"])
        mind_found = "мышлен" in lower
        if not (mercury_found or mind_found):
            raise LLMContentValidationError("missing mercury")
    if section.section_id == "shadow_trauma":
        # Relaxed: require at least one of Chiron or Lilith
        chiron_found = any(token in full_text for token in ["Хирон", "хирон", "⚷"])
        lilith_found = any(token in full_text for token in ["Лилит", "лилит", "⚸"])
        if not (chiron_found or lilith_found):
            raise LLMContentValidationError("missing chiron or lilith")
    if section.section_id == "nodes_growth":
        # Relaxed: require at least one of North or South node
        north_found = any(token in full_text for token in ["Север", "север", "☊"])
        south_found = any(token in full_text for token in ["Южн", "юж", "☋"])
        if not (north_found or south_found):
            raise LLMContentValidationError("missing nodes")
    if section.section_id == "vertex_fate":
        # Relaxed: allow "вертекс" or "vertex" or "судьб"
        vertex_found = any(token in full_text for token in ["Вертекс", "вертекс", "vertex", "✴️"])
        fate_found = "судьб" in lower
        if not (vertex_found or fate_found):
            raise LLMContentValidationError("missing vertex")
    if section.section_id == "love_intimacy":
        # Relaxed: require at least one of Venus or Mars (emoji or text)
        venus_found = any(token in full_text for token in ["Венера", "венер", "♀️"])
        mars_found = any(token in full_text for token in ["Марс", "марс", "♂️"])
        if not (venus_found and mars_found):
            raise LLMContentValidationError("missing venus or mars")
    if section.section_id == "money_realization":
        # Relaxed: require at least one of Jupiter or Saturn
        jupiter_found = any(token in full_text for token in ["Юпитер", "юпитер", "♃"])
        saturn_found = any(token in full_text for token in ["Сатурн", "сатурн", "♄"])
        if not (jupiter_found or saturn_found):
            raise LLMContentValidationError("missing jupiter or saturn")
    if section.section_id == "stars_transuranus":
        # Relaxed: require at least one of Uranus, Neptune, Pluto
        uranus_found = any(token in full_text for token in ["Уран", "уран", "♅"])
        neptune_found = any(token in full_text for token in ["Нептун", "нептун", "♆"])
        pluto_found = any(token in full_text for token in ["Плутон", "плутон", "♇"])
        if not (uranus_found or neptune_found or pluto_found):
            raise LLMContentValidationError("missing transuranus")
    if section.section_id == "week_strategy":
        required = [
            "главная тема",
            "статус недели",
            "подневная стратегия",
            "резюме по срезам",
        ]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("missing week strategy blocks")
    if section.section_id == "month_full_forecast":
        structure_text = " ".join(
            [
                str(block.get("text", ""))
                for block in blocks
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            ]
            + [
                str(block.get("title", ""))
                for block in blocks
                if isinstance(block, dict) and isinstance(block.get("title"), str)
            ]
        ).lower()
        required = [
            "статус месяца",
            "ключевые события",
            "стратегия по неделям",
            "итог месяца",
        ]
        if not all(token in structure_text for token in required):
            raise LLMContentValidationError("missing month full forecast blocks")
        action_tokens = [
            "что продвигать",
            "где не форсировать",
        ]
        if not all(token in lower for token in action_tokens):
            raise LLMContentValidationError("missing month full forecast blocks")
        status_callout = next(
            (
                block
                for block in blocks
                if isinstance(block, dict)
                and block.get("type") == "callout"
                and "статус месяца" in str(block.get("title", "")).lower()
            ),
            None,
        )
        if status_callout:
            status_content = str(status_callout.get("content", "")).lower()
            if (
                "новые возможности" in status_content
                or "новые инициативы" in status_content
                or re.search(r"важн\w+\s+задач", status_content)
            ):
                raise LLMContentValidationError("generic month status callout")
            if not re.search(
                r"переговор|деньг|отнош|документ|дедлайн|ритм|запуск|процесс|работ|карьер|срок",
                status_content,
            ):
                raise LLMContentValidationError("month status callout lacks concrete scene")
def _repair_section_content(
    section: SectionSpec, content: str, error: str
) -> str:
    blocks = _try_parse_blocks(content)
    if blocks is None:
        raise LLMBlockContractError("content is not a valid JSON array of blocks")
    blocks = _normalize_blocks(blocks)
    # We append a block with the missing info
    additions: List[str] = []
    if error == "natal input missing client":
        additions.append("**Владелец карты:** Имя клиента")
    elif error == "natal input missing birth date":
        additions.append("**Дата рождения:** указать дату и время")
    elif error == "natal input missing birth place":
        additions.append("**Место рождения:** указать место")
    elif error == "natal input missing house system":
        additions.append("**Система домов:** указать систему")
    elif error == "natal input missing planet table":
        # Can't easily add table block here without robust structure. Add note.
        additions.append("⚠️ Отсутствует таблица планет.")
    elif error == "natal input missing angles table":
        additions.append("⚠️ Отсутствуют угловые точки.")
    elif error == "natal synthesis missing metaphor":
        additions.append('> **Метафора:** "Ключевой образ".')
    elif error == "natal synthesis missing thesis":
        additions.append("**Главный тезис:** краткая формулировка.")
    elif error == "natal executive missing strengths_or_risks":
        additions.append("Назови одну опору карты и один ее перегиб живым человеческим языком.")
    elif error == "natal executive missing relationship":
        additions.append("Покажи, как этот паттерн влияет на отношения и близость.")
    elif error == "natal executive missing money":
        additions.append("Покажи, как этот паттерн влияет на деньги, работу или реализацию.")
    elif error == "natal executive missing development":
        additions.append("Покажи зрелый режим действия и короткий практический ход.")
    elif error == "natal framework missing dominants":
        additions.append("**Доминанта:** ОГОНЬ 🔥")
    elif error == "natal framework missing element balance":
        additions.append("* **Баланс Стихий:** Огонь, Земля, Воздух, Вода.")
    elif error == "natal framework missing deficit":
        additions.append("* **Дефицит:** зона, требующая подпитки.")
    elif error == "natal framework missing lifestyle":
        additions.append("**Стиль жизни:** ... **Формула баланса:** ...")
    elif error == "natal axes missing tokens":
        additions.append("ASC-DSC, IC-MC")
    elif error == "natal axes missing 2-8":
        additions.append("Ось 2-8")
    elif error == "natal axes missing 3-9":
        additions.append("Ось 3-9")
    elif error == "natal axes missing truths":
        additions.append("Твоя правда: ...")
    elif error == "natal aspects missing labels":
        additions.append("Якорь, Сценарий, Ресурс")
    elif error == "natal config missing heading":
        additions.append("Конфигурация")
    elif error == "natal config missing fields":
        additions.append("Геометрия, Дар, Риск, Ключ")
    elif error == "natal dispositor missing office":
        additions.append("Офис")
    elif error == "natal dispositor missing envelope":
        additions.append("Конверт")
    elif error == "natal dispositor missing boss":
        additions.append("Босс")
    elif error == "natal core missing triad":
        additions.append("ASC, Солнце, Луна")
    elif error == "natal core missing thesis":
        additions.append("Тезис, Описание")
    elif error == "natal core missing summary":
        additions.append("Сборка ядра")
    elif error == "natal mercury missing sections":
        additions.append("Стиль, Режим, Ловушки, Ключ")
    elif error == "natal shadow missing points":
        additions.append("Хирон, Лилит")
    elif error == "natal shadow missing labels":
        additions.append("Якорь, Сценарий, Ресурс")
    elif error == "natal nodes missing nodes":
        additions.append("Северный узел, Южный узел")
    elif error == "natal nodes missing trap":
        additions.append("Ловушка")
    elif error == "natal nodes missing mission":
        additions.append("Миссия")
    elif error == "natal nodes missing question":
        additions.append("Вопрос")
    elif error == "natal vertex missing name":
        additions.append("Вертекс")
    elif error == "natal vertex missing labels":
        additions.append("Якорь, Сценарий, Урок")
    elif error == "natal balance wheel missing labels":
        additions.append("Тема, В плюсе, В минусе, Триггер")
    elif error == "natal love missing planets":
        additions.append("Венера, Марс")
    elif error == "natal love missing secret":
        additions.append("Секрет успеха")
    elif error == "natal money missing houses":
        additions.append("2 дом, 6 дом, 10 дом")
    elif error == "natal money missing formula":
        additions.append("Главная формула")
    elif error == "natal transuranus missing planets":
        additions.append("Уран, Нептун, Плутон")
    elif error == "natal transuranus missing fields":
        additions.append("Дар, Риск")
    elif error == "natal time cycles missing fields":
        additions.append("Соляр, Асцендент, Зенит, Тренд")
    elif error == "natal final missing motto":
        additions.append("Девиз")
    elif error == "natal final missing advice":
        additions.append("Совет")
    elif error == "natal final invalid format":
        additions.append("Верни один success-callout с Девизом и Главным советом.")
    elif error == "missing status indicators":
        additions.append("Статус: 🟡")
    elif error == "missing month full forecast blocks":
        additions.append(
            "Статус месяца. Ключевые события. Стратегия по неделям. Что продвигать. Где не форсировать. Итог месяца."
        )
    elif error == "generic month status callout":
        additions.append(
            "Перепиши статус месяца без фраз 'новые возможности', 'важные задачи', 'новые инициативы'; назови реальную жизненную сцену."
        )
    elif error == "month status callout lacks concrete scene":
        additions.append(
            "Привяжи статус месяца к конкретной сцене: переговоры, деньги, отношения, документы, дедлайны, рабочий ритм или запуск."
        )
    if additions:
        if section.section_id in {"executive_summary", "final_synthesis"}:
            # For summary-compression sections, visible repair blocks hurt output more than
            # a clean retry/fallback to deterministic insight_pack verbalization.
            return content
        # Append as a remediation block
        text = "\n".join(additions)
        blocks.append({
            "type": "callout",
            "variant": "warning",
            "title": "Дополнено автоматически",
            "content": f"LLM пропустила: {text}"
        })
    return json.dumps(blocks, ensure_ascii=False)
def _parse_section_result(raw: str, section: SectionSpec) -> SectionResult:
    candidate = _strip_code_fences(raw.strip())
    blocks = _try_parse_blocks(candidate)
    if blocks is not None:
        blocks = _normalize_blocks(blocks)
        return SectionResult(
            section_id=section.section_id,
            title=section.title,
            content=json.dumps(blocks, ensure_ascii=False),
        )
    try:
        return SectionResult.model_validate_json(candidate)
    except ValidationError:
        candidate = _extract_json_text(candidate)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            snippet = raw[:400].replace("\n", " ").strip()
            logger.warning(
                "llm.invalid_json",
                block_id="LLM_PARSE",
                section_id=section.section_id,
                snippet=snippet,
                full_raw_len=len(raw),
            )
            # LOG FULL RAW FOR DEBUG
            if len(raw) < 5000:
                logger.debug("llm.invalid_json.full_raw", raw=raw)
            return _fallback_section_result(raw, section)
        if isinstance(data, dict):
            content = data.get("content")
            if isinstance(content, list):
                content = _normalize_blocks(content)
                return SectionResult(
                    section_id=section.section_id,
                    title=section.title,
                    content=json.dumps(content, ensure_ascii=False),
                )
            if isinstance(content, str):
                nested_blocks = _try_parse_blocks(content)
                if nested_blocks is not None:
                    nested_blocks = _normalize_blocks(nested_blocks)
                    return SectionResult(
                        section_id=section.section_id,
                        title=section.title,
                        content=json.dumps(nested_blocks, ensure_ascii=False),
                    )
                return SectionResult(
                    section_id=section.section_id,
                    title=section.title,
                    content=content,
                )
        try:
            return SectionResult.model_validate(data)
        except ValidationError:
            snippet = raw[:400].replace("\n", " ").strip()
            logger.warning(
                "llm.invalid_schema",
                block_id="LLM_PARSE",
                section_id=section.section_id,
                snippet=snippet,
            )
            return _fallback_section_result(raw, section)
# END_BLOCK: LLM_PARSE_VALIDATE
