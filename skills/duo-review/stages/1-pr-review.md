# 阶段 1: 并行 PR 审查

**执行者**: Orchestrator + Codex + Opus

## ⚠️ 重要规则

1. **禁止读取脚本内容** - 直接执行，不要检查脚本里写了什么
2. **必须使用 fireAndForget: true** - Codex 和 Opus 必须并行启动，不能串行

## 流程

```
初始化 Redis → 创建占位评论 → 并行启动 Codex/Opus (fireAndForget) → duo-wait 等待完成
```

## 1.1 初始化

```bash
$S/duo-init.sh $PR_NUMBER $REPO $PR_BRANCH $BASE_BRANCH
```

## 1.2 创建占位评论

```bash
PROGRESS_ID=$($S/post-comment.sh $PR_NUMBER $REPO "<!-- duo-review-progress -->
## 🔄 Duo Review 进度
<img src=\"https://github.com/user-attachments/assets/5ac382c7-e004-429b-8e35-7feb3e8f9c6f\" width=\"14\" /> 审查中...
")

CODEX_COMMENT=$($S/post-comment.sh $PR_NUMBER $REPO "<!-- duo-codex-r1 -->
<img src=\"https://unpkg.com/@lobehub/icons-static-svg@latest/icons/openai.svg\" width=\"18\" /> **Codex** 审查中...
")

OPUS_COMMENT=$($S/post-comment.sh $PR_NUMBER $REPO "<!-- duo-opus-r1 -->
<img src=\"https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claude-color.svg\" width=\"18\" /> **Opus** 审查中...
")

$S/duo-set.sh $PR_NUMBER progress_comment "$PROGRESS_ID"
$S/duo-set.sh $PR_NUMBER s1:codex:comment "$CODEX_COMMENT"
$S/duo-set.sh $PR_NUMBER s1:opus:comment "$OPUS_COMMENT"
```

## 1.3 启动 Codex

**⚠️ 必须使用 Execute 工具的 `fireAndForget: true` 参数！不要读脚本内容！**

脚本会自动写入 Redis（status, session, conclusion）。

```bash
$S/codex-exec.sh $PR_NUMBER "审查 PR #$PR_NUMBER ($REPO)。

1. 读 REVIEW.md 了解规范
2. 用 gh pr diff $PR_NUMBER --repo $REPO 查看变更
3. 审查后用 gh issue comment edit $CODEX_COMMENT --repo $REPO -b BODY 更新评论

评论格式:
<!-- duo-codex-r1 -->
## <img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/openai.svg' width='18' /> Codex | PR #$PR_NUMBER
> 🕐 YYYY-MM-DD HH:MM (GMT+8)

(审查内容)

结论: ✅未发现问题 或 🔴P0 🟠P1 🟡P2 🟢P3"
```

## 1.4 启动 Opus

**⚠️ 必须使用 Execute 工具的 `fireAndForget: true` 参数！不要读脚本内容！**

脚本会自动写入 Redis（status, session, conclusion）。

```bash
$S/opus-exec.sh $PR_NUMBER "审查 PR #$PR_NUMBER ($REPO)。

1. 读 REVIEW.md 了解规范
2. 用 gh pr diff $PR_NUMBER --repo $REPO 查看变更
3. 审查后用 gh issue comment edit $OPUS_COMMENT --repo $REPO -b BODY 更新评论

评论格式:
<!-- duo-opus-r1 -->
## <img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claude-color.svg' width='18' /> Opus | PR #$PR_NUMBER
> 🕐 YYYY-MM-DD HH:MM (GMT+8)

(审查内容)

结论: ✅未发现问题 或 🔴P0 🟠P1 🟡P2 🟢P3"
```

## 1.5 等待完成

```bash
$S/duo-wait.sh $PR_NUMBER s1:codex:status done s1:opus:status done
```

## 输出

完成后 Redis 中有：
- `s1:codex:status = done`
- `s1:codex:session = <UUID>`
- `s1:codex:conclusion = ok|p0|p1|p2|p3`
- `s1:opus:*` 同上

→ 进入阶段 2
