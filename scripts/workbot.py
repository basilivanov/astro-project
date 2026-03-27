#!/usr/bin/env python3
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_INFRA_PATTERNS = [
    r"browserType\.launch: Executable doesn't exist",
    r"Please run `?npx playwright install`?",
    r"Failed to launch the browser process",
    r"Error: browserType\.launch",
    r"ENOENT:.*(chromium|chrome|firefox|webkit)",
    r"Playwright was not found",
    r"Host system is missing dependencies",
    r"Missing dependencies.*playwright",
    r"libgtk|libgbm|libnss3|libasound2|libx11-xcb",
    r"Error: spawn .* ENOENT",
    r"Error: Cannot find module 'playwright'",
    r"Error: EACCES",
    r"Permission denied",
]

DEFAULT_CONFIG = {
    "context": {
        "files": ["/etc/workbot/rules/GRACE.md"],
        "max_chars": 8000,
    },
    "gemini": {
        "allowed_tools": [
            "read_file",
            "read_many_files",
            "list_directory",
            "search_file_content",
            "glob",
            "replace",
            "write_file",
        ],
    },
    "tasks": {
        "files": ["TASKS.md", "Task.md", "tasks.md"],
        "priority": {"order": ["P0", "P1", "P2", "P3"], "default": "P2"},
        "status": {"open": "[ ]", "done": "[x]", "blocked": "[~]"},
        "select": "highest_priority_first",
    },
    "pipeline": {
        "profile_default": "smoke",
        "max_rounds": 1,
        "logs_dir": "test-results",
        "state_dir": ".workbot",
        "auto_triage": {
            "enabled": False,
            "mark_task_blocked": False,
            "create_triage_task": False,
            "skip_fixers": True,
            "skip_review": True,
            "infra_patterns": DEFAULT_INFRA_PATTERNS,
        },
    },
    "profiles": {
        "smoke": {
            "steps": [
                {
                    "name": "grace-lint",
                    "cmd": ["python3", "scripts/grace_lint.py"],
                    "if": "exists:scripts/grace_lint.py",
                },
                {
                    "name": "backend-smoke",
                    "cmd": ["python3", "tests/grace_report_matrix.py"],
                    "if": "exists:tests/grace_report_matrix.py",
                },
                {
                    "name": "frontend-smoke",
                    "cmd": ["npm", "run", "test:e2e"],
                    "if": "npm_script:test:e2e",
                },
            ]
        },
        "full": {
            "steps": [
                {
                    "name": "grace-lint",
                    "cmd": ["python3", "scripts/grace_lint.py"],
                    "if": "exists:scripts/grace_lint.py",
                },
                {
                    "name": "backend-full",
                    "cmd": ["python3", "scripts/pipeline.py"],
                    "if": "exists:scripts/pipeline.py",
                },
                {
                    "name": "frontend-full",
                    "cmd": ["npm", "run", "test:e2e"],
                    "if": "npm_script:test:e2e",
                },
            ]
        },
        "lint": {
            "steps": [
                {
                    "name": "grace-lint",
                    "cmd": ["python3", "scripts/grace_lint.py"],
                    "if": "exists:scripts/grace_lint.py",
                }
            ]
        },
    },
    "roles": {
        "architect": {
            "tool": "codex",
            "model": "codex-codex3/gpt-5.4",
            "reasoning": "xhigh",
            "enabled": True,
        },
        "coder": {
            "tool": "gemini",
            "model": "gemini-3-pro-preview",
            "approval_mode": "yolo",
            "enabled": True,
        },
        "fixer": {
            "tool": "gemini",
            "model": "gemini-3-flash-preview",
            "approval_mode": "yolo",
            "enabled": True,
        },
        "reviewer": {
            "tool": "codex",
            "model": "codex-codex4/gpt-5.4",
            "reasoning": "xhigh",
            "enabled": True,
        },
    },
}

PROMPTS = {
    "architect": (
        "You are the Architect. Provide a short plan and acceptance criteria for the task. "
        "Do not edit files or run commands.\n\n"
        "Task:\n{task}\n\nDetails:\n{details}\n"
    ),
    "coder": (
        "You are the Coder. Implement the task in this repository. "
        "Follow Task.md rules: update DONE/Files/Tests for this task. "
        "Do not run tests; the pipeline will run them.\n\n"
        "Task:\n{task}\n\nDetails:\n{details}\n"
    ),
    "fixer": (
        "Tests failed. Fix the issues and update the task's Tests section. "
        "Do not run tests yourself. Use the log summary below.\n\n"
        "Task:\n{task}\n\nDetails:\n{details}\n\n"
        "Test log (tail):\n{log_tail}\n"
    ),
    "reviewer": (
        "Review the current uncommitted changes. Focus on bugs, regressions, missing tests. "
        "Output findings and risks."
    ),
}

