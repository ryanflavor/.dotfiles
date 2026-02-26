# 阶段 3: 交叉确认 - Agent

与对方 Agent 讨论审查分歧，对每个问题达成共识。

## 你的职责

1. 创建占位 PR 评论
2. 分析对方的审查发现
3. 对每个问题给出判断并说明理由
4. 更新 PR 评论为最终结论
5. 写入结果文件 + sentinel

---

## 1. 创建占位评论

```bash
TIMESTAMP=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')
```

### Agent icon

| Agent | Icon |
|-------|------|
| claude | `<img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claude-color.svg' width='14' />` |
| gpt | `<img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/openai.svg' width='14' />` |

占位评论格式：

```markdown
<!-- cr-crosscheck -->
## 🤝 交叉确认
> 🕐 {TIMESTAMP}

### 讨论中...

{ICON} **{AGENT}**: 分析问题中...
```

用 `cr-comment.sh post` 发布，将 node ID 保存到 `$CR_WORKSPACE/comments/cr-crosscheck.id`

**注意**：如果 `$CR_WORKSPACE/comments/cr-crosscheck.id` 已存在（说明对方 Agent 已创建占位），**跳过创建**，直接使用已有评论 ID 进行后续更新。

---

## 2. 分析并判断

### 判断选项

- 🔧 **Fix** - 确认需要修复，说明理由
- ⏭️ **Skip** - 跳过（误报 / 不值得修复），说明理由

### 规则

- 独立思考，不要盲目同意对方
- 如果对方的发现有道理，坦率承认
- 如果不同意，清楚说明你的理由
- 聚焦事实和代码，不做人身判断

---

## 3. 更新 PR 评论

分析完成后，用 `cr-comment.sh edit <NODE_ID>` 更新评论，追加你的分析：

```markdown
<!-- cr-crosscheck -->
## 🤝 交叉确认
> 🕐 {TIMESTAMP}

### 对话记录

{ICON_CLAUDE} **Claude**: 我认为 Issue1 需要修复，理由是...

{ICON_GPT} **GPT**: 同意 Issue1。对于 Issue2...

{ICON_CLAUDE} **Claude**: Issue2 也同意，达成共识。

### 结论

| 问题 | 状态 | 说明 |
|------|------|------|
| Issue1 | 🔧 Fix | 双方同意 |
| Issue2 | ⏭️ Skip | 误报 |
```

---

## 4. 输出格式（结果文件）

```markdown
# Cross-Check Analysis

## Issues

### Issue 1: {描述}
- **My judgment**: 🔧 Fix / ⏭️ Skip
- **Reason**: {1-2 句理由}

### Issue 2: {描述}
- **My judgment**: 🔧 Fix / ⏭️ Skip
- **Reason**: {1-2 句理由}

## Summary Table

| Issue | Judgment | Reason |
|-------|----------|--------|
| ... | 🔧 Fix | ... |
| ... | ⏭️ Skip | ... |
```

---

## 5. 完成

将结果写入指定的 result 文件，然后创建 sentinel `.done` 文件。
