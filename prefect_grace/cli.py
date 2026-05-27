# ############################################################################
# AI_HEADER: cli
# ROLE: Main facade and entrypoint for the GRACE CLI platform commands.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Expose a unified facade command line interface to run GRACE platform actions.
# inputs: CLI arguments.
# returns: None.
# side_effects: Executes selected subcommands, writes state, prints results, exits process.
# emitted_logs: None.
# error_behavior: Exits with non-zero code on parser errors or command execution failures.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
# END_MODULE_MAP

from __future__ import annotations

import sys

# Re-exporting models and all command functions for backward compatibility
from prefect_grace.models import (
    FeatureStatus,
    FrontendVisualVerdict,
    ObservabilityVerdict,
    ReasoningProfile,
    ReviewVerdict,
    TestVerdict,
    WaveVerdict,
)

# Common helpers
from prefect_grace.cli_commands.common import (
    _json_envelope,
    _print_json,
    _profile_config_path,
    _load_adapter_from_args,
    _packet_to_dict,
    _scan_project_packets,
    _scheduled_for_from_args,
)

# Command groups
from prefect_grace.cli_commands.legacy_feature import (
    _cmd_feature,
    _cmd_mark_feature,
    _cmd_packet,
    _cmd_run_codex,
    _cmd_run_verifier,
    _cmd_test_feature,
    _cmd_submit_feature,
    _cmd_submit_brief,
    _cmd_print_brief_template,
    _cmd_queue,
    _cmd_dashboard,
)
from prefect_grace.cli_commands.project_registry import (
    _cmd_validate_project,
    _cmd_scan_packets,
    _cmd_validate_packet,
    _cmd_sync_packets,
    _cmd_bootstrap_backlog,
    _cmd_packet_status,
    _cmd_registry_dump,
)
from prefect_grace.cli_commands.packet_submission import (
    _cmd_submit_packets,
)
from prefect_grace.cli_commands.prefect_smokes import (
    _cmd_registry_apply_smoke,
    _cmd_run_e2e_registry_seeded_smoke,
    _cmd_run_prefect_e2e_live_smoke,
    _cmd_run_prefect_e2e_batch_smoke,
    _cmd_run_prefect_e2e_real_dry_run_smoke,
    _cmd_run_nightly,
)
from prefect_grace.cli_commands.worktrees import (
    _cmd_worktree_create,
    _cmd_worktree_status,
    _cmd_worktree_cleanup,
    _cmd_worktree_scope_check,
    _cmd_run_worktree_scope_flow,
)
from prefect_grace.cli_commands.packet_execution import (
    _cmd_run_managed_packet,
    _cmd_run_e2e_packet,
    _cmd_run_e2e_packet_flow,
    _cmd_run_handoff,
)
from prefect_grace.cli_commands.evidence import (
    _cmd_review,
    _cmd_write_review,
    _cmd_write_evidence,
    _cmd_write_rework,
    _cmd_check_scope,
    _cmd_validate_evidence_contract,
    _cmd_validate_evidence_manifest,
)
from prefect_grace.cli_commands.executors import (
    _cmd_list_executors,
    _cmd_select_executor,
    _cmd_synthetic_edge_matrix,
)

# Parser constructor
from prefect_grace.cli_commands.parser import build_parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
