from __future__ import annotations

from prefect_grace.models import (
    FeatureStatus,
    FrontendVisualVerdict,
    ObservabilityVerdict,
    PacketStatus,
    ReviewVerdict,
    TestVerdict,
    WaveVerdict,
)
from prefect_grace.prefect_compat import flow, get_run_logger, tags, task
from prefect_grace.tasks.agent_output_parser import (
    parse_architect_artifact_plan_message,
    parse_planner_wave_plan_message,
    read_agent_message,
    resolve_reviewer_decision,
    resolve_verifier_result,
    resolve_wave_decision,
)
from prefect_grace.tasks.architect_artifacts import default_architect_artifact_plan, write_architect_artifacts
from prefect_grace.tasks.codex_launcher import launch_codex_for_packet
from prefect_grace.tasks.feature_bootstrap import bootstrap_feature, mark_feature_status, seed_test_feature
from prefect_grace.tasks.planner_contract import (
    default_wave_plan_contract,
    find_architect_wave_gate_packet_id,
    find_first_packet_id,
    materialize_planner_contract,
    normalize_wave_plan_contract,
)
from prefect_grace.tasks.prefect_artifacts import publish_feature_artifacts
from prefect_grace.tasks.review_router import (
    create_architect_decision_from_review,
    create_rework_bundle_from_review,
    create_rework_from_review,
    record_review,
    record_wave_review,
)
from prefect_grace.tasks.state_store import update_record
from prefect_grace.tasks.verifier_runner import run_verifier_for_packet
from prefect_grace.tasks.verification_router import record_verification
from prefect_grace.tasks.wave_executor import (
    append_unique_packet,
    group_packets_by_wave,
    missing_internal_dependencies,
    order_packets_for_wave,
    packet_has_downstream_reviewer,
    packet_map,
    packet_result_key,
    reviewer_target_packet_id,
)


@task(task_run_name="bootstrap:{feature_id}")
def bootstrap_task(feature_id: str, title: str, summary: str):
    logger = get_run_logger()
    record = bootstrap_feature(feature_id=feature_id, title=title, summary=summary)
    logger.info("Bootstrapped feature %s", feature_id)
    return record


@task(task_run_name="seed-packets:{feature_id}")
def seed_feature_packets_task(
    feature_id: str,
    title: str,
    summary: str,
    implementation_title: str,
    implementation_summary: str,
    verifier_backend_profile: str | None,
    verifier_frontend_profile: str | None,
    verifier_frontend_commands: list[str] | None,
    verifier_observability_profile: str | None,
    verifier_observability_commands: list[str] | None,
    verifier_artifact_globs: list[str] | None,
    verifier_touches_frontend: bool,
    verifier_requires_frontend_visual: bool,
    verifier_include_day_live_canary: bool,
    agent_workdir: str | None,
    agent_sandbox: str | None,
    business_context: dict | None = None,
    planner_contract: dict | None = None,
):
    logger = get_run_logger()
    logger.info("Seeding role packets for %s", feature_id)
    return seed_test_feature(
        feature_id=feature_id,
        title=title,
        summary=summary,
        implementation_title=implementation_title,
        implementation_summary=implementation_summary,
        verifier_backend_profile=verifier_backend_profile,
        verifier_frontend_profile=verifier_frontend_profile,
        verifier_frontend_commands=verifier_frontend_commands,
        verifier_observability_profile=verifier_observability_profile,
        verifier_observability_commands=verifier_observability_commands,
        verifier_artifact_globs=verifier_artifact_globs,
        verifier_touches_frontend=verifier_touches_frontend,
        verifier_requires_frontend_visual=verifier_requires_frontend_visual,
        verifier_include_day_live_canary=verifier_include_day_live_canary,
        agent_workdir=agent_workdir,
        agent_sandbox=agent_sandbox,
        business_context=business_context,
        planner_contract=planner_contract,
    )


