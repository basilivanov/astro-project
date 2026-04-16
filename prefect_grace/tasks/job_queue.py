from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from prefect_grace.tasks.state_store import find_record, load_state, update_state

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PENDING = "pending"
JOB_STATUS_SCHEDULED = "scheduled"
JOB_STATUS_DISPATCHING = "dispatching"
JOB_STATUS_SUBMITTED = "submitted"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_AWAITING_COMMIT = "awaiting_commit"
JOB_STATUS_ACCEPTED = "accepted"
JOB_STATUS_BLOCKED = "blocked"
JOB_STATUS_REWORK_REQUIRED = "rework_required"
JOB_STATUS_ENVIRONMENT_BLOCKED = "environment_blocked"
JOB_STATUS_FAILED = "failed"

JOB_READY_STATUSES = {JOB_STATUS_QUEUED, JOB_STATUS_SCHEDULED}
JOB_ACTIVE_STATUSES = {JOB_STATUS_DISPATCHING, JOB_STATUS_SUBMITTED, JOB_STATUS_RUNNING}
JOB_ADVANCING_SEQUENCE_STATUSES = {
    JOB_STATUS_AWAITING_COMMIT,
    JOB_STATUS_ACCEPTED,
    JOB_STATUS_BLOCKED,
    JOB_STATUS_REWORK_REQUIRED,
    JOB_STATUS_ENVIRONMENT_BLOCKED,
}
JOB_TERMINAL_STATUSES = JOB_ADVANCING_SEQUENCE_STATUSES | {JOB_STATUS_FAILED}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_queue_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    normalized = dict(payload or {})
    normalized["jobs"] = list(normalized.get("jobs") or [])
    normalized["sequences"] = list(normalized.get("sequences") or [])
    feature_locks = normalized.get("feature_locks") or {}
    normalized["feature_locks"] = (
        {str(key): dict(value or {}) for key, value in dict(feature_locks).items() if str(key).strip()}
        if isinstance(feature_locks, dict)
        else {}
    )
    return normalized


def _sequence_position(job: dict[str, Any]) -> tuple[int | None, int | None]:
    position_raw = job.get("sequence_position")
    total_raw = job.get("sequence_total")
    try:
        position = int(position_raw) if position_raw not in (None, "") else None
    except (TypeError, ValueError):
        position = None
    try:
        total = int(total_raw) if total_raw not in (None, "") else None
    except (TypeError, ValueError):
        total = None
    return position, total


def _sequence_label_ru(job: dict[str, Any]) -> str | None:
    position, total = _sequence_position(job)
    if position and total:
        return f"Фича {position}/{total}"
    return None


def _has_next_sequence_item(job: dict[str, Any]) -> bool:
    position, total = _sequence_position(job)
    return bool(position and total and position < total)


def _status_label_ru(status: str) -> str:
    normalized = str(status or "").strip().lower()
    return {
        JOB_STATUS_QUEUED: "запланирована",
        JOB_STATUS_PENDING: "запланирована",
        JOB_STATUS_SCHEDULED: "запланирована",
        JOB_STATUS_DISPATCHING: "в работе",
        JOB_STATUS_SUBMITTED: "в работе",
        JOB_STATUS_RUNNING: "в работе",
        JOB_STATUS_AWAITING_COMMIT: "ждёт коммита",
        JOB_STATUS_ACCEPTED: "принята",
        JOB_STATUS_BLOCKED: "заблокирована",
        JOB_STATUS_REWORK_REQUIRED: "требует доработки",
        JOB_STATUS_ENVIRONMENT_BLOCKED: "заблокирована средой",
        JOB_STATUS_FAILED: "требует внимания",
    }.get(normalized, normalized or "обновление")


