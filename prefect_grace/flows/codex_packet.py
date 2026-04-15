from __future__ import annotations

from prefect_grace.prefect_compat import flow, get_run_logger, task
from prefect_grace.tasks.codex_launcher import launch_codex_for_packet


@task(task_run_name="codex:{packet_id}")
def run_codex_packet_task(packet_id: str, dry_run: bool, timeout_seconds: int) -> dict:
    logger = get_run_logger()
    logger.info("Launching Codex for packet %s dry_run=%s", packet_id, dry_run)
    result = launch_codex_for_packet(packet_id, dry_run=dry_run, timeout_seconds=timeout_seconds, logger=logger)
    logger.info("Codex packet %s finished rc=%s launcher=%s", packet_id, result.get("returncode"), result.get("launcher"))
    return result


@flow(name="prefect-grace-codex-packet", flow_run_name="packet:{packet_id}")
def codex_packet_flow(packet_id: str, dry_run: bool = True, timeout_seconds: int = 3600):
    return run_codex_packet_task(packet_id, dry_run, timeout_seconds)
