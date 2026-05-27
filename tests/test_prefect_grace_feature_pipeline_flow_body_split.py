import ast
from pathlib import Path

import prefect_grace.flows.feature_pipeline as feature_pipeline
from scripts.check_size_limits import check_root


FEATURE_PIPELINE_PATH = Path("prefect_grace/flows/feature_pipeline.py")
PHASE_DIR = Path("prefect_grace/flows/pipeline_phases")


def _decorator_name(decorator: ast.expr) -> str:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return ""


def _decorated_inventory(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name: _decorator_name(node.decorator_list[0])
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.decorator_list
    }


def test_feature_pipeline_facade_body_is_bounded() -> None:
    source = FEATURE_PIPELINE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    feature = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "feature_pipeline")

    assert FEATURE_PIPELINE_PATH.read_text(encoding="utf-8").count("\n") < 1000
    assert feature.end_lineno - feature.lineno + 1 < 140
    assert "run_bootstrap_phase(runtime, deps)" in source
    assert "run_planning_phase(runtime, deps, state)" in source
    assert "run_wave_execution_phase(runtime, deps, state)" in source
    assert "run_finalization_phase(runtime, deps, state)" in source


def test_pipeline_phases_define_no_prefect_decorators_or_facade_imports() -> None:
    for path in sorted(PHASE_DIR.glob("*.py")):
        assert _decorated_inventory(path) == {}
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "prefect_grace.flows.feature_pipeline"
            if isinstance(node, ast.Import):
                assert all(alias.name != "prefect_grace.flows.feature_pipeline" for alias in node.names)


def test_feature_pipeline_builds_phase_dependencies_from_facade_globals(monkeypatch) -> None:
    def fake_mark_packet_status_task(*args, **kwargs):
        return {"args": args, "kwargs": kwargs}

    def fake_publish_feature_artifacts(*args, **kwargs):
        return ["patched"]

    monkeypatch.setattr(feature_pipeline, "mark_packet_status_task", fake_mark_packet_status_task)
    monkeypatch.setattr(feature_pipeline, "publish_feature_artifacts_task", fake_publish_feature_artifacts)

    deps = feature_pipeline._build_pipeline_deps()
    assert deps.mark_packet_status_task is fake_mark_packet_status_task
    assert deps.publish_feature_artifacts_task is fake_publish_feature_artifacts


def test_flow_size_check_passes_for_feature_pipeline_package() -> None:
    violations = check_root(Path("prefect_grace/flows"))
    assert [violation.message for violation in violations if not violation.allowed] == []
