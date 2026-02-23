# 阶段 4: 验证 - Agent

验证修复是否正确。

## 步骤

1. 创建占位 PR 评论
2. 查看修复 diff
3. 验证代码
4. 更新评论
5. 写入结果文件

---

## 1. 创建占位评论

```bash
TIMESTAMP=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')
```

### Agent icon

| Agent | Icon |
|-------|------|
| gpt | `<img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/openai.svg' width='18' />` |

占位评论格式：

```markdown
<!-- cr-gpt-verify -->
## {ICON} GPT 验证中
> 🕐 {TIMESTAMP}

{RANDOM_ING_WORD}...
```

**{RANDOM_ING_WORD}**: Verifying, Inspecting, Cross-checking, Running mental tests 等，自己想一个有趣的！

---

## 2. 查看修复

```bash
FIX_BRANCH=$(cat "$CR_WORKSPACE/state/s4-branch")
BASE=$(cat "$CR_WORKSPACE/state/base")
git fetch origin "$FIX_BRANCH"
git diff "origin/$BASE...origin/$FIX_BRANCH"
```

---

## 3. 验证

检查：
- 问题是否真正解决
- 是否引入新问题
- 代码质量是否符合规范

---

## 4. 更新评论

```markdown
<!-- cr-gpt-verify -->
## Verification by gpt
> 🕐 {TIMESTAMP}

### Result
✅ PASS / ❌ FAIL

### Details
{如果失败，说明原因}
```

---

## 5. 写入结果

将验证结果写入 `$CR_WORKSPACE/results/gpt-verify.md`。

结果第一行必须是 `PASS` 或 `FAIL`（Orchestrator 据此判断下一步）。

最后创建 sentinel：`touch $CR_WORKSPACE/results/gpt-verify.done`