@task(task_run_name="planner-contract:resolve")
def resolve_planner_contract_task(
    planner_run: dict,
    *,
    feature_id: str,
    implementation_title: str,
    implementation_summary: str,
    verifier_backend_profile: str | None,
    verifier_frontend_profile: str | None,
    verifier_frontend_commands: list[str] | None,
    verifier_observability_profile: str | None,
    verifier_observability_commands: list[str] | None,
    verifier_artifact_globs: list[str] | None,
    verifier_touches_frontend: bool,
    verifier_requires_frontend_visual: bool,
    verifier_include_day_live_canary: bool,
    planner_contract_override: dict | None,
    prefer_agent_output: bool,
) -> dict:
    logger = get_run_logger()
    parser_error = None
    contract = None
    if prefer_agent_output:
        try:
            payload = parse_planner_wave_plan_message(
                read_agent_message(planner_run.get('last_message_path'), planner_run.get('stdout_path'))
            )
            contract = normalize_wave_plan_contract(payload)
        except ValueError as exc:
            parser_error = str(exc)
    if contract is None and planner_contract_override:
        contract = normalize_wave_plan_contract(planner_contract_override)
        source = 'explicit_input'
    elif contract is None:
        contract = default_wave_plan_contract(
            feature_id=feature_id,
            implementation_title=implementation_title,
            implementation_summary=implementation_summary,
            verifier_backend_profile=verifier_backend_profile,
            verifier_frontend_profile=verifier_frontend_profile,
            verifier_frontend_commands=verifier_frontend_commands,
            verifier_observability_profile=verifier_observability_profile,
            verifier_observability_commands=verifier_observability_commands,
            verifier_artifact_globs=verifier_artifact_globs,
            verifier_touches_frontend=verifier_touches_frontend,
            verifier_requires_frontend_visual=verifier_requires_frontend_visual,
            verifier_include_day_live_canary=verifier_include_day_live_canary,
        )
        source = 'fallback'
    elif contract is not None:
        source = 'agent_output'
    logger.info('Resolved planner contract source=%s parser_error=%s', source, parser_error)
    return {'contract': contract, 'source': source, 'parser_error': parser_error}


@task(task_run_name="architect-artifacts:resolve:{feature_id}")
def resolve_architect_artifact_plan_task(
    architect_run: dict,
    *,
    feature_id: str,
    title: str,
    summary: str,
    business_context: dict | None,
    prefer_agent_output: bool,
) -> dict:
    logger = get_run_logger()
    parser_error = None
    payload = None
    if prefer_agent_output:
        try:
            payload = parse_architect_artifact_plan_message(
                read_agent_message(architect_run.get("last_message_path"), architect_run.get("stdout_path"))
            )
            source = "agent_output"
        except ValueError as exc:
            parser_error = str(exc)
    if payload is None:
        payload = default_architect_artifact_plan(
            feature_id=feature_id,
            title=title,
            summary=summary,
            business_context=business_context,
        )
        source = "fallback"
    logger.info("Resolved architect artifact plan source=%s parser_error=%s", source, parser_error)
    return {"payload": payload, "source": source, "parser_error": parser_error}


@task(task_run_name="architect-artifacts:write:{feature_id}")
def write_architect_artifacts_task(
    feature_id: str,
    architect_artifact_plan: dict,
) -> dict:
    logger = get_run_logger()
    written = write_architect_artifacts(
        feature_id=feature_id,
        architect_payload=architect_artifact_plan["payload"],
    )
    logger.info("Wrote architect slice docs for %s at %s", feature_id, written.get("slice_dir"))
    return written


@task(task_run_name="planner-contract:materialize:{feature_id}")
def materialize_planner_contract_task(
    feature_id: str,
    planner_packet_id: str,
    architect_packet_id: str,
    planner_contract_result: dict,
    agent_workdir: str | None,
    agent_sandbox: str | None,
    verifier_backend_profile: str | None,
    verifier_frontend_profile: str | None,
    verifier_frontend_commands: list[str] | None,
    verifier_observability_profile: str | None,
    verifier_observability_commands: list[str] | None,
    verifier_artifact_globs: list[str] | None,
    verifier_touches_frontend: bool,
    verifier_requires_frontend_visual: bool,
    verifier_include_day_live_canary: bool,
):
    logger = get_run_logger()
    base_execution_hints = {
        key: value
        for key, value in {
            'workdir': agent_workdir,
            'sandbox': agent_sandbox,
        }.items()
        if value not in (None, '')
    }
    materialized = materialize_planner_contract(
        feature_id=feature_id,
        planner_packet_id=planner_packet_id,
        architect_packet_id=architect_packet_id,
        contract=planner_contract_result['contract'],
        base_execution_hints=base_execution_hints,
        default_verifier_execution_hints={
            "runner": "verifier",
            "backend_profile": verifier_backend_profile,
            "frontend_profile": verifier_frontend_profile,
            "frontend_commands": verifier_frontend_commands or [],
            "observability_profile": verifier_observability_profile,
            "observability_commands": verifier_observability_commands or [],
            "artifact_globs": verifier_artifact_globs or [],
            "touches_frontend": verifier_touches_frontend,
            "requires_frontend_visual": verifier_requires_frontend_visual,
            "include_day_live_canary": verifier_include_day_live_canary,
        },
    )
    logger.info('Materialized planner contract with %s packets for %s', len(materialized['packets']), feature_id)
    return materialized


