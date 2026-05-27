# ############################################################################
# AI_HEADER: prefect_smokes
# ROLE: Execution of synthetic, dry-run, and batch Prefect smokes.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Run pipeline smokes, real dry-runs, batch smokes, and nightly verification.
# inputs: CLI argparse Namespace.
# returns: None.
# side_effects: Submits smoke runs, reads/writes project/state data, prints status.
# emitted_logs: None.
# error_behavior: Exits with appropriate status code (0/1/2) depending on smoke result.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
# END_MODULE_MAP

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from prefect_grace.cli_commands.common import (
    _json_envelope,
    _print_json,
    _load_adapter_from_args,
)


def _cmd_registry_apply_smoke(args: argparse.Namespace) -> None:
    command = "registry-apply-smoke"
    try:
        from prefect_grace.platform.registry_apply_smoke import run_registry_apply_smoke

        result = run_registry_apply_smoke(
            project_config=Path(args.project),
            state_root=Path(args.state_root),
            packet_root=Path(args.packet_root) if args.packet_root else None,
        )
        payload = result.to_dict()

        if args.json:
            _print_json(_json_envelope(
                ok=result.ok,
                command=command,
                project_key=result.project_key,
                result=payload,
                warnings=result.warnings,
                errors=result.errors,
            ))
        else:
            print(f"Registry apply smoke for {result.project_key}: {'OK' if result.ok else 'FAILED'}")
            print(f"  State root: {result.state_root}")
            print(f"  Bootstrap apply count: {result.bootstrap_apply_count}")
            print(f"  Cases: {sum(1 for case in result.cases if case.ok)}/{len(result.cases)}")
            print(f"  Prefect runs created: {result.prefect_runs_created}")

        if not result.ok:
            sys.exit(1)
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "REGISTRY_APPLY_SMOKE_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Registry apply smoke failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_run_e2e_registry_seeded_smoke(args: argparse.Namespace) -> None:
    command = "run-e2e-registry-seeded-smoke"
    try:
        from prefect_grace.platform.e2e_runner_registry_seeded_smoke import (
            run_e2e_runner_registry_seeded_smoke,
        )

        result = run_e2e_runner_registry_seeded_smoke(
            project_config=Path(args.project),
            state_root=Path(args.state_root),
            worktree_root=Path(args.worktree_root),
            packet_root=Path(args.packet_root),
        )
        payload = result.to_dict()

        if args.json:
            _print_json(_json_envelope(
                ok=result.ok,
                command=command,
                project_key=result.project_key,
                result=payload,
                warnings=result.warnings,
                errors=result.errors,
            ))
        else:
            print(f"E2E registry-seeded smoke for {result.project_key}: {'OK' if result.ok else 'FAILED'}")
            print(f"  State root: {result.state_root}")
            print(f"  Worktree root: {result.worktree_root}")
            print(f"  Packet root: {result.packet_root}")
            print(f"  Selected packet: {result.selected_packet_id or '-'}")
            print(f"  Bootstrap apply count: {result.bootstrap_apply_count}")
            print(f"  Prefect runs created: {result.prefect_runs_created}")
            print(f"  Live agents started: {result.live_agents_started}")

        if not result.ok:
            sys.exit(1)
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "E2E_REGISTRY_SEEDED_SMOKE_FAILED", "message": str(e)}],
            ))
        else:
            print(f"E2E registry-seeded smoke failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_run_prefect_e2e_live_smoke(args: argparse.Namespace) -> None:
    command = "run-prefect-e2e-live-smoke"
    try:
        from prefect_grace.platform.prefect_e2e_live_smoke import run_prefect_e2e_live_smoke

        _submitter = None
        if getattr(args, "offline_fake_submitter", False):
            def _submitter(**kwargs):
                packet_id = str(kwargs["parameters"].get("packet_id") or "unknown")
                return {
                    "flow_run_id": f"fake-live-smoke-{packet_id}",
                    "flow_run_name": f"e2e-packet:{packet_id}:attempt-1",
                    "deployment_name": "prefect-grace-e2e-packet-runner/live-e2e-packet-runner",
                    "work_queue_name": "grace-live",
                    "runner_kind": "e2e",
                    "status": "submitted",
                    "url": "http://prefect.local/flow-runs/fake-live-smoke",
                }

        result = run_prefect_e2e_live_smoke(
            project_config=Path(args.project_config),
            state_root=Path(args.state_root),
            worktree_root=Path(args.worktree_root),
            packet_root=Path(args.packet_root),
            dry_run=bool(args.dry_run),
            execute_agent=bool(args.execute_agent),
            allow_live_agent_smoke=bool(args.allow_live_agent_smoke),
            limit=int(getattr(args, "limit", 1)),
            submitter=_submitter,
        )

        if args.json:
            _print_json(_json_envelope(
                ok=result.ok,
                command=command,
                project_key=None,
                result=result.to_dict(),
                errors=result.errors,
            ))
        else:
            print(f"Prefect E2E live smoke: {result.status}")
            print(f"  Packet: {result.packet_id}")
            print(f"  Deployment: {result.deployment_name}")
            print(f"  Runner: {result.runner_kind}")
            print(f"  Submitted: {result.submitted}")
            if result.flow_run_id:
                print(f"  Flow run: {result.flow_run_id}")
        sys.exit(0 if result.ok else 1)
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "SMOKE_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Prefect E2E live smoke failed: {e}", file=sys.stderr)
        sys.exit(2)


