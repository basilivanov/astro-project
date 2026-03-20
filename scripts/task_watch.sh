#!/usr/bin/env bash
set -euo pipefail

# Watches Task.md and prints (and optionally tmux-notifies) when new tasks are marked as done.
#
# Usage:
#   ./scripts/task_watch.sh [task_file]
#
# Optional env:
#   WATCH_TMUX_TARGET="astro2"        # session/window to display-message into
#   WATCH_TMUX_CMD="tmux"             # set to "sudo tmux" if the tmux server runs as root
#   WATCH_READY_MARKER="READY_FOR_REVIEW"
#   WATCH_KICK_MARKER="KICK_CODER"
#   WATCH_DEMAND_TARGET="astro:0.0"   # pane to auto-handle "high demand" prompts (optional)
#   WATCH_DEMAND_REGEX="We are currently experiencing high demand"
#   WATCH_DEMAND_CHOICE="1"           # what to type before Enter ("1" => Keep trying). Empty => just Enter.
#   WATCH_DEMAND_COOLDOWN_SEC="20"    # minimum seconds between auto-answers
#   WATCH_CODER_TARGET="astro:0.0"    # tmux pane to send a prompt into (optional)
#   WATCH_CODER_PROMPT="..."          # custom prompt to send when kick marker appears
#   WATCH_ARCH_TARGET="astro2:0.0"    # tmux pane to send an architect prompt into (optional)
#   WATCH_ARCH_PROMPT="..."           # custom prompt to send when READY_FOR_REVIEW appears

TASK_FILE="${1:-Task.md}"

WATCH_TMUX_TARGET="${WATCH_TMUX_TARGET:-astro2}"
WATCH_TMUX_CMD="${WATCH_TMUX_CMD:-tmux}"
WATCH_READY_MARKER="${WATCH_READY_MARKER:-READY_FOR_REVIEW}"
WATCH_KICK_MARKER="${WATCH_KICK_MARKER:-KICK_CODER}"
WATCH_DEMAND_TARGET="${WATCH_DEMAND_TARGET:-astro:0.0}"
WATCH_DEMAND_REGEX="${WATCH_DEMAND_REGEX:-We are currently experiencing high demand}"
# Default: if Enter doesn't dismiss the prompt, type "1" then Enter ("Keep trying").
# Safety: we only type the explicit choice if the prompt is still visible after Enter.
WATCH_DEMAND_CHOICE="${WATCH_DEMAND_CHOICE:-1}"
WATCH_DEMAND_COOLDOWN_SEC="${WATCH_DEMAND_COOLDOWN_SEC:-20}"
WATCH_CODER_TARGET="${WATCH_CODER_TARGET:-}"
WATCH_CODER_PROMPT="${WATCH_CODER_PROMPT:-}"
WATCH_ARCH_TARGET="${WATCH_ARCH_TARGET:-}"
WATCH_ARCH_PROMPT="${WATCH_ARCH_PROMPT:-}"
WATCH_CODER_SUBMIT_KEY="${WATCH_CODER_SUBMIT_KEY:-C-m}"
WATCH_CODER_QUEUE_KEY="${WATCH_CODER_QUEUE_KEY:-Tab}"
WATCH_CODER_BUSY_REGEX="${WATCH_CODER_BUSY_REGEX:-tab to queue message|Working \\(|queued message|Inspecting|⠼|⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏}"
WATCH_ARCH_SUBMIT_KEY="${WATCH_ARCH_SUBMIT_KEY:-C-m}"
WATCH_ARCH_QUEUE_KEY="${WATCH_ARCH_QUEUE_KEY:-Tab}"
WATCH_ARCH_BUSY_REGEX="${WATCH_ARCH_BUSY_REGEX:-tab to queue message|Working \\(|queued message|Inspecting|⠼|⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏}"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

die() {
  echo "[$(ts)] task_watch: $*" >&2
  exit 1
}

extract_ids() {
  # Extract Task IDs from lines like:
  # - [x] **P0-ADMIN-DB-01: ...**
  # - [ ] **P0-ADMIN-DB-01: ...**
  local mark="$1"
  sed -nE "s/^- \\[${mark}\\] \\*\\*([A-Za-z0-9_-]+):.*/\\1/p" "$TASK_FILE" | sort -u
}

count_tasks() {
  rg -c --no-filename '^- \\[[ x]\\] \\*\\*[A-Za-z0-9_-]+:' "$TASK_FILE" 2>/dev/null || true
}

