from prefect_grace.tasks import prefect_artifacts


def test_publish_feature_artifacts_includes_architect_planner_and_reviewer(monkeypatch) -> None:
    created: list[dict] = []

    def _fake_create_markdown_artifact(**kwargs):
        created.append(kwargs)
        return f"artifact-{len(created)}"

    monkeypatch.setattr(prefect_artifacts, "create_markdown_artifact", _fake_create_markdown_artifact)

    feature = {
        "feature_id": "FEAT-X",
        "title": "Feature X",
        "status": "planned",
        "feature_dir": "/tmp/feature-x",
    }
    packet_results = {
        "architect_artifact_plan": {
            "source": "agent_output",
            "parser_error": None,
        },
        "architect_artifacts": {
            "slice_id": "SLICE-FEAT-X",
            "slice_slug": "feature-x",
            "slice_dir": "/tmp/docs/feature-x",
            "architect_manifest_path": "/tmp/docs/feature-x/architect_manifest.json",
            "architect_handoff_path": "/tmp/docs/feature-x/ARCHITECT_HANDOFF.md",
            "execution_packet_path": "/tmp/docs/feature-x/EXECUTION_PACKET.md",
            "requirements_slice_path": "/tmp/docs/feature-x/requirements.slice.feature-x.xml",
            "development_plan_slice_path": "/tmp/docs/feature-x/development-plan.slice.feature-x.xml",
            "verification_matrix_slice_path": "/tmp/docs/feature-x/verification-matrix.slice.feature-x.md",
            "knowledge_graph_slice_path": "/tmp/docs/feature-x/knowledge-graph.slice.feature-x.xml",
            "manifest": {
                "slice_id": "SLICE-FEAT-X",
                "impacted_modules": ["frontend/app/page.tsx"],
                "planner_inputs": ["/tmp/docs/feature-x/ARCHITECT_HANDOFF.md"],
                "waves": [{"wave_id": "W01", "title": "Main wave", "objective": "Ship feature"}],
                "root_deltas": {"development-plan.xml": "append W01"},
            },
        },
        "planner_contract": {
            "source": "agent_output",
            "parser_error": None,
            "contract": {
                "waves": [{"wave_id": "W01", "title": "Main wave", "objective": "Ship feature"}],
                "packets": [
                    {
                        "key": "coder_main",
                        "wave_id": "W01",
                        "role": "coder",
                        "title": "Coder Main",
                        "dependencies": [],
                        "review_target_key": "",
                        "verification_profile": {},
                    },
                    {
                        "key": "verifier_main",
                        "wave_id": "W01",
                        "role": "verifier",
                        "title": "Verifier Main",
                        "dependencies": ["coder_main"],
                        "review_target_key": "",
                        "verification_profile": {
                            "execution": {
                                "frontend_commands": ["./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts"],
                                "observability_commands": ["python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"],
                                "artifact_globs": ["frontend/test-results/**/*"],
                            }
                        },
                    },
                ],
            },
        },
        "planner_materialized": {
            "wave_plan_path": "/tmp/feature-x/wave-plan.md",
            "packets": [
                {
                    "packet_id": "FEAT-X-W01-CODER-MAIN",
                    "wave_id": "W01",
                    "role": "coder",
                    "status": "ready",
                    "dependencies": [],
                },
                {
                    "packet_id": "FEAT-X-W01-VERIFIER-MAIN",
                    "wave_id": "W01",
                    "role": "verifier",
                    "status": "review",
                    "dependencies": ["FEAT-X-W01-CODER-MAIN"],
                },
            ],
        },
        "planner_validation": {
            "valid": True,
            "issues": [],
        },
    }
    review_route = {
        "review": {
            "packet_id": "FEAT-X-W01-REVIEWER-VERDICT",
            "verdict": "accepted",
            "follow_up_action": "none",
            "review_path": "/tmp/feature-x/review.md",
            "reasons": [],
        }
    }

    artifact_ids = prefect_artifacts.publish_feature_artifacts(
        feature=feature,
        packet_results=packet_results,
        verification=None,
        review_route=review_route,
        wave_route=None,
        final_status=None,
    )

    assert len(artifact_ids) == 4
    keys = {item["key"] for item in created}
    assert "grace-feature-feat-x" in keys
    assert "grace-architect-feat-x" in keys
    assert "grace-planner-feat-x" in keys
    assert "grace-review-feat-x-w01-reviewer-verdict" in keys

    architect_markdown = next(item["markdown"] for item in created if item["key"] == "grace-architect-feat-x")
    planner_markdown = next(item["markdown"] for item in created if item["key"] == "grace-planner-feat-x")
    assert "SLICE-FEAT-X" in architect_markdown
    assert "frontend/app/page.tsx" in architect_markdown
    assert "coder_main" in planner_markdown
    assert "./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts" in planner_markdown
