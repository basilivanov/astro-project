# Prefect + GRACE Orchestration

Prefect is installed as shared infrastructure on this host, not as an Astro-only service.

## Runtime Boundary

- Common Prefect stack: `/opt/prefect`
- API/UI: `http://127.0.0.1:4200`
- Stack service: `prefect-stack.service`
- Astro process worker: `prefect-worker-astro.service`
- Astro work pool: `astro-process`

The Prefect server stack is owned by `root:prefect`. The worker runs as `astro`, because GRACE tasks must execute with Astro project access, `/home/astro` context, and the existing Ductor/Codex session state.

## Intended GRACE Mapping

Prefect owns orchestration mechanics:

- flow/deployment state
- retries and schedules
- run logs
- step ordering
- observable history in the UI

GRACE owns delivery semantics:

- architect plan
- wave slicing
- task packets
- acceptance criteria
- validation matrix
- reviewer gate
- launch/reporting rules

Initial flow shape:

```text
analyze -> blueprint -> create_task packets -> construct -> tests -> review -> deploy/report
```

The `create_task` and Ductor/Codex calls should happen inside Prefect tasks, not inside the Prefect server container. The host worker is intentionally process-based so these calls run under the `astro` account.

## Why Docker for Prefect server

Prefect can run in three practical modes:

- CLI-only ephemeral mode: good for local experiments, bad for persistent team orchestration.
- Remote API mode: good when an external managed/self-hosted Prefect already exists.
- Self-hosted server: best when you need your own UI, DB-backed history, schedules, workers, and artifacts.

For this project we use a split model:

- Prefect server/API/UI in Docker.
- Prefect process worker on the host.

This split is intentional:

- Docker is good for the long-lived Prefect control plane: API, UI, Postgres, Redis.
- Host worker is better for Astro execution because it needs direct access to:
  - `/opt/astro-project`
  - `codex1`
  - cliproxy credentials/session state
  - `docker exec astro-project-backend-1 ...`
  - `./scripts/run_e2e.sh`

So the orchestration code does not run inside the Prefect server container. It talks to the Prefect API and the host worker executes the actual project tasks.

## Runtime config and portability

Project-specific Prefect values are now isolated behind `prefect_grace/runtime.yaml.example`.

Main knobs:

- `api_url`
- `public_ui_url`
- `work_pool_name`
- `live_queue_name`
- `monitoring_queue_name`
- `working_directory`

Environment overrides are also supported:

- `PREFECT_GRACE_API_URL`
- `PREFECT_GRACE_WORK_POOL`
- `PREFECT_GRACE_LIVE_QUEUE`
- `PREFECT_GRACE_MONITORING_QUEUE`
- `PREFECT_GRACE_WORKDIR`

That makes this layer portable into another repo without rewriting flow logic. In the next project you mainly change runtime config, prompts, packet templates, and verifier profiles.

## Commands

```bash
export PREFECT_API_URL=http://127.0.0.1:4200/api
/opt/prefect/venv/bin/prefect work-pool ls
/opt/prefect/venv/bin/prefect deployment ls
```

```bash
systemctl status prefect-stack.service
systemctl status prefect-worker-astro.service
journalctl -u prefect-worker-astro.service -f
```
