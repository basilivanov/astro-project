import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_FILE = REPO_ROOT / "frontend/lib/week-brief.ts"
COMPAT_FILE = REPO_ROOT / "frontend/lib/week-brief-compat.ts"


def _run_node_mapping(case: dict) -> dict:
    script = r'''
require('./frontend/node_modules/ts-node').register({
  transpileOnly: true,
  compilerOptions: {
    module: 'CommonJS',
    moduleResolution: 'Node',
  },
});
const path = require('path');
const mod = require(path.join(process.cwd(), 'frontend/lib/week-brief.ts'));
const input = JSON.parse(process.argv[1]);
const result = mod.mapWeekReportToWeekBrief(input);
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

    assert result["headline"] == "Неделя держится на спокойном темпе и точных решениях"
    assert len(result["deepSections"]) == 1
    assert result["deepSections"][0]["slug"] == "focus"
    assert result["deepSections"][0]["title"] == "Focus"
    assert result["sectionsCount"] == 1



def test_frontend_mapping_keeps_canonical_surface_empty_when_week_brief_has_no_deep_sections_even_if_legacy_payload_exists():
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

    assert result["deepSections"] == []
    assert result["reportId"] == "report-42"
    assert result["sectionsCount"] == 0


def test_frontend_mapping_ignores_legacy_deep_sections_strings_and_chunks_for_canonical_surface():
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

    assert result["sectionsCount"] == 0
    assert result["deepSections"] == []


def test_frontend_mapping_keeps_only_brief_sections_without_reconstructing_missing_sections_from_chunks():
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

    assert [section["slug"] for section in result["deepSections"]] == ["focus", "money"]
    assert result["deepSections"][0]["body_markdown"] == "# Focus\nBody"
    assert result["deepSections"][1]["summary"] is None
    assert result["deepSections"][1]["body_markdown"] == ""
    assert result["sectionsCount"] == 2


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


def test_frontend_mapping_keeps_legacy_reconstruction_out_of_canonical_file():
    canonical_source = CANONICAL_FILE.read_text(encoding="utf-8")

    assert "extractReportFallbackText" not in canonical_source
    assert "export function mapLegacyWeekMigrationToSurface" not in canonical_source
    assert "export function hasExplicitWeekMigrationPayload" not in canonical_source


def test_frontend_mapping_moves_legacy_reconstruction_into_compatibility_module():
    compat_source = COMPAT_FILE.read_text(encoding="utf-8")

    assert 'import { extractReportFallbackText } from "../components/blocks/report-renderer";' in compat_source
    assert "export function mapLegacyWeekMigrationToSurface" in compat_source
    assert "export function hasExplicitWeekMigrationPayload" in compat_source
