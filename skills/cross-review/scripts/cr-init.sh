#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: cr-init.sh <repo> <pr_number> <base> <branch> <pr_node_id>

Initialize cross-review workspace and tmux socket.

Arguments:
  repo          Repository (owner/repo)
  pr_number     PR number
  base          Base branch name
  branch        PR branch name
  pr_node_id    PR GraphQL node ID

Environment (optional):
  CR_SOCKET_DIR   Socket directory (default: /tmp/cr-tmux-sockets)
USAGE
}

if [[ $# -lt 5 ]]; then
  usage
  exit 1
fi

REPO="$1"
PR_NUMBER="$2"
BASE="$3"
BRANCH="$4"
PR_NODE_ID="$5"

SAFE_REPO="$(echo "$REPO" | tr '/' '-')"
SOCKET_DIR="${CR_SOCKET_DIR:-/tmp/cr-tmux-sockets}"
WORKSPACE="/tmp/cr-${SAFE_REPO}-${PR_NUMBER}"
SOCKET="$SOCKET_DIR/cr-${SAFE_REPO}-${PR_NUMBER}.sock"

# Cleanup previous run
if [[ -S "$SOCKET" ]]; then
  tmux -S "$SOCKET" kill-server 2>/dev/null || true
fi
rm -rf "$WORKSPACE"

# Create directories
mkdir -p "$SOCKET_DIR"
mkdir -p "$WORKSPACE"/{state,tasks,results,comments}

# Write socket path
echo "$SOCKET" > "$WORKSPACE/socket.path"

# Write state
echo "$REPO"       > "$WORKSPACE/state/repo"
echo "$PR_NUMBER"  > "$WORKSPACE/state/pr-number"
echo "$BASE"       > "$WORKSPACE/state/base"
echo "$BRANCH"     > "$WORKSPACE/state/branch"
echo "$PR_NODE_ID" > "$WORKSPACE/state/pr-node-id"
echo "1"           > "$WORKSPACE/state/stage"

echo "CR_WORKSPACE=$WORKSPACE"
echo "CR_SOCKET=$SOCKET"
echo "Workspace initialized: $WORKSPACE"
