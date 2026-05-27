# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_RUNTIME_SECTIONS
# ROLE: Runtime section generation and LLM retry helpers.
# DEPENDENCIES: backend/app/llm, report workflow content modules
# GRACE_ANCHORS: [SECTION_RETRY, SECTION_GENERATION]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-RUNTIME-SECTIONS
# purpose: Generate individual report sections through static overrides, templates, LLM retries, and validation fallbacks.
# inputs:
#   - SectionSpec, report context, chart data, LLM clients, fallback model settings
# outputs:
#   - SectionResult instances with stable section_id/title/content/duration fields
# trace_obligations:
#   - Section generation start/complete logs preserve workflow module/contract/block/report attribution
# invariants:
#   - Static/template/LLM branch ordering and fallback behavior remain unchanged
# non_goals:
#   - Does not persist ReportChunk/ReportRun state or send notifications
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-RUNTIME-SECTIONS

# START_MODULE_MAP: M-REPORT-WORKFLOW-RUNTIME-SECTIONS
# entrypoints:
#   - generate_section_with_retries -> SECTION_RETRY_MODEL_CHAIN
#   - generate_section_content -> SECTION_STATIC_OVERRIDE / SECTION_LLM_GENERATION
#   - should_fallback_on_llm_error -> SECTION_FALLBACK_POLICY
# END_MODULE_MAP: M-REPORT-WORKFLOW-RUNTIME-SECTIONS

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import structlog

from ..llm.orchestrator import (
    CliLLMClient,
    LLMClient,
    LLMContentValidationError,
    LLMOrchestrator,
    NATAL_SECTION_IDS,
    OpenRouterClient,
    SectionResult,
    SectionSpec,
)
from ..llm.validator import validate_llm_hallucinations
from ..reporting.markdown_helpers import format_house_context, format_technical_appendix
from ..reporting.static_content import SECTION_INTROS
from .report_workflow_content import build_section_template_content, inject_planet_emojis
from .report_workflow_content_fallback import build_section_validation_fallback_content
from .report_workflow_forecast import (
    RU_PLANETS_FULL,
    RU_SIGNS,
    _render_month_forecast_content,
    _render_week_strategy_content,
)
from .report_workflow_logging import _workflow_log as _default_workflow_log

logger = structlog.get_logger()

def _facade_symbol(name: str, default):
    module = sys.modules.get("backend.app.services.report_workflow")
    return getattr(module, name, default) if module is not None else default

def _workflow_log(*args, **kwargs):
    return _facade_symbol("_workflow_log", _default_workflow_log)(*args, **kwargs)

# START_BLOCK: SECTION_RUNTIME_GENERATION
def should_fallback_on_llm_error(exc: Exception) -> bool:
    """
    # PURPOSE: Decide whether to use fallback content for an LLM error.
    # INPUT: exception from LLM call.
    # OUTPUT: True if fallback should be used.
    # CONTEXT: Keeps report generation resilient to credit/network issues.
    """

    message = str(exc)
    return any(
        token in message
        for token in (
            "OpenRouter error:",
            "OpenRouter connection error",
            "OpenRouter returned empty content",
            "CLI error:",
            "CLI timeout",
        )
    )

