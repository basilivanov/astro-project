from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from prefect_grace.models import (
    FeatureStatus,
    FrontendVisualVerdict,
    ObservabilityVerdict,
    ReasoningProfile,
    ReviewVerdict,
    TestVerdict,
    WaveVerdict,
)
from prefect_grace.tasks.feature_bootstrap import bootstrap_feature, create_packet, mark_feature_status
from prefect_grace.tasks.review_router import create_rework_from_review, record_review
from prefect_grace.tasks.codex_launcher import launch_codex_for_packet
from prefect_grace.tasks.grace_dashboard import build_grace_dashboard_snapshot, render_grace_dashboard
from prefect_grace.tasks.business_intake import TEMPLATE_PATH as BUSINESS_BRIEF_TEMPLATE_PATH, submit_feature_run_from_brief
from prefect_grace.tasks.prefect_runs import list_recent_feature_flow_runs
from prefect_grace.tasks.prefect_submitter import feature_flow_parameters, submit_feature_flow_run
from prefect_grace.platform.project_adapter import load_project_adapter
from prefect_grace.platform.verification_profile import load_verification_profiles
from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.state_store import PacketRegistryStore, RunStore, ExecutorHistoryStore
from pathlib import Path
import sys


def _json_envelope(
    *,
    ok: bool,
    command: str,
    project_key: str | None = None,
    result: dict | list | str | None = None,
    warnings: list | None = None,
    errors: list | None = None,
) -> dict:
    payload = result if result is not None else {}
    return {
        "ok": ok,
        "project_key": project_key,
        "command": command,
        "result": payload,
        "data": payload,
        "warnings": warnings or [],
        "errors": errors or [],
    }


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _profile_config_path(project_path: str | None) -> Path | None:
    if not project_path:
        return None
    path = Path(project_path)
    if path.is_file():
        project_root = path.parent.parent if path.name == "project.yaml" else path.parent
    else:
        project_root = path
    grace_path = project_root / "grace" / "policies" / "verification.yaml"
    if grace_path.exists():
        return grace_path
    legacy_path = project_root / "prefect_grace" / "policies" / "verification.yaml"
    if legacy_path.exists():
        return legacy_path
    return None


def _load_adapter_from_args(args: argparse.Namespace):
    return load_project_adapter(getattr(args, "project", None))


def _packet_to_dict(parsed, *, path: Path | None = None, repo_root: Path | None = None) -> dict:
    data = {
        "packet_id": parsed.packet_id,
        "feature_id": parsed.feature_id,
        "wave_id": parsed.wave_id,
        "title": parsed.title,
        "objective": parsed.objective,
        "status": parsed.status,
        "phase": parsed.phase,
        "depends_on": parsed.depends_on,
        "modules": parsed.modules,
        "allowed_write_scope": parsed.allowed_write_scope,
        "frozen_scope": parsed.frozen_scope,
        "must_preserve": parsed.must_preserve,
        "verification": parsed.verification,
        "expected_evidence": parsed.expected_evidence,
        "escalation_triggers": parsed.escalation_triggers,
        "source_hash": parsed.source_hash,
        "section_lines": parsed.section_lines,
        "legacy_warnings": parsed.legacy_warnings,
    }
    if path is not None:
        try:
            data["path"] = str(path.relative_to(repo_root or Path.cwd()))
        except ValueError:
            data["path"] = str(path)
    return data


def _scan_project_packets(adapter, *, mode: str) -> tuple[list[dict], list[str], list[dict]]:
    packets_dir = Path(adapter.repo_root) / adapter.packets_dir
    if not packets_dir.exists():
        raise FileNotFoundError(f"Packets directory not found at {packets_dir}")

    packets_data: list[dict] = []
    all_warnings: list[str] = []
    errors: list[dict] = []

    for path in sorted(packets_dir.glob("**/*.md")):
        try:
            parsed = parse_packet_markdown(path, mode=mode)
            packet_data = _packet_to_dict(parsed, path=path, repo_root=Path(adapter.repo_root))
            packet_data["status"] = packet_data["status"] or "ready"
            packets_data.append(packet_data)
            all_warnings.extend(parsed.legacy_warnings)
        except Exception as e:
            errors.append({"code": "PACKET_INVALID", "message": f"Packet {path}: {e}"})
            if mode == "strict":
                break
    return packets_data, all_warnings, errors