TASK_RE = re.compile(r"^\s*-\s*\[(?P<status>[ x~])\]\s*(?P<title>.+)$")
PRIORITY_RE = re.compile(r"\bP([0-3])\b", re.IGNORECASE)
PROFILE_RE = re.compile(r"\bprofile\s*:\s*([A-Za-z0-9_-]+)\b", re.IGNORECASE)


class WorkbotError(Exception):
    pass


def find_repo_root(cwd):
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True)
        return out.strip()
    except Exception:
        return cwd


def load_yaml_file(path):
    try:
        import yaml
    except ImportError:
        raise WorkbotError("PyYAML is required for YAML configs.")
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or {}


def deep_merge(base, override):
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = deep_merge(merged.get(key), value)
        return merged
    return override if override is not None else base


def load_config(repo_root):
    config = DEFAULT_CONFIG
    global_override = os.environ.get("WORKBOT_GLOBAL_CONFIG")
    global_candidates = []
    if global_override:
        global_candidates.append(Path(global_override))
    global_candidates.extend(
        [
            Path("/etc/workbot/workbot.yaml"),
            Path("/opt/workbot/workbot.yaml"),
        ]
    )
    for candidate in global_candidates:
        if candidate.exists():
            config = deep_merge(config, load_yaml_file(candidate))
            break
    for name in [".workbot.yml", "workbot.yml"]:
        path = Path(repo_root) / name
        if path.exists():
            config = deep_merge(config, load_yaml_file(path))
            break
    return config


def load_context(config, repo_root):
    context_cfg = config.get("context", {}) or {}
    files = context_cfg.get("files", [])
    max_chars = context_cfg.get("max_chars", 8000)
    chunks = []
    for entry in files:
        path = Path(entry)
        if not path.is_absolute():
            path = Path(repo_root) / path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + "\n...[truncated]\n"
        chunks.append(f"FILE: {path}\n{text}")
    if not chunks:
        return ""
    return "WORKBOT CONTEXT (rules):\n" + "\n\n".join(chunks)


def resolve_task_file(repo_root, config, override=None):
    if override:
        return Path(override)
    for name in config["tasks"]["files"]:
        path = Path(repo_root) / name
        if path.exists():
            return path
    return None


def start_watch(repo_root, config, from_start=False, pattern=None):
    log_dir = config["pipeline"].get("logs_dir", "test-results")
    watch_path = shutil.which("workbot-watch") or "/opt/workbot/bin/workbot-watch"
    watch_cmd = [watch_path, "--dir", log_dir]
    if pattern:
        watch_cmd += ["--pattern", pattern]
    if from_start:
        watch_cmd.append("--from-start")
    try:
        return subprocess.Popen(watch_cmd, cwd=repo_root)
    except FileNotFoundError:
        print("workbot watch: /opt/workbot/bin/workbot-watch not found, skipping.")
    except Exception as exc:
        print(f"workbot watch: failed to start ({exc}), skipping.")
    return None

def stop_watch(proc):
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

def parse_priority(text, default):
    match = PRIORITY_RE.search(text)
    if match:
        return f"P{match.group(1)}"
    return default

def parse_profile(text):
    match = PROFILE_RE.search(text)
    if match:
        return match.group(1)
    return None

def parse_tasks(path, config):
    tasks = []
    current = None
    default_priority = config["tasks"]["priority"]["default"]

    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    for idx, line in enumerate(lines):
        stripped = line.strip("\n")
        indent = len(line) - len(line.lstrip(" "))

        if indent == 0:
            match = TASK_RE.match(stripped)
            if match:
                if current:
                    tasks.append(current)
                title = match.group("title").strip()
                current = {
                    "status": match.group("status"),
                    "title": title,
                    "details": [],
                    "line": idx + 1,
                    "priority": parse_priority(title, default_priority),
                    "profile": parse_profile(title),
                    "raw": stripped,
                }
                continue

        if current and indent > 0:
            current["details"].append(stripped)
            if not current["profile"]:
                current["profile"] = parse_profile(stripped)
            if current["priority"] == default_priority:
                current["priority"] = parse_priority(stripped, default_priority)

    if current:
        tasks.append(current)
    return tasks

