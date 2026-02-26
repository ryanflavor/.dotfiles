#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: cr-status.sh

Show cross-review status: workspace state, agent sessions, results.

Environment (required):
  CR_WORKSPACE    Workspace path
  CR_SOCKET       tmux socket path (or reads from $CR_WORKSPACE/socket.path)
USAGE
}

if [[ -z "${CR_WORKSPACE:-}" ]]; then
  echo "Error: CR_WORKSPACE not set" >&2
  exit 1
fi

CR_SOCKET="${CR_SOCKET:-$(cat "$CR_WORKSPACE/socket.path")}"

echo "=== Cross Review Status ==="
echo ""

# State
echo "--- State ---"
for f in "$CR_WORKSPACE/state/"*; do
  [[ -f "$f" ]] || continue
  KEY=$(basename "$f")
  VALUE=$(cat "$f")
  printf "  %-15s %s\n" "$KEY:" "$VALUE"
done
echo ""

# Sessions
echo "--- Agent Sessions ---"
if tmux -S "$CR_SOCKET" list-sessions -F '#{session_name} #{session_attached} #{session_created_string}' 2>/dev/null; then
  :
else
  echo "  (no tmux server running)"
fi
echo ""

# Results
echo "--- Results ---"
if ls "$CR_WORKSPACE/results/"*.md 2>/dev/null; then
  for f in "$CR_WORKSPACE/results/"*.md; do
    LINES=$(wc -l < "$f")
    DONE=""
    [[ -f "${f%.md}.done" ]] && DONE=" [DONE]"
    echo "  $(basename "$f") (${LINES} lines)${DONE}"
  done
else
  echo "  (no results yet)"
fi
echo ""

# Comments
echo "--- PR Comments ---"
if ls "$CR_WORKSPACE/comments/"*.id 2>/dev/null; then
  for f in "$CR_WORKSPACE/comments/"*.id; do
    MARKER=$(basename "$f" .id)
    ID=$(cat "$f")
    echo "  $MARKER: $ID"
  done
else
  echo "  (no comments tracked)"
fi
