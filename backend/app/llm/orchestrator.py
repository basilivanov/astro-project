# ############################################################################
# AI_HEADER: MODULE_LLM_ORCHESTRATOR
# ROLE: Sectioned LLM generation with JSON validation.
# DEPENDENCIES: pydantic.
# GRACE_ANCHORS: [LLM_SCHEMAS, LLM_CLIENT, LLM_PROMPTS, LLM_ORCHESTRATOR]
# ############################################################################

# START_MODULE_CONTRACT: M-LLM-ORCHESTRATOR
# purpose: Provide stable LLM orchestration facade, provider clients, prompt assembly, and section generation.
# owns:
#   - backend/app/llm/orchestrator.py
# inputs:
#   - section specs, report context, provider environment, and raw provider output
# outputs:
#   - SectionResult lists and provider client instances through existing public imports
# invariants:
#   - provider routing, prompt text, fallback imports, and public symbols remain stable
#   - parsing and validation semantics are delegated without behavior changes
# non_goals:
#   - changing report schemas or LLM fallback business policy
# END_MODULE_CONTRACT: M-LLM-ORCHESTRATOR

# START_MODULE_MAP: M-LLM-ORCHESTRATOR
# public_entrypoints:
#   - LLMOrchestrator.generate_sections -> sectioned generation lifecycle
#   - build_cli_client_from_env -> CLI provider factory
#   - build_section_prompt -> section prompt assembly
# internal_entrypoints:
#   - OpenRouterClient.generate -> OpenRouter provider call
#   - CliLLMClient.generate -> local CLI provider call
# semantic_blocks:
#   - LLM_SCHEMAS: SectionSpec/SectionResult and validation errors
#   - LLM_CLIENT: provider clients, CLI parsing, and provider env resolution
#   - LLM_PROMPTS: prompt and runtime hint assembly
#   - LLM_ORCHESTRATOR: compatibility imports and section generation class
# owned_tests:
#   - tests/test_llm_cli_parsing.py
#   - tests/test_llm_fallback_chain.py
#   - tests/test_llm_model_routing.py
# adjacent_modules:
#   - backend/app/llm/orchestrator_parse.py
# END_MODULE_MAP: M-LLM-ORCHESTRATOR

import json
import os
import re
import socket
import shlex
import struct
import subprocess
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from pydantic import ValidationError
import structlog

# #START_BLOCK_LLM_SCHEMAS
from .orchestrator_contracts import (
    LLMBlockContractError,
    LLMContentValidationError,
    NATAL_SECTION_IDS,
    PREMIUM_NATAL_SECTION_IDS,
    SectionResult,
    SectionSpec,
    _contains_any,
)
# #END_BLOCK_LLM_SCHEMAS
@lru_cache(maxsize=1)
def _load_premium_natal_style_hint() -> str:
    fallback = (
        "STYLE_CONTRACT.md (canonical natal tone): 70% премиальный художественный нарратив, "
        "30% практическая навигация. Сначала жизнь, потом астрология. "
        "Рабочая формула секции: сцена -> механизм -> зрелый ход. "
        "Одна секция = одна центральная мысль. Один сильный образ на секцию достаточен; "
        "дальше работаем ясным языком. Совет рождается из описанного паттерна, а не приклеивается в конце. "
        "Не используй сухой учебниковый тон, коучинговые клише и одинаковый ритм секций."
    )

    contract_path = Path(__file__).resolve().parents[3] / "STYLE_CONTRACT.md"
    try:
        contract_text = contract_path.read_text(encoding="utf-8")
    except OSError:
        return fallback

    snippet_candidates = [
        "Главная формула: **70% премиальный художественный нарратив, 30% практическая навигация**.",
        "Сначала жизнь, потом астрология.",
        "Рабочая формула секции: **сцена -> механизм -> зрелый ход**.",
        "Одна секция = одна центральная мысль.",
        "Один сильный образ на секцию достаточен; дальше работаем уже ясным языком.",
        "Совет рождается из описанного паттерна, а не приклеивается в конце.",
        "Не делать каждую секцию одинаковой по ритму: ввод, список, вывод в одной и той же интонации.",
    ]
    selected = [
        candidate.replace("**", "")
        for candidate in snippet_candidates
        if candidate in contract_text
    ]
    if not selected:
        return fallback

    return "STYLE_CONTRACT.md (canonical natal tone): " + " ".join(selected)