def _status_summary_ru(job: dict[str, Any]) -> str:
    normalized = str(job.get("status") or "").strip().lower()
    label = str(job.get("sequence_label_ru") or "").strip() or _sequence_label_ru(job) or f"Фича {str(job.get('feature_id') or '').strip()}".strip()
    move_next = " Перехожу к следующей." if normalized in JOB_ADVANCING_SEQUENCE_STATUSES and _has_next_sequence_item(job) else ""
    if normalized in {JOB_STATUS_QUEUED, JOB_STATUS_PENDING}:
        return f"{label}: запланирована и ждёт своей очереди."
    if normalized == JOB_STATUS_SCHEDULED:
        return f"{label}: запланирована."
    if normalized in JOB_ACTIVE_STATUSES:
        return f"{label}: в работе."
    if normalized == JOB_STATUS_AWAITING_COMMIT:
        return f"{label}: ждёт коммита.{move_next}"
    if normalized == JOB_STATUS_ACCEPTED:
        return f"{label}: принята.{move_next}"
    if normalized == JOB_STATUS_BLOCKED:
        return f"{label}: заблокирована.{move_next}"
    if normalized == JOB_STATUS_REWORK_REQUIRED:
        return f"{label}: требует доработки.{move_next}"
    if normalized == JOB_STATUS_ENVIRONMENT_BLOCKED:
        return f"{label}: заблокирована средой.{move_next}"
    if normalized == JOB_STATUS_FAILED:
        return f"{label}: запуск завершился с ошибкой."
    return f"{label}: {_status_label_ru(normalized)}."


def _decorate_job(record: dict[str, Any]) -> dict[str, Any]:
    sequence_label_ru = _sequence_label_ru(record)
    status = str(record.get("status") or "")
    decorated = dict(record)
    decorated["sequence_label_ru"] = sequence_label_ru
    decorated["status_label_ru"] = _status_label_ru(status)
    decorated["status_summary_ru"] = _status_summary_ru({**decorated, "sequence_label_ru": sequence_label_ru})
    return decorated


def _decorate_sequence(record: dict[str, Any]) -> dict[str, Any]:
    decorated = dict(record)
    feature_ids = [str(item).strip() for item in list(decorated.get("feature_ids") or []) if str(item).strip()]
    decorated["feature_ids"] = feature_ids
    total = len(feature_ids)
    try:
        current_index = int(decorated.get("current_index") or 0)
    except (TypeError, ValueError):
        current_index = 0
    status = str(decorated.get("status") or "").strip().lower()
    if status == "completed":
        current_label_ru = f"Фича {total}/{total}" if total else None
        summary_ru = "Последовательность завершена."
    elif total and current_index < total:
        current_label_ru = f"Фича {current_index + 1}/{total}"
        if status == JOB_STATUS_FAILED:
            summary_ru = f"{current_label_ru}: требует внимания."
        elif status == JOB_STATUS_RUNNING:
            summary_ru = f"{current_label_ru}: в работе."
        else:
            summary_ru = f"{current_label_ru}: запланирована."
    else:
        current_label_ru = None
        summary_ru = "Последовательность ожидает обновления."
    decorated["current_label_ru"] = current_label_ru
    decorated["summary_ru"] = summary_ru
    return decorated