@task(task_run_name="feature-status:{feature_id}:in-progress")
def mark_feature_in_progress_task(feature_id: str):
    logger = get_run_logger()
    logger.info("Marking feature %s as in progress", feature_id)
    return mark_feature_status(feature_id, FeatureStatus.IN_PROGRESS)


@task(task_run_name="packet:{packet_id}")
def run_packet_task(packet_id: str, dry_run: bool, timeout_seconds: int):
    logger = get_run_logger()
    logger.info("Running packet %s dry_run=%s", packet_id, dry_run)
    return launch_codex_for_packet(packet_id, dry_run=dry_run, timeout_seconds=timeout_seconds)


@task(task_run_name="verifier:{packet_id}")
def run_verifier_packet_task(packet_id: str, dry_run: bool, timeout_seconds: int):
    logger = get_run_logger()
    logger.info("Running verifier packet %s dry_run=%s", packet_id, dry_run)
    return run_verifier_for_packet(packet_id, dry_run=dry_run, timeout_seconds=timeout_seconds)


@task(task_run_name="packet-status:{packet_id}:{status}")
def mark_packet_status_task(packet_id: str, status: str):
    logger = get_run_logger()
    PacketStatus(status)
    logger.info("Packet %s status=%s", packet_id, status)
    return update_record("packets", "packets", "packet_id", packet_id, {"status": status})


@task(task_run_name="review-route:{coder_packet_id}")
def route_reviewer_verdict_task(
    coder_packet_id: str,
    reviewer_packet_id: str,
    reviewer_decision: dict,
    create_rework: bool,
):
    logger = get_run_logger()
    verdict = ReviewVerdict(reviewer_decision["packet_verdict"])
    review_reasons = list(reviewer_decision.get("reasons") or [])
    follow_up_action = str(reviewer_decision.get("follow_up_action") or "none")
    rework = None
    decision = None
    review = record_review(
        packet_id=coder_packet_id,
        verdict=verdict,
        reasons=review_reasons,
        follow_up_action=follow_up_action,
    )
    if verdict == ReviewVerdict.ACCEPTED:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.ACCEPTED.value)
        mark_packet_status_task(coder_packet_id, PacketStatus.ACCEPTED.value)
    elif verdict == ReviewVerdict.REWORK_REQUIRED:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.ACCEPTED.value)
        if create_rework:
            rework = create_rework_bundle_from_review(
                packet_id=coder_packet_id,
                reviewer_packet_id=reviewer_packet_id,
                reasons=review_reasons,
            )
        mark_packet_status_task(coder_packet_id, PacketStatus.REWORK_REQUIRED.value)
    elif verdict == ReviewVerdict.ESCALATE_TO_ARCHITECT:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.ACCEPTED.value)
        decision = create_architect_decision_from_review(coder_packet_id, review_reasons)
        mark_packet_status_task(coder_packet_id, PacketStatus.ESCALATE_TO_ARCHITECT.value)
    else:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.BLOCKED.value)
        mark_packet_status_task(coder_packet_id, PacketStatus.BLOCKED.value)
    logger.info("Reviewer routed verdict=%s for packet %s", verdict.value, coder_packet_id)
    return {
        "review": review,
        "rework": rework,
        "decision": decision,
        "reviewer_verdict": verdict.value,
        "decision_source": reviewer_decision.get("source"),
        "parser_error": reviewer_decision.get("parser_error"),
    }


@task(task_run_name="wave-route:{feature_id}:{wave_id}")
def route_architect_wave_verdict_task(
    feature_id: str,
    wave_id: str,
    architect_packet_id: str,
    wave_decision: dict,
):
    logger = get_run_logger()
    verdict = WaveVerdict(wave_decision["wave_verdict"])
    wave_reasons = list(wave_decision.get("reasons") or [])
    review = record_wave_review(
        feature_id=feature_id,
        wave_id=wave_id,
        architect_packet_id=architect_packet_id,
        verdict=verdict,
        reasons=wave_reasons,
    )
    if verdict == WaveVerdict.ACCEPTED:
        mark_packet_status_task(architect_packet_id, PacketStatus.ACCEPTED.value)
    elif verdict == WaveVerdict.REWORK_REQUIRED:
        mark_packet_status_task(architect_packet_id, PacketStatus.REWORK_REQUIRED.value)
    else:
        mark_packet_status_task(architect_packet_id, PacketStatus.BLOCKED.value)
    logger.info("Architect wave gate routed verdict=%s for %s/%s", verdict.value, feature_id, wave_id)
    return {
        "wave_review": review,
        "wave_verdict": verdict.value,
        "decision_source": wave_decision.get("source"),
        "parser_error": wave_decision.get("parser_error"),
    }