def generate_section_with_retries(
    spec: SectionSpec,
    context: Dict[str, Any],
    *,
    primary_client: LLMClient,
    fallback_models: List[str],
    max_attempts: int,
) -> SectionResult:
    """
    # PURPOSE: Generate a section with retries + model switching on bad structure or API errors.
    # INPUT: spec, context, primary client, fallback models list, max attempts per model.
    # OUTPUT: SectionResult.
    """

    all_models = []
    # Add primary model if it's an OpenRouter client
    if isinstance(primary_client, OpenRouterClient):
        all_models.append(primary_client.model)
    
    # Add fallbacks
    for m in fallback_models:
        if m and m not in all_models:
            all_models.append(m)

    logger.info("report.section.model_chain", section_id=spec.section_id, models=all_models)

    if not all_models and not isinstance(primary_client, CliLLMClient):
         # If no models defined, at least use what we have
         all_models = ["default"]

    last_error: Optional[Exception] = None
    facts = context.get("facts")

    # Iterate over models in the chain
    for model_name in all_models:
        # Construct client for this specific model if it's not the primary one already active
        current_client = primary_client
        if isinstance(primary_client, OpenRouterClient) and model_name != primary_client.model:
            try:
                current_client = _facade_symbol("OpenRouterClient", OpenRouterClient).from_env(model_override=model_name)
            except Exception as e:
                logger.warning("report.section.client_init_failed", model=model_name, error=str(e))
                continue

        orchestrator = _facade_symbol("LLMOrchestrator", LLMOrchestrator)(current_client)
        
        # Try this model N times
        for attempt in range(max_attempts):
            try:
                result = orchestrator.generate_sections([spec], context=context)[0]
                
                # HALLUCINATION VALIDATION (Natal only)
                content = result.content or ""
                is_natal = spec.section_id in NATAL_SECTION_IDS or "natal" in str(spec.section_id)
                if is_natal and facts and ("[" in content and "]" in content):
                    try:
                        clean = content.strip()
                        if clean.startswith("```json"): clean = clean[7:]
                        elif clean.startswith("```"): clean = clean[3:]
                        if clean.endswith("```"): clean = clean[:-3]
                        
                        blocks = json.loads(clean.strip())
                        if isinstance(blocks, list):
                            errors = validate_llm_hallucinations(blocks, facts)
                            if errors:
                                msg = "; ".join(errors)
                                logger.warning("report.section.hallucination", section_id=spec.section_id, model=model_name, errors=msg)
                                raise LLMContentValidationError(f"Hallucination control failed: {msg}")
                    except json.JSONDecodeError:
                        pass 
                
                return result

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "report.section.retry",
                    block_id="REPORT_SECTION",
                    section_id=spec.section_id,
                    model=model_name,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    error=str(exc),
                )
                # If it's a validation error, we retry the SAME model.
                # If it's a 429 or other API error, we might want to skip to next model immediately,
                # but for simplicity we just finish all attempts for this model.
                continue
        
        # If we are here, all attempts for current model failed. 
        # Move to next model in chain.
        logger.error("report.section.model_failed", section_id=spec.section_id, model=model_name)

    if last_error:
        raise last_error
    raise LLMContentValidationError("content validation failed after trying all models")