def mark_task_blocked(task_path, task, config, reason):
    blocked_marker = config["tasks"]["status"].get("blocked", "[~]")
    blocked_char = blocked_marker.strip("[]") or "~"
    lines = Path(task_path).read_text(encoding="utf-8").splitlines()
    line_idx = task["line"] - 1
    if 0 <= line_idx < len(lines):
        line = lines[line_idx]
        if TASK_RE.match(line.strip()):
            line = re.sub(r"[\s*[x~ ]\s*]", f"[{blocked_char}]", line, count=1)
            lines[line_idx] = line

    next_idx = line_idx + 1
    while next_idx < len(lines):
        if TASK_RE.match(lines[next_idx].strip()) and (len(lines[next_idx]) - len(lines[next_idx].lstrip(" ")) == 0):
            break
        next_idx += 1

    blocked_prefix = "**BLOCKED:**"
    inserted = False
    for idx in range(line_idx + 1, next_idx):
        if blocked_prefix in lines[idx]:
            lines[idx] = re.sub(r"\*\*BLOCKED:\*\*.*", f"**BLOCKED:** {reason}", lines[idx])
            inserted = True
            break
    if not inserted:
        lines.insert(next_idx, f"    *   **BLOCKED:** {reason}")

    Path(task_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

def append_triage_task(task_path, task, config, triage, log_path):
    status_marker = config["tasks"]["status"].get("blocked", "[~]")
    entry_id = f"ARCH-TRIAGE-{time.strftime('%Y%m%d-%H%M%S')}"
    reason = format_triage_reason(triage)
    header = "## 🚨 Auto-Triage"

    lines = Path(task_path).read_text(encoding="utf-8").splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == header:
            header_idx = idx
            break

    if header_idx is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(header)
        lines.append("")
        header_idx = len(lines) - 2

    insert_idx = header_idx + 1
    while insert_idx < len(lines) and lines[insert_idx].strip() == "":
        insert_idx += 1

    entry_lines = [
        f"- {status_marker} **{entry_id}: Инфра-сбой тестов ({task['title']})**",
        f"    *   **BLOCKED:** {reason}",
        f"    *   **Details:** test-log: {log_path}",
    ]

    lines[insert_idx:insert_idx] = entry_lines + [""]
    Path(task_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

def select_task(tasks, config, task_id=None):
    open_tasks = [t for t in tasks if t["status"] == " "]
    if task_id:
        open_tasks = [t for t in open_tasks if task_id.lower() in t["title"].lower()]
    if not open_tasks:
        return None

    order = config["tasks"]["priority"]["order"]
    default_priority = config["tasks"]["priority"]["default"]

    def rank(task):
        priority = task.get("priority", default_priority)
        try:
            idx = order.index(priority)
        except ValueError:
            idx = order.index(default_priority) if default_priority in order else len(order)
        return (idx, task["line"])

    return sorted(open_tasks, key=rank)[0]

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def tail_text(path, limit=4000):
    try:
        data = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return "<no log>"
    if len(data) <= limit:
        return data
    return data[-limit:]

def write_state(repo_root, config, state):
    state_dir = Path(repo_root) / config["pipeline"]["state_dir"]
    ensure_dir(state_dir)
    state_path = state_dir / "state.json"
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

def run_cmd(cmd, cwd, log_path, env=None):
    ensure_dir(Path(log_path).parent)
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=log, stderr=subprocess.STDOUT)
    return proc.returncode

def build_llm_env(config, override_home=None):
    env = os.environ.copy()
    llm_home = override_home or os.environ.get("WORKBOT_LLM_HOME") or config.get("llm_home")
    if llm_home:
        env["HOME"] = str(llm_home)
    llm_env = config.get("llm_env")
    if isinstance(llm_env, dict):
        for key, value in llm_env.items():
            if value is None:
                env.pop(str(key), None)
            else:
                env[str(key)] = str(value)
    return env


# START_BLOCK_GEMINI_POOL
class GeminiPool:
    def __init__(self, base_home, size=4):
        self.base_home = Path(base_home) if base_home else Path(os.environ.get("HOME", "/tmp"))
        self.size = size
        self.lock_dir = self.base_home / ".workbot_locks"
        # Check if pool exists (acc0 must exist)
        self.enabled = (self.base_home / "acc0").exists()
        if self.enabled:
            self.lock_dir.mkdir(parents=True, exist_ok=True)

    def acquire(self, exclude=None):
        if not self.enabled:
            return None, self.base_home
            
        exclude = exclude or set()
        candidates = [i for i in range(self.size) if i not in exclude]
        # Sort by last usage? Random for now.
        random.shuffle(candidates)
        
        for i in candidates:
            if self._try_lock(i):
                return i, self.base_home / f"acc{i}"
        
        return None, None

    def _try_lock(self, index):
        lock_file = self.lock_dir / f"acc{index}.lock"
        cooldown_file = self.lock_dir / f"acc{index}.cooldown"
        
        # Check cooldown
        if cooldown_file.exists():
            if time.time() - cooldown_file.stat().st_mtime < 300: # 5 min cooldown
                return False
            cooldown_file.unlink(missing_ok=True)

        # Check lock
        if lock_file.exists():
            # Force unlock after 10 mins
            if time.time() - lock_file.stat().st_mtime > 600:
                lock_file.unlink()
            else:
                return False
        
        try:
            lock_file.write_text(str(os.getpid()), encoding="utf-8")
            return True
        except Exception:
            return False

    def release(self, index):
        if index is None or not self.enabled:
            return
        lock_file = self.lock_dir / f"acc{index}.lock"
        lock_file.unlink(missing_ok=True)
        
    def mark_bad(self, index):
        if index is None or not self.enabled:
            return
        cooldown_file = self.lock_dir / f"acc{index}.cooldown"
        try:
            cooldown_file.write_text(str(time.time()), encoding="utf-8")
        except Exception:
            pass
        self.release(index)
# END_BLOCK_GEMINI_POOL


def run_codex(prompt, repo_root, role, config, log_path):
    model = role.get("model")
    reasoning = role.get("reasoning")
    cmd = [
        "codex",
        "exec",
        "--model",
        model,
        "--sandbox",
        "workspace-write",
        "--full-auto",
        "--cd",
        repo_root,
    ]
    if reasoning:
        cmd += ["-c", f"model_reasoning_effort=\"{reasoning}\"" ]

    ensure_dir(Path(log_path).parent)
    env = build_llm_env(config)
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.run(cmd, input=prompt, cwd=repo_root, env=env, text=True, stdout=log, stderr=subprocess.STDOUT)
    return proc.returncode

# START_BLOCK_GEMINI_RUN
def run_gemini(prompt, repo_root, role, config, log_path):
    model = role.get("model")
    approval = role.get("approval_mode", "yolo")
    allowed_tools = role.get("allowed_tools") or config.get("gemini", {}).get("allowed_tools")
    output_format = role.get("output_format") or config.get("gemini", {}).get("output_format") or "stream-json"
    
    base_home = os.environ.get("WORKBOT_LLM_HOME") or config.get("llm_home")
    pool = GeminiPool(base_home)
    
    attempts = 0
    max_attempts = pool.size if pool.enabled else 1
    used_indices = set()
    
    ensure_dir(Path(log_path).parent)
    
    while attempts < max_attempts:
        idx, account_home = pool.acquire(exclude=used_indices)
        if account_home is None:
            # Pool exhausted or locked
            if pool.enabled:
                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"\nWORKBOT: No available Gemini accounts in pool (attempts={attempts}).\n")
                return 1
            else:
                # Should not happen if max_attempts=1 but safe fallback
                account_home = Path(os.environ.get("HOME"))

        if idx is not None:
            used_indices.add(idx)
        
        attempts += 1
        
        cmd = [
            "gemini",
            "--model",
            model,
            "--approval-mode",
            approval,
        ]
        if output_format:
            cmd += ["--output-format", output_format]
        if allowed_tools:
            cmd += ["--allowed-tools", ",".join(allowed_tools)]
        cmd.append(prompt)
        
        env = build_llm_env(config, override_home=account_home)
        
        # Log attempt
        with open(log_path, "a" if attempts > 1 else "w", encoding="utf-8") as log:
            header = f"\n--- Attempt {attempts}/{max_attempts} (Account: {account_home.name if idx is not None else 'default'}) ---\n"
            if attempts == 1:
                header = f"$ {' '.join(cmd)}\n" + (f"WORKBOT: Using account {account_home.name} (HOME={account_home})\n" if idx is not None else "")
            
            log.write(header)
            log.flush()
            
            proc = subprocess.run(cmd, cwd=repo_root, env=env, text=True, stdout=log, stderr=subprocess.STDOUT)
            
        # Check success
        if proc.returncode == 0:
            pool.release(idx)
            return 0
            
        # Analyze error
        try:
            log_content = Path(log_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            log_content = ""
            
        is_quota = "RetryableQuotaError" in log_content or "429" in log_content or "401" in log_content
        
        if is_quota and pool.enabled:
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"\nWORKBOT: Quota/Auth error detected on {account_home.name}. Rotating...\n")
            pool.mark_bad(idx)
            continue
        
        # Non-recoverable error
        pool.release(idx)
        return proc.returncode
        
    return 1