def _build_style_contract_hint(section_id: str) -> str:
    if section_id not in PREMIUM_NATAL_SECTION_IDS:
        return ""
    hint = _load_premium_natal_style_hint()
    if section_id == "executive_summary":
        hint += (
            " Дополнительно для Executive Summary: первая фраза должна быть точным life-first логлайном (сцена или внутренний закон карты), "
            "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО начинать с общих заходов вроде 'Ты находишься...', 'Ты способен...', "
            "'У тебя есть...' или 'Твоя задача...'. Пункты списка должны звучать как editorial navigation "
            "без повторяющихся префиксов и без двоеточий."
        )
    return f"{hint}\n"


def _format_runtime_hint_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("label", "text", "seed", "summary", "content"):
            text = str(value.get(key, "")).strip()
            if text:
                return text
        items = value.get("items")
        if isinstance(items, list):
            preview = [_format_runtime_hint_value(item) for item in items[:2]]
            preview = [item for item in preview if item]
            if preview:
                return ", ".join(preview)
        return ""
    if isinstance(value, list):
        preview = [_format_runtime_hint_value(item) for item in value[:2]]
        preview = [item for item in preview if item]
        return ", ".join(preview)
    if value is None:
        return ""
    return str(value).strip()


def _build_executive_summary_runtime_hint(context: Dict[str, Any], section_id: str) -> str:
    if section_id != "executive_summary":
        return ""

    insight_pack = (context.get("section_context") or {}).get("insight_pack")
    if not isinstance(insight_pack, dict) or not insight_pack:
        return ""

    scene = _format_runtime_hint_value(insight_pack.get("scene_seeds"))
    strength = _format_runtime_hint_value(insight_pack.get("strengths_score"))
    risk = _format_runtime_hint_value(insight_pack.get("risk_score"))
    relationship = _format_runtime_hint_value(insight_pack.get("relationship_theme"))
    money = _format_runtime_hint_value(insight_pack.get("money_theme"))
    development = _format_runtime_hint_value(insight_pack.get("development_focus"))
    best_mode = _format_runtime_hint_value(insight_pack.get("best_mode_of_action"))

    lines = [
        "EXECUTIVE SUMMARY RUNTIME CONTRACT: не своди секцию к набору общих команд или только к `what_to_do`.",
        "Секция будет отклонена runtime validation, если не будут ЯВНО покрыты все жизненные зоны ниже.",
        f"- жизненная сцена/внутренний закон: {scene or 'используй самый сильный scene_seed из insight_pack'}",
        f"- опора/ресурс: {strength or 'возьми top strength из strengths_score'}",
        f"- перегиб/риск: {risk or 'возьми top risk из risk_score'}",
        f"- отношения/близость: {relationship or 'возьми relationship_theme'}",
        f"- деньги/реализация: {money or 'возьми money_theme'}",
        f"- фокус роста: {development or 'возьми development_focus'}",
        f"- зрелый режим: {best_mode or 'возьми best_mode_of_action'}",
        "Хотя бы один пункт списка должен быть про отношения и хотя бы один про деньги/реализацию.",
        "Минимум три пункта списка должны быть описательными observation-lines о паттерне карты, а не чистыми императивами.",
    ]
    return "\n".join(lines) + "\n"

# #START_BLOCK_LLM_CLIENT
class LLMClient:
    """
    # PURPOSE: Define the minimal contract for an LLM client.
    # INPUT: prompt (str).
    # OUTPUT: JSON string returned by the model.
    # CONTEXT: Base interface for OpenAI/Anthropic implementations.
    """

    def generate(self, prompt: str, max_tokens_override: Optional[int] = None) -> tuple[str, Optional[Dict[str, Any]]]:
        raise NotImplementedError("LLMClient.generate must be implemented")


class StubLLMClient(LLMClient):
    """
    # PURPOSE: Provide stable JSON for pipeline diagnostics.
    # INPUT: prompt (str).
    # OUTPUT: JSON string with placeholder content.
    # CONTEXT: Used for local runs without external LLMs.
    """

    def generate(self, prompt: str, max_tokens_override: Optional[int] = None) -> tuple[str, Optional[Dict[str, Any]]]:
        return '[{"type":"paragraph","text":"Stub content"}]', {"total_tokens": 10}


