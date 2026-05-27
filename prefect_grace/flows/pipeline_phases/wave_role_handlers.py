# ############################################################################
# AI_HEADER: pipeline_phases.wave_role_handlers
# ROLE: Bounded role handlers for feature_pipeline wave execution.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Execute coder, verifier, reviewer, and architect wave-gate packet branches for the feature pipeline.
# inputs: Pipeline runtime, mutable wave state, packet records, run results, queue state, and facade-bound dependencies.
# returns: Optional final result dictionaries for blocking branches.
# side_effects: Delegates to Prefect tasks and state helpers for packet status, reviews, rework packets, notifications, and artifacts.
# emitted_logs: Delegated Prefect task logs.
# error_behavior: Preserves feature_pipeline branch-specific final statuses and return envelopes.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - function: handle_coder_packet
#   - function: handle_verifier_packet
#   - function: handle_reviewer_packet
#   - function: handle_architect_packet
# END_MODULE_MAP

from __future__ import annotations

from prefect_grace.flows.pipeline_helpers.rework_routing import (
    REWORK_MODE_LIGHT_RESUME,
    REWORK_ROUTE_REQUIRES_USER_DECISION,
    REWORK_ROUTE_SELF_RESOLVABLE,
    REWORK_ROUTING_ARCHITECT_FIRST,
)
from prefect_grace.flows.pipeline_phases.context import (
    PipelineDeps,
    PipelineRuntime,
    PipelineState,
    pipeline_return,
)
from prefect_grace.models import FeatureStatus, PacketStatus, ReviewVerdict, WaveVerdict


def _last_verification(state: PipelineState) -> dict | None:
    return state.verification_records[-1] if state.verification_records else None


def _last_review(state: PipelineState) -> dict | None:
    return state.review_routes[-1] if state.review_routes else None


def _last_wave(state: PipelineState) -> dict | None:
    return state.wave_routes[-1] if state.wave_routes else None


def _publish_final(deps: PipelineDeps, state: PipelineState, final_status: dict) -> dict:
    deps.publish_feature_artifacts_task(
        state.seeded["feature"],
        state.packet_results,
        _last_verification(state),
        _last_review(state),
        _last_wave(state),
        final_status,
    )
    return pipeline_return(state, final_status)


# START_FUNCTION_CONTRACT
# name: handle_coder_packet
# purpose: Mark coder packets ready for review or accepted when no downstream reviewer exists.
# inputs: Runtime, dependencies, state, current packet, packet id, and wave packets.
# returns: None because coder handling does not directly finalize the pipeline.
# side_effects: Updates packet status and completed packet ids.
# emitted_logs: Delegated Prefect task logs.
# error_behavior: Propagates status update errors.
# END_FUNCTION_CONTRACT
def handle_coder_packet(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    *,
    packet: dict,
    packet_id: str,
    wave_id: str,
    wave_packets: list[dict],
) -> None:
    del runtime
    with deps.tags(f"wave:{wave_id}", "role:coder"):
        deps.mark_packet_status_task(packet_id, PacketStatus.REVIEW.value)
    state.completed_packet_ids.add(packet_id)
    if not deps.packet_has_downstream_reviewer(packet_id, wave_packets):
        with deps.tags(f"wave:{wave_id}", "role:coder"):
            deps.mark_packet_status_task(packet_id, PacketStatus.ACCEPTED.value)
    del packet


