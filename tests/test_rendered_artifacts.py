from __future__ import annotations

import json
from pathlib import Path

from tools.rendered_artifacts import build_parity_details, build_parity_pilot_details, build_rendered_summary, load_rendered_summaries, stable_pass_mode, write_rendered_summary


def test_stable_pass_mode_supports_site_and_future_telegram() -> None:
    assert stable_pass_mode("site/web") == {"key": "site_web", "channel": "web", "path": "/"}
    assert stable_pass_mode("telegram") == {"key": "telegram_webapp", "channel": "telegram", "path": "webapp"}
    assert stable_pass_mode("both") == {"key": "both", "channel": "multi", "path": "site_web+telegram_webapp"}


def test_write_rendered_summary_materializes_compact_artifact(tmp_path: Path) -> None:
    target = write_rendered_summary(
        flow_id="FLOW-TODAY-PREMIUM",
        surface="today",
        scenario_id="today_rendered_compact",
        pass_mode="site/web",
        status="passed",
        assertion_class="rendered_hygiene",
        artifact_refs=["playwright://trace/today.zip", "screenshot://today.png"],
        details={"route": "/", "duplicate_factor_labels": ["Тонус"], "console_errors": 0},
        base_dir=tmp_path,
    )

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["flow_id"] == "FLOW-TODAY-PREMIUM"
    assert payload["surface"] == "today"
    assert payload["scenario_id"] == "today_rendered_compact"
    assert payload["pass_mode"] == {"key": "site_web", "channel": "web", "path": "/"}
    assert payload["status"] == "passed"
    assert payload["assertion_class"] == "rendered_hygiene"
    assert payload["artifact_refs"] == ["playwright://trace/today.zip", "screenshot://today.png"]
    assert payload["details"]["route"] == "/"
    assert payload["recorded_at"]

    summaries = load_rendered_summaries(tmp_path)
    assert [item["scenario_id"] for item in summaries] == ["today_rendered_compact"]


def test_build_rendered_summary_accepts_explicit_pass_mode_object() -> None:
    artifact = build_rendered_summary(
        flow_id="FLOW-WEEK-BRIEF",
        surface="week",
        scenario_id="week_rendered_compact",
        pass_mode={"key": "telegram_webapp", "channel": "telegram", "path": "webapp"},
        status="passed",
        assertion_class="rendered_hygiene",
        details={"route": "/week"},
    )

    assert artifact.pass_mode["key"] == "telegram_webapp"
    assert artifact.details["route"] == "/week"


def test_build_parity_details_keeps_compact_counterpart_representation() -> None:
    parity = build_parity_details(
        counterpart_pass_mode="site/web",
        parity_status="pilot_same_assertion_surface",
        notes=["telegram pilot uses same rendered assertions as site/web"],
    )

    assert parity == {
        "counterpart_pass_mode": {"key": "site_web", "channel": "web", "path": "/"},
        "parity_status": "pilot_same_assertion_surface",
        "notes": ["telegram pilot uses same rendered assertions as site/web"],
    }


def test_build_parity_pilot_details_keeps_shared_refs_and_invariants() -> None:
    parity = build_parity_pilot_details(
        counterpart_pass_mode="site/web",
        parity_status="pilot_dom_model_invariants",
        shared_artifact_refs=["dom://today-verdict", "dom://today-score-details-energy"],
        invariant_groups=["today.verdict", "today.score_details"],
        notes=["Today pilot checks the same compact DOM/UI-model invariants on both paths"],
    )

    assert parity == {
        "counterpart_pass_mode": {"key": "site_web", "channel": "web", "path": "/"},
        "parity_status": "pilot_dom_model_invariants",
        "notes": ["Today pilot checks the same compact DOM/UI-model invariants on both paths"],
        "shared_artifact_refs": ["dom://today-verdict", "dom://today-score-details-energy"],
        "invariant_groups": ["today.verdict", "today.score_details"],
    }


def test_load_rendered_summaries_returns_site_and_telegram_variants(tmp_path: Path) -> None:
    write_rendered_summary(
        flow_id="FLOW-TODAY-PREMIUM",
        surface="today",
        scenario_id="today_site",
        pass_mode="site/web",
        status="passed",
        assertion_class="rendered_hygiene",
        base_dir=tmp_path,
    )
    write_rendered_summary(
        flow_id="FLOW-TODAY-PREMIUM",
        surface="today",
        scenario_id="today_telegram",
        pass_mode="telegram_webapp",
        status="passed",
        assertion_class="rendered_harness",
        base_dir=tmp_path,
    )

    summaries = load_rendered_summaries(tmp_path)
    assert [(item["scenario_id"], item["pass_mode"]["key"]) for item in summaries] == [
        ("today_site", "site_web"),
        ("today_telegram", "telegram_webapp"),
    ]
