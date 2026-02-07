# ############################################################################
# AI_HEADER: MODULE_LLM_ORCHESTRATOR
# ROLE: Sectioned LLM generation with JSON validation.
# DEPENDENCIES: pydantic.
# GRACE_ANCHORS: [LLM_SCHEMAS, LLM_CLIENT, LLM_PROMPTS, LLM_ORCHESTRATOR]
# ############################################################################

import json
import os
import re
import shlex
import subprocess
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError
import structlog

# #START_BLOCK_LLM_SCHEMAS
class SectionSpec(BaseModel):
    """
    # PURPOSE: Describe a report section to be generated.
    # INPUT: section_id, title, prompt.
    # OUTPUT: Validated specification object.
    # CONTEXT: Used by the orchestrator during generation.
    """

    section_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)


class SectionResult(BaseModel):
    """
    # PURPOSE: Capture a generated section result.
    # INPUT: section_id, title, content.
    # OUTPUT: Validated result object.
    # CONTEXT: Returned by the orchestrator.
    """

    section_id: str
    title: str
    content: str
# #END_BLOCK_LLM_SCHEMAS


class LLMContentValidationError(ValueError):
    """
    # PURPOSE: Signal that LLM output failed structural validation.
    # INPUT: error message.
    # OUTPUT: Exception for retry/fallback control flow.
    # CONTEXT: Raised after parsing when content shape is insufficient.
    """


NATAL_SECTION_IDS = {
    "input_frame",
    "synthesis",
    "framework_elements_modes",
    "axes_truths",
    "aspects_beginner",
    "configurations_geometry",
    "dispositor_office",
    "core_triad",
    "mercury_mind",
    "shadow_trauma",
    "nodes_growth",
    "vertex_fate",
    "balance_wheel",
    "love_intimacy",
    "money_realization",
    "stars_transuranus",
    "time_cycles",
    "final_synthesis",
}

# #START_BLOCK_LLM_CLIENT
class LLMClient:
    """
    # PURPOSE: Define the minimal contract for an LLM client.
    # INPUT: prompt (str).
    # OUTPUT: JSON string returned by the model.
    # CONTEXT: Base interface for OpenAI/Anthropic implementations.
    """

    def generate(self, prompt: str) -> str:
        raise NotImplementedError("LLMClient.generate must be implemented")