tmux_notify() {
  local msg="$1"
  # Best-effort: do not fail the watcher if tmux isn't reachable.
  $WATCH_TMUX_CMD display-message -t "$WATCH_TMUX_TARGET" "$msg" 2>/dev/null || true
}

monitor_high_demand() {
  # PURPOSE: Auto-handle interactive "high demand" prompts from CLI tools.
  # CONTEXT: Gemini/Codex may show a TUI prompt:
  #   "We are currently experiencing high demand ... 1. Keep trying 2. Stop"
  # This loop presses "1" + Enter (or just Enter) with a cooldown to avoid spamming.
  local target="$WATCH_DEMAND_TARGET"
  local regex="$WATCH_DEMAND_REGEX"
  local choice="$WATCH_DEMAND_CHOICE"
  local cooldown="$WATCH_DEMAND_COOLDOWN_SEC"

  [ -n "$target" ] || return 0

  local last_action_ts=0
  while true; do
    sleep 1

    # Keep this best-effort: if tmux target doesn't exist, do nothing.
    local pane
    pane="$($WATCH_TMUX_CMD capture-pane -pt "$target" -S -160 2>/dev/null || true)"
    [ -n "$pane" ] || continue

    if printf '%s' "$pane" | rg -qi "$regex"; then
      local now
      now="$(date +%s)"
      if [ "$last_action_ts" -eq 0 ] || [ $((now - last_action_ts)) -ge "$cooldown" ]; then
        local msg="[$(ts)] High demand prompt detected in $target — auto-answering (choice=${choice:-<enter>})."
        echo "$msg"
        tmux_notify "$msg"

        # Prefer "Enter" first (usually "Keep trying" is already selected).
        # Only type an explicit choice if the prompt persists after Enter,
        # to avoid leaking "1" into the next screen after the prompt closes.
        $WATCH_TMUX_CMD send-keys -t "$target" "Enter" 2>/dev/null || true
        sleep 0.2

        pane="$($WATCH_TMUX_CMD capture-pane -pt "$target" -S -160 2>/dev/null || true)"
        if [ -n "$pane" ] && printf '%s' "$pane" | rg -qi "$regex"; then
          if [ -n "$choice" ]; then
            $WATCH_TMUX_CMD send-keys -t "$target" "$choice" 2>/dev/null || true
            sleep 0.1
          fi
          $WATCH_TMUX_CMD send-keys -t "$target" "Enter" 2>/dev/null || true
        fi

        last_action_ts="$now"
      fi
    fi
  done
}

is_pane_busy() {
  local target="$1"
  local busy_regex="$2"
  if [ -z "$target" ]; then
    return 1
  fi
  local pane
  pane="$($WATCH_TMUX_CMD capture-pane -pt "$target" -S -120 2>/dev/null || true)"
  printf '%s' "$pane" | rg -q "$busy_regex"
}

send_pane_prompt() {
  local target="$1"
  local prompt="$2"
  local queue_key="$3"
  local submit_key="$4"
  local busy_regex="$5"

  if [ -z "$target" ]; then
    return 0
  fi

  # 1. Reset TUI state and ensure focus on input
  $WATCH_TMUX_CMD send-keys -t "$target" "Escape" 2>/dev/null || true
  sleep 0.1
  $WATCH_TMUX_CMD send-keys -t "$target" "$submit_key" 2>/dev/null || true
  sleep 0.2

  # 2. Send the prompt text
  $WATCH_TMUX_CMD send-keys -t "$target" "$prompt" 2>/dev/null || true
  sleep 1.2

  # 3. Submit logic:
  if is_pane_busy "$target" "$busy_regex"; then
    # If busy, we MUST use queue key (Tab) then submit
    $WATCH_TMUX_CMD send-keys -t "$target" "$queue_key" 2>/dev/null || true
    sleep 0.3
    $WATCH_TMUX_CMD send-keys -t "$target" "$submit_key" 2>/dev/null || true
  else
    # Direct submit. Send multiple variations of 'Enter' with small pauses.
    $WATCH_TMUX_CMD send-keys -t "$target" "$submit_key" 2>/dev/null || true
    sleep 0.1
    $WATCH_TMUX_CMD send-keys -t "$target" "Enter" 2>/dev/null || true
    sleep 0.1
    $WATCH_TMUX_CMD send-keys -t "$target" "C-j" 2>/dev/null || true
    sleep 0.1
    $WATCH_TMUX_CMD send-keys -t "$target" "C-m" 2>/dev/null || true
  fi
}