class OpenRouterClient(LLMClient):
    """
    # PURPOSE: Call OpenRouter chat completions with an API key.
    # INPUT: prompt (str).
    # OUTPUT: JSON string returned by the model.
    # CONTEXT: Uses OpenRouter-compatible OpenAI API.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        temperature: float,
        max_tokens: int,
        app_name: str,
        site_url: str,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.app_name = app_name
        self.site_url = site_url

    @classmethod
    def from_env(cls, mode: str = "smart", model_override: Optional[str] = None) -> "OpenRouterClient":
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing")

        if model_override:
            model = model_override
        elif mode == "cheap":
            model = os.getenv("OPENROUTER_MODEL_CHEAP", "openai/gpt-4.1-nano")
        else:
            model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-nano")

        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        app_name = os.getenv("OPENROUTER_APP_NAME", "astro-saas")
        site_url = os.getenv("OPENROUTER_SITE_URL", "")

        max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "4000"))
        temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.4"))

        return cls(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            app_name=app_name,
            site_url=site_url,
        )

    def generate(self, prompt: str, max_tokens_override: Optional[int] = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return ONLY valid JSON. No code fences.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens_override or self.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": self.app_name,
        }

        if self.site_url:
            headers["HTTP-Referer"] = self.site_url

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            timeout_seconds = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "60"))
        except ValueError:
            timeout_seconds = 60

        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise ValueError(f"OpenRouter error: {exc.code} {error_body}") from exc
        except urllib.error.URLError as exc:
            raise ValueError(f"OpenRouter connection error: {exc}") from exc

        try:
            response_data = json.loads(raw)
        except json.JSONDecodeError as exc:
            snippet = raw[:400].replace("\n", " ").strip()
            raise ValueError(
                f"OpenRouter invalid JSON response: {snippet}"
            ) from exc
        try:
            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage")
            if content is None or (isinstance(content, str) and not content.strip()):
                 raise ValueError("OpenRouter returned empty content")
            return content, usage
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("OpenRouter response missing content") from exc
def _parse_gemini_cli_output(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Gemini CLI response missing content")
    # First try to extract a JSON array directly from the raw output.
    json_text = _extract_json_text(raw)
    if json_text and json_text.strip().startswith("["):
        return json_text.strip()

    decoder = json.JSONDecoder()
    start = raw.find("{")
    if start == -1:
        raise ValueError("Gemini CLI response missing JSON payload")
    try:
        data, _ = decoder.raw_decode(raw[start:])
    except json.JSONDecodeError:
        for line in raw.splitlines():
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                data = json.loads(line)
                break
            except json.JSONDecodeError:
                data = None
        if not data:
            raise
    response = data.get("response")
    if not response:
        raise ValueError("Gemini CLI response missing content")
    response = response.strip()
    if response.startswith("```"):
        response = _strip_code_fences(response)
    return response.strip()


def _parse_codex_cli_output(raw: str) -> str:
    last_text = None
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = payload.get("item")
        if payload.get("type") == "item.completed" and isinstance(item, dict):
            text = item.get("text")
            if text:
                last_text = text
    if last_text:
        return last_text.strip()
    raise ValueError("Codex CLI response missing content")


class CliLLMClient(LLMClient):
    """
    # PURPOSE: Use locally authenticated CLI models (Gemini/Codex) for LLM output.
    # INPUT: prompt (str).
    # OUTPUT: JSON string returned by the CLI model.
    # CONTEXT: Useful for low-cost tests without OpenRouter API usage.
    """

    def __init__(
        self,
        provider: str,
        model: Optional[str],
        timeout: int,
        reasoning: Optional[str],
        extra_args: Optional[List[str]],
    ) -> None:
        self.provider = provider
        self.model = model
        self.timeout = timeout
        self.reasoning = reasoning
        self.extra_args = extra_args or []

    def generate(self, prompt: str, max_tokens_override: Optional[int] = None) -> tuple[str, Optional[Dict[str, Any]]]:
        provider = (self.provider or "").strip().lower()
        logger = structlog.get_logger()
        subprocess_env = None
        if provider == "gemini":
            cmd = ["gemini", "--output-format", "json"]
            if self.model:
                cmd += ["--model", self.model]
        elif provider == "codex":
            cmd = ["codex", "exec", "--json"]
            subprocess_env = _build_codex_subprocess_env()
            if self.model:
                cmd += ["-m", self.model]
            if self.reasoning and not any(
                "model_reasoning_effort" in arg for arg in self.extra_args
            ):
                cmd += ["-c", f'model_reasoning_effort="{self.reasoning}"']
            if not any(arg == "--skip-git-repo-check" for arg in self.extra_args):
                cmd.append("--skip-git-repo-check")
        else:
            raise ValueError(f"Unsupported CLI provider: {self.provider}")

        if self.extra_args:
            cmd += self.extra_args

        cmd.append(prompt)
        logger.info(
            "llm.cli.request",
            block_id="LLM_CLIENT",
            provider=provider,
            model=self.model,
            prompt_len=len(prompt or ""),
        )
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                env=subprocess_env,
            )
        except subprocess.TimeoutExpired as exc:
            logger.error(
                "llm.cli.timeout",
                block_id="LLM_CLIENT",
                provider=provider,
                model=self.model,
                timeout=self.timeout,
            )
            raise ValueError(f"CLI timeout after {self.timeout}s") from exc

        if result.returncode != 0:
            err = (result.stderr or "").strip()
            logger.error(
                "llm.cli.error",
                block_id="LLM_CLIENT",
                provider=provider,
                model=self.model,
                error=err or "non-zero exit",
            )
            raise ValueError(f"CLI error: {err or 'non-zero exit'}")

        stdout = (result.stdout or "").strip()
        if not stdout:
            raise ValueError("CLI response was empty")

        if provider == "gemini":
            return _parse_gemini_cli_output(stdout), None
        return _parse_codex_cli_output(stdout), None


def _get_cli_setting(name: str, provider: str) -> str:
    provider_value = os.getenv(f"LLM_CLI_{name}_{provider.upper()}", "").strip()
    if provider_value:
        return provider_value
    return os.getenv(f"LLM_CLI_{name}", "").strip()


def _build_codex_subprocess_env(
    base_env: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    env = dict(base_env or os.environ)
    base_url = (
        env.get("LLM_CLI_OPENAI_BASE_URL_CODEX", "").strip()
        or env.get("OPENAI_BASE_URL", "").strip()
    )
    api_key = (
        env.get("LLM_CLI_OPENAI_API_KEY_CODEX", "").strip()
        or env.get("OPENAI_API_KEY", "").strip()
    )
    if "__DOCKER_HOST_GATEWAY__" in base_url:
        gateway = _resolve_docker_host_gateway()
        if gateway:
            base_url = base_url.replace("__DOCKER_HOST_GATEWAY__", gateway)
    if base_url:
        env["OPENAI_BASE_URL"] = base_url
    if api_key:
        env["OPENAI_API_KEY"] = api_key
    return env


def _resolve_docker_host_gateway() -> Optional[str]:
    try:
        with open("/proc/net/route", "r", encoding="utf-8") as route_file:
            next(route_file, None)
            for line in route_file:
                fields = line.strip().split()
                if len(fields) < 4 or fields[1] != "00000000":
                    continue
                flags = int(fields[3], 16)
                if not flags & 0x2:
                    continue
                gateway = struct.pack("<L", int(fields[2], 16))
                return socket.inet_ntoa(gateway)
    except (OSError, ValueError):
        return None
    return None


def build_cli_client_from_env(provider_override: Optional[str] = None) -> CliLLMClient:
    provider = (provider_override or os.getenv("LLM_CLI_PROVIDER", "gemini")).strip().lower()
    model = _get_cli_setting("MODEL", provider) or None
    if not model and provider == "gemini":
        model = "gemini-3-pro-preview"
    timeout = int(os.getenv("LLM_CLI_TIMEOUT", "120"))
    reasoning = (_get_cli_setting("REASONING", provider) or "medium").strip().lower() or None
    if reasoning in {"default", "auto", "none"}:
        reasoning = None
    extra_args_raw = _get_cli_setting("ARGS", provider)
    extra_args = shlex.split(extra_args_raw) if extra_args_raw else []
    return CliLLMClient(
        provider=provider,
        model=model,
        timeout=timeout,
        reasoning=reasoning,
        extra_args=extra_args,
    )
# #END_BLOCK_LLM_CLIENT

# #START_BLOCK_LLM_PROMPTS
def build_section_prompt(section: SectionSpec, context: Dict[str, Any]) -> str:
    """
    # PURPOSE: Build the prompt for a single section.
    # INPUT: section (SectionSpec), context (dict).
    # OUTPUT: Final prompt string.
    # CONTEXT: Used by the orchestrator before calling the client.
    """

    context_json = json.dumps(
        context,
        ensure_ascii=section.section_id != "executive_summary",
        separators=(",", ":"),
    )

    section_context_hint = ""
    if context.get("section_context"):
        section_context_hint = (
            "Если `section_context` присутствует — это ТОЛЬКО релевантные факты для этой секции. "
            "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО придумывать отсутствующие данные или опираться на факты вне этого среза.\n"
        )
    insight_pack_hint = ""
    if (context.get("section_context") or {}).get("insight_pack"):
        insight_pack_hint = (
            "КРИТИЧЕСКИ ВАЖНО: Если `section_context.insight_pack` присутствует — "
            "это канонический детерминированный вывод层的 (рассчитанный системой). "
            "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО заменять его собственными выводами или общими формулами. "
            "Используй поля из insight_pack (labels, scores, seeds, cross-links) как ОСНОВУ секции. "
            "Можешь вербализировать и организовать их, но НЕ подменяй альтернативными выводами.\n"
        )
    style_contract_hint = _build_style_contract_hint(section.section_id)
    executive_runtime_hint = _build_executive_summary_runtime_hint(context, section.section_id)

    return (
        "Return ONLY a valid JSON array of blocks.\n"
        "No code fences. No extra keys. No surrounding text.\n"
        "Use only the block types specified in the prompt.\n"
        f"{section_context_hint}"
        f"{insight_pack_hint}"
        f"{style_contract_hint}"
        f"{executive_runtime_hint}"
        f"section_id: {section.section_id}\n"
        f"title: {section.title}\n"
        f"prompt: {section.prompt}\n"
        f"context: {context_json}\n"
        "JSON example:\n"
        '[{"type":"header","level":2,"text":"Заголовок"},{"type":"paragraph","text":"Текст"}]\n'
    )
# #END_BLOCK_LLM_PROMPTS

from .orchestrator_parse import (
    _extract_json_text,
    _try_parse_blocks,
    _extract_text_from_blocks,
    _extract_house_numbers,
    _normalize_blocks,
    _fallback_section_result,
    validate_natal_section_content,
    validate_section_content,
    _repair_section_content,
    _parse_section_result,
)

# #START_BLOCK_LLM_ORCHESTRATOR
class LLMOrchestrator:
    """
    # PURPOSE: Orchestrate sectioned report generation.
    # INPUT: sections (list), context (dict), client (LLMClient).
    # OUTPUT: List of validated SectionResult items.
    # CONTEXT: Base layer between the API and external LLMs.
    """

    def __init__(self, client: LLMClient, *, validate_content: bool = True):
        self.client = client
        self.validate_content = validate_content

    def generate_sections(
        self, sections: List[SectionSpec], context: Dict[str, Any]
    ) -> List[SectionResult]:
        import time
        results: List[SectionResult] = []
        for section in sections:
            start_t = time.perf_counter()
            prompt = build_section_prompt(section, context)
            try:
                raw, usage = self.client.generate(prompt, max_tokens_override=section.max_tokens)
            except Exception as exc:
                raise ValueError(f"LLM call failed: {exc}") from exc
            try:
                result = _parse_section_result(raw, section)
                result.usage = usage
            except LLMContentValidationError:
                raise
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
            if self.validate_content:
                content = result.content or ""
                for _ in range(3):
                    try:
                        validate_section_content(section, content)
                        break
                    except LLMBlockContractError as exc:
                        logger.warning(
                            "llm.invalid_contract",
                            block_id="LLM_PARSE",
                            section_id=section.section_id,
                            error=str(exc),
                            length=len(content or ""),
                        )
                        raise
                    except LLMContentValidationError as exc:
                        logger.warning(
                            "llm.invalid_content",
                            block_id="LLM_PARSE",
                            section_id=section.section_id,
                            error=str(exc),
                            length=len(content or ""),
                        )
                        repaired = _repair_section_content(
                            section, content, str(exc)
                        )
                        if repaired == content:
                            raise
                        content = repaired
                else:
                    raise LLMContentValidationError("content repair failed")
                if content != result.content:
                    result.content = content
            
            result.duration_ms = int((time.perf_counter() - start_t) * 1000)
            results.append(result)
        return results
# #END_BLOCK_LLM_ORCHESTRATOR