def _cmd_run_prefect_e2e_batch_smoke(args: argparse.Namespace) -> None:
    command = "run-prefect-e2e-batch-smoke"
    try:
        from prefect_grace.platform.prefect_e2e_batch_smoke import (
            PrefectE2EBatchSmokeResult,
            run_prefect_e2e_batch_smoke,
        )
        from prefect_grace.tasks.prefect_submitter import E2E_PACKET_DEPLOYMENT_NAME

        batch_size = int(args.batch_size)
        if bool(getattr(args, "execute_agent", False)):
            result = PrefectE2EBatchSmokeResult(
                ok=False,
                mode="prefect_agent_dry_run",
                batch_size=batch_size,
                runner_kind="e2e",
                deployment_name=E2E_PACKET_DEPLOYMENT_NAME,
                work_queue_name=None,
                packets_planned=[],
                packets_submitted=[],
                records=[],
                errors=[{
                    "code": "BATCH_LIVE_AGENT_UNSUPPORTED",
                    "message": "Batch live-agent smoke is out of scope; omit --execute-agent.",
                }],
            )
        else:
            _submitter = None
            if getattr(args, "offline_fake_submitter", False):
                def _submitter(**kwargs):
                    packet_id = str(kwargs["parameters"].get("packet_id") or "unknown")
                    return {
                        "flow_run_id": f"fake-batch-smoke-{packet_id}",
                        "flow_run_name": f"e2e-packet:{packet_id}:attempt-1",
                        "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
                        "work_queue_name": "grace-live",
                        "runner_kind": "e2e",
                        "status": "submitted",
                        "url": f"http://prefect.local/flow-runs/fake-batch-smoke-{packet_id}",
                    }

            result = run_prefect_e2e_batch_smoke(
                project_config=Path(args.project_config),
                state_root=Path(args.state_root),
                worktree_root=Path(args.worktree_root),
                packet_root=Path(args.packet_root),
                batch_size=batch_size,
                submitter=_submitter,
            )

        if args.json:
            _print_json(_json_envelope(
                ok=result.ok,
                command=command,
                project_key=None,
                result=result.to_dict(),
                errors=result.errors,
            ))
        else:
            print("Prefect E2E batch smoke:")
            print(f"  Batch size: {result.batch_size}")
            print(f"  Submitted: {len(result.packets_submitted)}")
            print(f"  Deployment: {result.deployment_name}")
            print(f"  Queue: {result.work_queue_name or '-'}")
            for record in result.records:
                print(f"  Packet: {record.get('packet_id')} -> {record.get('flow_run_id')}")
            for error in result.errors:
                print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(0 if result.ok else 1)
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "BATCH_SMOKE_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Prefect E2E batch smoke failed: {e}", file=sys.stderr)
        sys.exit(2)