send_arch_prompt() {
  if [ -n "$WATCH_ARCH_TARGET" ]; then
    echo "[$(ts)] READY_FOR_REVIEW: отправляю промпт в $WATCH_ARCH_TARGET"
    send_pane_prompt "$WATCH_ARCH_TARGET" "$WATCH_ARCH_PROMPT" "$WATCH_ARCH_QUEUE_KEY" "$WATCH_ARCH_SUBMIT_KEY" "$WATCH_ARCH_BUSY_REGEX"
  fi
}

send_coder_prompt() {
  if [ -n "$WATCH_CODER_TARGET" ]; then
    echo "[$(ts)] KICK_CODER: отправляю промпт в $WATCH_CODER_TARGET"
    send_pane_prompt "$WATCH_CODER_TARGET" "$WATCH_CODER_PROMPT" "$WATCH_CODER_QUEUE_KEY" "$WATCH_CODER_SUBMIT_KEY" "$WATCH_CODER_BUSY_REGEX"
  fi
}

[ -n "$WATCH_CODER_PROMPT" ] || WATCH_CODER_PROMPT='@scripts/prompts/coder_kick.md'
[ -n "$WATCH_ARCH_PROMPT" ] || WATCH_ARCH_PROMPT='@scripts/prompts/architect_review.md'

[ -f "$TASK_FILE" ] || die "Task file not found: $TASK_FILE"

echo "[$(ts)] task_watch: watching $TASK_FILE (tmux target: $WATCH_TMUX_TARGET; tmux cmd: $WATCH_TMUX_CMD)"

# Background monitor for interactive CLI TUI prompts.
# (Does not depend on Task.md changes; runs continuously.)
monitor_high_demand &
DEMAND_PID="$!"
trap 'kill "$DEMAND_PID" 2>/dev/null || true' EXIT

prev_done="$(extract_ids x)"
prev_total="$(count_tasks)"
prev_ready_line=""
prev_kick_line=""

# Editors often do atomic replace; watch both close_write and moved_to.
inotifywait -m -q -e close_write,moved_to,create "$TASK_FILE" --format '%e' |
while read -r _event; do
  # Give editors a moment to finish atomic replace.
  sleep 0.05
  [ -f "$TASK_FILE" ] || continue

  cur_done="$(extract_ids x)"
  cur_total="$(count_tasks)"
  cur_ready_line="$(rg "^${WATCH_READY_MARKER}(\\s|$)" "$TASK_FILE" | tail -n 1 || true)"
  cur_kick_line="$(rg "^${WATCH_KICK_MARKER}(\\s|$)" "$TASK_FILE" | tail -n 1 || true)"

  # Detect "READY_FOR_REVIEW" marker change.
  if [ -n "$cur_ready_line" ]; then
    if [ "$cur_ready_line" != "$prev_ready_line" ]; then
      msg="[$(ts)] READY_FOR_REVIEW: маркер найден/изменен в $TASK_FILE — пора делать ревью."
      echo "$msg"
      tmux_notify "$msg"
      send_arch_prompt
    fi
  fi
  prev_ready_line="$cur_ready_line"

  # Detect "KICK_CODER" marker change.
  if [ -n "$cur_kick_line" ]; then
    if [ "$cur_kick_line" != "$prev_kick_line" ]; then
      msg="[$(ts)] KICK_CODER: маркер найден/изменен — отправляю промпт в $WATCH_CODER_TARGET"
      echo "$msg"
      tmux_notify "$msg"
      send_coder_prompt
    fi
  fi
  prev_kick_line="$cur_kick_line"

  # New completions since last tick.
  new_done="$(comm -13 <(printf '%s\n' "$prev_done") <(printf '%s\n' "$cur_done") || true)"
  if [ -n "$new_done" ]; then
    one_line="$(echo "$new_done" | tr '\n' ' ' | sed -E 's/\\s+/ /g' | sed -E 's/\\s+$//')"
    msg="[$(ts)] READY_FOR_REVIEW: новые выполненные задачи: $one_line"
    echo "$msg"
    tmux_notify "$msg"
    # No auto-architect prompt here to avoid duplicate triggers.
  fi

  # Detect accidental task deletions (protocol violation).
  if [ -n "$prev_total" ] && [ -n "$cur_total" ] && [ "$cur_total" -lt "$prev_total" ]; then
    warn="[$(ts)] WARNING: количество задач уменьшилось ($prev_total -> $cur_total). Проверь, что это осознанная архивация (Task_ARCHIVE.md), а не потеря задач."
    echo "$warn"
    tmux_notify "$warn"
  fi

  prev_done="$cur_done"
  prev_total="$cur_total"
done
