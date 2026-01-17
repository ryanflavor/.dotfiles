# Duo Review - GitHub Actions 配置

## 快速开始

在你的仓库创建 `.github/workflows/duo-review.yml`：

```yaml
name: Duo Review

on:
  pull_request:
    types: [opened, synchronize]

concurrency:
  group: duoduo-${{ github.event.pull_request.number }}
  cancel-in-progress: true

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  review:
    uses: notdp/.dotfiles/.github/workflows/duo-review.yml@main
    with:
      pr_number: ${{ github.event.pull_request.number }}
      pr_branch: ${{ github.head_ref }}
      base_branch: ${{ github.base_ref }}
      repo: ${{ github.repository }}
    secrets:
      # 选择以下任一方式
      # 方式 A: GitHub App
      DUO_APP_ID: ${{ secrets.DUO_APP_ID }}
      DUO_APP_PRIVATE_KEY: ${{ secrets.DUO_APP_PRIVATE_KEY }}
      # 方式 B: GitHub Actions Bot
      # GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 认证方式

### 方式 A：使用 GitHub App（推荐）

评论以你的 GitHub App 身份发布。

**配置步骤**：

1. 创建 GitHub App，配置权限：
   - `Contents`: Read-only
   - `Pull requests`: Read and write
   - `Issues`: Read and write
2. 安装到目标仓库
3. 在仓库 Settings → Secrets and variables → Actions 添加：
   - `DUO_APP_ID`: App ID
   - `DUO_APP_PRIVATE_KEY`: Private Key

```yaml
secrets:
  DUO_APP_ID: ${{ secrets.DUO_APP_ID }}
  DUO_APP_PRIVATE_KEY: ${{ secrets.DUO_APP_PRIVATE_KEY }}
```

### 方式 B：使用 GitHub Actions Bot

评论以 `github-actions[bot]` 身份发布，无需额外配置。

```yaml
secrets:
  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## @Mention 触发

在 PR 评论中 @mention bot 与已有审查交互，创建 `.github/workflows/duo-mention.yml`：

```yaml
name: Duo Mention

on:
  issue_comment:
    types: [created]

concurrency:
  group: duo-mention-${{ github.event.issue.number }}

jobs:
  get-info:
    if: |
      github.event.issue.pull_request &&
      (contains(github.event.comment.body, '@your-bot-name') ||
       (startsWith(github.event.comment.body, '>') &&
        contains(github.event.comment.body, 'Duo Review Summary')))
    runs-on: [self-hosted, macos, arm64]
    outputs:
      runner: ${{ steps.get.outputs.runner }}
      pr_branch: ${{ steps.get.outputs.pr_branch }}
      base_branch: ${{ steps.get.outputs.base_branch }}
    steps:
      - name: Get runner and PR info
        id: get
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 获取 PR 信息
          PR_INFO=$(gh pr view ${{ github.event.issue.number }} --repo ${{ github.repository }} --json baseRefName,headRefName)
          echo "pr_branch=$(echo $PR_INFO | jq -r .headRefName)" >> $GITHUB_OUTPUT
          echo "base_branch=$(echo $PR_INFO | jq -r .baseRefName)" >> $GITHUB_OUTPUT
          
          # 先尝试 Redis
          RUNNER=$(redis-cli HGET "duo:${{ github.event.issue.number }}" runner 2>/dev/null || echo "")
          
          # Redis 没有则从 summary 评论解析
          if [ -z "$RUNNER" ]; then
            RUNNER=$(gh pr view ${{ github.event.issue.number }} --repo ${{ github.repository }} --json comments -q '
              .comments[] | select(.body | contains("<!-- duoduo-summary -->")) | .body
            ' | grep -oE 'Runner: `[^`]+' | head -1 | sed 's/Runner: `//')
          fi
          
          echo "runner=$RUNNER" >> $GITHUB_OUTPUT

  duoduo:
    needs: get-info
    if: needs.get-info.outputs.runner != ''
    uses: notdp/.dotfiles/.github/workflows/duo-mention.yml@main
    with:
      pr_number: ${{ github.event.issue.number }}
      repo: ${{ github.repository }}
      pr_branch: ${{ needs.get-info.outputs.pr_branch }}
      base_branch: ${{ needs.get-info.outputs.base_branch }}
      comment_body: ${{ github.event.comment.body }}
      comment_author: ${{ github.event.comment.user.login }}
      runner: ${{ needs.get-info.outputs.runner }}
      bot_name: your-bot-name
    secrets:
      DUO_APP_ID: ${{ secrets.DUO_APP_ID }}
      DUO_APP_PRIVATE_KEY: ${{ secrets.DUO_APP_PRIVATE_KEY }}
```

将 `@your-bot-name` 替换为你的 GitHub App bot 用户名（如 `@duoduo-bot`）。

**触发方式**：
- `@your-bot-name` 直接 @ bot
- Quote reply Summary 评论

**用途**：审查完成后，通过 @mention 与 Orchestrator 对话，可以：
- 重新发起审查
- 纠正审查结果
- 询问问题

## 前置要求

- **Self-hosted runner**（macOS arm64）
- Runner 上需安装：
  - `droid` CLI（[Factory](https://factory.ai)）
  - `redis-server`
  - `gh` CLI（已认证）
