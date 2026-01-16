# 阶段 1: 并行 PR 审查

**执行者**: Orchestrator + Codex + Opus

## ⚠️ 重要规则

1. **禁止读取脚本内容** - 直接执行，不要检查脚本里写了什么
2. **必须使用 fireAndForget: true** - Codex 和 Opus 必须并行启动，不能串行

## 流程

```
初始化 Redis → 创建占位评论 → 并行启动 Codex/Opus (fireAndForget) → duo-wait 等待完成
```

## 审查指南 (传递给 Codex/Opus)

### Bug 检测规则
只有满足以下**所有**条件才标记为 Bug:
1. 实际影响代码的准确性、性能、安全或可维护性
2. 问题是具体且可操作的（非笼统问题）
3. 修复不需要超出代码库现有标准的严格程度
4. Bug 是本次提交引入的（不标记已存在的问题）
5. 作者知道后很可能会修复
6. 不依赖未说明的假设
7. 能明确指出受影响的代码位置（非猜测）
8. 明显不是故意为之

### 评论规范
- 清楚说明为什么是 Bug
- 恰当传达严重程度
- 简短 - 最多 1 段
- 代码块最多 3 行，用 markdown 包裹
- 清楚说明 Bug 触发的场景/环境
- 客观陈述，不带指责
- 原作者一眼能理解
- 忽略琐碎的风格问题，除非影响可读性或违反文档标准

### Priority 级别
- 🔴 **[P0]** - 必须立即修复，阻塞发布/运行
- 🟠 **[P1]** - 紧急，下个周期内处理
- 🟡 **[P2]** - 普通，待修复
- 🟢 **[P3]** - 低优先级，最好有

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

## 执行步骤
1. 读 REVIEW.md 了解规范
2. gh pr diff $PR_NUMBER --repo $REPO
3. 审查后更新评论: echo '内容' | \$S/edit-comment.sh $CODEX_COMMENT

## Bug 检测规则 (必须同时满足)
- 实际影响代码的准确性/性能/安全/可维护性
- 问题具体可操作（非笼统）
- 本次提交引入的（不标记已存在问题）
- 作者知道后很可能会修复
- 能明确指出受影响代码位置（非猜测）

## 评论规范
- 简短(最多1段)，代码块最多3行
- 清楚说明为什么是Bug和触发场景
- 客观陈述，忽略琐碎风格问题

## 评论格式
<!-- duo-codex-r1 -->
## <img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/openai.svg' width='18' /> Codex | PR #$PR_NUMBER
> 🕐 YYYY-MM-DD HH:MM (GMT+8)

### 发现 (或 '无问题')
- 🔴[P0]/🟠[P1]/🟡[P2]/🟢[P3] 标题 - 原因

### 结论
✅ 无问题 或 列出最高优先级"
```

## 1.4 启动 Opus

**⚠️ 必须使用 Execute 工具的 `fireAndForget: true` 参数！不要读脚本内容！**

脚本会自动写入 Redis（status, session, conclusion）。

```bash
$S/opus-exec.sh $PR_NUMBER "审查 PR #$PR_NUMBER ($REPO)。

## 执行步骤
1. 读 REVIEW.md 了解规范
2. gh pr diff $PR_NUMBER --repo $REPO
3. 审查后更新评论: echo '内容' | \$S/edit-comment.sh $OPUS_COMMENT

## Bug 检测规则 (必须同时满足)
- 实际影响代码的准确性/性能/安全/可维护性
- 问题具体可操作（非笼统）
- 本次提交引入的（不标记已存在问题）
- 作者知道后很可能会修复
- 能明确指出受影响代码位置（非猜测）

## 评论规范
- 简短(最多1段)，代码块最多3行
- 清楚说明为什么是Bug和触发场景
- 客观陈述，忽略琐碎风格问题

## 评论格式
<!-- duo-opus-r1 -->
## <img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claude-color.svg' width='18' /> Opus | PR #$PR_NUMBER
> 🕐 YYYY-MM-DD HH:MM (GMT+8)

### 发现 (或 '无问题')
- 🔴[P0]/🟠[P1]/🟡[P2]/🟢[P3] 标题 - 原因

### 结论
✅ 无问题 或 列出最高优先级"
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
