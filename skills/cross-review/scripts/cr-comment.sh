#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: cr-comment.sh <command> [args...]

GitHub PR comment operations.

Commands:
  post <body>                Post comment, print node ID
  post --stdin               Post comment from stdin
  edit <node_id> <body>      Edit comment
  edit <node_id> --stdin     Edit comment from stdin
  delete <node_id>           Delete comment
  list                       List DUO/CR comments
  review-post <body> <json>  Post PR review with inline comments

Environment (required):
  CR_WORKSPACE    Workspace path (reads repo, pr-number, pr-node-id from state/)
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

CMD="$1"
shift

if [[ -z "${CR_WORKSPACE:-}" ]]; then
  echo "Error: CR_WORKSPACE not set" >&2
  exit 1
fi

REPO="$(cat "$CR_WORKSPACE/state/repo")"
PR_NUMBER="$(cat "$CR_WORKSPACE/state/pr-number")"
PR_NODE_ID="$(cat "$CR_WORKSPACE/state/pr-node-id")"

case "$CMD" in
  post)
    BODY=""
    if [[ "${1:-}" == "--stdin" ]]; then
      BODY="$(cat)"
    else
      BODY="${1:-}"
    fi

    if [[ -z "$BODY" ]]; then
      echo "Error: empty body" >&2
      exit 1
    fi

    BODY_JSON=$(printf '%s' "$BODY" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
    QUERY="mutation { addComment(input: {subjectId: \"$PR_NODE_ID\", body: $BODY_JSON}) { commentEdge { node { id } } } }"

    RESULT=$(gh api graphql -f "query=$QUERY")
    NODE_ID=$(echo "$RESULT" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["data"]["addComment"]["commentEdge"]["node"]["id"])')
    echo "$NODE_ID"
    ;;

  edit)
    NODE_ID="${1:-}"
    shift || true
    BODY=""
    if [[ "${1:-}" == "--stdin" ]]; then
      BODY="$(cat)"
    else
      BODY="${1:-}"
    fi

    if [[ -z "$NODE_ID" || -z "$BODY" ]]; then
      echo "Error: node_id and body required" >&2
      exit 1
    fi

    BODY_JSON=$(printf '%s' "$BODY" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
    QUERY="mutation { updateIssueComment(input: {id: \"$NODE_ID\", body: $BODY_JSON}) { issueComment { id } } }"

    gh api graphql -f "query=$QUERY" >/dev/null
    echo "Updated $NODE_ID"
    ;;

  delete)
    NODE_ID="${1:-}"
    if [[ -z "$NODE_ID" ]]; then
      echo "Error: node_id required" >&2
      exit 1
    fi

    QUERY="mutation { deleteIssueComment(input: {id: \"$NODE_ID\"}) { clientMutationId } }"
    gh api graphql -f "query=$QUERY" >/dev/null
    echo "Deleted $NODE_ID"
    ;;

  list)
    gh pr view "$PR_NUMBER" --repo "$REPO" \
      --json comments \
      -q '.comments[] | select(.body | test("<!-- cr-")) | {id: .id, marker: (.body | capture("<!-- (?<m>cr-[a-z0-9-]+) -->") | .m), createdAt: .createdAt}' \
      2>/dev/null || echo "No comments found"
    ;;

  review-post)
    BODY="${1:-}"
    COMMENTS_JSON="${2:-[]}"

    COMMIT_SHA=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json headRefOid -q '.headRefOid' 2>/dev/null || \
                 gh api "repos/$REPO/pulls/$PR_NUMBER" -q '.head.sha')

    PAYLOAD=$(python3 -c "
import json, sys
print(json.dumps({
    'commit_id': '$COMMIT_SHA',
    'body': sys.argv[1],
    'event': 'COMMENT',
    'comments': json.loads(sys.argv[2]) if sys.argv[2] != '[]' else []
}))
" "$BODY" "$COMMENTS_JSON")

    OWNER="${REPO%%/*}"
    REPO_NAME="${REPO##*/}"

    RESULT=$(echo "$PAYLOAD" | gh api "/repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/reviews" --method POST --input -)
    REVIEW_ID=$(echo "$RESULT" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("id","?"))')
    echo "Created review $REVIEW_ID"
    ;;

  *)
    echo "Unknown command: $CMD" >&2
    usage
    exit 1
    ;;
esac