def _cmd_run_prefect_e2e_real_dry_run_smoke(args: argparse.Namespace) -> None:
    command = "run-prefect-e2e-real-dry-run-smoke"
    try:
        from prefect_grace.platform.prefect_e2e_real_dry_run_smoke import (
            PrefectE2ERealDryRunSmokeResult,
            run_prefect_e2e_real_dry_run_smoke,
        )
        from prefect_grace.tasks.prefect_submitter import E2E_PACKET_DEPLOYMENT_NAME

        if bool(getattr(args, "execute_agent", False)):
            result = PrefectE2ERealDryRunSmokeResult(
                ok=False,
                mode="prefect_real_e2e_agent_dry_run",
                packet_id="FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP-W01-REAL-E2E-DRY-RUN-SMOKE",
                runner_kind="e2e",
                deployment_name=E2E_PACKET_DEPLOYMENT_NAME,
                work_queue_name=None,
                flow_run_id=None,
                flow_run_name=None,
                flow_run_url=None,
                submitted=False,
                waited=False,
                prefect_state_type=None,
                prefect_state_name=None,
                domain_status=None,
                artifact_ids=[],
                errors=[{
                    "code": "REAL_DRY_RUN_EXECUTE_AGENT_REJECTED",
                    "message": "Real E2E dry-run smoke forbids live agent execution.",
                }],
            )
        else:
            result = run_prefect_e2e_real_dry_run_smoke(
                project_config=Path(args.project_config),
                state_root=Path(args.state_root),
                worktree_root=Path(args.worktree_root),
                packet_root=Path(args.packet_root),
                timeout_seconds=int(args.timeout_seconds),
                poll_interval_seconds=int(args.poll_interval_seconds),
                wait=not bool(args.no_wait),
                execute_agent=False,
            )

        if args.json:
            _print_json(_json_envelope(
                ok=result.ok,
                command=command,
                project_key=None,
                result=result.to_dict(),
                errors=result.errors,
            ))
        else:
            print("Prefect real E2E dry-run smoke:")
            print(f"  Submitted: {result.submitted}")
            print(f"  Packet: {result.packet_id}")
            print(f"  Deployment: {result.deployment_name}")
            print(f"  Queue: {result.work_queue_name or '-'}")
            print(f"  Flow run: {result.flow_run_id or '-'}")
            print(f"  URL: {result.flow_run_url or '-'}")
            print(f"  Waited: {result.waited}")
            print(f"  Prefect state: {result.prefect_state_name or '-'} ({result.prefect_state_type or '-'})")
            print(f"  Domain status: {result.domain_status or '-'}")
            for error in result.errors:
                print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(0 if result.ok else 1)
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "REAL_DRY_RUN_SMOKE_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Prefect real E2E dry-run smoke failed: {e}", file=sys.stderr)
        sys.exit(2)


def _cmd_run_nightly(args: argparse.Namespace) -> None:
    command = "run-nightly"
    try:
        adapter = _load_adapter_from_args(args)
        result = {
            "until_blocked": args.until_blocked,
            "submitted": [],
            "note": "Nightly execution is declared but not enabled in this contract-only MVP.",
        }
        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                project_key=adapter.project_key,
                result=result,
                warnings=["NIGHTLY_EXECUTION_NOT_ENABLED"],
            ))
        else:
            print(result["note"])
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "NIGHTLY_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Nightly failed: {e}", file=sys.stderr)
        sys.exit(1)
