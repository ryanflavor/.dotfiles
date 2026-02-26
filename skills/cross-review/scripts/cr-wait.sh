#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: cr-wait.sh <agent_name> <stage_tag> [timeout_seconds]

Wait for an agent to complete by polling for sentinel file.

The sentinel file is: $CR_WORKSPACE/results/{agent}-{stage_tag}.done

Arguments:
  agent_name      Agent session name (e.g., claude, gpt)
  stage_tag       Stage identifier (e.g., r1, crosscheck, fix, verify)
  timeout_seconds Timeout in seconds (default: 600)

Environment (required):
  CR_WORKSPACE    Workspace path
  CR_SOCKET       tmux socket path (or reads from $CR_WORKSPACE/socket.path)
USAGE
}

if [[ $# -lt 2 ]]; then
  usage
  exit 1
fi

AGENT="$1"
STAGE_TAG="$2"
TIMEOUT="${3:-600}"

if [[ -z "${CR_WORKSPACE:-}" ]]; then
  echo "Error: CR_WORKSPACE not set" >&2
  exit 1
fi

CR_SOCKET="${CR_SOCKET:-$(cat "$CR_WORKSPACE/socket.path")}"

SENTINEL="$CR_WORKSPACE/results/${AGENT}-${STAGE_TAG}.done"
RESULT="$CR_WORKSPACE/results/${AGENT}-${STAGE_TAG}.md"

START=$(date +%s)
DEADLINE=$((START + TIMEOUT))

echo "Waiting for $AGENT ($STAGE_TAG)... [timeout: ${TIMEOUT}s]"

while true; do
  # Primary: check sentinel file
  if [[ -f "$SENTINEL" ]]; then
    echo "$AGENT ($STAGE_TAG): DONE"
    if [[ -f "$RESULT" ]]; then
      echo "Result: $RESULT ($(wc -l < "$RESULT") lines)"
    fi
    exit 0
  fi

  # Secondary: check if tmux session is still alive
  if ! tmux -S "$CR_SOCKET" has-session -t "$AGENT" 2>/dev/null; then
    echo "Error: $AGENT session terminated unexpectedly" >&2
    exit 1
  fi

  # Tertiary: check if pane process is dead (remain-on-exit keeps session alive after crash)
  PANE_DEAD=$(tmux -S "$CR_SOCKET" display-message -t "$AGENT":0.0 -p '#{pane_dead}' 2>/dev/null || echo "")
  if [[ "$PANE_DEAD" == "1" ]]; then
    echo "Error: $AGENT pane process has died (remain-on-exit kept session alive)" >&2
    echo "Last pane output:" >&2
    tmux -S "$CR_SOCKET" capture-pane -p -J -t "$AGENT":0.0 -S -30 2>/dev/null >&2 || true
    exit 1
  fi

  # Timeout check
  NOW=$(date +%s)
  if (( NOW >= DEADLINE )); then
    echo "Timed out after ${TIMEOUT}s waiting for $AGENT ($STAGE_TAG)" >&2
    echo "Last pane output:" >&2
    tmux -S "$CR_SOCKET" capture-pane -p -J -t "$AGENT":0.0 -S -30 2>/dev/null >&2 || true
    exit 1
  fi

  # Progress indicator every 30s
  ELAPSED=$((NOW - START))
  if (( ELAPSED % 30 == 0 && ELAPSED > 0 )); then
    echo "  ... ${ELAPSED}s elapsed"
  fi

  sleep 1
done