# START_FUNCTION_CONTRACT
# name: handle_verifier_packet
# purpose: Run verifier packets, resolve verifier output, persist verification records, and publish intermediate artifacts.
# inputs: Runtime, dependencies, state, packet id, and wave id.
# returns: Optional final result on verifier run failure or parse failure.
# side_effects: Runs verifier task, writes verification state, updates packet status, and publishes artifacts.
# emitted_logs: Delegated Prefect task logs.
# error_behavior: Returns environment_blocked or pipeline_invalid final envelopes for verifier failures.
# END_FUNCTION_CONTRACT
def handle_verifier_packet(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    *,
    packet_id: str,
    wave_id: str,
) -> dict | None:
    with deps.tags(f"wave:{wave_id}", "role:verifier"):
        verifier_run = deps.run_verifier_packet_task(packet_id, runtime.dry_run, runtime.timeout_seconds)
    state.packet_results[deps.packet_result_key("verifier-run", packet_id)] = verifier_run
    if verifier_run.get("returncode") != 0:
        final_status = deps.final_failure(
            feature_id=runtime.feature_id,
            category="environment_blocked",
            next_action=f"inspect-failed-verifier:{packet_id}",
        )
        return _publish_final(deps, state, final_status)

    verifier_result = deps.resolve_verifier_result_task(
        verifier_run,
        runtime.verifier_test_verdict,
        runtime.verifier_observability_verdict,
        runtime.verifier_frontend_visual_verdict,
        runtime.verifier_commands_run,
        runtime.verifier_evidence_paths,
        runtime.verifier_blocking_issues,
        runtime.prefer_agent_output,
    )
    state.packet_results[deps.packet_result_key("verifier-result", packet_id)] = verifier_result
    if verifier_result.get("source") == "parse_error":
        with deps.tags(f"wave:{wave_id}", "role:verifier"):
            deps.mark_packet_status_task(packet_id, PacketStatus.BLOCKED.value)
        final_status = deps.final_failure(
            feature_id=runtime.feature_id,
            category="pipeline_invalid",
            next_action=f"inspect-verifier-parse-error:{packet_id}",
            reasons=list(verifier_result.get("blocking_issues") or []),
        )
        return _publish_final(deps, state, final_status)

    with deps.tags(f"wave:{wave_id}", "role:verifier"):
        verification_record = deps.record_verifier_result_task(packet_id, verifier_result)
        deps.mark_packet_status_task(packet_id, PacketStatus.ACCEPTED.value)
    state.verification_records.append(verification_record)
    state.packet_results[deps.packet_result_key("verification", packet_id)] = verification_record
    deps.publish_feature_artifacts_task(
        state.seeded["feature"],
        state.packet_results,
        verification_record,
        _last_review(state),
        _last_wave(state),
        None,
    )
    state.completed_packet_ids.add(packet_id)
    return None


# START_FUNCTION_CONTRACT
# name: handle_reviewer_packet
# purpose: Resolve reviewer verdicts, route review decisions, and enqueue direct rework follow-up packets.
# inputs: Runtime, dependencies, state, current packet, packet run, wave id, queue, and queue id set.
# returns: Optional final result for reviewer blocking branches.
# side_effects: Writes review state, creates rework packets, mutates queue, updates wave progression, and publishes artifacts.
# emitted_logs: Delegated Prefect task logs.
# error_behavior: Preserves existing reviewer accepted, rework, escalation, and blocked envelopes.
# END_FUNCTION_CONTRACT
def handle_reviewer_packet(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    *,
    packet: dict,
    packet_id: str,
    packet_run: dict,
    wave_id: str,
    queue_packets: list[dict],
    queue_ids: set[str],
) -> dict | None:
    target_packet_id = deps.reviewer_target_packet_id(packet, state.packets_by_id)
    reviewer_decision = _resolve_review_decision(runtime, deps, state, packet_run, target_packet_id)
    route_classification = deps.classify_rework_route(reviewer_decision)
    rework_mode = deps.classify_rework_mode(
        decision=reviewer_decision,
        route_classification=route_classification,
        target_packet=state.packets_by_id.get(target_packet_id),
    )
    architect_rework_packet = _maybe_build_architect_rework(
        runtime,
        deps,
        state,
        packet_id,
        target_packet_id,
        wave_id,
        reviewer_decision,
        route_classification,
        rework_mode,
    )
    if isinstance(architect_rework_packet, dict) and architect_rework_packet.get("final_result"):
        return architect_rework_packet["final_result"]

    state.reviewer_decision_index += 1
    with deps.tags(f"wave:{wave_id}", "role:reviewer"):
        review_route = deps.route_reviewer_verdict_task(
            target_packet_id,
            packet_id,
            reviewer_decision,
            runtime.create_rework,
            rework_routing_policy=runtime.rework_routing_policy,
            architect_rework_packet=architect_rework_packet,
        )
    state.review_route = review_route
    state.review_routes.append(review_route)
    state.packet_results[deps.packet_result_key("review", packet_id)] = review_route
    with deps.tags(f"wave:{wave_id}", "role:reviewer", "artifact:packet"):
        deps.publish_packet_review_artifacts_task(review_route)
    deps.publish_feature_artifacts_task(
        state.seeded["feature"],
        state.packet_results,
        _last_verification(state),
        review_route,
        _last_wave(state),
        None,
    )
    state.completed_packet_ids.add(packet_id)

    if review_route["reviewer_verdict"] == ReviewVerdict.REWORK_REQUIRED.value:
        return _handle_review_rework(
            runtime,
            deps,
            state,
            packet,
            packet_id,
            target_packet_id,
            reviewer_decision,
            wave_id,
            queue_packets,
            queue_ids,
        )
    if review_route["reviewer_verdict"] == ReviewVerdict.ESCALATE_TO_ARCHITECT.value:
        return _review_awaiting_architect(runtime, deps, state, wave_id, "architect-decision-required")
    if review_route["reviewer_verdict"] == ReviewVerdict.BLOCKED.value:
        reasons = list((review_route.get("review") or {}).get("reasons") or [])
        deps.set_wave_progression_status(
            feature_id=runtime.feature_id,
            wave_progression=state.wave_progression,
            wave_id=wave_id,
            status="blocked",
            reasons=reasons,
        )
        state.packet_results["wave_progression"] = [dict(item) for item in state.wave_progression]
        category = "verification_blocked"
        if any(
            "pipeline" in reason.lower()
            or "verifier packet is missing" in reason.lower()
            or "structured text" in reason.lower()
            for reason in reasons
        ):
            category = "pipeline_invalid"
        final_status = deps.final_failure(
            feature_id=runtime.feature_id,
            category=category,
            next_action=f"inspect-review-blockers:{packet_id}",
            reasons=reasons,
        )
        return _publish_final(deps, state, final_status)
    return None


