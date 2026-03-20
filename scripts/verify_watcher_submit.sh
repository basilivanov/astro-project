#!/usr/bin/env bash
set -euo pipefail

# PURPOSE: Verify that task_watch.sh actually SUBMITS the prompt.
# It checks if the prompt text is still in the input line after a kick.

TARGET_PANE="${1:-astro:0.0}"
TMUX_CMD="${TMUX_CMD:-sudo tmux}"
KICK_SCRIPT="./scripts/kick_coder.sh"

echo "--- Verifying Watcher Submission on $TARGET_PANE ---"

# 1. Clear pane or ensure we know the state
# (We don't want to disrupt work, so we just look at the bottom)

# 2. Trigger Kick
$KICK_SCRIPT Task.md
echo "KICK_CODER triggered. Waiting 5s for watcher..."
sleep 5

# 3. Capture pane
PANE_CONTENT=$($TMUX_CMD capture-pane -pt "$TARGET_PANE" -S -10)

# 4. Check for unsubmitted prompt
# Propts usually look like: "› @scripts/prompts/..."
# If it's still in the "input" area (usually the last few lines), it failed.
if printf '%s' "$PANE_CONTENT" | grep -q "› @scripts/prompts/"; then
    echo "FAIL: Prompt detected in input area (unsubmitted)."
    printf '%s
' "$PANE_CONTENT" | grep "› @scripts/prompts/"
    exit 1
else
    echo "SUCCESS: No unsubmitted prompt detected."
fi
