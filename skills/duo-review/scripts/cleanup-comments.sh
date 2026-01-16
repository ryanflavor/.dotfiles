#!/bin/bash
# 清理旧的 duo 评论（保留 progress）
# 用法: cleanup-comments.sh <PR_NUMBER> <REPO>

PR_NUMBER=$1
REPO=$2

if [ -n "$GH_TOKEN" ]; then
  export GH_TOKEN
fi

echo "清理 PR #$PR_NUMBER 的旧 duo 评论..."

# 获取所有需要删除的评论 ID（排除 progress）
IDS=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json comments -q '
  .comments[] 
  | select(.body | contains("<!-- duo-")) 
  | select(.body | contains("<!-- duo-review-progress -->") | not) 
  | .id
')

if [ -z "$IDS" ]; then
  echo "没有需要清理的评论"
  exit 0
fi

# 逐个删除
for id in $IDS; do
  echo "删除评论: $id"
  gh api graphql -f query="mutation { deleteIssueComment(input: {id: \"$id\"}) { clientMutationId } }" 2>/dev/null
  sleep 0.5  # 避免 rate limit
done

# 验证清理结果
REMAINING=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json comments -q '
  .comments[] 
  | select(.body | contains("<!-- duo-")) 
  | select(.body | contains("<!-- duo-review-progress -->") | not) 
  | .id
' | wc -l | tr -d ' ')

echo "清理完成，剩余 duo 评论: $REMAINING"