# END_BLOCK_GEMINI_RUN

def run_review(repo_root, role, config, log_path, prompt=None):
    model = role.get("model")
    reasoning = role.get("reasoning")
    cmd = ["codex", "review", "--uncommitted", "-c", f"model=\"{model}\"" ]
    if reasoning:
        cmd += ["-c", f"model_reasoning_effort=\"{reasoning}\"" ]
    if prompt:
        cmd.append("-")

    ensure_dir(Path(log_path).parent)
    env = build_llm_env(config)
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.run(
            cmd,
            input=prompt,
            cwd=repo_root,
            env=env,
            text=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    return proc.returncode

def check_condition(condition, repo_root, step_cwd):
    if not condition:
        return True
    base_dir = step_cwd or Path(repo_root)
    if condition.startswith("exists:"):
        target = condition.split(":", 1)[1]
        return (base_dir / target).exists()
    if condition.startswith("npm_script:"):
        script = condition.split(":", 1)[1]
        package = base_dir / "package.json"
        if not package.exists():
            return False
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
        except Exception:
            return False
        scripts = data.get("scripts", {})
        return script in scripts
    return False

def run_tests(repo_root, config, profile):
    profiles = config.get("profiles", {})
    if profile not in profiles:
        raise WorkbotError(f"Unknown profile: {profile}")

    log_dir = Path(repo_root) / config["pipeline"]["logs_dir"]
    ensure_dir(log_dir)
    log_path = log_dir / f"workbot-{time.strftime('%Y%m%d-%H%M%S')}-tests.log"

    steps = profiles[profile].get("steps", [])
    if not steps:
        return True, str(log_path)

    ok = True
    with open(log_path, "w", encoding="utf-8") as log:
        for step in steps:
            name = step.get("name", "step")
            cmd = step.get("cmd")
            condition = step.get("if")
            step_cwd = Path(repo_root) / step.get("cwd", "")
            if step.get("cwd") and not step_cwd.exists():
                log.write(f"SKIP {name}: cwd {step_cwd} not found\n")
                continue
            if not check_condition(condition, repo_root, step_cwd):
                log.write(f"SKIP {name}: condition {condition} not met\n")
                continue
            log.write(f"RUN {name}: {cmd} (cwd={step_cwd})\n")
            log.flush()
            timeout = step.get("timeout", 300) # Default 5 mins
            try:
                if isinstance(cmd, list):
                    proc = subprocess.run(cmd, cwd=step_cwd, text=True, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
                else:
                    proc = subprocess.run(cmd, cwd=step_cwd, text=True, shell=True, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
                if proc.returncode != 0:
                    ok = False
                    log.write(f"FAIL {name}: exit {proc.returncode}\n")
                    break
                log.write(f"PASS {name}\n")
            except subprocess.TimeoutExpired:
                ok = False
                log.write(f"FAIL {name}: timed out after {timeout}s\n")
                break
    return ok, str(log_path)

def classify_test_log(log_path, config):
    triage_cfg = config.get("pipeline", {}).get("auto_triage", {})
    if not triage_cfg.get("enabled"):
        return None
    patterns = triage_cfg.get("infra_patterns") or DEFAULT_INFRA_PATTERNS
    try:
        text = Path(log_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"kind": "code"}
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {"kind": "infra", "pattern": pattern, "match": match.group(0)}
    return {"kind": "code"}

def append_triage_note(log_path, triage):
    if not triage:
        return
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\nWORKBOT TRIAGE: {triage.get('kind', 'code')}\n")
        if triage.get("match"):
            log.write(f"WORKBOT TRIAGE MATCH: {triage['match']}\n")

def format_triage_reason(triage):
    if not triage:
        return "Инфраструктура/окружение: неизвестная причина"
    match = triage.get("match")
    if match:
        return f"Инфраструктура/окружение: {match}"
    return "Инфраструктура/окружение: неизвестная причина"

def handle_triage(test_log, config, state, task_path=None, task=None):
    triage_cfg = config.get("pipeline", {}).get("auto_triage", {})
    triage = classify_test_log(test_log, config)
    append_triage_note(test_log, triage)
    if triage:
        state["triage"] = triage

    skip_fixer = False
    skip_review = False
    if triage and triage.get("kind") == "infra":
        if task_path and task:
            if triage_cfg.get("mark_task_blocked"):
                mark_task_blocked(task_path, task, config, format_triage_reason(triage))
            if triage_cfg.get("create_triage_task"):
                append_triage_task(task_path, task, config, triage, test_log)
        skip_fixer = triage_cfg.get("skip_fixers", True)
        skip_review = triage_cfg.get("skip_review", True)

    return triage, skip_fixer, skip_review

def format_task_details(task):
    details = task.get("details", [])
    if not details:
        return "(no details)"
    return "\n".join(details)

def run_pipeline(args):
    repo_root = find_repo_root(os.getcwd())
    config = load_config(repo_root)
    context_text = load_context(config, repo_root)
    context_prefix = f"{context_text}\n\n" if context_text else ""
    watch_proc = None

    task_path = resolve_task_file(repo_root, config, args.task_file)
    if not task_path or not task_path.exists():
        raise WorkbotError("No task file found. Add Task.md/TASKS.md or pass --task-file.")

    tasks = parse_tasks(task_path, config)
    task = select_task(tasks, config, args.task_id)
    if not task:
        raise WorkbotError("No open tasks found.")

    profile = args.profile or task.get("profile") or config["pipeline"]["profile_default"]
    max_rounds = args.max_rounds or config["pipeline"]["max_rounds"]

    log_dir = Path(repo_root) / config["pipeline"]["logs_dir"]
    ensure_dir(log_dir)
    ts = time.strftime("%Y%m%d-%H%M%S")

    if args.watch or args.watch_from_start:
        watch_pattern = None if args.watch_all else f"workbot-{ts}-*.log"
        watch_proc = start_watch(
            repo_root,
            config,
            from_start=args.watch_from_start,
            pattern=watch_pattern,
        )

    state = {
        "task": task["title"],
        "task_file": str(task_path),
        "profile": profile,
        "started_at": ts,
    }

    details_text = format_task_details(task)

    if not args.no_architect:
        role = config["roles"].get("architect", {})
        if role.get("enabled"):
            prompt = context_prefix + PROMPTS["architect"].format(
                task=task["title"],
                details=details_text,
            )
            log_path = log_dir / f"workbot-{ts}-architect.log"
            run_codex(prompt, repo_root, role, config, str(log_path))
            state["architect_log"] = str(log_path)

    if not args.no_coder:
        role = config["roles"].get("coder", {})
        if role.get("enabled"):
            prompt = context_prefix + PROMPTS["coder"].format(
                task=task["title"],
                details=details_text,
            )
            log_path = log_dir / f"workbot-{ts}-coder.log"
            run_gemini(prompt, repo_root, role, config, str(log_path))
            state["coder_log"] = str(log_path)

    ok, test_log = run_tests(repo_root, config, profile)
    state["tests_log"] = test_log
    state["tests_ok"] = ok
    skip_fixer = False
    skip_review = False
    if not ok:
        _, skip_fixer, skip_review = handle_triage(
            test_log,
            config,
            state,
            task_path=task_path,
            task=task,
        )

    rounds = 0
    while not ok and not args.no_fixer and not skip_fixer and rounds < max_rounds:
        role = config["roles"].get("fixer", {})
        if role.get("enabled"):
            rounds += 1
            log_tail = tail_text(test_log, limit=4000)
            prompt = context_prefix + PROMPTS["fixer"].format(
                task=task["title"],
                details=details_text,
                log_tail=log_tail,
            )
            log_path = log_dir / f"workbot-{ts}-fixer-{rounds}.log"
            run_gemini(prompt, repo_root, role, config, str(log_path))
            state[f"fixer_log_{rounds}"] = str(log_path)
            ok, test_log = run_tests(repo_root, config, profile)
            state["tests_log"] = test_log
            state["tests_ok"] = ok
            if not ok:
                _, skip_fixer, skip_review = handle_triage(
                    test_log,
                    config,
                    state,
                    task_path=task_path,
                    task=task,
                )
        else:
            break

    if not args.no_review and not skip_review:
        role = config["roles"].get("reviewer", {})
        if role.get("enabled"):
            log_path = log_dir / f"workbot-{ts}-review.log"
            prompt = context_prefix + PROMPTS["reviewer"]
            run_review(repo_root, role, config, str(log_path), prompt=prompt)
            state["review_log"] = str(log_path)

    try:
        write_state(repo_root, config, state)
        return 0 if ok else 1
    finally:
        stop_watch(watch_proc)

def list_tasks(args):
    repo_root = find_repo_root(os.getcwd())
    config = load_config(repo_root)
    task_path = resolve_task_file(repo_root, config, args.task_file)
    if not task_path or not task_path.exists():
        raise WorkbotError("No task file found.")
    tasks = parse_tasks(task_path, config)
    open_tasks = [t for t in tasks if t["status"] == " "]
    if not open_tasks:
        print("No open tasks.")
        return 0
    for task in open_tasks:
        print(f"{task['priority']} {task['title']}")
    return 0

def run_only_tests(args):
    repo_root = find_repo_root(os.getcwd())
    config = load_config(repo_root)
    profile = args.profile or config["pipeline"]["profile_default"]
    ok, log_path = run_tests(repo_root, config, profile)
    if not ok:
        triage_state = {}
        triage, _, _ = handle_triage(log_path, config, triage_state)
        if triage:
            print(f"Auto triage: {triage.get('kind')}")
    print(f"Tests log: {log_path}")
    return 0 if ok else 1

def run_watch(args):
    repo_root = find_repo_root(os.getcwd())
    config = load_config(repo_root)
    log_dir = args.dir or config["pipeline"].get("logs_dir", "test-results")
    watch_path = shutil.which("workbot-watch") or "/opt/workbot/bin/workbot-watch"
    cmd = [watch_path, "--dir", log_dir]
    if args.pattern:
        cmd += ["--pattern", args.pattern]
    if args.from_start:
        cmd.append("--from-start")
    return subprocess.call(cmd, cwd=repo_root)

def main():
    parser = argparse.ArgumentParser(description="workbot: universal LLM pipeline runner")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run pipeline")
    run_parser.add_argument("--profile", help="Test profile")
    run_parser.add_argument("--task-id", help="Filter tasks by id substring")
    run_parser.add_argument("--task-file", help="Override task file path")
    run_parser.add_argument("--max-rounds", type=int, help="Max fix rounds")
    run_parser.add_argument("--no-architect", action="store_true")
    run_parser.add_argument("--no-coder", action="store_true")
    run_parser.add_argument("--no-fixer", action="store_true")
    run_parser.add_argument("--no-review", action="store_true")
    run_parser.add_argument("--watch", action="store_true", help="Stream phase logs to console")
    run_parser.add_argument("--watch-from-start", action="store_true", help="Stream logs from start")
    run_parser.add_argument("--watch-all", action="store_true", help="Stream logs from all runs")

    list_parser = subparsers.add_parser("list", help="List open tasks")
    list_parser.add_argument("--task-file", help="Override task file path")

    test_parser = subparsers.add_parser("test", help="Run tests only")
    test_parser.add_argument("--profile", help="Test profile")

    watch_parser = subparsers.add_parser("watch", help="Watch workbot logs")
    watch_parser.add_argument("--dir", help="Log directory (default: test-results)")
    watch_parser.add_argument("--pattern", help="Log glob pattern (default: workbot-*.log)")
    watch_parser.add_argument("--from-start", action="store_true", help="Print existing logs from start")

    args = parser.parse_args()
    if not args.command:
        args.command = "run"

    try:
        if args.command == "run":
            return run_pipeline(args)
        if args.command == "list":
            return list_tasks(args)
        if args.command == "test":
            return run_only_tests(args)
        if args.command == "watch":
            return run_watch(args)
    except WorkbotError as exc:
        print(f"workbot error: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
