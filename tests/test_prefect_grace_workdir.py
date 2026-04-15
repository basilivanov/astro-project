from pathlib import Path

from prefect_grace.tasks.business_intake import load_business_feature_brief
from prefect_grace.tasks.workdir import resolve_execution_workdir


def test_resolve_execution_workdir_falls_back_to_repo_for_missing_path() -> None:
    resolved = resolve_execution_workdir("/tmp/definitely-missing-prefect-grace-workdir")
    assert resolved == Path("/opt/astro-project")


def test_load_business_feature_brief_normalizes_missing_agent_workdir(tmp_path: Path) -> None:
    brief_path = tmp_path / "brief.yaml"
    brief_path.write_text(
        "\n".join(
            [
                "feature_id: FEAT-WORKDIR-BRIEF",
                "title: Workdir brief",
                "summary: Ensure missing workdir falls back safely",
                "agent_workdir: /tmp/definitely-missing-prefect-grace-workdir",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_business_feature_brief(brief_path)
    assert loaded["agent_workdir"] == "/opt/astro-project"
