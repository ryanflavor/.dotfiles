#!/bin/bash
# 编辑评论
# 用法: edit-comment.sh <COMMENT_ID> <NEW_BODY>
# 注意: 只需要两个参数！不需要传 REPO！
# 示例: edit-comment.sh IC_kwDOQX6cp87f3jZd "新的评论内容"

COMMENT_ID=$1
NEW_BODY=$2

# 参数检查
if [ -z "$COMMENT_ID" ] || [ -z "$NEW_BODY" ]; then
  echo "用法: edit-comment.sh <COMMENT_ID> <NEW_BODY>"
  echo "示例: edit-comment.sh IC_kwDOQX6cp87f3jZd \"新的评论内容\""
  exit 1
fi

# 使用 GH_TOKEN 环境变量（GitHub Actions 中为 bot 身份）
if [ -n "$GH_TOKEN" ]; then
  export GH_TOKEN
fi

gh api graphql -f query="mutation { updateIssueComment(input: {id: \"$COMMENT_ID\", body: $(echo "$NEW_BODY" | jq -Rs .)}) { issueComment { id } } }"
