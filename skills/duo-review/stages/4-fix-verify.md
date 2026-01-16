# 阶段 4: 修复验证（最多 10 轮）

**执行者**: Orchestrator + Opus + Codex

## 流程

```
创建分支 → Opus 修复 → push → Codex 验证 → 判断
    ↑                                        ↓
    └──────── 验证失败, ROUND++ ─────────────┘
```

## 初始化

```bash
$S/duo-set.sh $PR_NUMBER stage 4
$S/duo-set.sh $PR_NUMBER s4:round 1
$S/duo-set.sh $PR_NUMBER s4:branch "bot🤖/pr-$PR_NUMBER"

# 创建修复分支
git checkout -b "bot🤖/pr-$PR_NUMBER"
```

## 循环（ROUND <= 10）

### 4.1 启动 Opus 修复

```bash
OPUS_SESSION=$($S/duo-get.sh $PR_NUMBER s1:opus:session)
ROUND=$($S/duo-get.sh $PR_NUMBER s4:round)

$S/opus-resume.sh $OPUS_SESSION "
## 修复共识问题
读取 PR 评论，找到双方都认可的问题，修复它们。

## 要求
- 最小改动
- commit message: fix(duo): 修复内容
- git add + git commit

## 完成后
$S/duo-set.sh $PR_NUMBER s4:opus:status done
$S/duo-set.sh $PR_NUMBER s4:opus:commit \$(git rev-parse HEAD)

## 发布评论
echo '修复内容...' | $S/edit-comment.sh \$COMMENT_ID
"
```

### 4.2 等待 Opus 修复

```bash
$S/duo-wait.sh $PR_NUMBER s4:opus:status done
```

### 4.3 推送修复

```bash
BRANCH=$($S/duo-get.sh $PR_NUMBER s4:branch)
git push origin "$BRANCH" --force
```

### 4.4 启动 Codex 验证

```bash
CODEX_SESSION=$($S/duo-get.sh $PR_NUMBER s1:codex:session)

$S/codex-resume.sh $CODEX_SESSION "
## 验证修复
git diff origin/$PR_BRANCH..HEAD

## 检查
- 问题是否真正解决
- 是否引入新问题

## 完成后
$S/duo-set.sh $PR_NUMBER s4:codex:status done
$S/duo-set.sh $PR_NUMBER s4:verified <0|1>

## 发布评论
评论验证结果
"
```

### 4.5 等待 Codex 验证

```bash
$S/duo-wait.sh $PR_NUMBER s4:codex:status done
```

### 4.6 判断结果

```bash
VERIFIED=$($S/duo-get.sh $PR_NUMBER s4:verified)

if [ "$VERIFIED" = "1" ]; then
  # → 阶段 5
  echo "验证通过"
else
  # 清除状态，下一轮
  $S/duo-set.sh $PR_NUMBER s4:opus:status pending
  $S/duo-set.sh $PR_NUMBER s4:codex:status pending
  ROUND=$((ROUND + 1))
  $S/duo-set.sh $PR_NUMBER s4:round $ROUND
  # 继续循环
fi
```

## 退出条件

1. `s4:verified = 1` → 阶段 5
2. `s4:round > 10` → 强制进入阶段 5