def _resolve_review_decision(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    packet_run: dict,
    target_packet_id: str,
) -> dict:
    current_review_reasons = (
        runtime.review_reasons_script[state.reviewer_decision_index]
        if runtime.review_reasons_script and state.reviewer_decision_index < len(runtime.review_reasons_script)
        else runtime.review_reasons
    )
    current_reviewer_verdict = (
        runtime.reviewer_verdict_script[state.reviewer_decision_index]
        if runtime.reviewer_verdict_script and state.reviewer_decision_index < len(runtime.reviewer_verdict_script)
        else runtime.reviewer_verdict
    )
    reviewer_decision = deps.resolve_reviewer_decision_task(
        packet_run,
        current_reviewer_verdict,
        current_review_reasons,
        runtime.prefer_agent_output,
    )
    reviewer_decision = deps.normalize_reviewer_decision_for_pipeline(reviewer_decision)
    return deps.escalate_repeated_observability_rework_for_pipeline(
        reviewer_decision,
        target_packet_id=target_packet_id,
        packets_by_id=state.packets_by_id,
    )


def _maybe_build_architect_rework(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    packet_id: str,
    target_packet_id: str,
    wave_id: str,
    reviewer_decision: dict,
    route_classification: str,
    rework_mode: str,
) -> dict | None:
    if not (
        reviewer_decision.get("packet_verdict") == ReviewVerdict.REWORK_REQUIRED.value
        and runtime.create_rework
        and runtime.rework_routing_policy == REWORK_ROUTING_ARCHITECT_FIRST
        and route_classification == REWORK_ROUTE_SELF_RESOLVABLE
    ):
        return None
    architect_rework_router_packet = deps.create_architect_rework_packet_from_review(
        target_packet_id,
        packet_id,
        list(reviewer_decision.get("reasons") or []),
        route_classification=route_classification,
    )
    state.packets_by_id[str(architect_rework_router_packet["packet_id"])] = architect_rework_router_packet
    state.packet_results[deps.packet_result_key("architect_rework_packet", packet_id)] = architect_rework_router_packet
    with deps.tags(f"wave:{wave_id}", "role:architect"):
        deps.mark_packet_status_task(str(architect_rework_router_packet["packet_id"]), PacketStatus.CODING.value)
        architect_rework_run = deps.run_packet_task(
            str(architect_rework_router_packet["packet_id"]),
            runtime.dry_run,
            runtime.timeout_seconds,
        )
    state.packet_results[deps.packet_result_key("architect_rework_run", packet_id)] = architect_rework_run
    if architect_rework_run.get("returncode") != 0:
        final_status = deps.final_failure(
            feature_id=runtime.feature_id,
            category="environment_blocked",
            next_action=f"inspect-failed-architect-rework:{architect_rework_router_packet['packet_id']}",
        )
        deps.publish_feature_artifacts_task(
            state.seeded["feature"],
            state.packet_results,
            _last_verification(state),
            state.review_route,
            _last_wave(state),
            final_status,
        )
        return {"final_result": pipeline_return(state, final_status)}
    with deps.tags(f"wave:{wave_id}", "role:architect"):
        deps.mark_packet_status_task(str(architect_rework_router_packet["packet_id"]), PacketStatus.ACCEPTED.value)
    return deps.build_architect_direct_rework(
        coder_packet_id=target_packet_id,
        reviewer_packet_id=packet_id,
        reasons=list(reviewer_decision.get("reasons") or []),
        architect_run=architect_rework_run,
        route_classification=route_classification,
        rework_mode=rework_mode,
    )


