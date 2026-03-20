#!/usr/bin/env bash
set -euo pipefail

# Reliable prompt sender for Gemini/Codex CLI panes in tmux.
# Handles both idle and "tab to queue message" busy states.
#
# Usage:
#   ./scripts/send_tmux_prompt.sh <target-pane> "<prompt>"
# Example:
#   ./scripts/send_tmux_prompt.sh astro2:0.0 "@scripts/prompts/architect_review.md"

TARGET="${1:-astro2:0.0}"
PROMPT="${2:-@scripts/prompts/architect_review.md}"
TMUX_CMD="${TMUX_CMD:-sudo tmux}"
BUSY_REGEX="${BUSY_REGEX:-tab to queue message|Working \\(|queued message|Inspecting|⠼|⠋|⠙|⠹|⠸|⠴|⠦|⠧|⠇|⠏}"
HIGH_DEMAND_REGEX="${HIGH_DEMAND_REGEX:-We are currently experiencing high demand|Keep trying}"
INTERRUPTED_REGEX="${INTERRUPTED_REGEX:-Conversation interrupted|Something went wrong|Hit /feedback}"

is_busy() {
  local pane
  pane="$($TMUX_CMD capture-pane -pt "$TARGET" -S -120 2>/dev/null || true)"
  printf '%s' "$pane" | rg -qi "$BUSY_REGEX"
}

has_high_demand() {
  local pane
  pane="$($TMUX_CMD capture-pane -pt "$TARGET" -S -120 2>/dev/null || true)"
  printf '%s' "$pane" | rg -qi "$HIGH_DEMAND_REGEX"
}

has_interrupted() {
  local pane
  pane="$($TMUX_CMD capture-pane -pt "$TARGET" -S -120 2>/dev/null || true)"
  printf '%s' "$pane" | rg -qi "$INTERRUPTED_REGEX"
}

echo "[send_tmux_prompt] target=$TARGET"
echo "[send_tmux_prompt] prompt=$PROMPT"

# Light reset + focus input.
$TMUX_CMD send-keys -t "$TARGET" Escape 2>/dev/null || true
sleep 0.1

# Type prompt text.
$TMUX_CMD send-keys -t "$TARGET" "$PROMPT" 2>/dev/null || true
sleep 0.25

# Submit according to state.
if has_high_demand; then
  # Select "Keep trying"
  $TMUX_CMD send-keys -t "$TARGET" "1" 2>/dev/null || true
  sleep 0.12
  $TMUX_CMD send-keys -t "$TARGET" Enter 2>/dev/null || true
  sleep 0.2
fi

if has_interrupted; then
  # Clear the interrupted prompt and re-send.
  $TMUX_CMD send-keys -t "$TARGET" Enter 2>/dev/null || true
  sleep 0.2
  $TMUX_CMD send-keys -t "$TARGET" "$PROMPT" 2>/dev/null || true
  sleep 0.25
fi

if is_busy; then
  $TMUX_CMD send-keys -t "$TARGET" Tab 2>/dev/null || true
  sleep 0.12
  $TMUX_CMD send-keys -t "$TARGET" Enter 2>/dev/null || true
else
  $TMUX_CMD send-keys -t "$TARGET" Enter 2>/dev/null || true
  sleep 0.08
  $TMUX_CMD send-keys -t "$TARGET" C-m 2>/dev/null || true
fi

echo "[send_tmux_prompt] submitted"