def _cmd_feature(args: argparse.Namespace) -> None:
    record = bootstrap_feature(args.feature_id, args.title, args.summary)
    print(record["feature_dir"])


def _cmd_mark_feature(args: argparse.Namespace) -> None:
    record = mark_feature_status(args.feature_id, FeatureStatus(args.status))
    print(record)


def _cmd_packet(args: argparse.Namespace) -> None:
    record = create_packet(
        feature_id=args.feature_id,
        wave_id=args.wave_id,
        title=args.title,
        role=args.role,
        reasoning=ReasoningProfile(args.reasoning),
        summary=args.summary,
    )
    print(record["packet_path"])


def _cmd_run_codex(args: argparse.Namespace) -> None:
    result = launch_codex_for_packet(
        args.packet_id,
        dry_run=args.dry_run,
        timeout_seconds=args.timeout_seconds,
    )
    print(result)


def _cmd_run_verifier(args: argparse.Namespace) -> None:
    result = launch_codex_for_packet(
        args.packet_id,
        dry_run=args.dry_run,
        timeout_seconds=args.timeout_seconds,
    )
    print(result)


def _cmd_review(args: argparse.Namespace) -> None:
    reasons = args.reason or []
    record = record_review(
        packet_id=args.packet_id,
        verdict=ReviewVerdict(args.verdict),
        reasons=reasons,
        follow_up_action=args.follow_up_action,
    )
    print(record["review_path"])
    if args.verdict == ReviewVerdict.REWORK_REQUIRED.value and args.create_rework:
        rework = create_rework_from_review(args.packet_id, reasons)
        print(rework["packet_path"])


def _cmd_test_feature(args: argparse.Namespace) -> None:
    from prefect_grace.flows.feature_pipeline import feature_pipeline

    prefer_agent_output = args.parse_agent_output or args.execute
    reviewer_verdict = args.reviewer_verdict
    verifier_test_verdict = args.verifier_test_verdict
    verifier_observability_verdict = args.verifier_observability_verdict
    verifier_frontend_visual_verdict = args.verifier_frontend_visual_verdict
    wave_verdict = args.wave_verdict
    planner_contract = json.loads(args.planner_contract) if args.planner_contract else None
    review_reasons_script = [item.split("||") for item in args.review_reasons_script or []]
    wave_reasons_script = [item.split("||") for item in args.wave_reasons_script or []]
    if not prefer_agent_output:
        reviewer_verdict = reviewer_verdict or (
            ReviewVerdict.BLOCKED.value
            if (
                verifier_test_verdict == TestVerdict.FAILED.value
                or verifier_observability_verdict in {
                    ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value,
                    ObservabilityVerdict.UNEXPECTED_DEGRADATION.value,
                }
                or verifier_frontend_visual_verdict == FrontendVisualVerdict.INSUFFICIENT.value
            )
            else ReviewVerdict.ACCEPTED.value
        )
        reviewer_verdict = reviewer_verdict or ReviewVerdict.ACCEPTED.value
        verifier_test_verdict = verifier_test_verdict or TestVerdict.PASSED.value
        verifier_observability_verdict = verifier_observability_verdict or ObservabilityVerdict.CLEAN.value
        verifier_frontend_visual_verdict = (
            verifier_frontend_visual_verdict or FrontendVisualVerdict.NOT_APPLICABLE.value
        )
        wave_verdict = wave_verdict or WaveVerdict.ACCEPTED.value
    result = feature_pipeline(
        feature_id=args.feature_id,
        title=args.title,
        summary=args.summary,
        implementation_title=args.implementation_title,
        implementation_summary=args.implementation_summary,
        dry_run=not args.execute,
        timeout_seconds=args.timeout_seconds,
        verifier_backend_profile=args.backend_profile if args.backend_profile is not None else (None if args.skip_backend_quick else "backend_quick"),
        verifier_frontend_profile=args.frontend_profile if args.frontend_profile is not None else ("frontend_quick" if args.touches_frontend and not args.frontend_command else None),
        verifier_frontend_commands=args.frontend_command,
        verifier_observability_profile=args.observability_profile,
        verifier_observability_commands=args.observability_command,
        verifier_artifact_globs=args.artifact_glob,
        verifier_touches_frontend=args.touches_frontend or bool(args.frontend_command),
        verifier_requires_frontend_visual=args.touches_frontend or bool(args.frontend_command),
        verifier_include_day_live_canary=args.include_day_live_canary,
        agent_workdir=args.agent_workdir,
        agent_sandbox=args.agent_sandbox,
        commit_hash=args.commit_hash,
        planner_contract=planner_contract,
        run_planner=args.run_planner,
        reviewer_verdict=reviewer_verdict,
        review_reasons=args.review_reason,
        reviewer_verdict_script=args.reviewer_verdict_script,
        review_reasons_script=review_reasons_script or None,
        verifier_test_verdict=verifier_test_verdict,
        verifier_observability_verdict=verifier_observability_verdict,
        verifier_frontend_visual_verdict=verifier_frontend_visual_verdict,
        verifier_commands_run=args.verifier_command,
        verifier_evidence_paths=args.verifier_evidence,
        verifier_blocking_issues=args.verifier_issue,
        wave_verdict=wave_verdict,
        wave_reasons=args.wave_reason,
        wave_verdict_script=args.wave_verdict_script,
        wave_reasons_script=wave_reasons_script or None,
        create_rework=not args.no_create_rework,
        prefer_agent_output=prefer_agent_output,
    )
    print(result)


