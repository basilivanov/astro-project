from pathlib import Path

from prefect_grace.runtime_config import load_runtime_config


def test_load_runtime_config_defaults(tmp_path: Path) -> None:
    config = load_runtime_config(config_path=tmp_path / "missing.yaml", env={})
    assert config.api_url == "http://127.0.0.1:4200/api"
    assert config.work_pool_name == "astro-process"
    assert config.live_queue_name == "grace-live"
    assert config.monitoring_queue_name == "grace-monitoring"
    assert config.live_queue_limit == 1
    assert config.monitoring_interval_seconds == 300


def test_load_runtime_config_yaml_and_env_override(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text(
        "\n".join(
            [
                "api_url: http://prefect.internal:4200/api",
                "work_pool_name: project-process",
                "live_queue_name: project-live",
                "live_queue_limit: 4",
                "monitoring_queue_name: project-monitoring",
                "monitoring_queue_limit: null",
                "monitoring_interval_seconds: 120",
                "working_directory: /srv/project",
            ]
        ),
        encoding="utf-8",
    )

    config = load_runtime_config(
        config_path=config_path,
        env={
            "PREFECT_GRACE_WORK_POOL": "override-pool",
            "PREFECT_GRACE_MONITORING_QUEUE_LIMIT": "2",
        },
    )

    assert config.api_url == "http://prefect.internal:4200/api"
    assert config.work_pool_name == "override-pool"
    assert config.live_queue_name == "project-live"
    assert config.live_queue_limit == 4
    assert config.monitoring_queue_name == "project-monitoring"
    assert config.monitoring_queue_limit == 2
    assert config.monitoring_interval_seconds == 120
    assert config.working_directory == "/srv/project"
