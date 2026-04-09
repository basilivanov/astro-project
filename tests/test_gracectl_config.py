from pathlib import Path

from gracectl.config import load_config


def test_load_config_resolves_relative_repo_root_against_config_path(tmp_path: Path) -> None:
    config_path = tmp_path / "gracectl.yaml"
    config_path.write_text(
        "\n".join(
            [
                "defaults:",
                "  report_path: test-results/grace-report.json",
                "  log_dir: logs/gracectl",
                "  repo_root: .",
                "watch:",
                "  flows: []",
                "slices: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.defaults.repo_root == tmp_path
    assert config.defaults.report_path == tmp_path / "test-results" / "grace-report.json"
    assert config.defaults.log_dir == tmp_path / "logs" / "gracectl"
