import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_node_mapping(case: dict) -> dict:
    script = r'''
const fs = require('fs');
const path = require('path');
const Module = require('module');
const ts = require('./frontend/node_modules/typescript');

const filePath = path.join(process.cwd(), 'frontend/lib/week-brief.ts');
const original = fs.readFileSync(filePath, 'utf8');
const source = original.replace(
  'import { extractReportFallbackText } from "../components/blocks/report-renderer";',
  `const extractReportFallbackText = (content) => {
    if (typeof content === "string") {
      try {
        const parsed = JSON.parse(content);
        if (Array.isArray(parsed)) {
          const texts = parsed.flatMap((block) => {
            if (!block || typeof block !== "object") return [];
            if (typeof block.text === "string") return [block.text];
            if (Array.isArray(block.items)) return block.items.filter((item) => typeof item === "string");
            return [];
          }).filter(Boolean);
          return texts.join(" ").trim() || null;
        }
      } catch (error) {}
      return content;
    }
    return content == null ? null : JSON.stringify(content);
  };`
);
const transpiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    esModuleInterop: true,
  },
  fileName: filePath,
});
const mod = new Module(filePath, module);
mod.filename = filePath;
mod.paths = Module._nodeModulePaths(path.dirname(filePath));
mod._compile(transpiled.outputText, filePath);
const input = JSON.parse(process.argv[1]);
const result = mod.exports.mapWeekReportToWeekBrief(input);
process.stdout.write(JSON.stringify(result));
'''
    completed = subprocess.run(
        ["node", "-e", script, json.dumps(case, ensure_ascii=False)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)



def test_frontend_mapping_prefers_week_brief_deep_sections_over_legacy_chunks():
    result = _run_node_mapping(
        {
            "weekBrief": {
                "status": "ready",
                "summary": {"headline": "Week headline", "subhead": "Week subhead", "theme": "Week theme", "week_type": "balance"},
                "deep_sections": [
                    {
                        "id": "brief-1",
                        "slug": "focus",
                        "title": "Focus",
                        "summary": "Brief summary",
                        "body_markdown": "# Focus\nBody",
                        "is_primary": True,
                        "order": 0,
                    }
                ],
            },
            "legacyWeekMap": {"thesis": "Legacy thesis", "theme": "Legacy theme", "deep_sections": ["legacy section"]},
            "chunks": [
                {"id": "chunk-1", "section": "legacy", "title": "Legacy", "content": "legacy body"}
            ],
        }
    )

    assert result["headline"] == "Week headline"
    assert len(result["deepSections"]) == 1
    assert result["deepSections"][0]["slug"] == "focus"
    assert result["deepSections"][0]["title"] == "Focus"
    assert result["sectionsCount"] == 1



def test_frontend_mapping_falls_back_to_legacy_report_chunks_when_week_brief_has_no_deep_sections():
    result = _run_node_mapping(
        {
            "weekBrief": {
                "status": "ready",
                "summary": {"headline": "Week headline", "subhead": "Week subhead", "theme": "Week theme", "week_type": "balance"},
                "deep_sections": [],
            },
            "legacyWeekMap": {
                "thesis": "Legacy thesis",
                "theme": "Legacy theme",
                "day_cards": [],
                "domains": {},
                "actions": [],
                "risks": [],
                "major_factors": [],
                "deep_sections": ["legacy section should not drive read surface directly"],
            },
            "chunks": [
                {
                    "id": "chunk-1",
                    "section": "week_strategy",
                    "title": "Стратегия недели",
                    "content": '[{"type":"paragraph","text":"Legacy chunk summary"}]',
                },
                {
                    "id": "chunk-2",
                    "section": "money",
                    "title": "Работа и деньги",
                    "content": "legacy body",
                },
            ],
            "latestReportId": "report-42",
        }
    )

    assert len(result["deepSections"]) == 2
    assert [section["slug"] for section in result["deepSections"]] == ["week_strategy", "money"]
    assert result["deepSections"][0]["summary"] == "Legacy chunk summary"
    assert result["deepSections"][1]["body_markdown"] == "legacy body"
    assert result["reportId"] == "report-42"
    assert result["sectionsCount"] == 2


def test_frontend_mapping_ignores_legacy_deep_sections_strings_for_read_surface_when_chunks_exist():
    result = _run_node_mapping(
        {
            "weekBrief": {
                "status": "ready",
                "summary": {
                    "headline": "Week headline",
                    "subhead": "Week subhead",
                    "theme": "Week theme",
                    "week_type": "balance",
                },
                "deep_sections": [],
            },
            "legacyWeekMap": {
                "thesis": "Legacy thesis",
                "theme": "Legacy theme",
                "deep_sections": [
                    "legacy strings must stay compatibility-only",
                    "they should not replace the readable sections",
                ],
            },
            "chunks": [
                {
                    "id": "chunk-1",
                    "section": "focus",
                    "title": "Фокус недели",
                    "content": '[{"type":"paragraph","text":"Readable chunk body"}]',
                }
            ],
        }
    )

    assert result["sectionsCount"] == 1
    assert result["deepSections"][0]["slug"] == "focus"
    assert result["deepSections"][0]["summary"] == "Readable chunk body"
    assert "compatibility-only" not in (result["deepSections"][0]["body_markdown"] or "")


def test_frontend_mapping_reconstructs_missing_degraded_sections_from_live_chunks_without_overriding_valid_brief_sections():
    result = _run_node_mapping(
        {
            "weekBrief": {
                "status": "ready",
                "fallback_mode": False,
                "summary": {
                    "headline": "Week headline",
                    "subhead": "Week subhead",
                    "theme": "Week theme",
                    "week_type": "balance",
                },
                "deep_sections": [
                    {
                        "id": "brief-1",
                        "slug": "focus",
                        "title": "Фокус недели",
                        "summary": "Brief summary",
                        "body_markdown": "# Focus\nBody",
                        "is_primary": True,
                        "order": 0,
                    },
                    {
                        "id": "brief-2",
                        "slug": "money",
                        "title": "Работа и деньги",
                        "summary": None,
                        "body_markdown": "",
                        "is_primary": False,
                        "order": 1,
                    },
                ],
            },
            "legacyWeekMap": {
                "thesis": "Legacy thesis",
                "theme": "Legacy theme",
                "deep_sections": ["compat-only legacy string"],
            },
            "chunks": [
                {
                    "id": "chunk-1",
                    "section": "money",
                    "title": "Работа и деньги",
                    "content": '[{"type":"paragraph","text":"Recovered money chunk"}]',
                },
                {
                    "id": "chunk-2",
                    "section": "relationships",
                    "title": "Отношения",
                    "content": "Recovered relationship chunk",
                },
            ],
            "latestReportId": "report-live-7",
        }
    )

    assert [section["slug"] for section in result["deepSections"]] == ["focus", "money", "relationships"]
    assert result["deepSections"][0]["body_markdown"] == "# Focus\nBody"
    assert result["deepSections"][1]["summary"] == "Recovered money chunk"
    assert result["deepSections"][1]["body_markdown"] == '[{"type":"paragraph","text":"Recovered money chunk"}]'
    assert result["deepSections"][2]["summary"] == "Recovered relationship chunk"
    assert result["deepSections"][2]["is_primary"] is False
    assert result["sectionsCount"] == 3


def test_frontend_mapping_humanizes_explainability_context_without_losing_telemetry_fields():
    result = _run_node_mapping(
        {
            "weekBrief": {
                "status": "ready",
                "summary": {
                    "headline": "Week headline",
                    "subhead": "Week subhead",
                    "theme": "Week theme",
                    "week_type": "balance",
                },
                "major_factors": [
                    {"id": "factor-1", "label": "Фон недели", "impact": "high", "explanation_human": "Собирайте всё в коротких циклах."}
                ],
                "explainability": {
                    "confidence": 0.81,
                    "birth_time_used": True,
                    "factor_count": 3,
                    "top_signal_source": "transit_natal",
                },
            },
            "latestReportId": "report-77",
        }
    )

    assert result["explainability"]["confidence"] == 0.81
    assert result["explainability"]["birth_time_used"] is True
    assert result["confidenceLabel"] == "Высокая опора на текущие данные"
    assert result["confidenceShortLabel"] == "высокая"
    assert result["birthTimeLabel"] == "учтено точное время рождения"
    assert result["topSignalLabel"] == "личная натальная опора и текущие транзиты"
