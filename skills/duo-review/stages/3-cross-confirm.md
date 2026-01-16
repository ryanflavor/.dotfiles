# 阶段 3: 交叉确认（最多 10 轮）

**执行者**: Orchestrator + Opus + Codex

## 流程

```
ROUND=2 → Opus 回应 Codex → Codex 回应 Opus → 判断共识
    ↑                                              ↓
    └──────────── 未达成共识, ROUND++ ─────────────┘
```

## 初始化

```bash
$S/duo-set.sh $PR_NUMBER stage 3
$S/duo-set.sh $PR_NUMBER s3:round 2
```

## 循环（ROUND <= 10）

### 3.1 启动 Opus 回应

```bash
CODEX_SESSION=$($S/duo-get.sh $PR_NUMBER s1:codex:session)
OPUS_SESSION=$($S/duo-get.sh $PR_NUMBER s1:opus:session)
ROUND=$($S/duo-get.sh $PR_NUMBER s3:round)

$S/opus-resume.sh $OPUS_SESSION "
## 回应 Codex 的审查
读取 PR #$PR_NUMBER 的 Codex 评论，逐个问题回应：
- ✅ 认可: 问题确实存在
- ❌ 不认可: 说明原因

## 完成后
$S/duo-set.sh $PR_NUMBER s3:opus:status done
$S/duo-set.sh $PR_NUMBER s3:opus:agrees <0|1>

## 发布评论
echo '内容' | $S/edit-comment.sh \$COMMENT_ID
"
```

### 3.2 等待 Opus

```bash
$S/duo-wait.sh $PR_NUMBER s3:opus:status done
```

### 3.3 启动 Codex 回应

```bash
$S/codex-resume.sh $CODEX_SESSION "
## 回应 Opus 的审查
读取 PR #$PR_NUMBER 的 Opus 评论，逐个问题回应：
- ✅ 认可: 问题确实存在
- ❌ 不认可: 说明原因

## 完成后
$S/duo-set.sh $PR_NUMBER s3:codex:status done
$S/duo-set.sh $PR_NUMBER s3:codex:agrees <0|1>

## 发布评论
echo '内容' | $S/edit-comment.sh \$COMMENT_ID
"
```

### 3.4 等待 Codex

```bash
$S/duo-wait.sh $PR_NUMBER s3:codex:status done
```

### 3.5 判断共识

```bash
OPUS_AGREES=$($S/duo-get.sh $PR_NUMBER s3:opus:agrees)
CODEX_AGREES=$($S/duo-get.sh $PR_NUMBER s3:codex:agrees)

if [ "$OPUS_AGREES" = "1" ] && [ "$CODEX_AGREES" = "1" ]; then
  $S/duo-set.sh $PR_NUMBER s3:consensus 1
  # → 阶段 4（有问题需修复）或阶段 5（无问题）
else
  # 清除状态，下一轮
  $S/duo-set.sh $PR_NUMBER s3:opus:status pending
  $S/duo-set.sh $PR_NUMBER s3:codex:status pending
  ROUND=$((ROUND + 1))
  $S/duo-set.sh $PR_NUMBER s3:round $ROUND
  # 继续循环
fi
```

## 退出条件

1. `s3:consensus = 1` → 根据结论进入阶段 4 或 5
2. `s3:round > 10` → 强制进入阶段 5