@task(task_run_name="verifier-result:resolve")
def resolve_verifier_result_task(
    verifier_run: dict,
    verifier_test_verdict: str | None,
    verifier_observability_verdict: str | None,
    verifier_frontend_visual_verdict: str | None,
    verifier_commands_run: list[str] | None,
    verifier_evidence_paths: list[str] | None,
    verifier_blocking_issues: list[str] | None,
    prefer_agent_output: bool,
):
    logger = get_run_logger()
    try:
        result = resolve_verifier_result(
            verifier_run,
            fallback_test_verdict=verifier_test_verdict,
            fallback_observability_verdict=verifier_observability_verdict,
            fallback_frontend_visual_verdict=verifier_frontend_visual_verdict,
            fallback_commands_run=verifier_commands_run,
            fallback_evidence_paths=verifier_evidence_paths,
            fallback_blocking_issues=verifier_blocking_issues,
            prefer_agent_output=prefer_agent_output,
        )
    except ValueError as exc:
        result = {
            "test_verdict": TestVerdict.FAILED.value,
            "observability_verdict": ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value,
            "frontend_visual_verdict": FrontendVisualVerdict.NOT_APPLICABLE.value,
            "commands_run": [],
            "evidence_paths": [],
            "blocking_issues": [f"Verifier output parse failed: {exc}"],
            "source": "parse_error",
            "parser_error": str(exc),
            "raw_message": "",
        }
    logger.info(
        "Resolved verifier result source=%s test=%s obs=%s",
        result.get("source"),
        result.get("test_verdict"),
        result.get("observability_verdict"),
    )
    return result


@task(task_run_name="record-verifier:{verifier_packet_id}")
def record_verifier_result_task(
    verifier_packet_id: str,
    verifier_result: dict,
):
    logger = get_run_logger()
    record = record_verification(
        packet_id=verifier_packet_id,
        test_verdict=verifier_result["test_verdict"],
        observability_verdict=verifier_result["observability_verdict"],
        frontend_visual_verdict=verifier_result["frontend_visual_verdict"],
        commands_run=list(verifier_result.get("commands_run") or []),
        evidence_paths=list(verifier_result.get("evidence_paths") or []),
        blocking_issues=list(verifier_result.get("blocking_issues") or []),
    )
    logger.info("Recorded verifier evidence for %s", verifier_packet_id)
    return record


@task(task_run_name="feature-artifacts:{feature[feature_id]}")
def publish_feature_artifacts_task(
    feature: dict,
    packet_results: dict,
    verification: dict | None,
    review_route: dict | None,
    wave_route: dict | None,
    final_status: dict | None,
):
    logger = get_run_logger()
    artifact_ids = publish_feature_artifacts(
        feature=feature,
        packet_results=packet_results,
        verification=verification,
        review_route=review_route,
        wave_route=wave_route,
        final_status=final_status,
    )
    logger.info("Published %s feature artifacts", len(artifact_ids))
    return artifact_ids


@task(task_run_name="review-decision:resolve")
def resolve_reviewer_decision_task(
    reviewer_run: dict,
    reviewer_verdict: str | None,
    review_reasons: list[str] | None,
    prefer_agent_output: bool,
):
    logger = get_run_logger()
    try:
        decision = resolve_reviewer_decision(
            reviewer_run,
            fallback_verdict=reviewer_verdict,
            fallback_reasons=review_reasons,
            prefer_agent_output=prefer_agent_output,
        )
    except ValueError as exc:
        decision = {
            "packet_verdict": ReviewVerdict.BLOCKED.value,
            "follow_up_action": "none",
            "reasons": [f"Reviewer output parse failed: {exc}"],
            "source": "parse_error",
            "parser_error": str(exc),
            "raw_message": "",
        }
    logger.info("Resolved reviewer decision source=%s verdict=%s", decision.get("source"), decision.get("packet_verdict"))
    return decision


@task(task_run_name="wave-decision:resolve")
def resolve_wave_decision_task(
    architect_wave_run: dict,
    wave_verdict: str | None,
    wave_reasons: list[str] | None,
    prefer_agent_output: bool,
):
    logger = get_run_logger()
    try:
        decision = resolve_wave_decision(
            architect_wave_run,
            fallback_verdict=wave_verdict,
            fallback_reasons=wave_reasons,
            prefer_agent_output=prefer_agent_output,
        )
    except ValueError as exc:
        decision = {
            "wave_verdict": WaveVerdict.BLOCKED.value,
            "reasons": [f"Architect wave output parse failed: {exc}"],
            "source": "parse_error",
            "parser_error": str(exc),
            "raw_message": "",
        }
    logger.info("Resolved architect wave decision source=%s verdict=%s", decision.get("source"), decision.get("wave_verdict"))
    return decision


