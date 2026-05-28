# ############################################################################
# AI_HEADER: git_mutation
# ROLE: CLI command handlers for guarded Git mutation planning and apply.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Expose the Git mutation gate through the split GRACE CLI.
# inputs: argparse Namespace.
# returns: None.
# side_effects: Prints JSON/text; may apply Git mutations only through platform gate flags.
# emitted_logs: None.
# error_behavior: Exits 0 for success, 1 for blocked gate, 2 for command errors.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - function: _cmd_git_mutation_gate
# END_MODULE_MAP

from __future__ import annotations

import argparse
import sys

from prefect_grace.cli_commands.common import _json_envelope, _print_json


def _cmd_git_mutation_gate(args: argparse.Namespace) -> None:
    command = "git-mutation-gate"
    try:
        from prefect_grace.platform.git_mutation_gate import run_git_mutation_gate

        result = run_git_mutation_gate(
            packet=args.packet,
            repo_root=args.repo_root,
            worktree_root=args.worktree_root,
            worktree_path=args.worktree_path,
            project_key=args.project_key,
            packet_id=args.packet_id,
            attempt=int(args.attempt),
            base_ref=args.base_ref,
            target_branch=args.target_branch,
            remote=args.remote,
            dry_run=bool(args.dry_run) or not bool(args.apply),
            apply=bool(args.apply),
            commit=bool(args.commit),
            push=bool(args.push),
            merge=bool(args.merge),
            understand_merge=bool(args.i_understand_merge),
        )
        payload = result.to_dict()
        if args.json:
            _print_json(_json_envelope(
                ok=result.ok,
                command=command,
                result=payload,
                errors=result.blockers,
            ))
        else:
            print(f"Git mutation gate: {result.status}")
            print(f"  Packet: {result.packet_id}")
            print(f"  Commit: {result.mutations.get('commit')}")
            print(f"  Push: {result.mutations.get('push')}")
            print(f"  Merge: {result.mutations.get('merge')}")
            if result.blocker_reason:
                print(f"  Blocker: {result.blocker_reason}")
        sys.exit(0 if result.ok else 1)
    except Exception as exc:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "GIT_MUTATION_GATE_COMMAND_FAILED", "message": str(exc)}],
            ))
        else:
            print(f"Git mutation gate failed: {exc}", file=sys.stderr)
        sys.exit(2)
