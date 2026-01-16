# 阶段 2: 判断共识

**执行者**: Orchestrator

## 流程

```
获取结论 → 判断 → 设置 s2:result → 决定下一阶段
```

## 获取结论

```bash
CODEX=$($S/duo-get.sh $PR_NUMBER s1:codex:conclusion)
OPUS=$($S/duo-get.sh $PR_NUMBER s1:opus:conclusion)
```

## 判断逻辑

```bash
$S/duo-set.sh $PR_NUMBER stage 2

if [ "$CODEX" = "ok" ] && [ "$OPUS" = "ok" ]; then
  # 双方都没发现问题
  $S/duo-set.sh $PR_NUMBER s2:result both_ok
  # → 阶段 5
  
elif [ "$CODEX" = "$OPUS" ]; then
  # 双方发现相同级别的问题
  $S/duo-set.sh $PR_NUMBER s2:result same_issues
  # → 阶段 4（直接修复）
  
else
  # 有分歧
  $S/duo-set.sh $PR_NUMBER s2:result divergent
  # → 阶段 3（交叉确认）
fi
```

## 决策树

| Codex | Opus | 结果 | 下一阶段 |
|-------|------|------|----------|
| ok | ok | both_ok | 5 |
| p0 | p0 | same_issues | 4 |
| p1 | p1 | same_issues | 4 |
| ok | p1 | divergent | 3 |
| p0 | p1 | divergent | 3 |
| ... | ... | divergent | 3 |

## 输出

- `s2:result = both_ok | same_issues | divergent`
- 决定下一阶段
