#!/bin/bash
# 清理所有 duo 评论（包括 progress）
# 用法: cleanup-comments.sh <PR_NUMBER> <REPO>

PR_NUMBER=$1
REPO=$2

if [ -n "$GH_TOKEN" ]; then
  export GH_TOKEN
fi

echo "清理 PR #$PR_NUMBER 的所有 duo 评论..."

# 使用 REST API 获取所有评论，筛选 duo 相关的
IDS=$(gh api "repos/$REPO/issues/$PR_NUMBER/comments" --jq '.[] | select(.body | contains("<!-- duo-")) | .id')

if [ -z "$IDS" ]; then
  echo "没有需要清理的评论"
  exit 0
fi

# 逐个删除 (REST API)
for id in $IDS; do
  echo "删除评论 ID: $id"
  gh api -X DELETE "repos/$REPO/issues/comments/$id" 2>/dev/null
  sleep 0.3
done

echo "清理完成"
