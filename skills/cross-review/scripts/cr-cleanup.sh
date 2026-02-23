#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: cr-cleanup.sh [--keep-workspace]

Kill all agent tmux sessions and optionally remove workspace.

Options:
  --keep-workspace    Don't remove workspace directory

Environment (required):
  CR_WORKSPACE    Workspace path
  CR_SOCKET       tmux socket path (or reads from $CR_WORKSPACE/socket.path)
USAGE
}

KEEP_WORKSPACE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-workspace) KEEP_WORKSPACE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "${CR_WORKSPACE:-}" ]]; then
  echo "Error: CR_WORKSPACE not set" >&2
  exit 1
fi

CR_SOCKET="${CR_SOCKET:-$(cat "$CR_WORKSPACE/socket.path" 2>/dev/null || echo "")}"

# Kill tmux server
if [[ -n "$CR_SOCKET" ]] && [[ -S "$CR_SOCKET" ]]; then
  echo "Killing tmux server on $CR_SOCKET..."
  tmux -S "$CR_SOCKET" kill-server 2>/dev/null || true
  rm -f "$CR_SOCKET"
  echo "  Done"
fi

# Remove workspace
if [[ "$KEEP_WORKSPACE" == "false" ]]; then
  echo "Removing workspace: $CR_WORKSPACE"
  rm -rf "$CR_WORKSPACE"
  echo "  Done"
else
  echo "Workspace preserved: $CR_WORKSPACE"
fi

echo "Cleanup complete"