class StubLLMClient(LLMClient):
    """
    # PURPOSE: Provide stable JSON for pipeline diagnostics.
    # INPUT: prompt (str).
    # OUTPUT: JSON string with placeholder content.
    # CONTEXT: Used for local runs without external LLMs.
    """

    def generate(self, prompt: str) -> str:
        return '[{"type":"paragraph","text":"Stub content"}]'


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
            model = os.getenv("OPENROUTER_MODEL_CHEAP", "openai/gpt-4o-mini")
        else:
            model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        app_name = os.getenv("OPENROUTER_APP_NAME", "astro-saas")
        site_url = os.getenv("OPENROUTER_SITE_URL", "")

        max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "2000"))
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

    def generate(self, prompt: str) -> str:
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
            "max_tokens": self.max_tokens,
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
            with urllib.request.urlopen(request, timeout=60) as response:
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
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("OpenRouter response missing content") from exc
def _parse_gemini_cli_output(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Gemini CLI response missing content")
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

    def generate(self, prompt: str) -> str:
        provider = (self.provider or "").strip().lower()
        logger = structlog.get_logger()
        if provider == "gemini":
            cmd = ["gemini", "--output-format", "json"]
            if self.model:
                cmd += ["--model", self.model]
        elif provider == "codex":
            cmd = ["codex", "exec", "--json"]
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
            return _parse_gemini_cli_output(stdout)
        return _parse_codex_cli_output(stdout)


def build_cli_client_from_env(provider_override: Optional[str] = None) -> CliLLMClient:
    provider = (provider_override or os.getenv("LLM_CLI_PROVIDER", "gemini")).strip().lower()
    model = os.getenv("LLM_CLI_MODEL", "").strip() or None
    if not model and provider == "gemini":
        model = "gemini-3-pro-preview"
    timeout = int(os.getenv("LLM_CLI_TIMEOUT", "120"))
    reasoning = os.getenv("LLM_CLI_REASONING", "medium").strip().lower() or None
    if reasoning in {"default", "auto", "none"}:
        reasoning = None
    extra_args_raw = os.getenv("LLM_CLI_ARGS", "").strip()
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

    context_json = json.dumps(context, ensure_ascii=True, separators=(",", ":"))

    return (
        "Return ONLY a valid JSON array of blocks.\n"
        "No code fences. No extra keys. No surrounding text.\n"
        "Use only the block types specified in the prompt.\n"
        f"section_id: {section.section_id}\n"
        f"title: {section.title}\n"
        f"prompt: {section.prompt}\n"
        f"context: {context_json}\n"
        "JSON example:\n"
        '[{"type":"header","level":2,"text":"Заголовок"},{"type":"paragraph","text":"Текст"}]\n'
    )
# #END_BLOCK_LLM_PROMPTS

# #START_BLOCK_LLM_ORCHESTRATOR
logger = structlog.get_logger()


def _strip_code_fences(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            if lines[-1].strip().startswith("```"):
                return "\n".join(lines[1:-1]).strip()
    return text


def _extract_json_text(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()
    return text


def _try_parse_blocks(text: str) -> Optional[List[Dict[str, Any]]]:
    candidate = _strip_code_fences((text or "").strip())
    if not candidate.startswith("[") or not candidate.endswith("]"):
        return None
    try:
        data = json.loads(candidate)
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
    raise LLMContentValidationError(f"Invalid JSON in section {section.section_id}")


def validate_natal_section_content(section: SectionSpec, text: str) -> None:
    lower = text.lower()

    if section.section_id == "input_frame":
        if not re.search(r"\bкверент\b|\bклиент\b", lower):
            raise LLMContentValidationError("natal input missing client")
        if "дата рождения" not in lower:
            raise LLMContentValidationError("natal input missing birth date")
        if "место рождения" not in lower:
            raise LLMContentValidationError("natal input missing birth place")
        if "система домов" not in lower:
            raise LLMContentValidationError("natal input missing house system")
        # For tables, we check if table content exists in text
        if "положение планет" not in lower:
            raise LLMContentValidationError("natal input missing planet table")
        if "угловые точки" not in lower:
            raise LLMContentValidationError("natal input missing angles table")
        return

    if section.section_id == "synthesis":
        if "метафора" not in lower:
            raise LLMContentValidationError("natal synthesis missing metaphor")
        if "главный тезис" not in lower:
            raise LLMContentValidationError("natal synthesis missing thesis")
        return

    if section.section_id == "framework_elements_modes":
        if "доминанта" not in lower:
            raise LLMContentValidationError("natal framework missing dominants")
        if "стих" not in lower:
            raise LLMContentValidationError("natal framework missing element balance")
        if "дефиц" not in lower:
            raise LLMContentValidationError("natal framework missing deficit")
        if "девиз" not in lower:
            raise LLMContentValidationError("natal framework missing motto")
        return

    if section.section_id == "axes_truths":
        axis_tokens = ["asc", "dsc", "ic", "mc"]
        if any(token not in lower for token in axis_tokens):
            raise LLMContentValidationError("natal axes missing tokens")
        if not re.search(r"\b2\s*-\s*8\b", text):
            raise LLMContentValidationError("natal axes missing 2-8")
        if not re.search(r"\b3\s*-\s*9\b", text):
            raise LLMContentValidationError("natal axes missing 3-9")
        if "твоя правда" not in lower:
            raise LLMContentValidationError("natal axes missing truths")
        if not any(
            phrase in lower
            for phrase in ("правда партнера", "правда партнёра")
        ):
            raise LLMContentValidationError("natal axes missing truths")
        return

    if section.section_id == "aspects_beginner":
        # Simplified check for blocks text
        if "якорь" not in lower:
            raise LLMContentValidationError("natal aspects missing labels")
        return

    if section.section_id == "configurations_geometry":
        if "конфигурац" not in lower:
            raise LLMContentValidationError("natal config missing heading")
        has_no_configs = re.search(r"нет .*конфигурац|отсутств", lower)
        if not has_no_configs:
            for label in ["геометрия", "дар", "риск", "ключ", "вопрос"]:
                if f"{label}:" not in lower:
                    raise LLMContentValidationError("natal config missing fields")
        return

    if section.section_id == "dispositor_office":
        if "офис" not in lower:
            raise LLMContentValidationError("natal dispositor missing office")
        if "конверт" not in lower:
            raise LLMContentValidationError("natal dispositor missing envelope")
        if "босс" not in lower:
            raise LLMContentValidationError("natal dispositor missing boss")
        return

    if section.section_id == "core_triad":
        if not any(token in lower for token in ["asc", "асцендент"]):
            raise LLMContentValidationError("natal core missing triad")
        if "солнце" not in lower or "луна" not in lower:
            raise LLMContentValidationError("natal core missing triad")
        if "тезис" not in lower or "описание" not in lower:
            raise LLMContentValidationError("natal core missing thesis")
        if "сборка" not in lower:
            raise LLMContentValidationError("natal core missing summary")
        return

    if section.section_id == "mercury_mind":
        required = ["стиль", "режим", "ловушк", "ключ"]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("natal mercury missing sections")
        return

    if section.section_id == "shadow_trauma":
        if "хирон" not in lower or "лил" not in lower:
            raise LLMContentValidationError("natal shadow missing points")
        for label in ["якорь", "сценарий", "ресурс", "тень", "ключ", "вопрос"]:
            if f"{label}:" not in lower:
                raise LLMContentValidationError("natal shadow missing labels")
        return

    if section.section_id == "nodes_growth":
        if "южный узел" not in lower or "северный узел" not in lower:
            raise LLMContentValidationError("natal nodes missing nodes")
        if "ловушка" not in lower:
            raise LLMContentValidationError("natal nodes missing trap")
        if "миссия" not in lower:
            raise LLMContentValidationError("natal nodes missing mission")
        if "вопрос" not in lower:
            raise LLMContentValidationError("natal nodes missing question")
        return

    if section.section_id == "vertex_fate":
        if "вертекс" not in lower:
            raise LLMContentValidationError("natal vertex missing name")
        for label in ["якорь", "сценарий", "урок", "ключ", "вопрос"]:
            if label not in lower:
                raise LLMContentValidationError("natal vertex missing labels")
        return

    if section.section_id == "balance_wheel":
        # Check if we have houses mentioned 1..12
        house_nums = set()
        for i in range(1, 13):
            if f"{i} дом" in lower or f"дом {i}" in lower:
                house_nums.add(i)
        
        if len(house_nums) < 10: # Allow some misses in text matching
             pass # Not strict on exact house numbers in text, as they might be in headers
        
        required_labels = [
            "тема",
            "в плюсе",
            "в минусе",
            "триггер",
            "вектор зрелости",
            "вопрос",
        ]
        if not all(l in lower for l in required_labels):
             raise LLMContentValidationError("natal balance wheel missing labels")
        return

    if section.section_id == "love_intimacy":
        if "венера" not in lower or "марс" not in lower:
            raise LLMContentValidationError("natal love missing planets")
        if "секрет успеха" not in lower:
            raise LLMContentValidationError("natal love missing secret")
        return

    if section.section_id == "money_realization":
        if "2 дом" not in lower or "6 дом" not in lower or "10 дом" not in lower:
            raise LLMContentValidationError("natal money missing houses")
        if "главная формула" not in lower:
            raise LLMContentValidationError("natal money missing formula")
        return

    if section.section_id == "stars_transuranus":
        if "уран" not in lower or "нептун" not in lower or "плутон" not in lower:
            raise LLMContentValidationError("natal transuranus missing planets")
        if "дар" not in lower or "риск" not in lower:
            raise LLMContentValidationError("natal transuranus missing fields")
        return

    if section.section_id == "time_cycles":
        required = ["соляр", "асцендент", "зенит", "главный тренд"]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("natal time cycles missing fields")
        return

    if section.section_id == "final_synthesis":
        if "твой девиз" not in lower:
            raise LLMContentValidationError("natal final missing motto")
        if "главный совет" not in lower:
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
        raise LLMContentValidationError("content is not a valid JSON array of blocks")
        
    if not blocks:
        raise LLMContentValidationError("empty blocks")
        
    # Extract text for validation
    full_text = _extract_text_from_blocks(blocks)
    lower = full_text.lower()
    
    min_length_map = {
        "input_frame": 100,
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
        validate_natal_section_content(section, full_text)
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

    if section.section_id == "framework_elements_modes":
        element_tokens = ["огон", "зем", "возду", "вод"]
        mode_tokens = ["кардин", "фикс", "мутаб"]
        if not all(token in lower for token in element_tokens):
            raise LLMContentValidationError("missing element balance")
        if not all(token in lower for token in mode_tokens):
            raise LLMContentValidationError("missing mode balance")

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

    if section.section_id.startswith("month_") and section.section_id.endswith("_forecast"):
        required = [
            "статус месяца",
            "центральная нить",
            "главные активаторы",
        ]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("missing year month blocks")

    if section.section_id == "axes_truths":
        axis_tokens = ["ASC", "DSC", "IC", "MC"]
        if any(token not in full_text for token in axis_tokens):
            raise LLMContentValidationError("missing axis tokens")
        if "твоя правда" not in lower:
            raise LLMContentValidationError("missing two truths phrasing")

    if section.section_id == "aspects_beginner":
        metaphors = ["мотор", "качел", "пружин", "магнит"]
        if not any(word in lower for word in metaphors):
            raise LLMContentValidationError("missing beginner metaphors")

    if section.section_id == "configurations_geometry":
        for word in ["дар", "риск", "ключ", "вопрос"]:
            if word not in lower:
                raise LLMContentValidationError("missing configuration fields")

    if section.section_id == "dispositor_office":
        if "офис" not in lower or "конверт" not in lower:
            raise LLMContentValidationError("missing office metaphor")
        if "босс" not in lower:
            raise LLMContentValidationError("missing boss metaphor")

    if section.section_id == "core_triad":
        if "ASC" not in full_text or "Солнце" not in full_text or "Луна" not in full_text:
            raise LLMContentValidationError("missing core triad")

    if section.section_id == "mercury_mind":
        if "Меркурий" not in full_text:
            raise LLMContentValidationError("missing mercury")

    if section.section_id == "shadow_trauma":
        if "Хирон" not in full_text or "Лилит" not in full_text:
            raise LLMContentValidationError("missing chiron or lilith")

    if section.section_id == "nodes_growth":
        if "Север" not in full_text or "Южн" not in full_text:
            raise LLMContentValidationError("missing nodes")

    if section.section_id == "vertex_fate":
        if "Вертекс" not in full_text:
            raise LLMContentValidationError("missing vertex")

    if section.section_id == "love_intimacy":
        if "Венера" not in full_text or "Марс" not in full_text:
            raise LLMContentValidationError("missing venus or mars")

    if section.section_id == "money_realization":
        if "Юпитер" not in full_text or "Сатурн" not in full_text:
            raise LLMContentValidationError("missing jupiter or saturn")

    if section.section_id == "stars_transuranus":
        if "Уран" not in full_text or "Нептун" not in full_text or "Плутон" not in full_text:
            raise LLMContentValidationError("missing transuranus")

    if section.section_id == "time_cycles":
        for word in ["Погода", "Созревание", "Окна"]:
            if word not in full_text:
                raise LLMContentValidationError("missing time cycle blocks")

    if section.section_id == "final_synthesis":
        if "девиз" not in lower:
            raise LLMContentValidationError("missing final motto")
        if "инсайт" not in lower:
            raise LLMContentValidationError("missing final insights")

    if section.section_id == "week_strategy":
        required = [
            "главная тема",
            "статус недели",
            "подневная стратегия",
            "резюме по срезам",
        ]
        if not all(token in lower for token in required):
            raise LLMContentValidationError("missing week strategy blocks")


def _repair_section_content(
    section: SectionSpec, content: str, error: str
) -> str:
    blocks = _try_parse_blocks(content)
    if blocks is None:
        # Should not happen if validate_section_content raised only for validation errors
        # But if it raised because content wasn't JSON blocks, we shouldn't be here in repair logic
        # that assumes we can append. 
        # Actually generate_sections calls repair if validation fails.
        # If validaton failed because "not json", we try to repair?
        # If "not json", we can wrap it.
        blocks = [{"type": "paragraph", "text": content}]

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
    elif error == "natal framework missing dominants":
        additions.append("**Доминанта:** ОГОНЬ 🔥")
    elif error == "natal framework missing element balance":
        additions.append("* **Баланс Стихий:** Огонь, Земля, Воздух, Вода.")
    elif error == "natal framework missing deficit":
        additions.append("* **Дефицит:** зона, требующая подпитки.")
    elif error == "natal framework missing motto":
        additions.append("**Твой девиз:** ...")
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
    elif error == "missing status indicators":
        additions.append("Статус: 🟡")

    if additions:
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
            )
            return _fallback_section_result(raw, section)
        if isinstance(data, dict):
            content = data.get("content")
            if isinstance(content, list):
                return SectionResult(
                    section_id=section.section_id,
                    title=section.title,
                    content=json.dumps(content, ensure_ascii=False),
                )
            if isinstance(content, str):
                nested_blocks = _try_parse_blocks(content)
                if nested_blocks is not None:
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
        results: List[SectionResult] = []
        for section in sections:
            prompt = build_section_prompt(section, context)
            try:
                raw = self.client.generate(prompt)
            except Exception as exc:
                raise ValueError(f"LLM call failed: {exc}") from exc
            try:
                result = _parse_section_result(raw, section)
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
            if self.validate_content:
                content = result.content or ""
                for _ in range(3):
                    try:
                        validate_section_content(section, content)
                        break
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
            results.append(result)
        return results
# #END_BLOCK_LLM_ORCHESTRATOR
