#!/usr/bin/env bash
set -euo pipefail

# Creates/starts a "watch" window in an existing tmux session to monitor Task.md updates.
#
# By default this assumes tmux server is running as root (common if you started tmux via sudo),
# so it uses `sudo tmux`. Override with TMUX_CMD="tmux".
#
# Usage:
#   ./scripts/tmux_watch_setup.sh [tmux_session]
#
# Example:
#   ./scripts/tmux_watch_setup.sh astro2

SESSION="${1:-astro2}"
TMUX_CMD="${TMUX_CMD:-sudo tmux}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_FILE="${TASK_FILE:-$REPO_ROOT/Task.md}"

WINDOW_NAME="${WINDOW_NAME:-watch}"

exists_window() {
  $TMUX_CMD list-windows -t "$SESSION" -F '#{window_name}' 2>/dev/null | rg -qx "$WINDOW_NAME"
}

main() {
  if ! $TMUX_CMD has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session not found: $SESSION" >&2
    exit 1
  fi
  if [ ! -f "$TASK_FILE" ]; then
    echo "Task file not found: $TASK_FILE" >&2
    exit 1
  fi

  if exists_window; then
    echo "tmux window already exists: $SESSION:$WINDOW_NAME"
    exit 0
  fi

  # The watcher prints into the window; it also best-effort notifies the main session via display-message.
  $TMUX_CMD new-window -t "$SESSION" -n "$WINDOW_NAME" \
    \"cd '$REPO_ROOT' && WATCH_TMUX_TARGET='$SESSION' WATCH_TMUX_CMD='$TMUX_CMD' WATCH_READY_MARKER='${WATCH_READY_MARKER:-READY_FOR_REVIEW}' WATCH_KICK_MARKER='${WATCH_KICK_MARKER:-KICK_CODER}' WATCH_CODER_TARGET='${WATCH_CODER_TARGET:-}' WATCH_DEMAND_CHOICE='1' ./scripts/task_watch.sh '$TASK_FILE'\"

  echo "created tmux window: $SESSION:$WINDOW_NAME"
}

main "$@"
