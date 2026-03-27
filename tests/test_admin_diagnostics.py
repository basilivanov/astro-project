import importlib
import sys
import types
from dataclasses import dataclass

import pytest


class CaptureLogger:
    def __init__(self):
        self.events = []

    def info(self, event, **kwargs):
        self.events.append({"level": "info", "event": event, **kwargs})

    def error(self, event, **kwargs):
        self.events.append({"level": "error", "event": event, **kwargs})


@pytest.fixture
def diagnostics_module(monkeypatch):
    fake_stellium = types.ModuleType("stellium_engine")
    fake_orchestrator_module = types.ModuleType("backend.app.llm.orchestrator")

    @dataclass
    class FakeGeneratedSection:
        section_id: str
        title: str
        content: str

    @dataclass
    class FakeSectionSpec:
        section_id: str
        title: str
        prompt: str

    class FakeStubLLMClient:
        pass

    class FakeStelliumEngine:
        def create_natal_chart(self, name, dt, location):
            if name == "Partner":
                assert dt == "1995-05-20 12:00"
                assert location == "Moscow"
                return type("PartnerChart", (), {"positions": [5, 6]})()
            assert name == "Diagnostic"
            assert dt == "1990-01-15 12:00"
            assert location == "Sochi, Russia"
            return type("NatalChart", (), {"positions": [1, 2, 3, 4]})()

        def create_transit_chart(self, dt, location):
            assert dt == "2026-06-15 12:00"
            assert location == "Sochi, Russia"
            return object()

        def find_transit_aspects(self, natal, transit, orb):
            assert orb == 1.5
            return [{"aspect": "trine"}, {"aspect": "sextile"}]

        def calculate_forecast_month_data(self, natal, dt, location):
            assert dt == "2026-03-01 12:00"
            assert location == "Sochi, Russia"
            return {"ingresses": ["mars", "venus"]}

        def calculate_synastry_data(self, natal, partner):
            return {"score": 87}

    class FakeLLMOrchestrator:
        def __init__(self, client, validate_content=False):
            self.client = client
            self.validate_content = validate_content

        def generate_sections(self, sections, context):
            assert len(sections) == 1
            assert sections[0].section_id == "core"
            assert sections[0].title == "Core Profile"
            assert context == {"client_id": "diagnostic"}
            return [
                FakeGeneratedSection(
                    section_id="core",
                    title="Core Profile",
                    content="Stubbed core content.",
                )
            ]

    fake_stellium.StelliumEngine = FakeStelliumEngine
    fake_orchestrator_module.LLMOrchestrator = FakeLLMOrchestrator
    fake_orchestrator_module.SectionSpec = FakeSectionSpec
    fake_orchestrator_module.StubLLMClient = FakeStubLLMClient

    monkeypatch.setitem(sys.modules, "stellium_engine", fake_stellium)
    monkeypatch.setitem(sys.modules, "backend.app.llm.orchestrator", fake_orchestrator_module)
    sys.modules.pop("backend.app.diagnostics", None)
    module = importlib.import_module("backend.app.diagnostics")

    @dataclass
    class FakeReportSection:
        section_id: str
        title: str
        content: str

    def fake_assemble_markdown(title, sections):
        assert title == "Diagnostic Report"
        assert len(sections) == 1
        assert isinstance(sections[0], FakeReportSection)
        return f"# {title}\n\n## {sections[0].title}\n\n{sections[0].content}"

    monkeypatch.setattr(module, "ReportSection", FakeReportSection, raising=False)
    monkeypatch.setattr(module, "assemble_markdown", fake_assemble_markdown, raising=False)
    return module


def test_run_diagnostics_returns_ok_steps_and_log_evidence(diagnostics_module, monkeypatch):
    logger = CaptureLogger()
    monkeypatch.setattr(diagnostics_module, "logger", logger)

    result = diagnostics_module.run_diagnostics()

    assert result == {
        "status": "ok",
        "steps": [
            {"name": "natal", "ok": True},
            {"name": "transit", "ok": True},
            {"name": "month_data", "ok": True},
            {"name": "synastry", "ok": True},
            {"name": "llm", "ok": True},
            {"name": "report", "ok": True},
        ],
    }

    event_names = [event["event"] for event in logger.events]
    assert event_names == [
        "diagnostic.natal",
        "diagnostic.transit",
        "diagnostic.month",
        "diagnostic.synastry",
        "diagnostic.llm",
        "diagnostic.report",
    ]
    assert all(event["level"] == "info" for event in logger.events)

    assert logger.events[0]["block_id"] == "DIAG_NATAL"
    assert logger.events[0]["client_id"] == "diagnostic"
    assert logger.events[0]["report_id"] == "diagnostic"
    assert logger.events[0]["positions"] == 4
    assert logger.events[1]["aspects"] == 2
    assert logger.events[2]["ingresses"] == 2
    assert logger.events[3]["score"] == 87
    assert logger.events[4]["sections"] == 1
    assert logger.events[5]["length"] > 0


@pytest.mark.parametrize(
    ("failing_method", "expected_event", "expected_block", "expected_steps"),
    [
        ("create_natal_chart", "diagnostic.natal.error", "DIAG_NATAL", []),
        ("find_transit_aspects", "diagnostic.engine.error", "DIAG_ENGINE", [{"name": "natal", "ok": True}]),
        ("generate_sections", "diagnostic.llm.error", "DIAG_LLM", [
            {"name": "natal", "ok": True},
            {"name": "transit", "ok": True},
            {"name": "month_data", "ok": True},
            {"name": "synastry", "ok": True},
        ]),
        ("assemble_markdown", "diagnostic.report.error", "DIAG_REPORT", [
            {"name": "natal", "ok": True},
            {"name": "transit", "ok": True},
            {"name": "month_data", "ok": True},
            {"name": "synastry", "ok": True},
            {"name": "llm", "ok": True},
        ]),
    ],
)
def test_run_diagnostics_logs_failure_telemetry(diagnostics_module, monkeypatch, failing_method, expected_event, expected_block, expected_steps):
    logger = CaptureLogger()
    monkeypatch.setattr(diagnostics_module, "logger", logger)

    if failing_method == "generate_sections":
        original = diagnostics_module.LLMOrchestrator

        class FailingLLMOrchestrator(original):
            def generate_sections(self, sections, context):
                raise RuntimeError("llm boom")

        monkeypatch.setattr(diagnostics_module, "LLMOrchestrator", FailingLLMOrchestrator)
    elif failing_method == "assemble_markdown":
        def raise_report(*_args, **_kwargs):
            raise RuntimeError("report boom")

        monkeypatch.setattr(diagnostics_module, "assemble_markdown", raise_report, raising=False)
    else:
        original_engine = diagnostics_module.StelliumEngine

        class FailingEngine(original_engine):
            def create_natal_chart(self, *args, **kwargs):
                if failing_method == "create_natal_chart":
                    raise RuntimeError("natal boom")
                return super().create_natal_chart(*args, **kwargs)

            def find_transit_aspects(self, *args, **kwargs):
                if failing_method == "find_transit_aspects":
                    raise RuntimeError("engine boom")
                return super().find_transit_aspects(*args, **kwargs)

        monkeypatch.setattr(diagnostics_module, "StelliumEngine", FailingEngine)

    result = diagnostics_module.run_diagnostics()

    assert result == {"status": "failed", "steps": expected_steps}
    assert logger.events[-1]["level"] == "error"
    assert logger.events[-1]["event"] == expected_event
    assert logger.events[-1]["block_id"] == expected_block
    assert "error" in logger.events[-1]