def _handle_review_rework(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    packet: dict,
    packet_id: str,
    target_packet_id: str,
    reviewer_decision: dict,
    wave_id: str,
    queue_packets: list[dict],
    queue_ids: set[str],
) -> dict | None:
    review_route = state.review_routes[-1]
    rework_object = review_route.get("rework")
    reasons = list((review_route.get("review") or {}).get("reasons") or [])
    deps.set_wave_progression_status(
        feature_id=runtime.feature_id,
        wave_progression=state.wave_progression,
        wave_id=wave_id,
        status="blocked",
        reasons=reasons,
    )
    state.packet_results["wave_progression"] = [dict(item) for item in state.wave_progression]
    missing = (
        review_route.get("route_classification") == REWORK_ROUTE_SELF_RESOLVABLE
        and runtime.rework_routing_policy == REWORK_ROUTING_ARCHITECT_FIRST
        and not (isinstance(rework_object, dict) and rework_object.get("packet_id"))
    )
    if missing:
        final_status = deps.final_failure(
            feature_id=runtime.feature_id,
            category="pipeline_invalid",
            next_action=f"missing-architect-direct-rework:{packet_id}",
            reasons=[f"Architect-first rework for {packet_id} did not yield a bounded direct coder packet."],
        )
        return _publish_final(deps, state, final_status)

    rework_packets, rework_reviewer_packet_id = _resolve_rework_packets(
        deps,
        state,
        packet,
        packet_id,
        target_packet_id,
        reviewer_decision,
        review_route,
        rework_object,
    )
    if rework_packets:
        _enqueue_rework_packets(
            deps,
            state,
            wave_id,
            packet_id,
            target_packet_id,
            rework_packets,
            rework_reviewer_packet_id,
            queue_packets,
            queue_ids,
        )
        deps.set_wave_progression_status(
            feature_id=runtime.feature_id,
            wave_progression=state.wave_progression,
            wave_id=wave_id,
            status="running",
        )
        state.packet_results["wave_progression"] = [dict(item) for item in state.wave_progression]
        return None
    if review_route.get("decision"):
        next_action = (
            "architect-user-decision-required"
            if review_route.get("route_classification") == REWORK_ROUTE_REQUIRES_USER_DECISION
            else "architect-planner-decomposition-required"
        )
        return _review_awaiting_architect(runtime, deps, state, wave_id, next_action)

    final_status = deps.final_failure(
        feature_id=runtime.feature_id,
        category="pipeline_invalid",
        next_action=f"missing-rework-packet:{packet_id}",
    )
    return _publish_final(deps, state, final_status)


def _resolve_rework_packets(
    deps: PipelineDeps,
    state: PipelineState,
    packet: dict,
    packet_id: str,
    target_packet_id: str,
    reviewer_decision: dict,
    review_route: dict,
    rework_object: object,
) -> tuple[list[dict], str]:
    if isinstance(rework_object, dict) and rework_object.get("packet_id"):
        direct_rework_packet = dict(rework_object)
        if (
            str(direct_rework_packet.get("rework_mode") or "") == REWORK_MODE_LIGHT_RESUME
            and str(direct_rework_packet.get("review_target_packet_id") or "") == str(target_packet_id)
        ):
            light_resume_followup = deps.build_light_resume_followup(
                source_reviewer_packet=packet,
                resumed_packet=dict(state.packets_by_id.get(target_packet_id) or {}),
                reasons=list((review_route.get("review") or {}).get("reasons") or reviewer_decision.get("reasons") or []),
                reviewer_packet_id=packet_id,
                packets_by_id=state.packets_by_id,
            )
            review_route["rework"] = light_resume_followup["rework"]
            review_route["light_resume_stage"] = True
            return list(light_resume_followup["packets"]), str(light_resume_followup["reviewer_packet_id"] or "")
        return deps.build_direct_rework_followup_packets(
            source_reviewer_packet=packet,
            direct_rework_packet=direct_rework_packet,
            target_packet_id=target_packet_id,
            packets_by_id=state.packets_by_id,
        )
    rework_bundle = rework_object or {}
    if not isinstance(rework_bundle, dict):
        return [], ""
    return [
        packet_obj
        for packet_obj in [
            rework_bundle.get("rework"),
            rework_bundle.get("verifier"),
            rework_bundle.get("reviewer"),
        ]
        if isinstance(packet_obj, dict) and packet_obj.get("packet_id")
    ], str(rework_bundle.get("reviewer", {}).get("packet_id") or "")


