import ast
import importlib
from pathlib import Path

from prefect_grace.tasks import state_store
import prefect_grace.flows.feature_pipeline as feature_pipeline
from prefect_grace.flows.pipeline_helpers import (
    evidence_collector,
    normalizers,
    rework_routing,
    status_formatter,
    wave_progression,
)


FEATURE_PIPELINE_PATH = Path("prefect_grace/flows/feature_pipeline.py")
HELPER_DIR = Path("prefect_grace/flows/pipeline_helpers")
TASK_DIR = Path("prefect_grace/flows/pipeline_tasks")

EXPECTED_DECORATED = {
    "bootstrap_task": {"decorator": "task", "task_run_name": "bootstrap:{feature_id}"},
    "seed_feature_packets_task": {"decorator": "task", "task_run_name": "seed-packets:{feature_id}"},
    "resolve_planner_contract_task": {"decorator": "task", "task_run_name": "packet-graph:resolve"},
    "resolve_architect_artifact_plan_task": {"decorator": "task", "task_run_name": "architect-artifacts:resolve:{feature_id}"},
    "write_architect_artifacts_task": {"decorator": "task", "task_run_name": "architect-artifacts:write:{feature_id}"},
    "materialize_planner_contract_task": {"decorator": "task", "task_run_name": "packet-graph:materialize:{feature_id}"},
    "validate_planner_contract_task": {"decorator": "task", "task_run_name": "packet-graph:validate:{feature_id}"},
    "mark_feature_in_progress_task": {"decorator": "task", "task_run_name": "feature-status:{feature_id}:in-progress"},
    "run_packet_task": {"decorator": "task", "task_run_name": "packet:{packet_id}"},
    "run_verifier_packet_task": {"decorator": "task", "task_run_name": "verifier:{packet_id}"},
    "mark_packet_status_task": {"decorator": "task", "task_run_name": "packet-status:{packet_id}:{status}"},
    "record_canon_digest_task": {"decorator": "task", "task_run_name": "canon-digest:record:{feature_id}"},
    "route_reviewer_verdict_task": {"decorator": "task", "task_run_name": "review-route:{coder_packet_id}"},
    "route_architect_wave_verdict_task": {"decorator": "task", "task_run_name": "wave-route:{feature_id}:{wave_id}"},
    "resolve_verifier_result_task": {"decorator": "task", "task_run_name": "verifier-result:resolve"},
    "record_verifier_result_task": {"decorator": "task", "task_run_name": "record-verifier:{verifier_packet_id}"},
    "publish_packet_review_artifacts_task": {"decorator": "task", "task_run_name": "packet-review-artifacts:{review_route[review][packet_id]}"},
    "publish_feature_artifacts_task": {"decorator": "task", "task_run_name": "feature-artifacts:{feature[feature_id]}"},
    "resolve_reviewer_decision_task": {"decorator": "task", "task_run_name": "review-decision:resolve"},
    "resolve_wave_decision_task": {"decorator": "task", "task_run_name": "wave-decision:resolve"},
    "feature_pipeline": {
        "decorator": "flow",
        "name": "prefect-grace-feature-pipeline",
        "flow_run_name": "feature:{feature_id}",
    },
    "review_task": {"decorator": "task", "task_run_name": "review-record:{packet_id}:{verdict}"},
    "review_router_flow": {
        "decorator": "flow",
        "name": "prefect-grace-review-router",
        "flow_run_name": "review:{packet_id}:{verdict}",
    },
}

STATE_MUTATING_HELPERS = {
    "_final_failure",
    "_post_acceptance_final_status",
    "_persist_wave_progression",
    "_set_wave_progression_status",
    "_build_direct_rework_followup_packets",
    "_build_architect_direct_rework",
    "_build_light_resume_followup",
}

FORBIDDEN_HELPER_TOKENS = (
    "update_record",
    "mark_feature_status",
    "create_packet",
    "sync_packet_file",
    "write_text",
    "record_review",
    "record_wave_review",
    "record_verification",
    "publish_feature_artifacts",
    "publish_packet_task_artifacts",
    "notify_feature_event",
    "notify_packet_event",
    "launch_codex_for_packet",
)


def _decorator_name(decorator: ast.expr) -> str:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return ""


def _decorator_string_kw(decorator: ast.expr, key: str) -> str | None:
    if not isinstance(decorator, ast.Call):
        return None
    for keyword in decorator.keywords:
        if keyword.arg == key and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    return None


def _decorated_inventory(path: Path) -> dict[str, dict[str, str | None]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    inventory: dict[str, dict[str, str | None]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.decorator_list:
            continue
        decorator = node.decorator_list[0]
        inventory[node.name] = {
            "decorator": _decorator_name(decorator),
            "name": _decorator_string_kw(decorator, "name"),
            "task_run_name": _decorator_string_kw(decorator, "task_run_name"),
            "flow_run_name": _decorator_string_kw(decorator, "flow_run_name"),
        }
    return inventory


def test_feature_pipeline_decorated_inventory_preserved_in_facade() -> None:
    inventory: dict[str, dict[str, str | None]] = {}
    for path in [FEATURE_PIPELINE_PATH, *sorted(TASK_DIR.glob("*.py"))]:
        inventory.update(_decorated_inventory(path))

    assert set(inventory) == set(EXPECTED_DECORATED)
    for name, expected in EXPECTED_DECORATED.items():
        for key, value in expected.items():
            assert inventory[name][key] == value
        assert hasattr(feature_pipeline, name)


def test_feature_pipeline_facade_keeps_only_flow_decorators() -> None:
    inventory = _decorated_inventory(FEATURE_PIPELINE_PATH)
    assert set(inventory) == {"feature_pipeline", "review_router_flow"}
    assert inventory["feature_pipeline"]["flow_run_name"] == "feature:{feature_id}"
    assert inventory["review_router_flow"]["flow_run_name"] == "review:{packet_id}:{verdict}"


def test_pipeline_helper_modules_do_not_define_prefect_tasks_or_flows() -> None:
    for path in sorted(HELPER_DIR.glob("*.py")):
        inventory = _decorated_inventory(path)
        assert inventory == {}


def test_feature_pipeline_compatibility_aliases_resolve_to_moved_helpers() -> None:
    assert feature_pipeline._final_user_summary is status_formatter.final_user_summary
    assert feature_pipeline._normalize_observability_scope is normalizers.normalize_observability_scope
    assert feature_pipeline._collect_candidate_commit_files is evidence_collector.collect_candidate_commit_files
    assert feature_pipeline._enrich_verifier_evidence_paths is evidence_collector.enrich_verifier_evidence_paths
    assert feature_pipeline._plan_wave_sequence is wave_progression.plan_wave_sequence
    assert feature_pipeline._build_wave_progression is wave_progression.build_wave_progression
    assert feature_pipeline._normalize_reviewer_decision_for_pipeline is rework_routing.normalize_reviewer_decision_for_pipeline
    assert feature_pipeline._classify_rework_route is rework_routing.classify_rework_route


def test_state_mutating_helpers_remain_in_feature_pipeline() -> None:
    for name in STATE_MUTATING_HELPERS:
        helper = getattr(feature_pipeline, name)
        assert helper.__module__ == "prefect_grace.flows.feature_pipeline"


def test_moved_helper_modules_do_not_import_state_mutating_operations() -> None:
    for path in sorted(HELPER_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_HELPER_TOKENS:
            assert token not in source


def test_importing_helper_modules_has_no_state_file_side_effects(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    for module in [evidence_collector, normalizers, rework_routing, status_formatter, wave_progression]:
        importlib.reload(module)
    assert not state_store.STATE_DIR.exists()