def _scheduled_for_from_args(args: argparse.Namespace) -> str | None:
    scheduled_for = getattr(args, "scheduled_for", None)
    delay_minutes = getattr(args, "delay_minutes", None)
    if scheduled_for and delay_minutes is not None:
        raise SystemExit("Use either --scheduled-for or --delay-minutes, not both.")
    if scheduled_for:
        parsed = datetime.fromisoformat(str(scheduled_for).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    if delay_minutes is not None:
        return (datetime.now(timezone.utc) + timedelta(minutes=int(delay_minutes))).isoformat()
    return None


def _cmd_submit_feature(args: argparse.Namespace) -> None:
    parameters = feature_flow_parameters(
        feature_id=args.feature_id,
        title=args.title,
        summary=args.summary,
        implementation_title=args.implementation_title,
        implementation_summary=args.implementation_summary,
        execute=args.execute,
        timeout_seconds=args.timeout_seconds,
        verifier_backend_profile=args.backend_profile if args.backend_profile is not None else (None if args.skip_backend_quick else "backend_quick"),
        verifier_frontend_profile=args.frontend_profile if args.frontend_profile is not None else ("frontend_quick" if args.touches_frontend and not args.frontend_command else None),
        verifier_frontend_commands=args.frontend_command,
        verifier_observability_profile=args.observability_profile,
        verifier_observability_commands=args.observability_command,
        verifier_artifact_globs=args.artifact_glob,
        verifier_touches_frontend=args.touches_frontend or bool(args.frontend_command),
        verifier_requires_frontend_visual=args.touches_frontend or bool(args.frontend_command),
        verifier_include_day_live_canary=args.include_day_live_canary,
        prefer_agent_output=True,
        run_planner=args.run_planner,
        agent_workdir=args.agent_workdir,
        agent_sandbox=args.agent_sandbox,
        commit_hash=args.commit_hash,
    )
    record = submit_feature_flow_run(
        parameters=parameters,
        scheduled_for=_scheduled_for_from_args(args),
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))


def _cmd_submit_brief(args: argparse.Namespace) -> None:
    record = submit_feature_run_from_brief(args.path, scheduled_for=_scheduled_for_from_args(args))
    print(json.dumps(record, ensure_ascii=False, indent=2))


def _cmd_print_brief_template(args: argparse.Namespace) -> None:
    print(BUSINESS_BRIEF_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _cmd_queue(args: argparse.Namespace) -> None:
    print(json.dumps({"runs": list_recent_feature_flow_runs(limit=args.limit)}, ensure_ascii=False, indent=2))


def _cmd_dashboard(args: argparse.Namespace) -> None:
    snapshot = build_grace_dashboard_snapshot()
    if args.json:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return
    print(render_grace_dashboard(snapshot))


def _cmd_validate_project(args: argparse.Namespace) -> None:
    command = "validate-project"
    try:
        adapter = _load_adapter_from_args(args)
        profiles = load_verification_profiles(_profile_config_path(getattr(args, "project", None)))
        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                project_key=adapter.project_key,
                result={
                    "project": adapter.to_dict(),
                    "verification_profiles": profiles
                },
            ))
        else:
            print("Project configuration and verification profiles are valid.")
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "VALIDATION_FAILED", "message": str(e)}],
            ))
            sys.exit(1)
        else:
            print(f"Validation failed: {e}", file=sys.stderr)
            sys.exit(1)