def _active_feature_locks(jobs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    locks: dict[str, dict[str, Any]] = {}
    for job in jobs:
        status = str(job.get("status") or "").strip().lower()
        feature_id = str(job.get("feature_id") or "").strip()
        if status not in JOB_ACTIVE_STATUSES or not feature_id:
            continue
        locks[feature_id] = {
            "job_id": str(job.get("job_id") or ""),
            "sequence_id": str(job.get("sequence_id") or "").strip() or None,
            "locked_at": str(job.get("started_at") or _now()),
        }
    return locks


def _job_record(
    *,
    feature_id: str,
    title: str,
    summary: str,
    implementation_title: str | None = None,
    implementation_summary: str | None = None,
    execute: bool = False,
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
    prefer_agent_output: bool = True,
    run_planner: bool | None = None,
    agent_workdir: str | None = None,
    agent_sandbox: str | None = None,
    business_context: dict[str, Any] | None = None,
    planner_contract: dict[str, Any] | None = None,
    brief_path: str | None = None,
    commit_hash: str | None = None,
    status: str = JOB_STATUS_SCHEDULED,
    sequence_id: str | None = None,
    sequence_index: int | None = None,
    sequence_total: int | None = None,
    sequence_feature_ids: list[str] | None = None,
) -> dict[str, Any]:
    record = {
        "job_id": f"job-{uuid.uuid4()}",
        "job_type": "feature_pipeline",
        "feature_id": feature_id,
        "title": title,
        "summary": summary,
        "implementation_title": implementation_title or "Live Implementation Packet",
        "implementation_summary": implementation_summary
        or "Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.",
        "execute": bool(execute),
        "timeout_seconds": int(timeout_seconds),
        "verifier_backend_profile": verifier_backend_profile,
        "verifier_frontend_profile": verifier_frontend_profile,
        "verifier_frontend_commands": list(verifier_frontend_commands or []),
        "verifier_observability_profile": verifier_observability_profile,
        "verifier_observability_commands": list(verifier_observability_commands or []),
        "verifier_artifact_globs": list(verifier_artifact_globs or []),
        "verifier_touches_frontend": bool(verifier_touches_frontend),
        "verifier_requires_frontend_visual": bool(verifier_requires_frontend_visual),
        "verifier_include_day_live_canary": bool(verifier_include_day_live_canary),
        "prefer_agent_output": bool(prefer_agent_output),
        "run_planner": run_planner if run_planner is not None else None,
        "agent_workdir": agent_workdir,
        "agent_sandbox": agent_sandbox,
        "business_context": dict(business_context or {}),
        "planner_contract": dict(planner_contract or {}) if planner_contract else None,
        "brief_path": brief_path,
        "commit_hash": str(commit_hash or "").strip() or None,
        "status": str(status or JOB_STATUS_SCHEDULED),
        "flow_run_id": None,
        "deployment_id": None,
        "submitted_at": _now(),
        "started_at": None,
        "finished_at": None,
        "error": None,
        "sequence_id": str(sequence_id or "").strip() or None,
        "sequence_index": int(sequence_index) if sequence_index is not None else None,
        "sequence_position": (int(sequence_index) + 1) if sequence_index is not None else None,
        "sequence_total": int(sequence_total) if sequence_total is not None else None,
        "sequence_feature_ids": list(sequence_feature_ids or []),
    }
    return _decorate_job(record)


def list_jobs() -> list[dict[str, Any]]:
    payload = _normalize_queue_payload(load_state("job_queue"))
    return [_decorate_job(dict(item)) for item in list(payload.get("jobs") or [])]


def list_sequences() -> list[dict[str, Any]]:
    payload = _normalize_queue_payload(load_state("job_queue"))
    return [_decorate_sequence(dict(item)) for item in list(payload.get("sequences") or [])]


def enqueue_feature_job(
    *,
    feature_id: str,
    title: str,
    summary: str,
    implementation_title: str | None = None,
    implementation_summary: str | None = None,
    execute: bool = False,
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
    prefer_agent_output: bool = True,
    run_planner: bool | None = None,
    agent_workdir: str | None = None,
    agent_sandbox: str | None = None,
    business_context: dict[str, Any] | None = None,
    planner_contract: dict[str, Any] | None = None,
    brief_path: str | None = None,
    commit_hash: str | None = None,
    initial_status: str = JOB_STATUS_SCHEDULED,
) -> dict[str, Any]:
    record = _job_record(
        feature_id=feature_id,
        title=title,
        summary=summary,
        implementation_title=implementation_title,
        implementation_summary=implementation_summary,
        execute=execute,
        timeout_seconds=timeout_seconds,
        verifier_backend_profile=verifier_backend_profile,
        verifier_frontend_profile=verifier_frontend_profile,
        verifier_frontend_commands=verifier_frontend_commands,
        verifier_observability_profile=verifier_observability_profile,
        verifier_observability_commands=verifier_observability_commands,
        verifier_artifact_globs=verifier_artifact_globs,
        verifier_touches_frontend=verifier_touches_frontend,
        verifier_requires_frontend_visual=verifier_requires_frontend_visual,
        verifier_include_day_live_canary=verifier_include_day_live_canary,
        prefer_agent_output=prefer_agent_output,
        run_planner=run_planner,
        agent_workdir=agent_workdir,
        agent_sandbox=agent_sandbox,
        business_context=business_context,
        planner_contract=planner_contract,
        brief_path=brief_path,
        commit_hash=commit_hash,
        status=initial_status,
    )

    def mutator(payload: dict[str, Any]) -> dict[str, Any]:
        normalized = _normalize_queue_payload(payload)
        items = list(normalized.get("jobs") or [])
        items.append(record)
        normalized["jobs"] = items
        normalized["feature_locks"] = _active_feature_locks(items)
        return normalized

    update_state("job_queue", mutator)
    return record


def enqueue_feature_sequence(
    *,
    items: list[dict[str, Any]],
    execute: bool = False,
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
    prefer_agent_output: bool = True,
    run_planner: bool | None = None,
    agent_workdir: str | None = None,
    agent_sandbox: str | None = None,
    planner_contract: dict[str, Any] | None = None,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    ordered_items = [dict(item or {}) for item in items if isinstance(item, dict)]
    if not ordered_items:
        raise ValueError("Feature sequence requires at least one feature item.")

    feature_ids = [str(item.get("feature_id") or "").strip() for item in ordered_items]
    if any(not feature_id for feature_id in feature_ids):
        raise ValueError("Feature sequence items must include non-empty feature_id values.")

    sequence_id = f"sequence-{uuid.uuid4()}"
    submitted_at = _now()
    total = len(ordered_items)
    jobs: list[dict[str, Any]] = []
    sequence_record = _decorate_sequence(
        {
            "sequence_id": sequence_id,
            "feature_ids": feature_ids,
            "current_index": 0,
            "current_job_id": None,
            "status": JOB_STATUS_SCHEDULED,
            "submitted_at": submitted_at,
            "started_at": None,
            "finished_at": None,
            "last_completed_job_id": None,
            "last_completed_status": None,
        }
    )

    for index, item in enumerate(ordered_items):
        jobs.append(
            _job_record(
                feature_id=str(item["feature_id"]).strip(),
                title=str(item.get("title") or "").strip(),
                summary=str(item.get("summary") or "").strip(),
                implementation_title=str(item.get("implementation_title") or "").strip() or None,
                implementation_summary=str(item.get("implementation_summary") or "").strip() or None,
                execute=execute,
                timeout_seconds=timeout_seconds,
                verifier_backend_profile=item.get("verifier_backend_profile", verifier_backend_profile),
                verifier_frontend_profile=item.get("verifier_frontend_profile", verifier_frontend_profile),
                verifier_frontend_commands=list(item.get("verifier_frontend_commands") or verifier_frontend_commands or []),
                verifier_observability_profile=item.get("verifier_observability_profile", verifier_observability_profile),
                verifier_observability_commands=list(item.get("verifier_observability_commands") or verifier_observability_commands or []),
                verifier_artifact_globs=list(item.get("verifier_artifact_globs") or verifier_artifact_globs or []),
                verifier_touches_frontend=bool(item.get("verifier_touches_frontend", verifier_touches_frontend)),
                verifier_requires_frontend_visual=bool(
                    item.get("verifier_requires_frontend_visual", verifier_requires_frontend_visual)
                ),
                verifier_include_day_live_canary=bool(
                    item.get("verifier_include_day_live_canary", verifier_include_day_live_canary)
                ),
                prefer_agent_output=bool(item.get("prefer_agent_output", prefer_agent_output)),
                run_planner=item.get("run_planner", run_planner),
                agent_workdir=str(item.get("agent_workdir") or agent_workdir or "").strip() or None,
                agent_sandbox=str(item.get("agent_sandbox") or agent_sandbox or "").strip() or None,
                business_context=dict(item.get("business_context") or {}),
                planner_contract=dict(item.get("planner_contract") or planner_contract or {})
                if item.get("planner_contract") or planner_contract
                else None,
                brief_path=str(item.get("brief_path") or "").strip() or None,
                commit_hash=str(item.get("commit_hash") or commit_hash or "").strip() or None,
                status=JOB_STATUS_SCHEDULED if index == 0 else JOB_STATUS_PENDING,
                sequence_id=sequence_id,
                sequence_index=index,
                sequence_total=total,
                sequence_feature_ids=feature_ids,
            )
        )

    def mutator(payload: dict[str, Any]) -> dict[str, Any]:
        normalized = _normalize_queue_payload(payload)
        stored_jobs = list(normalized.get("jobs") or [])
        stored_jobs.extend(jobs)
        normalized["jobs"] = stored_jobs
        sequences = list(normalized.get("sequences") or [])
        sequence_with_job = dict(sequence_record)
        sequence_with_job["current_job_id"] = jobs[0]["job_id"]
        sequences.append(_decorate_sequence(sequence_with_job))
        normalized["sequences"] = sequences
        normalized["feature_locks"] = _active_feature_locks(stored_jobs)
        return normalized

    update_state("job_queue", mutator)
    return {
        "sequence_id": sequence_id,
        "feature_ids": feature_ids,
        "current_index": 0,
        "status": JOB_STATUS_SCHEDULED,
        "jobs": jobs,
        "summary_ru": f"Фича 1/{total}: запланирована." if total else "Последовательность создана.",
    }


def enqueue_canonical_feature_sequence(
    *,
    feature_ids: list[str],
    implementation_title: str | None = None,
    implementation_summary: str | None = None,
    execute: bool = False,
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
    prefer_agent_output: bool = True,
    run_planner: bool | None = None,
    agent_workdir: str | None = None,
    agent_sandbox: str | None = None,
    planner_contract: dict[str, Any] | None = None,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for feature_id in feature_ids:
        normalized_feature_id = str(feature_id or "").strip()
        if not normalized_feature_id:
            raise ValueError("Feature sequence feature_ids must be non-empty strings.")
        feature = find_record("features", "features", "feature_id", normalized_feature_id)
        business_context = dict(feature.get("business_context") or {})
        items.append(
            {
                "feature_id": normalized_feature_id,
                "title": str(feature.get("title") or "").strip(),
                "summary": str(feature.get("summary") or "").strip(),
                "implementation_title": implementation_title,
                "implementation_summary": implementation_summary,
                "business_context": business_context,
                "brief_path": str(business_context.get("brief_path") or "").strip() or None,
            }
        )

    return enqueue_feature_sequence(
        items=items,
        execute=execute,
        timeout_seconds=timeout_seconds,
        verifier_backend_profile=verifier_backend_profile,
        verifier_frontend_profile=verifier_frontend_profile,
        verifier_frontend_commands=verifier_frontend_commands,
        verifier_observability_profile=verifier_observability_profile,
        verifier_observability_commands=verifier_observability_commands,
        verifier_artifact_globs=verifier_artifact_globs,
        verifier_touches_frontend=verifier_touches_frontend,
        verifier_requires_frontend_visual=verifier_requires_frontend_visual,
        verifier_include_day_live_canary=verifier_include_day_live_canary,
        prefer_agent_output=prefer_agent_output,
        run_planner=run_planner,
        agent_workdir=agent_workdir,
        agent_sandbox=agent_sandbox,
        planner_contract=planner_contract,
        commit_hash=commit_hash,
    )


def claim_next_job() -> dict[str, Any] | None:
    claimed: dict[str, Any] | None = None

    def mutator(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal claimed
        normalized = _normalize_queue_payload(payload)
        items = list(normalized.get("jobs") or [])
        sequences = list(normalized.get("sequences") or [])
        if any(str(item.get("status") or "").strip().lower() in JOB_ACTIVE_STATUSES for item in items):
            normalized["feature_locks"] = _active_feature_locks(items)
            return normalized

        prioritized_sequence_job_ids: list[str] = []
        active_sequence_ids = {
            str(item.get("sequence_id") or "").strip()
            for item in items
            if str(item.get("status") or "").strip().lower() in JOB_READY_STATUSES | JOB_ACTIVE_STATUSES
            and str(item.get("sequence_id") or "").strip()
        }
        for sequence in sequences:
            sequence_status = str(sequence.get("status") or "").strip().lower()
            if sequence_status != JOB_STATUS_SCHEDULED:
                continue
            try:
                current_index = int(sequence.get("current_index") or 0)
            except (TypeError, ValueError):
                current_index = 0
            if current_index <= 0:
                continue
            current_job_id = str(sequence.get("current_job_id") or "").strip()
            if current_job_id:
                prioritized_sequence_job_ids.append(current_job_id)

        candidate_ids = prioritized_sequence_job_ids + [
            str(item.get("job_id") or "")
            for item in items
            if str(item.get("status") or "").strip().lower() in JOB_READY_STATUSES
            and (
                not str(item.get("sequence_id") or "").strip()
                or str(item.get("sequence_id") or "").strip() in active_sequence_ids
            )
        ]
        active_locks = _active_feature_locks(items)
        now = _now()
        for job_id in candidate_ids:
            for index, item in enumerate(items):
                if str(item.get("job_id") or "") != job_id:
                    continue
                status = str(item.get("status") or "").strip().lower()
                feature_id = str(item.get("feature_id") or "").strip()
                if status not in JOB_READY_STATUSES or not feature_id or feature_id in active_locks:
                    break
                claimed = _decorate_job(
                    {
                        **item,
                        "status": JOB_STATUS_DISPATCHING,
                        "started_at": now,
                        "error": None,
                    }
                )
                items[index] = claimed
                for sequence_index, sequence in enumerate(sequences):
                    if str(sequence.get("sequence_id") or "") != str(claimed.get("sequence_id") or ""):
                        continue
                    updated_sequence = dict(sequence)
                    updated_sequence["status"] = JOB_STATUS_RUNNING
                    updated_sequence["current_job_id"] = claimed["job_id"]
                    updated_sequence["started_at"] = str(updated_sequence.get("started_at") or now)
                    updated_sequence["updated_at"] = now
                    sequences[sequence_index] = _decorate_sequence(updated_sequence)
                    break
                normalized["jobs"] = items
                normalized["sequences"] = sequences
                normalized["feature_locks"] = _active_feature_locks(items)
                return normalized
        normalized["jobs"] = items
        normalized["sequences"] = sequences
        normalized["feature_locks"] = _active_feature_locks(items)
        return normalized

    update_state("job_queue", mutator)
    return claimed


def update_job(job_id: str, **updates: Any) -> dict[str, Any]:
    updated: dict[str, Any] = {}

    def mutator(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal updated
        normalized = _normalize_queue_payload(payload)
        items = list(normalized.get("jobs") or [])
        sequences = list(normalized.get("sequences") or [])
        now = _now()
        for index, item in enumerate(items):
            if str(item.get("job_id")) != job_id:
                continue
            previous_status = str(item.get("status") or "").strip().lower()
            updated = _decorate_job({**item, **updates})
            items[index] = updated
            sequence_id = str(updated.get("sequence_id") or "").strip()
            next_sequence_job_id: str | None = None
            if sequence_id:
                for sequence_index, sequence in enumerate(sequences):
                    if str(sequence.get("sequence_id") or "").strip() != sequence_id:
                        continue
                    sequence_record = dict(sequence)
                    current_status = str(updated.get("status") or "").strip().lower()
                    try:
                        sequence_position = int(updated.get("sequence_index") or 0)
                    except (TypeError, ValueError):
                        sequence_position = 0
                    feature_ids = [str(value).strip() for value in list(sequence_record.get("feature_ids") or []) if str(value).strip()]
                    total = len(feature_ids)
                    sequence_record["updated_at"] = now
                    if current_status in JOB_ACTIVE_STATUSES:
                        sequence_record["status"] = JOB_STATUS_RUNNING
                        sequence_record["current_index"] = sequence_position
                        sequence_record["current_job_id"] = updated["job_id"]
                        sequence_record["started_at"] = str(sequence_record.get("started_at") or now)
                    elif current_status in JOB_ADVANCING_SEQUENCE_STATUSES and previous_status not in JOB_TERMINAL_STATUSES:
                        next_index = sequence_position + 1
                        sequence_record["last_completed_job_id"] = updated["job_id"]
                        sequence_record["last_completed_status"] = current_status
                        if next_index < total:
                            sequence_record["status"] = JOB_STATUS_SCHEDULED
                            sequence_record["current_index"] = next_index
                            for next_job_index, queued_job in enumerate(items):
                                if str(queued_job.get("sequence_id") or "").strip() != sequence_id:
                                    continue
                                try:
                                    queued_position = int(queued_job.get("sequence_index") or -1)
                                except (TypeError, ValueError):
                                    queued_position = -1
                                if queued_position != next_index:
                                    continue
                                next_job_status = str(queued_job.get("status") or "").strip().lower()
                                if next_job_status in {JOB_STATUS_PENDING, JOB_STATUS_QUEUED, JOB_STATUS_SCHEDULED}:
                                    queued_job = _decorate_job({**queued_job, "status": JOB_STATUS_SCHEDULED})
                                    items[next_job_index] = queued_job
                                next_sequence_job_id = str(queued_job.get("job_id") or "").strip() or None
                                sequence_record["current_job_id"] = next_sequence_job_id
                                break
                        else:
                            sequence_record["status"] = "completed"
                            sequence_record["current_index"] = total
                            sequence_record["current_job_id"] = None
                            sequence_record["finished_at"] = now
                    elif current_status == JOB_STATUS_FAILED and previous_status not in JOB_TERMINAL_STATUSES:
                        sequence_record["status"] = JOB_STATUS_FAILED
                        sequence_record["current_index"] = sequence_position
                        sequence_record["current_job_id"] = updated["job_id"]
                    sequences[sequence_index] = _decorate_sequence(sequence_record)
                    break
            updated = _decorate_job(
                {
                    **updated,
                    "sequence_next_job_id": next_sequence_job_id,
                }
            )
            items[index] = updated
            normalized["jobs"] = items
            normalized["sequences"] = sequences
            normalized["feature_locks"] = _active_feature_locks(items)
            return normalized
        raise KeyError(f"No queued job with job_id={job_id}")

    update_state("job_queue", mutator)
    return updated
