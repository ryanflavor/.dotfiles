# 阶段 1: 并行 PR 审查 - Orchestrator

## 前置条件（CI 已完成）

- Workspace `$CR_WORKSPACE` 已创建，state 文件已写入
- tmux socket `$CR_SOCKET` 已就绪
- 你在 tmux orchestrator session 中运行

## 禁止操作

- 不要执行 `cr-init.sh`（workspace 已就绪）
- 不要执行 `cr-spawn.sh orchestrator`（你就是 orchestrator）
- 不要执行 `cr-cleanup.sh` 或 `kill-server`（CI 负责清理）

## 概述

启动 Claude 和 GPT 并行审查 PR。

## 执行

```bash
echo "1" > "$CR_WORKSPACE/state/stage"

MODEL_CLAUDE="${CR_MODEL_CLAUDE:-custom:claude-opus-4-6}"
MODEL_GPT="${CR_MODEL_GPT:-custom:gpt-5.3-codex}"

# 启动两个 Agent（仅 claude 和 gpt，不要 spawn orchestrator）
$HOME/.factory/skills/cross-review/scripts/cr-spawn.sh claude "$MODEL_CLAUDE"
$HOME/.factory/skills/cross-review/scripts/cr-spawn.sh gpt "$MODEL_GPT"
```

## 发送任务

为每个 Agent 写入任务文件，包含必要上下文：

```bash
REPO=$(cat "$CR_WORKSPACE/state/repo")
PR_NUMBER=$(cat "$CR_WORKSPACE/state/pr-number")
BASE=$(cat "$CR_WORKSPACE/state/base")
BRANCH=$(cat "$CR_WORKSPACE/state/branch")

for AGENT in claude gpt; do
  cat > "$CR_WORKSPACE/tasks/${AGENT}-review.md" << EOF
<system-instruction>
你是 ${AGENT}，cross-review 审查者。
⛔ FIRST STEP: load skill: cross-review
</system-instruction>

# PR Review Task

You are reviewing PR #$PR_NUMBER in $REPO ($BRANCH → $BASE).

## Instructions

Read ~/.factory/skills/cross-review/stages/1-review-agent.md for detailed review guidelines.
注意：先创建占位评论！

## Context

- Repository: $REPO
- PR: #$PR_NUMBER
- Branch: $BRANCH → $BASE
- Workspace: $CR_WORKSPACE
- Your agent name: $AGENT

## Required Output

1. Post a PR comment (placeholder first, then update with findings)
2. Write review findings to: $CR_WORKSPACE/results/${AGENT}-r1.md
3. When FULLY complete, run: touch $CR_WORKSPACE/results/${AGENT}-r1.done
EOF

  # Send to agent (NOTE: -l and Enter must be separate send-keys calls)
  tmux -S "$CR_SOCKET" send-keys -t "$AGENT":0.0 -l "Read and execute $CR_WORKSPACE/tasks/${AGENT}-review.md"
  tmux -S "$CR_SOCKET" send-keys -t "$AGENT":0.0 Enter
done
```

## 等待

```bash
$HOME/.factory/skills/cross-review/scripts/cr-wait.sh claude r1 600 &
$HOME/.factory/skills/cross-review/scripts/cr-wait.sh gpt r1 600 &
wait
```

两个 Agent 都完成后，读取结果并进入阶段 2。