def _cmd_scan_packets(args: argparse.Namespace) -> None:
    command = "scan-packets"
    try:
        adapter = _load_adapter_from_args(args)
        mode = args.mode or "legacy_warn"
        packets_data, all_warnings, errors = _scan_project_packets(adapter, mode=mode)

        if errors:
            if args.json:
                _print_json(_json_envelope(
                    ok=False,
                    command=command,
                    project_key=adapter.project_key,
                    warnings=all_warnings,
                    errors=errors,
                ))
                sys.exit(1)
            else:
                for err in errors:
                    print(err["message"], file=sys.stderr)
                sys.exit(1)

        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                project_key=adapter.project_key,
                result={
                    "packets": packets_data
                },
                warnings=all_warnings,
            ))
        else:
            print(f"Successfully scanned {len(packets_data)} packets.")
            if all_warnings:
                print(f"Collected {len(all_warnings)} warnings:")
                for w in all_warnings:
                    print(f" - {w}")
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "SCAN_FAILED", "message": str(e)}],
            ))
            sys.exit(1)
        else:
            print(f"Scan failed: {e}", file=sys.stderr)
            sys.exit(1)


def _cmd_validate_packet(args: argparse.Namespace) -> None:
    command = "validate-packet"
    try:
        mode = "strict" if args.strict else "legacy_warn"
        path = Path(args.path)
        if not path.exists():
            raise FileNotFoundError(f"Packet file not found at {path}")

        parsed = parse_packet_markdown(path, mode=mode)
        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                result=_packet_to_dict(parsed, path=path),
                warnings=parsed.legacy_warnings,
            ))
        else:
            print(f"Packet {parsed.packet_id} is valid.")
            if parsed.legacy_warnings:
                print("Warnings:")
                for w in parsed.legacy_warnings:
                    print(f" - {w}")
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "PACKET_INVALID", "message": str(e)}],
            ))
            sys.exit(1)
        else:
            print(f"Packet validation failed: {e}", file=sys.stderr)
            sys.exit(1)