def _enqueue_rework_packets(
    deps: PipelineDeps,
    state: PipelineState,
    wave_id: str,
    packet_id: str,
    target_packet_id: str,
    rework_packets: list[dict],
    rework_reviewer_packet_id: str,
    queue_packets: list[dict],
    queue_ids: set[str],
) -> None:
    for rework_packet in rework_packets:
        rework_packet_id = str(rework_packet["packet_id"])
        state.packets_by_id[rework_packet_id] = rework_packet
        state.wave_packet_sets.setdefault(wave_id, set()).add(rework_packet_id)
        if state.review_routes[-1].get("light_resume_stage") is True and rework_packet_id == str(target_packet_id):
            state.completed_packet_ids.discard(rework_packet_id)
        if rework_packet_id not in queue_ids and rework_packet_id not in state.completed_packet_ids:
            deps.append_unique_packet(queue_packets, rework_packet)
            queue_ids.add(rework_packet_id)
    if not rework_reviewer_packet_id:
        return
    for queued_packet in queue_packets:
        if str(queued_packet.get("role") or "") != "architect":
            continue
        if str(queued_packet.get("wave_id") or "") != wave_id:
            continue
        dependencies = list(queued_packet.get("dependencies") or [])
        if packet_id in dependencies and rework_reviewer_packet_id not in dependencies:
            queued_packet["dependencies"] = [*dependencies, rework_reviewer_packet_id]
            deps.update_record(
                "packets",
                "packets",
                "packet_id",
                str(queued_packet["packet_id"]),
                {"dependencies": queued_packet["dependencies"]},
            )


def _review_awaiting_architect(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    wave_id: str,
    next_action: str,
) -> dict:
    review_route = state.review_routes[-1]
    reasons = list((review_route.get("review") or {}).get("reasons") or [])
    deps.set_wave_progression_status(
        feature_id=runtime.feature_id,
        wave_progression=state.wave_progression,
        wave_id=wave_id,
        status="blocked",
        reasons=reasons,
    )
    state.packet_results["wave_progression"] = [dict(item) for item in state.wave_progression]
    feature_record = deps.mark_feature_status(runtime.feature_id, FeatureStatus.ARCHITECT_READY)
    final_status = {
        "feature": feature_record,
        "has_failures": False,
        "final_outcome": "awaiting_architect",
        "user_facing_status": FeatureStatus.ARCHITECT_READY.value,
        "user_summary": deps.final_user_summary(
            outcome="awaiting_architect",
            status=FeatureStatus.ARCHITECT_READY.value,
            summary=str(feature_record.get("summary") or runtime.summary),
            next_action=next_action,
            reasons=reasons,
        ),
        "next_action": next_action,
        "reasons": reasons,
        "wave_progression": [dict(item) for item in state.wave_progression],
    }
    deps.notify_feature_event(
        feature_id=runtime.feature_id,
        title=str(state.seeded["feature"].get("title") or runtime.title),
        status=FeatureStatus.ARCHITECT_READY.value,
        summary=final_status["user_summary"],
        blockers=reasons,
        next_action=next_action,
    )
    return _publish_final(deps, state, final_status)