async def generate_section_content(
    spec: SectionSpec,
    context: dict,
    chart_data: dict,
    llm_client: Optional[LLMClient],
    fallback_models: List[str],
    retry_attempts: int,
    use_template: bool
) -> SectionResult:
    """
    # START_CONTRACT: FN-ENQUEUE-REPORT-GENERATION
    # purpose: Produce a single section payload through static override, llm generation, or fallback policy.
    # inputs: section spec, section/global context, chart data, llm client config, retry/fallback settings.
    # returns: SectionResult with normalized content and usage metrics.
    # side_effects: emits section generation trace logs aligned with workflow/admin monitoring.
    # errors: propagates non-fallback generation failures to caller.
    # END_CONTRACT: FN-ENQUEUE-REPORT-GENERATION
    """
    import time
    start_t = time.perf_counter()
    _workflow_log(
        "info",
        "report.workflow.section_generation_start",
        fn="generate_section_content",
        contract="FN-ENQUEUE-REPORT-GENERATION",
        block="SECTION_STATIC_OVERRIDE",
        report_id=context.get("report_id") or context.get("client", {}).get("report_id"),
        section_id=spec.section_id,
        title=spec.title,
    )

    # START_BLOCK: SECTION_STATIC_OVERRIDE
    # 1. Static Overrides
    if spec.section_id == "input_frame":
        _workflow_log(
            "info",
            "report.workflow.section_static_override",
            fn="generate_section_content",
            contract="FN-ENQUEUE-REPORT-GENERATION",
            block="SECTION_STATIC_OVERRIDE",
            report_id=context.get("report_id") or context.get("client", {}).get("report_id"),
            section="input_frame",
            section_id=spec.section_id,
        )
        
        blocks = []
        
        # 1. Intro Callout
        intro_text = SECTION_INTROS.get("input_frame", "")
        if intro_text:
            blocks.append({
                "type": "callout",
                "variant": "info",
                "title": "Паспорт карты",
                "content": intro_text
            })
            
        # 2. Client Data
        c = context.get("client", {})
        birth_time_known = c.get("birth_time_known", True)
        
        # House System Localization
        hs_raw = str(chart_data.get("house_system") or "Placidus")
        if not birth_time_known:
            hs_display = "Космограмма (без домов)"
        elif "Whole" in hs_raw: hs_display = "Цельнознаковая"
        elif "Placidus" in hs_raw: hs_display = "Плацидус"
        elif "Equal" in hs_raw: hs_display = "Равнодомная"
        elif "Koch" in hs_raw: hs_display = "Кох"
        elif "Regio" in hs_raw: hs_display = "Региомонтан"
        elif "Porph" in hs_raw: hs_display = "Порфирий"
        else: hs_display = hs_raw

        # Date Formatting
        tz = c.get("birth_timezone") or "UTC"
        display_date = c.get('birth_date') or "-"
        
        if display_date != "-":
            try:
                clean_iso = display_date.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_iso)
                if dt.tzinfo and tz != "UTC":
                    dt = dt.astimezone(ZoneInfo(tz))
                
                if birth_time_known:
                    display_date = dt.strftime("%d.%m.%Y %H:%M")
                else:
                    display_date = dt.strftime("%d.%m.%Y (время неизв.)")
                
                if tz == "UTC" and birth_time_known:
                    display_date = f"{display_date} (UTC)"
            except Exception:
                pass

        blocks.append({
            "type": "header",
            "level": 3,
            "text": "Данные рождения"
        })
        
        blocks.append({
            "type": "key_value",
            "items": [
                {"key": "Кверент", "value": c.get('name') or "Unknown"},
                {"key": "Дата", "value": display_date},
                {"key": "Место", "value": c.get('birth_location') or "-"},
                {"key": "Часовой пояс", "value": tz if birth_time_known else "-"},
                {"key": "Дома", "value": hs_display}
            ]
        })
        
        # Check for High Latitude switch
        lat = c.get("birth_lat")
        if birth_time_known and lat and abs(lat) >= 60.0 and "Whole" in str(hs_raw):
             blocks.append({
                "type": "callout",
                "variant": "warning",
                "title": "⚠️ Особенности расчета",
                "content": f"Место рождения находится в высоких широтах ({lat:.2f}°). Система домов автоматически переключена на «Полнознаковую» (Whole Sign), так как стандартная система Плацидус не работает корректно за полярным кругом."
            })

        # 3. Planets Table Preparation
        positions = chart_data.get("positions", [])
        
        angles_data = []
        planets_data = []
        
        for p in positions:
            name_raw = p["name"]
            if name_raw in ["RAMC", "Zero"]: continue
            
            name_ru = RU_PLANETS_FULL.get(name_raw, name_raw)
            sign_ru = RU_SIGNS.get(p["sign"], p["sign"])
            house = str(p.get("house", "-")) if birth_time_known else "-"
            
            deg = int(p["sign_degree"])
            minute = int((p["sign_degree"] - deg) * 60)
            deg_str = f"{deg}°{minute:02d}'"
            
            retro = "R" if p.get("is_retrograde") else ""
            
            # Row: [Name, Sign, House, Degree, Retro]
            row = [name_ru, sign_ru, house, deg_str, retro]
            
            if name_raw in ["ASC", "MC", "DSC", "IC", "Vertex", "Part of Fortune"]:
                angles_data.append(row)
            else:
                planets_data.append(row)

        # 4. Render Tables
        if angles_data and birth_time_known:
             blocks.append({
                "type": "header",
                "level": 3,
                "text": "Угловые точки"
            })
             # Angles usually don't have Retro, so we use 4 columns
             blocks.append({
                "type": "table",
                "columns": [
                    {"header": "Точка", "width": "35%"},
                    {"header": "Знак", "width": "25%"},
                    {"header": "Дом", "width": "15%", "align": "center"},
                    {"header": "Град.", "width": "25%", "align": "right", "nowrap": True}
                ],
                "rows": [row[:4] for row in angles_data]
            })

        if planets_data:
            blocks.append({
                "type": "header",
                "level": 3,
                "text": "Планеты"
            })
            
            has_retro = any(row[4] for row in planets_data)
            p_cols = [
                {"header": "Планета", "width": "35%"},
                {"header": "Знак", "width": "25%"},
            ]
            if birth_time_known:
                p_cols.append({"header": "Дом", "width": "15%", "align": "center"})
            
            p_cols.append({"header": "Град.", "width": "25%", "align": "right", "nowrap": True})
            
            final_rows = []
            if has_retro:
                p_cols.append({"header": "R", "width": "30px", "align": "center"})
                if birth_time_known:
                    final_rows = planets_data
                else:
                    # Filter out house column (index 2)
                    final_rows = [[r[0], r[1], r[3], r[4]] for r in planets_data]
            else:
                if birth_time_known:
                    final_rows = [row[:4] for row in planets_data]
                else:
                    # Filter out house column (index 2)
                    final_rows = [[r[0], r[1], r[3]] for r in planets_data]

            blocks.append({
                "type": "table",
                "columns": p_cols,
                "rows": final_rows
            })
            
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=json.dumps(blocks, ensure_ascii=False))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id == "horary_00_passport":
        logger.info("gen.content.static", section="horary_00_passport")
        c = context.get("client", {})
        question = c.get("question") or c.get("note") or "Вопрос не указан"
        dt_str = chart_data.get("datetime_local") or chart_data.get("datetime_utc")
        
        dt_display = dt_str
        try:
            if dt_str:
                if dt_str.endswith("Z"): dt_str = dt_str[:-1]
                dt_val = datetime.fromisoformat(dt_str)
                
                # Timezone conversion
                tz_name = chart_data.get("location", {}).get("timezone")
                if tz_name:
                    if dt_val.tzinfo is None:
                        dt_val = dt_val.replace(tzinfo=timezone.utc)
                    dt_val = dt_val.astimezone(ZoneInfo(tz_name))
                
                dt_display = dt_val.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass
            
        loc = chart_data.get("location", {}).get("name", "Неизвестно")
        
        blocks = [
            {"type": "header", "level": 2, "text": "Паспорт вопроса"},
            {
                "type": "key_value",
                "items": [
                    {"key": "Вопрос", "value": question},
                    {"key": "Дата и время", "value": dt_display},
                    {"key": "Место", "value": loc},
                ],
            },
        ]
        content = json.dumps(blocks, ensure_ascii=False)
        logger.info("gen.content.passport.result", content_len=len(content), content_preview=content[:50])
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=content)
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id == "horary_00_technical":
        h = chart_data.get("horary", {})
        if not h:
             res = SectionResult(section_id=spec.section_id, title=spec.title, content=json.dumps([{"type": "paragraph", "text": "_Нет данных хорара._"}], ensure_ascii=False))
             res.duration_ms = int((time.perf_counter() - start_t) * 1000)
             return res

        blocks = []
        
        # 1. Scenario
        adapter_name = h.get('adapter_name', 'Не определен')
        blocks.append({"type": "header", "level": 2, "text": f"🧩 Сценарий: {adapter_name}"})
        
        # 2. Roles
        roles = h.get("roles", {})
        if roles:
            blocks.append({"type": "header", "level": 3, "text": "🎭 Сигнификаторы (Роли)"})
            
            priority = ["querent", "quesited", "opponent", "judge", "law", "verdict", "money", "wallet", "fine", "profit", "job", "partner", "moon"]
            sorted_keys = sorted(roles.keys(), key=lambda k: priority.index(k) if k in priority else 99)
            
            role_names_ru = {
                "querent": "Кверент (Ты)", "quesited": "Квестит (Вопрос)", "opponent": "Оппонент",
                "judge": "Судья/Власть", "law": "Закон", "verdict": "Итог дела", "money": "Деньги",
                "wallet": "Твой кошелек", "fine": "Штраф/Потери", "profit": "Выгода",
                "job": "Работа", "partner": "Партнер", "moon": "Луна"
            }
            
            rows = []
            for key in sorted_keys:
                r = roles[key]
                role_name = role_names_ru.get(key, key.capitalize())
                planet = r.get('planet_ru', '-')
                house = str(r.get('house', '-'))
                desc = r.get('description', '')
                rows.append([role_name, planet, house, desc])
            
            blocks.append({
                "type": "table",
                "columns": [
                    {"header": "Роль", "width": "25%"},
                    {"header": "Планета", "width": "20%"},
                    {"header": "Дом", "width": "15%", "align": "center"},
                    {"header": "Описание", "width": "40%"}
                ],
                "rows": rows
            })

        # 3. Radicality
        rad = h.get("radicality", {})
        if rad:
            score = rad.get('score', '?')
            try:
                score_val = float(score)
            except: 
                score_val = 0
                
            blocks.append({"type": "rating", "value": score_val, "max": 10, "label": "🛡️ Радикальность"})
            
            issues = rad.get('issues', [])
            warnings = rad.get('warnings', [])
            
            if issues:
                blocks.append({
                    "type": "callout", 
                    "variant": "error", 
                    "title": "Проблемы радикальности",
                    "content": "\n".join([f"• {i}" for i in issues])
                })
            
            if warnings:
                blocks.append({
                    "type": "callout", 
                    "variant": "warning", 
                    "title": "Предупреждения",
                    "content": "\n".join([f"• {w}" for w in warnings])
                })
                
            if not issues and not warnings:
                blocks.append({
                    "type": "callout", 
                    "variant": "success", 
                    "title": "Карта радикальна",
                    "content": "Суждение надежно, можно приступать к анализу."
                })

        res = SectionResult(section_id=spec.section_id, title=spec.title, content=json.dumps(blocks, ensure_ascii=False))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id == "technical_appendix":
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=format_technical_appendix(chart_data))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id in {"executive_summary", "final_synthesis"}:
        insight_pack = (context.get("section_context") or {}).get("insight_pack")
        if insight_pack:
            content = build_section_validation_fallback_content(spec, context)
            res = SectionResult(section_id=spec.section_id, title=spec.title, content=content)
            res.duration_ms = int((time.perf_counter() - start_t) * 1000)
            return res

    # 2. Template Mode
    if use_template:
        if spec.section_id == "week_strategy":
            content = _render_week_strategy_content(context)
        elif spec.section_id in {"month_full_forecast", "month_theme"}:
            content = _render_month_forecast_content(context)
        else:
            content = build_section_template_content(spec)
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=inject_planet_emojis(content))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    # 3. LLM Generation
    effective_spec = spec
    if spec.section_id in ["balance_wheel_1_6", "balance_wheel_7_12"]:
        structured_house_pack = (
            (context.get("section_context", {}).get("insight_pack") or {}).get("house_pack")
        )
        if structured_house_pack:
            house_ctx = json.dumps(structured_house_pack, ensure_ascii=False)
            new_prompt = (
                spec.prompt
                + "\n\n### СТРУКТУРНЫЙ HOUSE PACK ДЛЯ АНАЛИЗА (ИСПОЛЬЗУЙ КАК ОСНОВУ, НЕ ВЫХОДИ ЗА НЕГО):\n"
                + house_ctx
            )
        else:
            house_ctx = (
                context.get("section_context", {}).get("house_context")
                or context.get("houses_summary")
                or format_house_context(chart_data)
            )
            new_prompt = spec.prompt + f"\n\n### ДАННЫЕ ПО ДОМАМ ДЛЯ АНАЛИЗА (ИСПОЛЬЗУЙ ИХ!):\n{house_ctx}\n\nОписывай каждый дом, учитывая знак куспида, положение управителя и планеты внутри."
        effective_spec = SectionSpec(
            section_id=spec.section_id,
            title=spec.title,
            prompt=new_prompt,
            max_tokens=spec.max_tokens
        )

    result = await asyncio.to_thread(
        _facade_symbol("generate_section_with_retries", generate_section_with_retries),
        effective_spec,
        context,
        primary_client=llm_client,
        fallback_models=fallback_models,
        max_attempts=retry_attempts,
    )
    
    raw = result.content
    
    # JSON Cleanup: Strip code blocks if present
    if raw:
        import re
        # Find content between ```json and ```
        match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
        else:
            # Fallback: find content between ``` and ```
            match = re.search(r"```\s*(.*?)\s*```", raw, re.DOTALL)
            if match:
                raw = match.group(1).strip()

    if spec.section_id == "week_strategy" and context.get("week_forecast_data"):
        raw = _render_week_strategy_content(context, llm_content=raw)
    if spec.section_id in {"month_full_forecast", "month_theme"} and context.get("month_forecast_data"):
        raw = _render_month_forecast_content(context, llm_content=raw)

    # 4. Intro Injection (JSON-safe)
    intro = SECTION_INTROS.get(spec.section_id)
    if intro and raw and raw.strip().startswith("["):
        try:
            blocks = json.loads(raw)
            if isinstance(blocks, list):
                # Prepend intro block
                blocks.insert(0, {
                    "type": "paragraph",
                    "text": intro.strip()
                })
                raw = json.dumps(blocks, ensure_ascii=False)
        except:
            # If parsing fails, we can't safely inject. 
            # But generate_section_with_retries should guarantee valid JSON if valid.
            pass
        
    # END_BLOCK: SECTION_STATIC_OVERRIDE
    # START_BLOCK: SECTION_LLM_GENERATION
    result.content = inject_planet_emojis(raw)
    result.duration_ms = int((time.perf_counter() - start_t) * 1000)
    _workflow_log(
        "info",
        "report.workflow.section_generation_complete",
        fn="generate_section_content",
        contract="FN-ENQUEUE-REPORT-GENERATION",
        block="SECTION_LLM_GENERATION",
        report_id=context.get("report_id") or context.get("client", {}).get("report_id"),
        section_id=spec.section_id,
        duration_ms=result.duration_ms,
    )
    # END_BLOCK: SECTION_LLM_GENERATION
    return result
# END_BLOCK: SECTION_RUNTIME_GENERATION
