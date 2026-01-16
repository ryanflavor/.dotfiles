# 阶段 5: 汇总

**执行者**: Orchestrator

## 获取状态

```bash
$S/duo-set.sh $PR_NUMBER stage 5

RESULT=$($S/duo-get.sh $PR_NUMBER s2:result)
CODEX_CONCLUSION=$($S/duo-get.sh $PR_NUMBER s1:codex:conclusion)
OPUS_CONCLUSION=$($S/duo-get.sh $PR_NUMBER s1:opus:conclusion)
PROGRESS_ID=$($S/duo-get.sh $PR_NUMBER progress_comment)
```

## 生成汇总

根据 `$RESULT` 生成汇总内容：

### both_ok
```markdown
<!-- duo-review-summary -->
## ✅ Duo Review | PR #$PR_NUMBER

| Agent | 结论 |
|-------|------|
| Codex | ✅ 未发现问题 |
| Opus | ✅ 未发现问题 |

**结论**: 双方都未发现问题，PR 可以合并。
```

### same_issues（修复后）
```markdown
<!-- duo-review-summary -->
## ✅ Duo Review | PR #$PR_NUMBER

| Agent | 结论 |
|-------|------|
| Codex | 发现问题 → 验证通过 |
| Opus | 发现问题 → 已修复 |

**修复分支**: [bot🤖/pr-$PR_NUMBER](...)

**结论**: 问题已修复并验证通过。
```

### divergent（交叉确认后）
```markdown
<!-- duo-review-summary -->
## 🔄 Duo Review | PR #$PR_NUMBER

| Agent | 结论 |
|-------|------|
| Codex | ... |
| Opus | ... |

**交叉确认**: N 轮
**结论**: (达成共识/未达成共识)
```

## 更新评论

```bash
echo "$SUMMARY_CONTENT" | $S/edit-comment.sh $PROGRESS_ID
```

## 清理

```bash
# Redis 会自动过期（2小时），或手动清理
# redis-cli DEL "duo:$PR_NUMBER"
```