# START_FUNCTION_CONTRACT
# name: handle_architect_packet
# purpose: Resolve architect wave-gate decisions and finalize blocked or rework-required wave branches.
# inputs: Runtime, dependencies, state, packet id, packet run, and wave id.
# returns: Optional final result for non-accepted wave-gate decisions.
# side_effects: Records wave routes, updates wave progression, sends notifications, and publishes artifacts.
# emitted_logs: Delegated Prefect task logs.
# error_behavior: Preserves accepted, rework_required, and blocked architect wave-gate behavior.
# END_FUNCTION_CONTRACT
def handle_architect_packet(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    *,
    packet_id: str,
    packet_run: dict,
    wave_id: str,
) -> dict | None:
    current_wave_reasons = (
        runtime.wave_reasons_script[state.wave_decision_index]
        if runtime.wave_reasons_script and state.wave_decision_index < len(runtime.wave_reasons_script)
        else runtime.wave_reasons
    )
    current_wave_verdict = (
        runtime.wave_verdict_script[state.wave_decision_index]
        if runtime.wave_verdict_script and state.wave_decision_index < len(runtime.wave_verdict_script)
        else runtime.wave_verdict
    )
    wave_decision = deps.resolve_wave_decision_task(
        packet_run,
        current_wave_verdict,
        current_wave_reasons,
        runtime.prefer_agent_output,
    )
    state.wave_decision_index += 1
    with deps.tags(f"wave:{wave_id}", "role:architect"):
        wave_route = deps.route_architect_wave_verdict_task(runtime.feature_id, wave_id, packet_id, wave_decision)
    wave_route["wave_progress"] = _wave_progress(state, wave_id)
    state.wave_routes.append(wave_route)
    state.packet_results[deps.packet_result_key("wave", packet_id)] = wave_route
    deps.publish_feature_artifacts_task(
        state.seeded["feature"],
        state.packet_results,
        _last_verification(state),
        _last_review(state),
        wave_route,
        None,
    )
    state.completed_packet_ids.add(packet_id)
    if wave_route["wave_verdict"] == WaveVerdict.ACCEPTED.value:
        deps.set_wave_progression_status(
            feature_id=runtime.feature_id,
            wave_progression=state.wave_progression,
            wave_id=wave_id,
            status="accepted",
        )
        wave_route["wave_progress"] = _wave_progress(state, wave_id)
        state.packet_results["wave_progression"] = [dict(item) for item in state.wave_progression]
        return None
    return _finalize_architect_block(runtime, deps, state, wave_id, wave_route)


def _wave_progress(state: PipelineState, wave_id: str) -> dict:
    return next(
        (dict(item) for item in state.wave_progression if str(item.get("wave_id") or "") == wave_id),
        {},
    )


def _finalize_architect_block(
    runtime: PipelineRuntime,
    deps: PipelineDeps,
    state: PipelineState,
    wave_id: str,
    wave_route: dict,
) -> dict:
    reasons = list((wave_route.get("wave_review") or {}).get("reasons") or [])
    deps.set_wave_progression_status(
        feature_id=runtime.feature_id,
        wave_progression=state.wave_progression,
        wave_id=wave_id,
        status="blocked",
        reasons=reasons,
    )
    wave_route["wave_progress"] = _wave_progress(state, wave_id)
    state.packet_results["wave_progression"] = [dict(item) for item in state.wave_progression]
    if wave_route["wave_verdict"] == WaveVerdict.REWORK_REQUIRED.value:
        feature_record = deps.mark_feature_status(
            runtime.feature_id,
            FeatureStatus.IN_PROGRESS,
            blocker_reasons=reasons,
        )
        final_status = {
            "feature": feature_record,
            "has_failures": False,
            "final_outcome": "rework_required",
            "user_facing_status": FeatureStatus.IN_PROGRESS.value,
            "user_summary": deps.final_user_summary(
                outcome="rework_required",
                status=FeatureStatus.IN_PROGRESS.value,
                summary=str(feature_record.get("summary") or runtime.summary),
                next_action=f"architect-wave-rework-required:{wave_id}",
                reasons=reasons,
            ),
            "next_action": f"architect-wave-rework-required:{wave_id}",
            "reasons": reasons,
            "wave_progression": [dict(item) for item in state.wave_progression],
        }
        deps.notify_feature_event(
            feature_id=runtime.feature_id,
            title=str(state.seeded["feature"].get("title") or runtime.title),
            status=FeatureStatus.IN_PROGRESS.value,
            summary=final_status["user_summary"],
            wave_id=wave_id,
            blockers=reasons,
            next_action=final_status["next_action"],
        )
    else:
        final_status = deps.final_failure(
            feature_id=runtime.feature_id,
            category="product_blocked",
            next_action=f"architect-wave-blocked:{wave_id}",
            reasons=reasons,
        )
    deps.publish_feature_artifacts_task(
        state.seeded["feature"],
        state.packet_results,
        _last_verification(state),
        _last_review(state),
        wave_route,
        final_status,
    )
    return pipeline_return(state, final_status)
