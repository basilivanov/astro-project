from __future__ import annotations

import argparse
import json

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
from prefect_grace.tasks.job_queue import enqueue_feature_job, list_jobs
from prefect_grace.tasks.business_intake import TEMPLATE_PATH as BUSINESS_BRIEF_TEMPLATE_PATH, enqueue_feature_job_from_brief


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


def _cmd_submit_feature(args: argparse.Namespace) -> None:
    record = enqueue_feature_job(
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
    print(json.dumps(record, ensure_ascii=False, indent=2))


def _cmd_submit_brief(args: argparse.Namespace) -> None:
    record = enqueue_feature_job_from_brief(args.path)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def _cmd_print_brief_template(args: argparse.Namespace) -> None:
    print(BUSINESS_BRIEF_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _cmd_queue(args: argparse.Namespace) -> None:
    print(json.dumps({"jobs": list_jobs()}, ensure_ascii=False, indent=2))


def _cmd_dashboard(args: argparse.Namespace) -> None:
    snapshot = build_grace_dashboard_snapshot()
    if args.json:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return
    print(render_grace_dashboard(snapshot))


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
    submit_feature.add_argument("--execute", action="store_true")
    submit_feature.set_defaults(func=_cmd_submit_feature)

    submit_brief = subparsers.add_parser("submit-brief")
    submit_brief.add_argument("path")
    submit_brief.set_defaults(func=_cmd_submit_brief)

    print_brief_template = subparsers.add_parser("print-brief-template")
    print_brief_template.set_defaults(func=_cmd_print_brief_template)

    queue = subparsers.add_parser("queue")
    queue.set_defaults(func=_cmd_queue)

    dashboard = subparsers.add_parser("dashboard")
    dashboard.add_argument("--json", action="store_true")
    dashboard.set_defaults(func=_cmd_dashboard)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