def _cmd_sync_packets(args: argparse.Namespace) -> None:
    command = "sync-packets"
    try:
        from prefect_grace.platform.backlog_controller import BacklogController

        adapter = _load_adapter_from_args(args)

        sync_result = BacklogController.sync(
            project=adapter,
            dry_run=args.dry_run,
            retry_blocked=getattr(args, "retry_blocked", False),
            rerun_changed=getattr(args, "rerun_changed", False),
        )

        if sync_result.errors:
            if args.json:
                _print_json(_json_envelope(
                    ok=False,
                    command=command,
                    project_key=adapter.project_key,
                    result={
                        "packets_total": sync_result.packets_total,
                        "registry_updates": sync_result.registry_updates,
                        "ready": sync_result.ready,
                        "accepted": sync_result.accepted,
                        "blocked": sync_result.blocked,
                        "changed_after_acceptance": sync_result.changed_after_acceptance,
                        "ready_for_retry": sync_result.ready_for_retry,
                        "cascading_blocked": sync_result.cascading_blocked,
                        "cycles": sync_result.cycles,
                    },
                    warnings=sync_result.warnings,
                    errors=sync_result.errors,
                ))
            else:
                for err in sync_result.errors:
                    print(err, file=sys.stderr)
            sys.exit(2)

        result = {
            "dry_run": args.dry_run,
            "packets_total": sync_result.packets_total,
            "registry_updates": sync_result.registry_updates,
            "ready": sync_result.ready,
            "accepted": sync_result.accepted,
            "blocked": sync_result.blocked,
            "changed_after_acceptance": sync_result.changed_after_acceptance,
            "ready_for_retry": sync_result.ready_for_retry,
            "cascading_blocked": sync_result.cascading_blocked,
            "cycles": sync_result.cycles,
        }

        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                project_key=adapter.project_key,
                result=result,
                warnings=sync_result.warnings,
            ))
        else:
            verb = "Would sync" if args.dry_run else "Synced"
            print(f"{verb} {sync_result.packets_total} packets for {adapter.project_key}.")
            print(f"Ready: {len(sync_result.ready)}, Accepted: {len(sync_result.accepted)}, Blocked: {len(sync_result.blocked)}")
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "SYNC_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Sync failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_packet_status(args: argparse.Namespace) -> None:
    command = "packet-status"
    try:
        adapter = _load_adapter_from_args(args)
        registry = PacketRegistryStore(Path(adapter.runtime_state_root) / "state")
        packet = registry.load_packet(args.packet_id)
        if packet is None:
            raise KeyError(f"Packet {args.packet_id} not found in registry")
        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                project_key=adapter.project_key,
                result={"packet": packet},
            ))
        else:
            print(json.dumps(packet, indent=2, ensure_ascii=False))
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "PACKET_NOT_FOUND", "message": str(e)}],
            ))
        else:
            print(f"Packet status failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_registry_dump(args: argparse.Namespace) -> None:
    command = "registry-dump"
    try:
        adapter = _load_adapter_from_args(args)
        state_root = Path(adapter.runtime_state_root) / "state"
        result = {
            "packets": PacketRegistryStore(state_root).list_packets(adapter.project_key),
            "runs": RunStore(state_root).list_runs(),
            "executor_history": ExecutorHistoryStore(state_root).list_executions(),
        }
        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                project_key=adapter.project_key,
                result=result,
            ))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "REGISTRY_DUMP_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Registry dump failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_submit_packets(args: argparse.Namespace) -> None:
    command = "submit-packets"
    try:
        from prefect_grace.platform.backlog_controller import BacklogController

        adapter = _load_adapter_from_args(args)

        # Read registry state and plan submission
        submission_plan = BacklogController.plan_submission(adapter)

        # Check if RuntimeLock/Worktree/Scope lifecycle is available
        # For MVP-2, fail closed with safety error
        if args.execute:
            safety_error = {
                "code": "SAFETY_GATE_NOT_READY",
                "message": (
                    "Live packet execution requires RuntimeLock, WorktreeManager, and Scope Guard lifecycle. "
                    "These safety gates are not yet implemented. Use --dry-run to validate submission plan only."
                ),
                "required_gates": ["RuntimeLock", "WorktreeManager", "ScopeGuardLifecycle"],
                "current_mvp": "MVP-2",
                "execution_enabled_in": "MVP-5+",
            }
            if args.json:
                _print_json(_json_envelope(
                    ok=False,
                    command=command,
                    project_key=adapter.project_key,
                    errors=[safety_error],
                ))
            else:
                print(f"ERROR: {safety_error['message']}", file=sys.stderr)
            sys.exit(5)  # Exit code 5 for security/scope violation

        result = {
            "dry_run": not args.execute,
            "packets_to_submit": submission_plan.packets_to_submit,
            "submission_order": submission_plan.submission_order,
            "blocked_packets": submission_plan.blocked_packets,
            "note": "Submission plan validated. Use --execute when safety gates are ready.",
        }

        if submission_plan.errors:
            if args.json:
                _print_json(_json_envelope(
                    ok=False,
                    command=command,
                    project_key=adapter.project_key,
                    result=result,
                    warnings=submission_plan.warnings,
                    errors=submission_plan.errors,
                ))
            else:
                for err in submission_plan.errors:
                    print(f"ERROR: {err}", file=sys.stderr)
            sys.exit(3)  # Exit code 3 for dependency/DAG invalid

        if args.json:
            _print_json(_json_envelope(
                ok=True,
                command=command,
                project_key=adapter.project_key,
                result=result,
                warnings=submission_plan.warnings,
            ))
        else:
            print(f"Submission plan for {adapter.project_key}:")
            print(f"  Packets to submit: {len(submission_plan.packets_to_submit)}")
            print(f"  Submission order: {submission_plan.submission_order}")
            print(f"  Blocked packets: {len(submission_plan.blocked_packets)}")
            if submission_plan.warnings:
                print(f"  Warnings: {len(submission_plan.warnings)}")
    except Exception as e:
        if args.json:
            _print_json(_json_envelope(
                ok=False,
                command=command,
                errors=[{"code": "SUBMIT_FAILED", "message": str(e)}],
            ))
        else:
            print(f"Submit failed: {e}", file=sys.stderr)
        sys.exit(1)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prefect-grace")
    subparsers = parser.add_subparsers(required=True)

    feature = subparsers.add_parser("feature")
    feature.add_argument("feature_id")
    feature.add_argument("title")
    feature.add_argument("summary")
    feature.set_defaults(func=_cmd_feature)

    mark_feature = subparsers.add_parser("mark-feature")
    mark_feature.add_argument("feature_id")
    mark_feature.add_argument("status", choices=[item.value for item in FeatureStatus])
    mark_feature.set_defaults(func=_cmd_mark_feature)

    packet = subparsers.add_parser("packet")
    packet.add_argument("feature_id")
    packet.add_argument("wave_id")
    packet.add_argument("title")
    packet.add_argument("summary")
    packet.add_argument("--role", default="coder")
    packet.add_argument("--reasoning", choices=[item.value for item in ReasoningProfile], default=ReasoningProfile.HIGH.value)
    packet.set_defaults(func=_cmd_packet)

    run_codex = subparsers.add_parser("run-codex")
    run_codex.add_argument("packet_id")
    run_codex.add_argument("--dry-run", action="store_true")
    run_codex.add_argument("--timeout-seconds", type=int, default=3600)
    run_codex.set_defaults(func=_cmd_run_codex)

    run_verifier = subparsers.add_parser("run-verifier")
    run_verifier.add_argument("packet_id")
    run_verifier.add_argument("--dry-run", action="store_true")
    run_verifier.add_argument("--timeout-seconds", type=int, default=3600)
    run_verifier.set_defaults(func=_cmd_run_verifier)

    review = subparsers.add_parser("review")
    review.add_argument("packet_id")
    review.add_argument("verdict", choices=[item.value for item in ReviewVerdict])
    review.add_argument("--reason", action="append")
    review.add_argument("--follow-up-action", default="none")
    review.add_argument("--create-rework", action="store_true")
    review.set_defaults(func=_cmd_review)

    test_feature = subparsers.add_parser("test-feature")
    test_feature.add_argument("feature_id")
    test_feature.add_argument("title")
    test_feature.add_argument("summary")
    test_feature.add_argument(
        "--implementation-title",
        default="Test Implementation Packet",
    )
    test_feature.add_argument(
        "--implementation-summary",
        default="Run a bounded end-to-end test feature through architect, planner, coder, verifier, and reviewer packets.",
    )
    test_feature.add_argument(
        "--reviewer-verdict",
        choices=[item.value for item in ReviewVerdict],
    )
    test_feature.add_argument("--review-reason", action="append")
    test_feature.add_argument("--skip-backend-quick", action="store_true")
    test_feature.add_argument("--backend-profile")
    test_feature.add_argument("--touches-frontend", action="store_true")
    test_feature.add_argument("--frontend-profile")
    test_feature.add_argument("--frontend-command", action="append")
    test_feature.add_argument("--observability-profile")
    test_feature.add_argument("--observability-command", action="append")
    test_feature.add_argument("--artifact-glob", action="append")
    test_feature.add_argument("--include-day-live-canary", action="store_true")
    test_feature.add_argument("--agent-workdir")
    test_feature.add_argument("--agent-sandbox")
    test_feature.add_argument("--commit-hash")
    test_feature.add_argument("--planner-contract")
    test_feature.add_argument("--run-planner", action="store_true")
    test_feature.add_argument("--reviewer-verdict-script", action="append")
    test_feature.add_argument("--review-reasons-script", action="append")
    test_feature.add_argument("--wave-verdict-script", action="append")
    test_feature.add_argument("--wave-reasons-script", action="append")
    test_feature.add_argument(
        "--verifier-test-verdict",
        choices=[item.value for item in TestVerdict],
    )
    test_feature.add_argument(
        "--verifier-observability-verdict",
        choices=[item.value for item in ObservabilityVerdict],
    )
    test_feature.add_argument(
        "--verifier-frontend-visual-verdict",
        choices=[item.value for item in FrontendVisualVerdict],
    )
    test_feature.add_argument("--verifier-command", action="append")
    test_feature.add_argument("--verifier-evidence", action="append")
    test_feature.add_argument("--verifier-issue", action="append")
    test_feature.add_argument(
        "--wave-verdict",
        choices=[item.value for item in WaveVerdict],
    )
    test_feature.add_argument("--wave-reason", action="append")
    test_feature.add_argument("--no-create-rework", action="store_true")
    test_feature.add_argument("--parse-agent-output", action="store_true")
    test_feature.add_argument("--timeout-seconds", type=int, default=3600)
    test_feature.add_argument("--execute", action="store_true")
    test_feature.set_defaults(func=_cmd_test_feature)

    submit_feature = subparsers.add_parser("submit-feature")
    submit_feature.add_argument("feature_id")
    submit_feature.add_argument("title")
    submit_feature.add_argument("summary")
    submit_feature.add_argument(
        "--implementation-title",
        default="Live Implementation Packet",
    )
    submit_feature.add_argument(
        "--implementation-summary",
        default="Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.",
    )
    submit_feature.add_argument("--skip-backend-quick", action="store_true")
    submit_feature.add_argument("--backend-profile")
    submit_feature.add_argument("--touches-frontend", action="store_true")
    submit_feature.add_argument("--frontend-profile")
    submit_feature.add_argument("--frontend-command", action="append")
    submit_feature.add_argument("--observability-profile")
    submit_feature.add_argument("--observability-command", action="append")
    submit_feature.add_argument("--artifact-glob", action="append")
    submit_feature.add_argument("--include-day-live-canary", action="store_true")
    submit_feature.add_argument("--agent-workdir")
    submit_feature.add_argument("--agent-sandbox")
    submit_feature.add_argument("--commit-hash")
    submit_feature.add_argument("--run-planner", action="store_true")
    submit_feature.add_argument("--timeout-seconds", type=int, default=7200)
    submit_feature.add_argument("--scheduled-for")
    submit_feature.add_argument("--delay-minutes", type=int)
    submit_feature.add_argument("--execute", action="store_true")
    submit_feature.set_defaults(func=_cmd_submit_feature)

    submit_brief = subparsers.add_parser("submit-brief")
    submit_brief.add_argument("path")
    submit_brief.add_argument("--scheduled-for")
    submit_brief.add_argument("--delay-minutes", type=int)
    submit_brief.set_defaults(func=_cmd_submit_brief)

    print_brief_template = subparsers.add_parser("print-brief-template")
    print_brief_template.set_defaults(func=_cmd_print_brief_template)

    queue = subparsers.add_parser("queue")
    queue.add_argument("--limit", type=int, default=50)
    queue.set_defaults(func=_cmd_queue)

    dashboard = subparsers.add_parser("dashboard")
    dashboard.add_argument("--json", action="store_true")
    dashboard.set_defaults(func=_cmd_dashboard)

    validate_project = subparsers.add_parser("validate-project")
    validate_project.add_argument("--project")
    validate_project.add_argument("--json", action="store_true")
    validate_project.set_defaults(func=_cmd_validate_project)

    scan_packets = subparsers.add_parser("scan-packets")
    scan_packets.add_argument("--project")
    scan_packets.add_argument("--mode", choices=["legacy_warn", "strict"], default="legacy_warn")
    scan_packets.add_argument("--json", action="store_true")
    scan_packets.set_defaults(func=_cmd_scan_packets)

    validate_packet = subparsers.add_parser("validate-packet")
    validate_packet.add_argument("path")
    validate_packet.add_argument("--strict", action="store_true")
    validate_packet.add_argument("--json", action="store_true")
    validate_packet.set_defaults(func=_cmd_validate_packet)

    sync_packets = subparsers.add_parser("sync-packets")
    sync_packets.add_argument("--project")
    sync_packets.add_argument("--dry-run", action="store_true")
    sync_packets.add_argument("--retry-blocked", action="store_true")
    sync_packets.add_argument("--rerun-changed", action="store_true")
    sync_packets.add_argument("--json", action="store_true")
    sync_packets.set_defaults(func=_cmd_sync_packets)

    submit_packets = subparsers.add_parser("submit-packets")
    submit_packets.add_argument("--project")
    submit_packets.add_argument("--execute", action="store_true")
    submit_packets.add_argument("--json", action="store_true")
    submit_packets.set_defaults(func=_cmd_submit_packets)

    run_nightly = subparsers.add_parser("run-nightly")
    run_nightly.add_argument("--project")
    run_nightly.add_argument("--until-blocked", action="store_true")
    run_nightly.add_argument("--json", action="store_true")
    run_nightly.set_defaults(func=_cmd_run_nightly)

    packet_status = subparsers.add_parser("packet-status")
    packet_status.add_argument("--project")
    packet_status.add_argument("--packet-id", required=True)
    packet_status.add_argument("--json", action="store_true")
    packet_status.set_defaults(func=_cmd_packet_status)

    registry_dump = subparsers.add_parser("registry-dump")
    registry_dump.add_argument("--project")
    registry_dump.add_argument("--json", action="store_true")
    registry_dump.set_defaults(func=_cmd_registry_dump)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
