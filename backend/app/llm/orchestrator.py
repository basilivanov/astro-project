# ############################################################################
# AI_HEADER: MODULE_LLM_ORCHESTRATOR
# ROLE: Sectioned LLM generation with JSON validation.
# DEPENDENCIES: pydantic.
# GRACE_ANCHORS: [LLM_SCHEMAS, LLM_CLIENT, LLM_PROMPTS, LLM_ORCHESTRATOR]
# ############################################################################

import json
import os
import re
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
        return (
            '{"section_id":"stub","title":"Stub Section","content":"Stub content"}'
        )


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
            model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

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
    base = (
        "Return ONLY valid JSON with keys: section_id, title, content.\n"
        "No code fences. No extra keys.\n"
        f"section_id: {section.section_id}\n"
        f"title: {section.title}\n"
        f"prompt: {section.prompt}\n"
        f"context: {context_json}\n"
        "JSON example:\n"
        '{"section_id":"id","title":"Title","content":"Markdown content"}\n'
    )
    if section.section_id in NATAL_SECTION_IDS:
        return (
            base
            + "The content value must follow the section prompt and match "
            "the structure of Svetlana_Natal_Report.md. Use Markdown headings, "
            "lists, and tables only as requested in the prompt.\n"
        )
    return (
        base
        + "The content value must be well-structured Markdown with an intro, "
        "subheadings, a bullet list, and a recommendations block. "
        "Emojis are allowed in subheadings. Use tables when data-heavy.\n"
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


def _fallback_section_result(raw: str, section: SectionSpec) -> SectionResult:
    text = _strip_code_fences(raw.strip())
    match = re.search(r'"content"\s*:\s*"(.*)', text, flags=re.DOTALL)
    if match:
        content = match.group(1)
        content = content.rsplit('"', 1)[0].strip()
    else:
        content = text.strip()

    if not content:
        content = "LLM output was empty."

    snippet = text[:200].replace("\n", " ").strip()
    logger.warning(
        "llm.invalid_json.fallback",
        block_id="LLM_PARSE",
        section_id=section.section_id,
        snippet=snippet,
    )
    return SectionResult(
        section_id=section.section_id,
        title=section.title,
        content=content,
    )

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
        if "положение планет" not in lower or "| планета |" not in lower:
            raise LLMContentValidationError("natal input missing planet table")
        if "угловые точки" not in lower or "asc" not in lower:
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
        if len(re.findall(r"^####\s+\**\d+\.", text, flags=re.MULTILINE)) < 3:
            raise LLMContentValidationError("natal aspects missing count")
        for label in ["якорь", "сценарий", "ресурс", "тень", "ключ", "вопрос"]:
            if f"{label}:" not in lower:
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
        house_matches = list(
            re.finditer(
                r"#{3,4}\s+\**(\d+)\s+дом\b",
                text,
                flags=re.IGNORECASE,
            )
        )
        house_nums = {
            int(match.group(1))
            for match in house_matches
            if match.group(1).isdigit()
        }
        if house_nums != set(range(1, 13)):
            raise LLMContentValidationError("natal balance wheel missing houses")
        required_labels = [
            "тема:",
            "в плюсе:",
            "в минусе:",
            "триггер:",
            "вектор зрелости:",
            "вопрос:",
        ]
        for idx, match in enumerate(house_matches):
            start = match.end()
            end = house_matches[idx + 1].start() if idx + 1 < len(house_matches) else len(text)
            segment = text[start:end].lower()
            for label in required_labels:
                if label not in segment:
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
    # INPUT: section spec and markdown content.
    # OUTPUT: None (raises on invalid structure).
    # CONTEXT: Used to trigger retries/fallbacks for weak LLM output.
    """

    text = (content or "").strip()
    min_length_map = {
        "input_frame": 320,
        "synthesis": 300,
        "framework_elements_modes": 360,
        "axes_truths": 420,
        "aspects_beginner": 420,
        "configurations_geometry": 380,
        "dispositor_office": 420,
        "core_triad": 360,
        "mercury_mind": 340,
        "shadow_trauma": 340,
        "nodes_growth": 340,
        "vertex_fate": 320,
        "balance_wheel": 1100,
        "love_intimacy": 340,
        "money_realization": 360,
        "stars_transuranus": 340,
        "time_cycles": 340,
        "final_synthesis": 300,
    }
    min_length = min_length_map.get(
        section.section_id, 140 if section.section_id in NATAL_SECTION_IDS else 80
    )
    if len(text) < min_length:
        raise LLMContentValidationError("content too short")

    if section.section_id in NATAL_SECTION_IDS:
        validate_natal_section_content(section, text)
        return

    lines = text.splitlines()
    has_blockquote = any(re.match(r"^\s*>", line) for line in lines)
    has_heading = any(re.match(r"^\s*#{3,}\s+", line) for line in lines)
    has_about_block = any(
        re.search(r"###\s+.*о\s+ч[её]м\s+этот\s+блок", line, re.I)
        for line in lines
    )
    has_card_heading = any(
        re.search(r"###\s+.*краткая\s+карта\s+блока", line, re.I)
        for line in lines
    )
    has_table = False
    for idx, line in enumerate(lines[:-1]):
        if "|" in line and re.search(r"\|?\s*-{3,}", lines[idx + 1]):
            has_table = True
            break
    about_index = None
    for idx, line in enumerate(lines):
        if re.search(r"###\s+.*о\s+ч[её]м\s+этот\s+блок", line, re.I):
            about_index = idx
            break
    has_about_text = False
    if about_index is not None:
        for line in lines[about_index + 1 :]:
            if not line.strip():
                continue
            if line.strip().startswith("#"):
                break
            has_about_text = True
            break
    has_recommendations = any(
        re.search(r"^###\s+.*рекомендации", line, re.I) for line in lines
    )
    bullet_count = sum(
        1 for line in lines if re.match(r"^\s*[-*]\s+", line)
    )

    if bullet_count < 2:
        raise LLMContentValidationError("not enough bullet items")
    if section.section_id not in {"month_theme"}:
        if not has_recommendations:
            raise LLMContentValidationError("missing recommendations block")
    if bullet_count < 2:
        raise LLMContentValidationError("not enough bullet items")

    if section.section_id == "synthesis":
        bullets = [line for line in lines if re.match(r"^\s*[-*]\s+", line)]
        if len(bullets) < 10:
            raise LLMContentValidationError("synthesis needs 10 bullet lines")
        required = {
            "Метафора": 1,
            "Тезис": 1,
            "Ресурс": 3,
            "Узел": 3,
            "Ключ": 2,
        }
        for key, count in required.items():
            found = sum(1 for line in bullets if key in line)
            if found < count:
                raise LLMContentValidationError("synthesis missing labels")

    if section.section_id == "input_frame":
        if not (re.search(r"\bИмя\b", text) or re.search(r"\bКлиент\b", text)):
            raise LLMContentValidationError("input frame missing name")
        if "Дата" not in text:
            raise LLMContentValidationError("input frame missing date")
        if "Место" not in text:
            raise LLMContentValidationError("input frame missing place")
        if not any(word in text.lower() for word in ["натал", "аспект", "дом"]):
            raise LLMContentValidationError("input frame missing scope list")
        if "| Параметр |" not in text or "| Содержание |" not in text:
            raise LLMContentValidationError("input frame missing summary table header")

    if section.section_id == "framework_elements_modes":
        lower = text.lower()
        element_tokens = ["огон", "зем", "возду", "вод"]
        mode_tokens = ["кардин", "фикс", "мутаб"]
        if not all(token in lower for token in element_tokens):
            raise LLMContentValidationError("missing element balance")
        if not all(token in lower for token in mode_tokens):
            raise LLMContentValidationError("missing mode balance")

    if section.section_id == "month_theme":
        lower = text.lower()
        required_blocks = [
            "заголовок и метаданные",
            "статус месяца",
            "центральная нить смысла",
            "главные активаторы",
            "карта сфер",
            "событийный слой",
            "личный слой",
            "глубинный слой",
            "солярный контекст",
            "тайм-лорды",
            "фиксирован",
            "трансураны",
            "итог месяца",
        ]
        if not all(token in lower for token in required_blocks):
            raise LLMContentValidationError("missing month forecast blocks")
        if not any(indicator in text for indicator in ["🟢", "🟡", "🔴"]):
            raise LLMContentValidationError("missing status indicators")
        if "→" not in text:
            raise LLMContentValidationError("missing activator format")

    if section.section_id == "axes_truths":
        axis_tokens = ["ASC", "DSC", "IC", "MC"]
        if any(token not in text for token in axis_tokens):
            raise LLMContentValidationError("missing axis tokens")

        lower = text.lower()

        def has_axis_pair(
            first: str,
            second: str,
            roman_first: str,
            roman_second: str,
        ) -> bool:
            if re.search(rf"{first}\s*[-–]\s*{second}", text):
                return True
            if re.search(
                rf"{roman_first}\s*[-–]\s*{roman_second}",
                text,
                flags=re.IGNORECASE,
            ):
                return True
            if re.search(rf"{first}\s*(?:-?й|-?я|-?е)?\s*дом", lower) and re.search(
                rf"{second}\s*(?:-?й|-?я|-?е)?\s*дом",
                lower,
            ):
                return True
            return False

        if not has_axis_pair("2", "8", "II", "VIII"):
            raise LLMContentValidationError("missing 2-8 axis")
        if not has_axis_pair("5", "11", "V", "XI"):
            raise LLMContentValidationError("missing 5-11 axis")
        if "твоя правда" not in lower:
            raise LLMContentValidationError("missing two truths phrasing")
        if not any(
            phrase in lower
            for phrase in ("правда партнера", "правда партнёра", "правда мира")
        ):
            raise LLMContentValidationError("missing two truths phrasing")

    if section.section_id == "aspects_beginner":
        metaphors = ["мотор", "качел", "пружин", "магнит"]
        if not any(word in text.lower() for word in metaphors):
            raise LLMContentValidationError("missing beginner metaphors")

    if section.section_id == "configurations_geometry":
        for word in ["дар", "риск", "ключ", "вопрос"]:
            if word not in text.lower():
                raise LLMContentValidationError("missing configuration fields")

    if section.section_id == "dispositor_office":
        if "офис" not in text.lower() or "конверт" not in text.lower():
            raise LLMContentValidationError("missing office metaphor")
        if "босс" not in text.lower():
            raise LLMContentValidationError("missing boss metaphor")

    if section.section_id == "core_triad":
        if "ASC" not in text or "Солнце" not in text or "Луна" not in text:
            raise LLMContentValidationError("missing core triad")

    if section.section_id == "mercury_mind":
        if "Меркурий" not in text:
            raise LLMContentValidationError("missing mercury")

    if section.section_id == "shadow_trauma":
        if "Хирон" not in text or "Лилит" not in text:
            raise LLMContentValidationError("missing chiron or lilith")

    if section.section_id == "nodes_growth":
        if "Север" not in text or "Южн" not in text:
            raise LLMContentValidationError("missing nodes")

    if section.section_id == "vertex_fate":
        if "Вертекс" not in text:
            raise LLMContentValidationError("missing vertex")

    if section.section_id == "balance_wheel":
        house_heads = re.findall(r"^###\s+Дом\s+(\d+)", text, flags=re.MULTILINE)
        unique_houses = {int(item) for item in house_heads if item.isdigit()}
        if unique_houses != set(range(1, 13)):
            raise LLMContentValidationError("balance wheel must include 12 houses")
        segments = re.split(r"^###\s+Дом\s+\d+.*$", text, flags=re.MULTILINE)
        required_labels = [
            "Тема",
            "В плюсе",
            "В минусе",
            "Триггер",
            "Вектор зрелости",
            "Вопрос",
        ]
        if len(segments) < 13:
            raise LLMContentValidationError("balance wheel segments missing")
        for segment in segments[1:13]:
            for label in required_labels:
                if not re.search(rf"{label}\s*:", segment):
                    raise LLMContentValidationError("balance wheel label missing")

    if section.section_id == "love_intimacy":
        if "Венера" not in text or "Марс" not in text:
            raise LLMContentValidationError("missing venus or mars")

    if section.section_id == "money_realization":
        if not re.search(r"\b2\s*дом\b", text) or not re.search(
            r"\b6\s*дом\b", text
        ) or not re.search(r"\b10\s*дом\b", text):
            raise LLMContentValidationError("missing 2/6/10 houses")
        if "Юпитер" not in text or "Сатурн" not in text:
            raise LLMContentValidationError("missing jupiter or saturn")

    if section.section_id == "stars_transuranus":
        if "Уран" not in text or "Нептун" not in text or "Плутон" not in text:
            raise LLMContentValidationError("missing transuranus")

    if section.section_id == "time_cycles":
        for word in ["Погода", "Созревание", "Окна"]:
            if word not in text:
                raise LLMContentValidationError("missing time cycle blocks")

    if section.section_id == "final_synthesis":
        if "девиз" not in text.lower():
            raise LLMContentValidationError("missing final motto")
        if "инсайт" not in text.lower():
            raise LLMContentValidationError("missing final insights")
        if "ритуал" not in text.lower():
            raise LLMContentValidationError("missing final ritual")


def _repair_section_content(
    section: SectionSpec, content: str, error: str
) -> str:
    text = (content or "").strip()
    additions: List[str] = []

    if error == "natal input missing client":
        additions.append("**Кверент:** Имя клиента")
    elif error == "natal input missing birth date":
        additions.append("**Дата рождения:** указать дату и время")
    elif error == "natal input missing birth place":
        additions.append("**Место рождения:** указать место")
    elif error == "natal input missing house system":
        additions.append("**Система домов:** указать систему")
    elif error == "natal input missing planet table":
        additions.append(
            "### 🪐 Положение Планет (Фундамент)\n"
            "| Планета | Знак Зодиака | Градус | Статус (Сила) |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **Солнце** | | | |\n"
            "| **Луна** | | | |\n"
            "| **Меркурий** | | | |"
        )
    elif error == "natal input missing angles table":
        additions.append(
            "### 🏠 Угловые точки и Узлы\n"
            "| Точка | Знак | Градус |\n"
            "| :--- | :--- | :--- |\n"
            "| **ASC (Асцендент)** | | |\n"
            "| **MC (Зенит)** | | |\n"
            "| **Вертекс** | | |"
        )
    elif error == "natal synthesis missing metaphor":
        additions.append(
            '> **Метафора:** "Ключевой образ".\n'
            "Короткое раскрытие метафоры."
        )
    elif error == "natal synthesis missing thesis":
        additions.append("**Главный тезис:** краткая формулировка.")
    elif error == "natal framework missing dominants":
        additions.append("**Доминанта: ОГОНЬ 🔥 и КАРДИНАЛЬНОСТЬ 🚀**")
    elif error == "natal framework missing element balance":
        additions.append(
            "* **Баланс Стихий:** Огонь, Земля, Воздух, Вода."
        )
    elif error == "natal framework missing deficit":
        additions.append("* **Дефицит:** зона, требующая подпитки.")
    elif error == "natal framework missing motto":
        additions.append("**Твой девиз по Каркасу:** *Короткий девиз*.")
    elif error == "natal axes missing tokens":
        additions.append("⬆️ ASC — ⬇️ DSC, 🏠 IC — 🏔️ MC")
    elif error == "natal axes missing 2-8":
        additions.append("2-8")
    elif error == "natal axes missing 3-9":
        additions.append("3-9")
    elif error == "natal axes missing truths":
        additions.append(
            "Твоя правда: ...\nПравда партнера: ...\nЗадача: ..."
        )
    elif error == "natal aspects missing count":
        additions.append(
            "#### 1. 🌙 Луна — «Опора»\n"
            "Якорь: ...\n"
            "Сценарий: ...\n"
            "Ресурс: ...\n"
            "Тень: ...\n"
            "Ключ: ...\n"
            "Вопрос: ...\n\n"
            "#### 2. ☿ Меркурий — «Спор»\n"
            "Якорь: ...\n"
            "Сценарий: ...\n"
            "Ресурс: ...\n"
            "Тень: ...\n"
            "Ключ: ...\n"
            "Вопрос: ...\n\n"
            "#### 3. ☀️ Солнце — «Импульс»\n"
            "Якорь: ...\n"
            "Сценарий: ...\n"
            "Ресурс: ...\n"
            "Тень: ...\n"
            "Ключ: ...\n"
            "Вопрос: ..."
        )
    elif error == "natal aspects missing labels":
        additions.append(
            "Якорь: ...\nСценарий: ...\nРесурс: ...\n"
            "Тень: ...\nКлюч: ...\nВопрос: ..."
        )
    elif error == "natal config missing heading":
        additions.append("#### **Конфигурация: ...**")
    elif error == "natal config missing fields":
        additions.append(
            "* **Геометрия:** ...\n"
            "* **Дар:** ...\n"
            "* **Риск:** ...\n"
            "* **Ключ:** ...\n"
            "* **Вопрос:** ..."
        )
    elif error == "natal dispositor missing office":
        additions.append("Офисная метафора с отделами и сотрудниками.")
    elif error == "natal dispositor missing envelope":
        additions.append("Образ «передачи конвертов» между отделами.")
    elif error == "natal dispositor missing boss":
        additions.append("**ГЛАВНЫЙ БОСС:** ключевой диспозитор.")
    elif error == "natal core missing triad":
        additions.append("ASC, Солнце, Луна")
    elif error == "natal core missing thesis":
        additions.append("**Тезис:** ...\n**Описание:** ...")
    elif error == "natal core missing summary":
        additions.append("#### ⚖️ Сборка Ядра (Главный конфликт)\n**Решение:** ...")
    elif error == "natal mercury missing sections":
        additions.append(
            "#### **Стиль мышления:** ...\n"
            "#### **Режим «Гения»:** ...\n"
            "#### **Ментальные ловушки:**\n"
            "1. ...\n"
            "#### **Ключ к эффективному мышлению:** ..."
        )
    elif error == "natal shadow missing points":
        additions.append("⚷ Хирон и 🌑 Лилит")
    elif error == "natal shadow missing labels":
        additions.append(
            "Якорь: ...\nСценарий: ...\nРесурс: ...\n"
            "Тень: ...\nКлюч: ...\nВопрос: ..."
        )
    elif error == "natal nodes missing nodes":
        additions.append("Южный узел и Северный узел")
    elif error == "natal nodes missing trap":
        additions.append("Ловушка: ...")
    elif error == "natal nodes missing mission":
        additions.append("Миссия: ...")
    elif error == "natal nodes missing question":
        additions.append("Вопрос: ...")
    elif error == "natal vertex missing name":
        additions.append("Вертекс")
    elif error == "natal vertex missing labels":
        additions.append(
            "Якорь: ...\nСценарий встреч: ...\nУрок судьбы: ...\n"
            "Ключ: ...\nВопрос: ..."
        )
    elif error == "natal balance wheel missing houses":
        house_blocks = []
        for house in range(1, 13):
            house_blocks.append(
                f"#### **{house} ДОМ — ...**\n"
                "Тема: ...\n"
                "В плюсе: ...\n"
                "В минусе: ...\n"
                "Триггер: ...\n"
                "Вектор зрелости: ...\n"
                "Вопрос: ..."
            )
        additions.append("\n".join(house_blocks))
    elif error == "natal balance wheel missing labels":
        additions.append(
            "Тема: ...\nВ плюсе: ...\nВ минусе: ...\n"
            "Триггер: ...\nВектор зрелости: ...\nВопрос: ..."
        )
    elif error == "natal love missing planets":
        additions.append("### ♀️ ВЕНЕРА ...\n### ♂️ МАРС ...")
    elif error == "natal love missing secret":
        additions.append("🔑 **Секрет успеха:** ...")
    elif error == "natal money missing houses":
        additions.append("💰 2 ДОМ ... 6 ДОМ ... 10 ДОМ ...")
    elif error == "natal money missing formula":
        additions.append("🔑 **Главная формула:** ...")
    elif error == "natal transuranus missing planets":
        additions.append("⚡️ Уран ... 🌊 Нептун ... 🌋 Плутон ...")
    elif error == "natal transuranus missing fields":
        additions.append("Дар: ... Риск: ...")
    elif error == "natal time cycles missing fields":
        additions.append(
            "* **Главный тренд года:** ...\n"
            "* **Солярный Асцендент:** ...\n"
            "* **Наложение на Натал:** ...\n"
            "* **Зенит года (MC):** ..."
        )
    elif error == "natal final missing motto":
        additions.append("**Твой девиз:** *...*")
    elif error == "natal final missing advice":
        additions.append("**Главный совет:** ...")
    elif error == "missing blockquote":
        additions.append("> Короткая метафора или тезис.")
    elif error == "missing subheading":
        additions.append("### ✨ Детали\nКороткое пояснение по теме блока.")
    elif error == "missing block intro heading":
        additions.append("### 🧭 О чем этот блок\nКороткое пояснение смысла блока.")
    elif error == "missing block intro text":
        additions.append("Этот блок объясняет ключевые смыслы и фокус раздела.")
    elif error == "missing card heading":
        additions.append(
            "### 📊 Краткая карта блока\n"
            "| Параметр | Содержание |\n"
            "| --- | --- |\n"
            "| Фокус | Основная тема блока |\n"
            "| Ритм | Ключевая динамика |\n"
            "| Итог | Направление внимания |"
        )
    elif error == "missing table":
        additions.append(
            "| Параметр | Содержание |\n"
            "| --- | --- |\n"
            "| Фокус | Основная тема блока |\n"
            "| Ресурс | Точка роста |\n"
            "| Риск | Узел напряжения |"
        )
    elif error == "not enough bullet items":
        additions.append(
            "- Ключевой фокус блока.\n"
            "- Потенциал и ресурс для роста.\n"
            "- Риск и зона внимания."
        )
    elif error == "missing recommendations block":
        additions.append(
            "### 💡 Рекомендации\n"
            "- Сфокусируйся на главном ресурсе.\n"
            "- Разгрузи зону напряжения через практику."
        )
    elif error == "missing depth formula":
        additions.append(
            "Формула: Якорь — Перевод — Сценарий — Ресурс — Тень — Ключ — Вопрос\n"
            "Якорь: Базовая точка.\n"
            "Перевод: Смысловой перенос.\n"
            "Сценарий: Как проявляется.\n"
            "Ресурс: Что дает.\n"
            "Тень: Где искажается.\n"
            "Ключ: Что включает рост.\n"
            "Вопрос: Контрольная проверка."
        )
    elif error == "missing beginner metaphors":
        additions.append("Метафоры: мотор, качели, пружина, магнит.")
    elif error == "missing configuration fields":
        additions.append(
            "Дар: Основная сила конфигурации.\n"
            "Риск: Точка перегиба.\n"
            "Ключ: Условие раскрытия.\n"
            "Вопрос: Что проверить на практике."
        )
    elif error == "missing element balance":
        additions.append("Стихии: Огонь, Земля, Воздух, Вода.")
    elif error == "missing mode balance":
        additions.append(
            "Модальности: Кардинальность, Фиксированность, Мутабельность."
        )
    elif error in {
        "synthesis needs 10 bullet lines",
        "synthesis missing labels",
    }:
        additions.append(
            "- Метафора: ключевой образ.\n"
            "- Тезис: суть блока.\n"
            "- Ресурс 1: главный ресурс.\n"
            "- Ресурс 2: поддержка.\n"
            "- Ресурс 3: резерв.\n"
            "- Узел 1: зона напряжения.\n"
            "- Узел 2: повторяющийся паттерн.\n"
            "- Узел 3: точка роста.\n"
            "- Ключ 1: поворотный элемент.\n"
            "- Ключ 2: главный фокус."
        )
    elif error == "input frame missing name":
        additions.append("Имя клиента: указать имя.")
    elif error == "input frame missing date":
        additions.append("Дата рождения: указать дату.")
    elif error == "input frame missing place":
        additions.append("Место рождения: указать место.")
    elif error == "input frame missing scope list":
        additions.append(
            "Считаем: натал, аспекты, дома, узлы, диспозиторы, конфигурации."
        )
    elif error == "input frame missing summary table header":
        additions.append(
            "### 📊 Краткая карта блока\n"
            "| Параметр | Содержание |\n"
            "| --- | --- |\n"
            "| Имя | ... |\n"
            "| Дата | ... |\n"
            "| Место | ... |"
        )
    elif error in {
        "missing axis tokens",
        "missing 2-8 axis",
        "missing 5-11 axis",
        "missing two truths phrasing",
    }:
        additions.append(
            "### 🧭 Оси и две правды\n"
            "**⬆️ ASC–⬇️ DSC**\n"
            "Твоя правда: ...\n"
            "Правда партнера/мира: ...\n"
            "**🏠 IC–🏔️ MC**\n"
            "Твоя правда: ...\n"
            "Правда партнера/мира: ...\n"
            "**2-8**\n"
            "Твоя правда: ...\n"
            "Правда партнера/мира: ...\n"
            "**5-11**\n"
            "Твоя правда: ...\n"
            "Правда партнера/мира: ..."
        )
    elif error in {
        "balance wheel must include 12 houses",
        "balance wheel segments missing",
        "balance wheel label missing",
    }:
        house_blocks = []
        for house in range(1, 13):
            house_blocks.append(
                f"### Дом {house}\n"
                "Тема: ...\n"
                "В плюсе: ...\n"
                "В минусе: ...\n"
                "Триггер: ...\n"
                "Вектор зрелости: ...\n"
                "Вопрос: ..."
            )
        additions.append("\n".join(house_blocks))
    elif error == "missing venus or mars":
        additions.append("Фокус: ♀️ Венера и ♂️ Марс.")
    elif error == "missing 2/6/10 houses":
        additions.append("Важные дома: 2 дом, 6 дом, 10 дом.")
    elif error == "missing jupiter or saturn":
        additions.append("Фокус: ♃ Юпитер и ♄ Сатурн.")
    elif error == "missing transuranus":
        additions.append("Трансураны: ♅ Уран, ♆ Нептун, ♇ Плутон.")
    elif error == "missing time cycle blocks":
        additions.append(
            "### Погода\nКороткая характеристика периода.\n"
            "### Созревание\nЧто доходит до результата.\n"
            "### Окна\nГде открываются возможности."
        )
    elif error == "missing final motto":
        additions.append("Девиз: главный смысл периода.")
    elif error == "missing final insights":
        additions.append("Инсайт: ключевое открытие.")
    elif error == "missing final ritual":
        additions.append("Ритуал: короткая практика закрепления.")

    if not additions:
        return text

    suffix = "\n\n".join(additions).strip()
    if not text:
        return suffix
    return f"{text}\n\n{suffix}"


def _parse_section_result(raw: str, section: SectionSpec) -> SectionResult:
    candidate = _strip_code_fences(raw.strip())
    try:
        return SectionResult.model_validate_json(candidate)
    except ValidationError:
        candidate = _extract_json_text(candidate)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            snippet = raw[:400].replace("\n", " ").strip()
            logger.warning(
                "llm.invalid_json",
                block_id="LLM_PARSE",
                section_id=section.section_id,
                snippet=snippet,
            )
            return _fallback_section_result(raw, section)
        try:
            return SectionResult.model_validate(data)
        except ValidationError as exc:
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
