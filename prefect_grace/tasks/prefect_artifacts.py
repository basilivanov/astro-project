from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import re

try:
    from prefect.artifacts import create_markdown_artifact
except ModuleNotFoundError:  # pragma: no cover - local fallback mode
    create_markdown_artifact = None


def _bullet(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item and str(item).strip()]
    return "\n".join(f"- {item}" for item in cleaned) if cleaned else "- none"


def _artifact_key(*parts: object) -> str:
    raw = "-".join(str(part) for part in parts if part not in (None, ""))
    key = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
    return re.sub(r"-+", "-", key) or "grace-artifact"


def _artifact_description(title: str, **fields: object) -> str:
    details = [f"{name}={value}" for name, value in fields.items() if value not in (None, "", [], {})]
    if not details:
        return title
    return f"{title} ({', '.join(details)})"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_none_\n"
    header_row = "| " + " | ".join(headers) + " |"
    divider_row = "| " + " | ".join("---" for _ in headers) + " |"
    body_rows = ["| " + " | ".join(cell.replace("\n", "<br>") for cell in row) + " |" for row in rows]
    return "\n".join([header_row, divider_row, *body_rows]) + "\n"


def _packet_run_lines(packet_results: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for name, payload in packet_results.items():
        if not isinstance(payload, dict):
            continue
        returncode = payload.get("returncode", "-")
        runner = payload.get("launcher") or payload.get("runner") or "n/a"
        last_message = payload.get("last_message_path") or "-"
        lines.append(f"{name}: rc={returncode}, runner={runner}, last_message={last_message}")
    return lines


def _business_context_lines(context: dict[str, Any]) -> list[str]:
    if not context:
        return ["none"]
    lines: list[str] = []
    brief_path = context.get("brief_path")
    if brief_path:
        lines.append(f"brief_path: {brief_path}")
    for key in ["scope", "acceptance_criteria", "non_goals", "visual_expectations", "open_decisions"]:
        values = list(context.get(key) or [])
        if values:
            lines.append(f"{key}: {'; '.join(str(value) for value in values)}")
    return lines or ["none"]


def _feature_summary_markdown(
    *,
    feature: dict[str, Any],
    verification: dict[str, Any] | None,
    review_route: dict[str, Any] | None,
    wave_route: dict[str, Any] | None,
    final_status: dict[str, Any] | None,
    packet_results: dict[str, Any],
) -> str:
    final_feature = dict((final_status or {}).get("feature") or feature)
    review = dict((review_route or {}).get("review") or {})
    wave_review = dict((wave_route or {}).get("wave_review") or {})
    feature_id = final_feature.get("feature_id") or feature.get("feature_id")
    lines = [
        f"# GRACE Feature Snapshot: {feature_id}",
        "",
        f"- updated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- feature_id: {feature_id}",
        f"- title: {final_feature.get('title') or feature.get('title')}",
        f"- status: {final_feature.get('status') or feature.get('status')}",
        f"- next_action: {(final_status or {}).get('next_action', 'n/a')}",
        f"- feature_dir: {final_feature.get('feature_dir', '-')}",
        f"- wave_plan_path: {final_feature.get('wave_plan_path', '-')}",
        f"- brief_path: {(final_feature.get('business_context') or {}).get('brief_path', '-')}",
        f"- architect_slice_dir: {final_feature.get('architect_slice_dir', '-')}",
        f"- architect_manifest_path: {final_feature.get('architect_manifest_path', '-')}",
        f"- requirements_slice_path: {final_feature.get('requirements_slice_path', '-')}",
        f"- development_plan_slice_path: {final_feature.get('development_plan_slice_path', '-')}",
        f"- verification_matrix_slice_path: {final_feature.get('verification_matrix_slice_path', '-')}",
        f"- knowledge_graph_slice_path: {final_feature.get('knowledge_graph_slice_path', '-')}",
        "",
        "## Business Context",
        _bullet(_business_context_lines(final_feature.get('business_context') or {})),
        "",
        "## Packet Runs",
        _bullet(_packet_run_lines(packet_results)),
    ]
    if verification:
        lines.extend(
            [
                "",
                "## Verification",
                _bullet(
                    [
                        f"packet_id: {verification.get('packet_id', '-')}",
                        f"test_verdict: {verification.get('test_verdict', '-')}",
                        f"observability_verdict: {verification.get('observability_verdict', '-')}",
                        f"frontend_visual_verdict: {verification.get('frontend_visual_verdict', '-')}",
                        f"verification_path: {verification.get('verification_path', '-')}",
                    ]
                ),
            ]
        )
    if review:
        lines.extend(
            [
                "",
                "## Reviewer Gate",
                _bullet(
                    [
                        f"verdict: {review.get('verdict', '-')}",
                        f"follow_up_action: {review.get('follow_up_action', '-')}",
                        f"review_path: {review.get('review_path', '-')}",
                    ]
                ),
            ]
        )
    if wave_review:
        lines.extend(
            [
                "",
                "## Architect Wave Gate",
                _bullet(
                    [
                        f"verdict: {wave_review.get('verdict', '-')}",
                        f"review_path: {wave_review.get('review_path', '-')}",
                    ]
                ),
            ]
        )
    return "\n".join(lines) + "\n"


def _verification_markdown(verification: dict[str, Any]) -> str:
    packet_id = verification.get("packet_id", "-")
    wave_id = str(packet_id).split("-")[3] if str(packet_id).count("-") >= 3 else "-"
    return "\n".join(
        [
            f"# Verifier Snapshot: {packet_id}",
            "",
            f"- packet_id: {packet_id}",
            f"- wave_id: {wave_id}",
            f"- test_verdict: {verification.get('test_verdict', '-')}",
            f"- observability_verdict: {verification.get('observability_verdict', '-')}",
            f"- frontend_visual_verdict: {verification.get('frontend_visual_verdict', '-')}",
            "",
            "## Commands Run",
            _bullet(list(verification.get("commands_run") or [])),
            "",
            "## Evidence Paths",
            _bullet(list(verification.get("evidence_paths") or [])),
            "",
            "## Blocking Issues",
            _bullet(list(verification.get("blocking_issues") or [])),
            "",
            f"- verification_path: {verification.get('verification_path', '-')}",
        ]
    ) + "\n"


def _review_markdown(review_route: dict[str, Any]) -> str:
    review = dict(review_route.get("review") or {})
    rework = dict(review_route.get("rework") or {})
    decision = dict(review_route.get("decision") or {})
    packet_id = review.get("packet_id", "-")
    wave_id = str(packet_id).split("-")[3] if str(packet_id).count("-") >= 3 else "-"
    return "\n".join(
        [
            f"# Reviewer Snapshot: {packet_id}",
            "",
            f"- packet_id: {packet_id}",
            f"- wave_id: {wave_id}",
            f"- verdict: {review.get('verdict', '-')}",
            f"- follow_up_action: {review.get('follow_up_action', '-')}",
            f"- review_path: {review.get('review_path', '-')}",
            "",
            "## Reasons",
            _bullet(list(review.get("reasons") or [])),
            "",
            "## Follow-up Objects",
            _bullet(
                [
                    f"rework_packet: {rework.get('packet_id', '-')}" if rework else "",
                    f"architect_decision: {decision.get('decision_id', '-')}" if decision else "",
                ]
            ),
        ]
    ) + "\n"


def _wave_markdown(wave_route: dict[str, Any]) -> str:
    review = dict(wave_route.get("wave_review") or {})
    return "\n".join(
        [
            f"# Architect Wave Snapshot: {review.get('architect_packet_id', '-')}",
            "",
            f"- feature_id: {review.get('feature_id', '-')}",
            f"- wave_id: {review.get('wave_id', '-')}",
            f"- verdict: {review.get('verdict', '-')}",
            f"- review_path: {review.get('review_path', '-')}",
            "",
            "## Reasons",
            _bullet(list(review.get("reasons") or [])),
        ]
    ) + "\n"


def publish_feature_artifacts(
    *,
    feature: dict[str, Any],
    packet_results: dict[str, Any],
    verification: dict[str, Any] | None = None,
    review_route: dict[str, Any] | None = None,
    wave_route: dict[str, Any] | None = None,
    final_status: dict[str, Any] | None = None,
) -> list[str]:
    if create_markdown_artifact is None:
        return []

    feature_id = str(feature.get("feature_id") or "unknown-feature")
    artifact_ids = [
        str(
            create_markdown_artifact(
                key=_artifact_key("grace-feature", feature_id),
                description=_artifact_description(
                    "Live GRACE feature snapshot",
                    feature_id=feature_id,
                    status=(final_status or {}).get("feature", {}).get("status") if isinstance((final_status or {}).get("feature"), dict) else feature.get("status"),
                ),
                markdown=_feature_summary_markdown(
                    feature=feature,
                    verification=verification,
                    review_route=review_route,
                    wave_route=wave_route,
                    final_status=final_status,
                    packet_results=packet_results,
                ),
            )
        )
    ]
    if verification:
        artifact_ids.append(
            str(
                    create_markdown_artifact(
                    key=_artifact_key("grace-verification", verification.get("packet_id", feature_id)),
                    description=_artifact_description(
                        "Verifier evidence snapshot",
                        packet_id=verification.get("packet_id"),
                        test=verification.get("test_verdict"),
                        obs=verification.get("observability_verdict"),
                    ),
                    markdown=_verification_markdown(verification),
                )
            )
        )
    if review_route and review_route.get("review"):
        artifact_ids.append(
            str(
                    create_markdown_artifact(
                    key=_artifact_key("grace-review", review_route["review"].get("packet_id", feature_id)),
                    description=_artifact_description(
                        "Reviewer gate snapshot",
                        packet_id=review_route["review"].get("packet_id"),
                        verdict=review_route["review"].get("verdict"),
                    ),
                    markdown=_review_markdown(review_route),
                )
            )
        )
    if wave_route and wave_route.get("wave_review"):
        wave_review = dict(wave_route["wave_review"])
        artifact_ids.append(
            str(
                    create_markdown_artifact(
                    key=_artifact_key("grace-wave", wave_review.get("feature_id", feature_id), wave_review.get("wave_id", "W00")),
                    description=_artifact_description(
                        "Architect wave gate snapshot",
                        feature_id=wave_review.get("feature_id", feature_id),
                        wave_id=wave_review.get("wave_id", "W00"),
                        verdict=wave_review.get("verdict"),
                    ),
                    markdown=_wave_markdown(wave_route),
                )
            )
        )
    return artifact_ids


def publish_live_dashboard_artifact(
    *,
    feature_status_counts: dict[str, int],
    packet_status_counts: dict[str, int],
    job_status_counts: dict[str, int],
    blocked_features: list[str],
    blocked_packets: list[str],
    pending_packets: list[str],
    active_jobs: list[str],
    run_mappings: list[str],
) -> str | None:
    if create_markdown_artifact is None:
        return None
    markdown = "\n".join(
        [
            "# GRACE Live Dashboard",
            "",
            f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Feature Statuses",
            _bullet([f"{key}: {value}" for key, value in sorted(feature_status_counts.items())]),
            "",
            "## Packet Statuses",
            _bullet([f"{key}: {value}" for key, value in sorted(packet_status_counts.items())]),
            "",
            "## Job Statuses",
            _bullet([f"{key}: {value}" for key, value in sorted(job_status_counts.items())]),
            "",
            "## Blocked Features",
            _bullet(blocked_features),
            "",
            "## Blocked Packets",
            _bullet(blocked_packets),
            "",
            "## Pending / Ready Packets",
            _bullet(pending_packets),
            "",
            "## Active Jobs",
            _bullet(active_jobs),
            "",
            "## Prefect Run Mapping",
            _bullet(run_mappings),
            "",
        ]
    )
    return str(
        create_markdown_artifact(
            key="grace-live-dashboard",
            description=_artifact_description("Live GRACE status dashboard", scope="features+packets+waves+jobs"),
            markdown=markdown,
        )
    )


def publish_run_mapping_artifact(*, mappings: list[dict[str, Any]]) -> str | None:
    if create_markdown_artifact is None:
        return None
    rows: list[list[str]] = []
    for item in mappings:
        artifact_paths = list(item.get("artifact_paths") or [])
        rows.append(
            [
                str(item.get("flow_run_id") or "-"),
                str(item.get("feature_id") or "-"),
                str(item.get("wave") or "-"),
                str(item.get("packet_id") or "-"),
                str(item.get("role") or "-"),
                str(item.get("status") or "-"),
                "<br>".join(artifact_paths) if artifact_paths else "-",
            ]
        )
    markdown = "\n".join(
        [
            "# GRACE Run Mapping",
            "",
            f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
            "",
            _markdown_table(
                ["flow_run_id", "feature_id", "wave", "packet_id", "role", "status", "artifact_paths"],
                rows,
            ),
        ]
    )
    return str(
        create_markdown_artifact(
            key="grace-run-mapping",
            description=_artifact_description("GRACE run mapping table", scope="flow+feature+wave+packet"),
            markdown=markdown,
        )
    )