@flow(name="prefect-grace-feature-pipeline", flow_run_name="feature:{feature_id}")
def feature_pipeline(
    feature_id: str,
    title: str,
    summary: str,
    implementation_title: str = "Test Implementation Packet",
    implementation_summary: str = "Run a bounded end-to-end test feature through architect, planner, coder, verifier, and reviewer packets.",
    dry_run: bool = True,
    timeout_seconds: int = 3600,
    verifier_backend_profile: str | None = "backend_quick",
    verifier_frontend_profile: str | None = None,
    verifier_frontend_commands: list[str] | None = None,
    verifier_observability_profile: str | None = None,
    verifier_observability_commands: list[str] | None = None,
    verifier_artifact_globs: list[str] | None = None,
    verifier_touches_frontend: bool = False,
    verifier_requires_frontend_visual: bool = False,
    verifier_include_day_live_canary: bool = False,
    agent_workdir: str | None = None,
    agent_sandbox: str | None = None,
    business_context: dict | None = None,
    planner_contract: dict | None = None,
    reviewer_verdict: str | None = ReviewVerdict.ACCEPTED.value,
    review_reasons: list[str] | None = None,
    verifier_test_verdict: str | None = TestVerdict.PASSED.value,
    verifier_observability_verdict: str | None = ObservabilityVerdict.CLEAN.value,
    verifier_frontend_visual_verdict: str | None = FrontendVisualVerdict.NOT_APPLICABLE.value,
    verifier_commands_run: list[str] | None = None,
    verifier_evidence_paths: list[str] | None = None,
    verifier_blocking_issues: list[str] | None = None,
    wave_verdict: str | None = WaveVerdict.ACCEPTED.value,
    wave_reasons: list[str] | None = None,
    create_rework: bool = True,
    prefer_agent_output: bool = False,
    reviewer_verdict_script: list[str] | None = None,
    review_reasons_script: list[list[str]] | None = None,
    wave_verdict_script: list[str] | None = None,
    wave_reasons_script: list[list[str]] | None = None,
):
    with tags(f"feature:{feature_id}", "flow:feature-pipeline"):
        seeded = seed_feature_packets_task(
            feature_id=feature_id,
            title=title,
            summary=summary,
            implementation_title=implementation_title,
            implementation_summary=implementation_summary,
            verifier_backend_profile=verifier_backend_profile,
            verifier_frontend_profile=verifier_frontend_profile,
            verifier_frontend_commands=verifier_frontend_commands,
            verifier_observability_profile=verifier_observability_profile,
            verifier_observability_commands=verifier_observability_commands,
            verifier_artifact_globs=verifier_artifact_globs,
            verifier_touches_frontend=verifier_touches_frontend,
            verifier_requires_frontend_visual=verifier_requires_frontend_visual,
            verifier_include_day_live_canary=verifier_include_day_live_canary,
            agent_workdir=agent_workdir,
            agent_sandbox=agent_sandbox,
            business_context=business_context,
            planner_contract=planner_contract,
        )
        mark_feature_in_progress_task(feature_id)

        packet_results: dict[str, dict] = {}
        review_route = None

        architect_packet_id = seeded["packets"]["architect"]["packet_id"]
        planner_packet_id = seeded["packets"]["planner"]["packet_id"]

        with tags("wave:W00", "role:architect"):
            architect_run = run_packet_task(architect_packet_id, dry_run, timeout_seconds)
        packet_results["architect"] = architect_run
        if architect_run.get("returncode") != 0:
            final_status = {
                "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                "has_failures": True,
                "next_action": "inspect-failed-architect",
            }
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}
        with tags("wave:W00", "role:architect"):
            mark_packet_status_task(architect_packet_id, PacketStatus.ACCEPTED.value)

        architect_artifact_plan = resolve_architect_artifact_plan_task(
            architect_run,
            feature_id=feature_id,
            title=title,
            summary=summary,
            business_context=business_context,
            prefer_agent_output=prefer_agent_output,
        )
        packet_results["architect_artifact_plan"] = architect_artifact_plan
        architect_artifacts = write_architect_artifacts_task(feature_id, architect_artifact_plan)
        packet_results["architect_artifacts"] = architect_artifacts

        with tags("wave:W00", "role:planner"):
            planner_run = run_packet_task(planner_packet_id, dry_run, timeout_seconds)
        packet_results["planner"] = planner_run
        if planner_run.get("returncode") != 0:
            final_status = {
                "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                "has_failures": True,
                "next_action": "inspect-failed-planner",
            }
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}
        with tags("wave:W00", "role:planner"):
            mark_packet_status_task(planner_packet_id, PacketStatus.ACCEPTED.value)

        planner_contract_result = resolve_planner_contract_task(
            planner_run,
            feature_id=feature_id,
            implementation_title=implementation_title,
            implementation_summary=implementation_summary,
            verifier_backend_profile=verifier_backend_profile,
            verifier_frontend_profile=verifier_frontend_profile,
            verifier_frontend_commands=verifier_frontend_commands,
            verifier_observability_profile=verifier_observability_profile,
            verifier_observability_commands=verifier_observability_commands,
            verifier_artifact_globs=verifier_artifact_globs,
            verifier_touches_frontend=verifier_touches_frontend,
            verifier_requires_frontend_visual=verifier_requires_frontend_visual,
            verifier_include_day_live_canary=verifier_include_day_live_canary,
            planner_contract_override=planner_contract,
            prefer_agent_output=prefer_agent_output,
        )
        packet_results["planner_contract"] = planner_contract_result
        materialized_contract = materialize_planner_contract_task(
            feature_id,
            planner_packet_id,
            architect_packet_id,
            planner_contract_result,
            agent_workdir,
            agent_sandbox,
            verifier_backend_profile,
            verifier_frontend_profile,
            verifier_frontend_commands,
            verifier_observability_profile,
            verifier_observability_commands,
            verifier_artifact_globs,
            verifier_touches_frontend,
            verifier_requires_frontend_visual,
            verifier_include_day_live_canary,
        )
        packet_results["planner_materialized"] = materialized_contract

        generated_packets = list(materialized_contract["packets"])
        packets_by_id = packet_map(generated_packets)
        wave_groups = group_packets_by_wave(generated_packets)

        verification_records: list[dict] = []
        review_routes: list[dict] = []
        wave_routes: list[dict] = []
        wave_packet_sets: dict[str, set[str]] = {
            wave_id: {str(packet["packet_id"]) for packet in packets}
            for wave_id, packets in wave_groups
        }
        completed_packet_ids: set[str] = {architect_packet_id, planner_packet_id}
        reviewer_decision_index = 0
        wave_decision_index = 0

        for wave_id, wave_packets in wave_groups:
            ordered_packets = order_packets_for_wave(wave_packets)
            queue_packets = list(ordered_packets)
            queue_ids = {str(packet["packet_id"]) for packet in queue_packets}
            wave_route = None
            idle_steps = 0

            while queue_packets:
                packet = queue_packets.pop(0)
                packet_id = str(packet["packet_id"])
                role = str(packet.get("role") or "")
                queue_ids.discard(packet_id)

                missing_dependencies = missing_internal_dependencies(
                    packet,
                    known_packet_ids=set(packets_by_id),
                    completed_packet_ids=completed_packet_ids,
                )
                if missing_dependencies:
                    append_unique_packet(queue_packets, packet)
                    queue_ids.add(packet_id)
                    idle_steps += 1
                    if idle_steps > max(len(queue_packets), 1) + 1:
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                            "has_failures": True,
                            "next_action": f"dependency-deadlock:{packet_id}",
                        }
                        packet_results[packet_result_key("dependency_error", packet_id)] = {
                            "packet_id": packet_id,
                            "missing_dependencies": missing_dependencies,
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    continue

                idle_steps = 0

                if role in {"coder", "planner", "architect", "reviewer"}:
                    with tags(f"wave:{wave_id}", f"role:{role}"):
                        packet_run = run_packet_task(packet_id, dry_run, timeout_seconds)
                    packet_results[packet_result_key("run", packet_id)] = packet_run
                    if packet_run.get("returncode") != 0:
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                            "has_failures": True,
                            "next_action": f"inspect-failed-packet:{packet_id}",
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }

                if role == "coder":
                    with tags(f"wave:{wave_id}", "role:coder"):
                        mark_packet_status_task(packet_id, PacketStatus.REVIEW.value)
                    completed_packet_ids.add(packet_id)
                    if not packet_has_downstream_reviewer(packet_id, wave_packets):
                        with tags(f"wave:{wave_id}", "role:coder"):
                            mark_packet_status_task(packet_id, PacketStatus.ACCEPTED.value)
                    continue

                if role == "verifier":
                    with tags(f"wave:{wave_id}", "role:verifier"):
                        verifier_run = run_verifier_packet_task(packet_id, dry_run, timeout_seconds)
                    packet_results[packet_result_key("verifier-run", packet_id)] = verifier_run
                    if verifier_run.get("returncode") != 0:
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                            "has_failures": True,
                            "next_action": f"inspect-failed-verifier:{packet_id}",
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    verifier_result = resolve_verifier_result_task(
                        verifier_run,
                        verifier_test_verdict,
                        verifier_observability_verdict,
                        verifier_frontend_visual_verdict,
                        verifier_commands_run,
                        verifier_evidence_paths,
                        verifier_blocking_issues,
                        prefer_agent_output,
                    )
                    packet_results[packet_result_key("verifier-result", packet_id)] = verifier_result
                    if verifier_result.get("source") == "parse_error":
                        with tags(f"wave:{wave_id}", "role:verifier"):
                            mark_packet_status_task(packet_id, PacketStatus.BLOCKED.value)
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                            "has_failures": True,
                            "next_action": f"inspect-verifier-parse-error:{packet_id}",
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    with tags(f"wave:{wave_id}", "role:verifier"):
                        verification_record = record_verifier_result_task(packet_id, verifier_result)
                        mark_packet_status_task(packet_id, PacketStatus.ACCEPTED.value)
                    verification_records.append(verification_record)
                    packet_results[packet_result_key("verification", packet_id)] = verification_record
                    completed_packet_ids.add(packet_id)
                    continue

                if role == "reviewer":
                    target_packet_id = reviewer_target_packet_id(packet, packets_by_id)
                    current_review_reasons = (
                        review_reasons_script[reviewer_decision_index]
                        if review_reasons_script and reviewer_decision_index < len(review_reasons_script)
                        else review_reasons
                    )
                    current_reviewer_verdict = (
                        reviewer_verdict_script[reviewer_decision_index]
                        if reviewer_verdict_script and reviewer_decision_index < len(reviewer_verdict_script)
                        else reviewer_verdict
                    )
                    reviewer_decision = resolve_reviewer_decision_task(
                        packet_run,
                        current_reviewer_verdict,
                        current_review_reasons,
                        prefer_agent_output,
                    )
                    reviewer_decision_index += 1
                    with tags(f"wave:{wave_id}", "role:reviewer"):
                        review_route = route_reviewer_verdict_task(
                            target_packet_id,
                            packet_id,
                            reviewer_decision,
                            create_rework,
                        )
                    review_routes.append(review_route)
                    packet_results[packet_result_key("review", packet_id)] = review_route
                    completed_packet_ids.add(packet_id)

                    if review_route["reviewer_verdict"] == ReviewVerdict.REWORK_REQUIRED.value:
                        rework_bundle = review_route.get("rework") or {}
                        rework_packets = [
                            packet_obj
                            for packet_obj in [
                                rework_bundle.get("rework"),
                                rework_bundle.get("verifier"),
                                rework_bundle.get("reviewer"),
                            ]
                            if isinstance(packet_obj, dict) and packet_obj.get("packet_id")
                        ]
                        if rework_packets:
                            for rework_packet in rework_packets:
                                rework_packet_id = str(rework_packet["packet_id"])
                                packets_by_id[rework_packet_id] = rework_packet
                                wave_packet_sets.setdefault(wave_id, set()).add(rework_packet_id)
                                if rework_packet_id not in queue_ids and rework_packet_id not in completed_packet_ids:
                                    append_unique_packet(queue_packets, rework_packet)
                                    queue_ids.add(rework_packet_id)
                            rework_reviewer_packet_id = str(rework_bundle.get("reviewer", {}).get("packet_id") or "")
                            for queued_packet in queue_packets:
                                if str(queued_packet.get("role") or "") != "architect":
                                    continue
                                if str(queued_packet.get("wave_id") or "") != wave_id:
                                    continue
                                dependencies = list(queued_packet.get("dependencies") or [])
                                if packet_id in dependencies and rework_reviewer_packet_id and rework_reviewer_packet_id not in dependencies:
                                    queued_packet["dependencies"] = [*dependencies, rework_reviewer_packet_id]
                                    update_record(
                                        "packets",
                                        "packets",
                                        "packet_id",
                                        str(queued_packet["packet_id"]),
                                        {"dependencies": queued_packet["dependencies"]},
                                    )
                            feature_status = FeatureStatus.IN_PROGRESS
                            next_action = "run-rework-packet"
                            continue
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                            "has_failures": True,
                            "next_action": f"missing-rework-packet:{packet_id}",
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_route,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    if review_route["reviewer_verdict"] == ReviewVerdict.ESCALATE_TO_ARCHITECT.value:
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.ARCHITECT_READY),
                            "has_failures": False,
                            "next_action": "architect-decision-required",
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_route,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    if review_route["reviewer_verdict"] == ReviewVerdict.BLOCKED.value:
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                            "has_failures": True,
                            "next_action": f"inspect-review-blockers:{packet_id}",
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_route,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    continue

                if role == "architect":
                    current_wave_reasons = (
                        wave_reasons_script[wave_decision_index]
                        if wave_reasons_script and wave_decision_index < len(wave_reasons_script)
                        else wave_reasons
                    )
                    current_wave_verdict = (
                        wave_verdict_script[wave_decision_index]
                        if wave_verdict_script and wave_decision_index < len(wave_verdict_script)
                        else wave_verdict
                    )
                    wave_decision = resolve_wave_decision_task(
                        packet_run,
                        current_wave_verdict,
                        current_wave_reasons,
                        prefer_agent_output,
                    )
                    wave_decision_index += 1
                    with tags(f"wave:{wave_id}", "role:architect"):
                        wave_route = route_architect_wave_verdict_task(
                            feature_id,
                            wave_id,
                            packet_id,
                            wave_decision,
                        )
                    wave_routes.append(wave_route)
                    packet_results[packet_result_key("wave", packet_id)] = wave_route
                    completed_packet_ids.add(packet_id)
                    if wave_route["wave_verdict"] == WaveVerdict.ACCEPTED.value:
                        continue
                    if wave_route["wave_verdict"] == WaveVerdict.REWORK_REQUIRED.value:
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.IN_PROGRESS),
                            "has_failures": False,
                            "next_action": f"architect-wave-rework-required:{wave_id}",
                        }
                    else:
                        final_status = {
                            "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                            "has_failures": True,
                            "next_action": f"architect-wave-blocked:{wave_id}",
                        }
                    publish_feature_artifacts_task(
                        seeded["feature"],
                        packet_results,
                        verification_records[-1] if verification_records else None,
                        review_routes[-1] if review_routes else None,
                        wave_route,
                        final_status,
                    )
                    return {
                        "feature": seeded["feature"],
                        "seeded": seeded,
                        "runs": packet_results,
                        "verification_records": verification_records,
                        "review_routes": review_routes,
                        "wave_routes": wave_routes,
                        "final_status": final_status,
                    }

            if wave_route is None:
                final_status = {
                    "feature": mark_feature_status(feature_id, FeatureStatus.BLOCKED),
                    "has_failures": True,
                    "next_action": f"missing-architect-wave-gate:{wave_id}",
                }
                publish_feature_artifacts_task(
                    seeded["feature"],
                    packet_results,
                    verification_records[-1] if verification_records else None,
                    review_routes[-1] if review_routes else None,
                    wave_routes[-1] if wave_routes else None,
                    final_status,
                )
                return {
                    "feature": seeded["feature"],
                    "seeded": seeded,
                    "runs": packet_results,
                    "verification_records": verification_records,
                    "review_routes": review_routes,
                    "wave_routes": wave_routes,
                    "final_status": final_status,
                }

        final_status = {
            "feature": mark_feature_status(feature_id, FeatureStatus.ACCEPTED),
            "has_failures": False,
            "next_action": "feature-complete",
        }
        publish_feature_artifacts_task(
            seeded["feature"],
            packet_results,
            verification_records[-1] if verification_records else None,
            review_routes[-1] if review_routes else None,
            wave_routes[-1] if wave_routes else None,
            final_status,
        )
        return {
            "feature": seeded["feature"],
            "seeded": seeded,
            "runs": packet_results,
            "verification_records": verification_records,
            "review_routes": review_routes,
            "wave_routes": wave_routes,
            "verification": verification_records[-1] if verification_records else None,
            "review_route": review_routes[-1] if review_routes else None,
            "wave_route": wave_routes[-1] if wave_routes else None,
            "final_status": final_status,
        }


@task(task_run_name="review-record:{packet_id}:{verdict}")
def review_task(packet_id: str, verdict: str, reasons: list[str], create_rework: bool):
    review = record_review(
        packet_id=packet_id,
        verdict=ReviewVerdict(verdict),
        reasons=reasons,
        follow_up_action="localized_rework" if create_rework else "none",
    )
    rework = None
    if verdict == ReviewVerdict.REWORK_REQUIRED.value and create_rework:
        rework = create_rework_from_review(packet_id, reasons)
    return {"review": review, "rework": rework}


@flow(name="prefect-grace-review-router", flow_run_name="review:{packet_id}:{verdict}")
def review_router_flow(
    packet_id: str,
    verdict: str,
    reasons: list[str] | None = None,
    create_rework: bool = True,
):
    return review_task(
        packet_id=packet_id,
        verdict=verdict,
        reasons=reasons or [],
        create_rework=create_rework,
    )


if __name__ == "__main__":
    feature_pipeline(
        feature_id="FEAT-PREFECT-GRACE-SCAFFOLD",
        title="Prefect Grace Scaffold",
        summary="Bootstrap file-backed Prefect orchestration for strict GRACE workflows.",
        dry_run=True,
    )
