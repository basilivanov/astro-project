import argparse

import prefect_grace.cli as cli


EXPECTED_COMMANDS = {
    "bootstrap-backlog",
    "check-scope",
    "dashboard",
    "feature",
    "list-executors",
    "mark-feature",
    "packet",
    "packet-status",
    "print-brief-template",
    "queue",
    "registry-apply-smoke",
    "registry-dump",
    "review",
    "run-codex",
    "run-e2e-packet",
    "run-e2e-packet-flow",
    "run-e2e-registry-seeded-smoke",
    "run-handoff",
    "run-managed-packet",
    "run-nightly",
    "run-prefect-e2e-batch-smoke",
    "run-prefect-e2e-live-smoke",
    "run-prefect-e2e-real-dry-run-smoke",
    "run-prefect-real-dry-run-seeded-smoke",
    "run-verifier",
    "run-worktree-scope-flow",
    "scan-packets",
    "select-executor",
    "submit-brief",
    "submit-feature",
    "submit-packets",
    "sync-packets",
    "synthetic-edge-matrix",
    "test-feature",
    "validate-evidence-contract",
    "validate-evidence-manifest",
    "validate-packet",
    "validate-project",
    "worktree-cleanup",
    "worktree-create",
    "worktree-scope-check",
    "worktree-status",
    "write-evidence",
    "write-review",
    "write-rework",
}

EXPECTED_FACADE_EXPORTS = {
    "_cmd_bootstrap_backlog",
    "_cmd_check_scope",
    "_cmd_dashboard",
    "_cmd_feature",
    "_cmd_list_executors",
    "_cmd_mark_feature",
    "_cmd_packet",
    "_cmd_packet_status",
    "_cmd_print_brief_template",
    "_cmd_queue",
    "_cmd_registry_apply_smoke",
    "_cmd_registry_dump",
    "_cmd_review",
    "_cmd_run_codex",
    "_cmd_run_e2e_packet",
    "_cmd_run_e2e_packet_flow",
    "_cmd_run_e2e_registry_seeded_smoke",
    "_cmd_run_handoff",
    "_cmd_run_managed_packet",
    "_cmd_run_nightly",
    "_cmd_run_prefect_e2e_batch_smoke",
    "_cmd_run_prefect_e2e_live_smoke",
    "_cmd_run_prefect_e2e_real_dry_run_smoke",
    "_cmd_run_prefect_real_dry_run_seeded_smoke",
    "_cmd_run_verifier",
    "_cmd_run_worktree_scope_flow",
    "_cmd_scan_packets",
    "_cmd_select_executor",
    "_cmd_submit_brief",
    "_cmd_submit_feature",
    "_cmd_submit_packets",
    "_cmd_sync_packets",
    "_cmd_synthetic_edge_matrix",
    "_cmd_test_feature",
    "_cmd_validate_evidence_contract",
    "_cmd_validate_evidence_manifest",
    "_cmd_validate_packet",
    "_cmd_validate_project",
    "_cmd_worktree_cleanup",
    "_cmd_worktree_create",
    "_cmd_worktree_scope_check",
    "_cmd_worktree_status",
    "_cmd_write_evidence",
    "_cmd_write_review",
    "_cmd_write_rework",
    "_json_envelope",
    "_load_adapter_from_args",
    "_packet_to_dict",
    "_print_json",
    "_profile_config_path",
    "_scan_project_packets",
    "_scheduled_for_from_args",
    "build_parser",
    "main",
}


def _subparsers(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    return next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))


def _command_parser(name: str) -> argparse.ArgumentParser:
    return _subparsers(cli.build_parser()).choices[name]


def _option_strings(command: str) -> set[str]:
    return {
        option
        for action in _command_parser(command)._actions
        for option in action.option_strings
    }


def test_parser_inventory_matches_pre_split_commands() -> None:
    assert set(_subparsers(cli.build_parser()).choices) == EXPECTED_COMMANDS


def test_cli_facade_preserves_pre_split_exports() -> None:
    missing = sorted(name for name in EXPECTED_FACADE_EXPORTS if not hasattr(cli, name))
    assert missing == []


def test_submit_packets_safety_flags_are_unchanged() -> None:
    parser = cli.build_parser()
    assert parser.parse_args(["submit-packets"]).execute is False
    assert parser.parse_args(["submit-packets", "--dry-run"]).execute is False
    assert parser.parse_args(["submit-packets", "--execute"]).execute is True

    options = _option_strings("submit-packets")
    assert {"--project", "--project-config", "--runner", "--execute", "--dry-run"} <= options
    assert {"--base-ref", "--timeout-seconds", "--continue-on-error", "--json"} <= options


def test_live_smoke_safety_flags_are_unchanged() -> None:
    live_options = _option_strings("run-prefect-e2e-live-smoke")
    assert {"--dry-run", "--no-dry-run", "--execute-agent", "--allow-live-agent-smoke"} <= live_options
    assert {"--state-root", "--worktree-root", "--packet-root", "--json"} <= live_options

    batch_options = _option_strings("run-prefect-e2e-batch-smoke")
    assert {"--execute-agent", "--offline-fake-submitter", "--batch-size", "--json"} <= batch_options
    assert "--allow-live-agent-smoke" not in batch_options


def test_legacy_queue_dashboard_commands_remain_registered() -> None:
    assert "--limit" in _option_strings("queue")
    assert "--json" in _option_strings("dashboard")
