#!/usr/bin/env python3
"""Autonomous supervisor for Ductor background tasks.

This script keeps a machine-readable queue, enforces the autonomy policy,
launches/resumes background workers, and routes ask_parent questions.

Typical usage (one pass):
    python3 astro_workloop.py --max-running 2

Use cron/systemd to run it periodically.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent
AUTOMATION_DIR = REPO_ROOT / "automation"
QUEUE_PATH = AUTOMATION_DIR / "task_queue.yaml"
POLICY_PATH = AUTOMATION_DIR / "autonomy_policy.yaml"
QUESTIONS_PATH = AUTOMATION_DIR / "worker_questions.yaml"
LOG_PATH = AUTOMATION_DIR / "workloop.log"
RR_STATE_PATH = AUTOMATION_DIR / "model_rr_state.json"
MODEL_HEALTH_PATH = AUTOMATION_DIR / "model_health.yaml"
DEFAULT_CLI_HEALTH_PATH = AUTOMATION_DIR / ".runtime" / "cli_health.json"

TASK_TOOL_DIR = Path.home() / ".ductor" / "workspace" / "tools" / "task_tools"

STATUS_ORDER = ["queued", "running", "blocked", "review", "done", "failed"]

RR_MODELS = [
    # Verified live profiles. Keep gpt-5.4 variants only for these IDs.
    "codex-codex1/gpt-5.4",
    "codex-codex2/gpt-5.4",
    "codex-codex3/gpt-5.4",
    "codex-codex4/gpt-5.4",
    "codex-codex5/gpt-5.4",
    "codex-codex6/gpt-5.4",
    "codex-codex7/gpt-5.4",
    "codex-codex8/gpt-5.4",
    "codex-codex9/gpt-5.4",
]

MODEL_ERROR_PATTERNS = (
    "not supported when using Codex",
    "Model metadata for `codex-",
    "rate limit",
)

OPENAI_BASE_URL = os.environ.get("SUPERVISOR_OPENAI_BASE_URL", "http://127.0.0.1:8317/v1")
OPENAI_API_KEY = os.environ.get("SUPERVISOR_OPENAI_API_KEY", "dummy")
HEALTH_INTERVAL_SECONDS = int(os.environ.get("SUPERVISOR_MODEL_HEALTH_INTERVAL", "120"))
HEALTH_COOLDOWN_SECONDS = int(os.environ.get("SUPERVISOR_MODEL_COOLDOWN", "300"))
HEALTH_PENALTY_SECONDS = int(os.environ.get("SUPERVISOR_MODEL_PENALTY", "900"))
HEALTH_PING_TIMEOUT = int(os.environ.get("SUPERVISOR_MODEL_PING_TIMEOUT", "5"))
CLI_WARMUP_SECONDS = int(os.environ.get("SUPERVISOR_CLI_WARMUP", "60"))

REASONING_DEFAULT = {
    "backend": "high",
    "frontend": "high",
    "docs": "medium",
}

MODEL_DEFAULTS = {
    "codex": "codex-codex3/gpt-5.4",
}

CREATE_ID_PATTERN = re.compile(r"task_id:\s*([0-9a-fA-F-]+)")

NOTIFY_URL = os.environ.get("SUPERVISOR_NOTIFY_URL", "http://127.0.0.1:8001/notify")
NOTIFY_CHAT_ID = int(os.environ.get("SUPERVISOR_NOTIFY_CHAT_ID") or os.environ.get("DUCTOR_CHAT_ID") or 0)
HEALTH_STATUS_LABELS = {"healthy", "degraded", "down"}


class QueueState(Dict[str, Any]):
    tasks: List[Dict[str, Any]]


class QuestionState(Dict[str, Any]):
    questions: List[Dict[str, Any]]


def load_yaml(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default.copy()
    data = yaml.safe_load(path.read_text())
    if not data:
        return default.copy()
    return data


def save_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def iso_to_dt(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def dt_to_iso(value: dt.datetime) -> str:
    return value.replace(tzinfo=dt.UTC).isoformat()


def default_model_health() -> dict[str, Any]:
    now = dt.datetime.now(dt.UTC)
    return {
        "version": 1,
        "models": {
            model: {
                "status": "healthy",
                "checked_at": now.isoformat(),
                "retry_at": now.isoformat(),
            }
            for model in RR_MODELS
        },
    }


def load_model_health() -> dict[str, Any]:
    if not MODEL_HEALTH_PATH.exists():
        payload = default_model_health()
        save_yaml(MODEL_HEALTH_PATH, payload)
        return payload
    data = yaml.safe_load(MODEL_HEALTH_PATH.read_text()) or {}
    models = data.get("models") or {}
    for model in RR_MODELS:
        if model not in models:
            now = dt.datetime.now(dt.UTC)
            models[model] = {
                "status": "healthy",
                "checked_at": now.isoformat(),
                "retry_at": now.isoformat(),
            }
    data["models"] = models
    return data


def save_model_health(payload: dict[str, Any]) -> None:
    save_yaml(MODEL_HEALTH_PATH, payload)


def save_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def list_remote_tasks() -> dict[str, dict[str, Any]]:
    """Return mapping of worker task_id -> metadata from the task API."""
    if not TASK_TOOL_DIR.exists():
        return {}
    sys.path.insert(0, str(TASK_TOOL_DIR))
    try:
        from _shared import detect_agent_name, get_api_url, get_json  # type: ignore
    except ImportError:
        return {}
    sender = detect_agent_name()
    path = f"/tasks/list?from={sender}" if sender else "/tasks/list"
    try:
        result = get_json(get_api_url(path))
    except Exception:
        return {}
    tasks = result.get("tasks", [])
    return {str(task.get("task_id")): task for task in tasks}


def run_task_tool(tool: str, args: List[str], dry_run: bool = False) -> subprocess.CompletedProcess[str]:
    script = TASK_TOOL_DIR / tool
    if dry_run:
        print(f"[dry-run] {script} {' '.join(args)}")
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    completed = subprocess.run(
        ["python3", str(script), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{tool} failed: {completed.stdout}\n{completed.stderr}".strip()
        )
    return completed


def send_chat_notification(message: str) -> None:
    if not NOTIFY_CHAT_ID or not NOTIFY_URL:
        return
    payload = {
        "telegram_id": NOTIFY_CHAT_ID,
        "text": message,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        NOTIFY_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5):
            return
    except urllib.error.URLError:
        return


def dependencies_satisfied(task: Dict[str, Any], queue: QueueState) -> bool:
    deps = task.get("depends_on") or []
    if not deps:
        return True
    status_map = {item.get("id"): item.get("status") for item in queue.get("tasks", [])}
    return all(status_map.get(dep) == "done" for dep in deps)


def utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def mark_task(queue_task: Dict[str, Any], status: str, **updates: Any) -> None:
    queue_task["status"] = status
    queue_task.update(updates)
    queue_task["updated_at"] = utc_now_iso()


def load_rr_index() -> int:
    if RR_STATE_PATH.exists():
        try:
            data = json.loads(RR_STATE_PATH.read_text())
            idx = int(data.get("index", 0))
            return idx % max(1, len(RR_MODELS))
        except Exception:
            return 0
    return 0


def save_rr_index(idx: int) -> None:
    RR_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RR_STATE_PATH.write_text(json.dumps({"index": idx}))


def reconcile_running(queue: QueueState, remote: dict[str, dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
    changed = False
    transitions: List[Dict[str, Any]] = []
    for task in queue.get("tasks", []):
        if task.get("status") != "running":
            continue
        worker_id = task.get("worker_task_id")
        if not worker_id:
            mark_task(task, "failed", last_error="Missing worker_task_id while running")
            transitions.append({"task_id": task.get("id"), "worker": worker_id, "to": "failed", "reason": "missing worker id"})
            changed = True
            continue
        worker = remote.get(worker_id)
        if not worker:
            mark_task(task, "review", result_summary="Worker finished (not in list).")
            transitions.append({"task_id": task.get("id"), "worker": worker_id, "to": "review", "reason": "worker missing from API"})
            changed = True
            continue
        worker_status = worker.get("status")
        if worker_status == "running":
            continue
        if worker_status == "done":
            summary = worker.get("last_output", "Done")
            mark_task(task, "review", result_summary=summary)
            transitions.append({"task_id": task.get("id"), "worker": worker_id, "to": "review", "reason": "worker done"})
            changed = True
        elif worker_status in {"failed", "cancelled"}:
            error = worker.get("error") or worker.get("last_output", "Worker failed")
            mark_task(task, "failed", last_error=error)
            transitions.append({"task_id": task.get("id"), "worker": worker_id, "to": "failed", "reason": error})
            changed = True
    return changed, transitions


def auto_review(queue: QueueState) -> Tuple[bool, List[str]]:
    changed = False
    reviewed: List[str] = []
    for task in queue.get("tasks", []):
        if task.get("status") != "review":
            continue
        # Simple heuristic: mark done immediately unless flagged
        if task.get("result_summary"):
            mark_task(task, "done")
        else:
            mark_task(task, "done", result_summary="Auto-approved without summary.")
        reviewed.append(task.get("id"))
        changed = True
    return changed, reviewed


def launch_tasks(queue: QueueState, remote: dict[str, dict[str, Any]], max_running: int, dry_run: bool, health: dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]], int, bool]:
    changed = False
    started: List[Dict[str, Any]] = []
    current_running = sum(1 for task in queue.get("tasks", []) if task.get("status") == "running")
    available_slots = max(0, max_running - current_running)
    if available_slots <= 0:
        return False, started, 0, False

    rr_index = load_rr_index()
    rr_used = False
    healthy_models = [
        model
        for model in RR_MODELS
        if health.get("models", {}).get(model, {}).get("status", "healthy") == "healthy"
    ]
    for task in queue.get("tasks", []):
        if available_slots <= 0:
            break
        if task.get("status") != "queued" or not task.get("auto_run", True):
            continue
        if not dependencies_satisfied(task, queue):
            continue
        prompt = task.get("prompt")
        if not prompt:
            continue
        name = task.get("title") or task.get("id")
        args = ["--name", name]
        provider = task.get("provider") or "codex"
        model = task.get("model") or MODEL_DEFAULTS.get(provider, "")
        resolved_model = model
        model_str = str(model or "").strip().lower()
        if provider == "codex" and (not model_str or model_str in {"auto", "round_robin", "rr"}):
            pool = healthy_models or RR_MODELS
            if pool:
                resolved_model = pool[rr_index % len(pool)]
                rr_index = (rr_index + 1) % len(pool)
                rr_used = True
            else:
                resolved_model = MODEL_DEFAULTS.get(provider, "")
        elif provider == "codex":
            if "gpt-5.4-codex" in model_str:
                resolved_model = model_str.replace("gpt-5.4-codex", "gpt-5.4")
            elif "codex" in model_str and "gpt-5.4" not in model_str and "/gpt-5" not in model_str:
                resolved_model = f"{model_str.split('/')[0]}/gpt-5.4"
        reasoning = task.get("reasoning", "auto")
        if provider:
            args += ["--provider", provider]
        if resolved_model:
            args += ["--model", resolved_model]
        # Reasoning inference: default to high for backend/frontend tasks, medium otherwise
        inferred_reasoning = "high"
        title_lower = (task.get("title") or "").lower()
        if reasoning not in {"high", "medium"}:
            if any(keyword in title_lower for keyword in ["doc", "policy", "summary"]):
                inferred_reasoning = "medium"
        else:
            inferred_reasoning = reasoning
        args += ["--thinking", inferred_reasoning]
        args.append(prompt)
        try:
            result = run_task_tool("create_task.py", args, dry_run=dry_run)
        except RuntimeError as exc:
            last_err = str(exc)
            mark_task(task, "failed", last_error=last_err)
            changed = True
            if provider == "codex" and any(pattern in last_err for pattern in MODEL_ERROR_PATTERNS):
                mark_task(task, "queued", last_error=last_err)
                task.setdefault("metadata", {})["last_model_error"] = last_err
                continue
        worker_id = None
        if result.stdout:
            match = CREATE_ID_PATTERN.search(result.stdout)
            if match:
                worker_id = match.group(1)
        if not worker_id:
            worker_id = f"pending-{task.get('id')}"
        mark_task(task, "running", worker_task_id=worker_id, resolved_model=resolved_model)
        started.append({"task_id": task.get("id"), "worker": worker_id})
        available_slots -= 1
        changed = True
        print(f"Started background task {task.get('id')} -> worker {worker_id}")
    return changed, started, rr_index, rr_used


def match_auto_answer(question: str, policy: dict[str, Any]) -> Optional[str]:
    question_lower = question.lower()
    for rule in policy.get("auto_answer_rules", []):
        keywords = [k.lower() for k in rule.get("keywords", [])]
        if keywords and all(keyword in question_lower for keyword in keywords):
            return rule.get("response")
    return None


def process_questions(queue: QueueState, questions: QuestionState, policy: dict[str, Any], dry_run: bool) -> tuple[bool, bool, List[Dict[str, Any]]]:
    queue_changed = False
    questions_changed = False
    events: List[Dict[str, Any]] = []
    for entry in questions.get("questions", []):
        if entry.get("status") != "open":
            continue
        task_id = entry.get("task_id")
        question_text = entry.get("question", "")
        queue_task = next((item for item in queue.get("tasks", []) if item.get("worker_task_id") == task_id or item.get("id") == task_id), None)
        answer = match_auto_answer(question_text, policy)
        if answer:
            prompt = f"Ответ на вопрос воркера:\n{question_text}\n\n{answer}"
            try:
                run_task_tool("resume_task.py", [task_id, prompt], dry_run=dry_run)
                entry["status"] = "answered"
                entry["answered_at"] = dt.datetime.now(dt.UTC).isoformat()
                entry["answer"] = answer
                questions_changed = True
                if queue_task and queue_task.get("status") == "blocked":
                    mark_task(queue_task, "running")
                    queue_changed = True
                print(f"Auto-answered question for task {task_id}")
            except RuntimeError as exc:
                entry["status"] = "failed"
                entry["answer"] = str(exc)
                entry["answered_at"] = dt.datetime.now(dt.UTC).isoformat()
                questions_changed = True
            events.append({"task_id": task_id, "action": "auto_answer", "status": entry.get("status")})
        else:
            entry["status"] = "needs_user"
            entry["answered_at"] = dt.datetime.now(dt.UTC).isoformat()
            questions_changed = True
            if queue_task and queue_task.get("status") != "blocked":
                mark_task(queue_task, "blocked", last_error=question_text)
                queue_changed = True
            print(f"Question for task {task_id} needs user input.")
            events.append({"task_id": task_id, "action": "needs_user"})
    return queue_changed, questions_changed, events


def ensure_files_exist() -> None:
    AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
    if not QUEUE_PATH.exists():
        save_yaml(QUEUE_PATH, {"version": 1, "tasks": []})
    if not POLICY_PATH.exists():
        save_yaml(POLICY_PATH, {"version": 1})
    if not QUESTIONS_PATH.exists():
        save_yaml(QUESTIONS_PATH, {"version": 1, "questions": []})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autonomous supervisor workloop")
    parser.add_argument("--max-running", type=int, default=1, help="Max number of concurrent background tasks")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing task tools")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_files_exist()
    queue: QueueState = load_yaml(QUEUE_PATH, {"version": 1, "tasks": []})
    policy: dict[str, Any] = load_yaml(POLICY_PATH, {"version": 1})
    questions: QuestionState = load_yaml(QUESTIONS_PATH, {"version": 1, "questions": []})

    if not codex_cli_available():
        send_chat_notification("🛰️ Supervisor tick\nCodex CLI недоступен, повтор через warmup")
        return

    remote_tasks = list_remote_tasks()

    queue_dirty = False
    questions_dirty = False

    queue_changed, transitions = reconcile_running(queue, remote_tasks)
    queue_dirty |= queue_changed
    auto_changed, auto_reviewed = auto_review(queue)
    queue_dirty |= auto_changed
    health = load_model_health()
    launch_changed, started, next_rr_index, rr_used = launch_tasks(queue, remote_tasks, args.max_running, args.dry_run, health)
    queue_dirty |= launch_changed
    q_changed, qs_changed, question_events = process_questions(queue, questions, policy, args.dry_run)
    queue_dirty |= q_changed
    questions_dirty |= qs_changed

    if queue_dirty:
        save_yaml(QUEUE_PATH, queue)
        print(f"Updated queue saved to {QUEUE_PATH}")
    if questions_dirty:
        save_yaml(QUESTIONS_PATH, questions)
        print(f"Updated question log saved to {QUESTIONS_PATH}")

    if rr_used:
        save_rr_index(next_rr_index)

    counts = Counter(task.get("status") for task in queue.get("tasks", []))
    running_tasks = [
        {"task_id": item.get("id"), "worker": item.get("worker_task_id")}
        for item in queue.get("tasks", [])
        if item.get("status") == "running"
    ]

    summary = {
        "timestamp": utc_now_iso(),
        "counts": dict(counts),
        "started": started,
        "transitions": transitions,
        "auto_reviewed": auto_reviewed,
        "question_actions": question_events,
        "running_tasks": running_tasks,
    }
    log_line = json.dumps(summary, ensure_ascii=False)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(log_line + "\n")

    print(log_line)
    print("Workloop complete.")

    health, health_events = refresh_model_health(dt.datetime.now(dt.UTC), health)
    summary["model_health"] = {
        model: entry.get("status", "unknown")
        for model, entry in health.get("models", {}).items()
    }

    if started or transitions or health_events:
        lines = ["🛰️ Supervisor tick"]
        if started:
            lines.append("Запущены: " + ", ".join(f"{item['task_id']} → {item['worker']}" for item in started))
        if transitions:
            parts = []
            for entry in transitions:
                parts.append(f"{entry['task_id']} → {entry['to']}")
            lines.append("Переходы: " + ", ".join(parts))
        if health_events:
            lines.append("Профили: " + "; ".join(health_events))
        send_chat_notification("\n".join(lines))


def default_model_health() -> dict[str, Any]:
    now = dt.datetime.now(dt.UTC)
    return {
        "version": 1,
        "models": {
            model: {
                "status": "healthy",
                "checked_at": now.isoformat(),
                "retry_at": now.isoformat(),
            }
            for model in RR_MODELS
        },
    }


def load_model_health() -> dict[str, Any]:
    if not MODEL_HEALTH_PATH.exists():
        payload = default_model_health()
        save_yaml(MODEL_HEALTH_PATH, payload)
        return payload
    data = yaml.safe_load(MODEL_HEALTH_PATH.read_text()) or {}
    models = data.get("models") or {}
    for model in RR_MODELS:
        if model not in models:
            now = dt.datetime.now(dt.UTC)
            models[model] = {
                "status": "healthy",
                "checked_at": now.isoformat(),
                "retry_at": now.isoformat(),
            }
    data["models"] = models
    return data


def save_model_health(payload: dict[str, Any]) -> None:
    save_yaml(MODEL_HEALTH_PATH, payload)


def cli_health_path() -> Path:
    configured = os.environ.get("SUPERVISOR_CLI_HEALTH_PATH")
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_CLI_HEALTH_PATH


def codex_cli_available() -> bool:
    from ductor_bot.cli.codex_health import CodexHealthMonitor

    status = CodexHealthMonitor().to_payload(force=True)
    health_path = cli_health_path()
    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(json.dumps(status, ensure_ascii=False) + "\n")
    return bool(status.get("ok"))


def _ping_model(model: str) -> tuple[bool, str]:
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 3,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OPENAI_BASE_URL}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=HEALTH_PING_TIMEOUT) as resp:
            if resp.status == 200:
                return True, "ok"
            return False, f"status {resp.status}"
    except urllib.error.HTTPError as err:
        return False, f"http {err.code}: {err.read().decode(errors='ignore')[:200]}"
    except urllib.error.URLError as err:
        return False, f"network: {err.reason}"
    except Exception as exc:
        return False, str(exc)


def refresh_model_health(now: dt.datetime, health: dict[str, Any]) -> tuple[dict[str, Any], List[str]]:
    events: List[str] = []
    changed = False
    models = health.get("models", {})
    for model in RR_MODELS:
        entry = models.setdefault(model, {
            "status": "healthy",
            "checked_at": now.isoformat(),
            "retry_at": now.isoformat(),
        })
        retry_at = iso_to_dt(entry.get("retry_at")) or now
        checked_at = iso_to_dt(entry.get("checked_at")) or now
        status = entry.get("status", "healthy")
        needs_ping = False
        if (now - checked_at).total_seconds() >= HEALTH_INTERVAL_SECONDS:
            needs_ping = True
        elif status != "healthy" and now >= retry_at:
            needs_ping = True
        if not needs_ping:
            continue
        ok, info = _ping_model(model)
        entry["checked_at"] = now.isoformat()
        if ok:
            if status != "healthy":
                events.append(f"{model} healthy")
            entry["status"] = "healthy"
            entry["retry_at"] = now.isoformat()
        else:
            entry["status"] = "down"
            next_retry = now + dt.timedelta(seconds=HEALTH_COOLDOWN_SECONDS)
            entry["retry_at"] = next_retry.isoformat()
            events.append(f"{model} down: {info[:60]}")
        changed = True
    if changed:
        health["models"] = models
        save_model_health(health)
    return health, events


if __name__ == "__main__":
    main()
