# 阶段 5: 汇总 - Orchestrator

## 禁止操作

- 不要执行 `cr-init.sh`、`cr-cleanup.sh`、`kill-server`
- 不要执行 `cr-spawn.sh orchestrator`
- Cleanup 由 CI workflow 自动处理

生成最终汇总评论，结束审查流程。

## 执行

```bash
echo "5" > "$CR_WORKSPACE/state/stage"
```

## 步骤

### 1. 发布占位评论

```bash
TIMESTAMP=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')
```

```markdown
<!-- cr-summary -->
## ⏳ Cross Review Summary
> 🕐 {TIMESTAMP}

正在生成总结...
```

### 2. 收集所有结果 + 清理旧评论

#### 收集结果

```bash
CLAUDE_REVIEW=$(cat "$CR_WORKSPACE/results/claude-r1.md" 2>/dev/null || echo "N/A")
GPT_REVIEW=$(cat "$CR_WORKSPACE/results/gpt-r1.md" 2>/dev/null || echo "N/A")
S2_RESULT=$(cat "$CR_WORKSPACE/state/s2-result" 2>/dev/null || echo "N/A")
CROSSCHECK=$(cat "$CR_WORKSPACE/results/crosscheck-summary.md" 2>/dev/null || echo "N/A")
FIX_RESULT=$(cat "$CR_WORKSPACE/results/claude-fix.md" 2>/dev/null || echo "N/A")
VERIFY_RESULT=$(cat "$CR_WORKSPACE/results/gpt-verify.md" 2>/dev/null || echo "N/A")
```

#### 清理旧评论

删除 Agent 的中间评论（审查、交叉确认、修复、验证），保留 summary：

```bash
REPO=$(cat "$CR_WORKSPACE/state/repo")
PR_NUMBER=$(cat "$CR_WORKSPACE/state/pr-number")

# 列出所有 cr- 评论（排除 cr-summary），逐个删除
gh pr view "$PR_NUMBER" --repo "$REPO" \
  --json comments \
  -q '.comments[] | select(.body | test("<!-- cr-")) | select(.body | test("<!-- cr-summary -->") | not) | .id' \
| while read -r NODE_ID; do
  [[ -n "$NODE_ID" ]] && $HOME/.factory/skills/cross-review/scripts/cr-comment.sh delete "$NODE_ID"
done
```

### 3. 生成汇总 + inline comments

**注意**：仅在此阶段允许 Orchestrator 读取代码（用于 inline comments）。

```bash
BASE=$(cat "$CR_WORKSPACE/state/base")
BRANCH=$(cat "$CR_WORKSPACE/state/branch")
git diff "origin/$BASE...HEAD"
```

#### 3.1 汇总评论模板

```markdown
<!-- cr-summary -->
## {✅|⚠️} Cross Review Summary
> 🕐 {TIMESTAMP}

### Timeline

| Time (UTC+8) | Event |
|---------------|-------|
| MM-DD HH:MM | Claude & GPT parallel review started |
| ... | ... |

{如有 findings:}
### Findings

| # | Issue | Priority | Status |
|---|-------|----------|--------|
| 1 | ... | 🔴 P0 | ✅ Fixed / ⏭️ Skipped / ⚠️ Unfixed |

{如有修复:}
**Fix branch**: [`{branch}`](https://github.com/{REPO}/compare/{BRANCH}...{fix_branch}) ([`{short_hash}`](https://github.com/{REPO}/commit/{full_hash}))

### Conclusion

| Agent | Model | Verdict |
|-------|-------|---------|
| <img src="https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claude-color.svg" width="16" /> Claude | {model} | {结论} |
| <img src="https://unpkg.com/@lobehub/icons-static-svg@latest/icons/openai.svg" width="16" /> GPT | {model} | {结论} |

**Result**: {一句话总结}

<details>
<summary>Session Info</summary>

- Workspace: `$CR_WORKSPACE`
- Socket: `$CR_SOCKET`
- Claude model: `$CR_MODEL_CLAUDE`
- GPT model: `$CR_MODEL_GPT`
</details>
```

#### 3.2 生成 inline comments（仅已修复的 findings）

**仅针对已修复的 findings** 生成 inline comments，在代码位置标注：
- 问题是什么
- 影响是什么
- 如何修复的

**跳过的 findings 不生成 inline comment**（已在 summary 表格说明跳过原因）。

**⚠️ 关键：inline comment 必须指向原 PR diff 中的问题行**

修复在独立分支（如 `cr/pr20-fix-xxx`），但 inline comment 要发到原 PR 上：

```bash
# 获取原 PR 的 diff（不是修复后的 HEAD）
git diff origin/$BASE...origin/$BRANCH
```

行号必须是**原 PR diff 中有问题的代码行**，而不是修复后的行号。

**JSON 格式：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `path` | ✅ | 文件路径（相对仓库根目录） |
| `line` | ✅ | 结束行号（原 PR diff 中的新文件行号） |
| `start_line` | ❌ | 起始行号（多行时需要，单行时省略） |
| `body` | ✅ | 评论内容（见下方模板） |

**注意**：行号必须在原 PR diff 的变更范围内（新增或修改的行），否则 API 报 422。

**Body 模板：**

```markdown
**<sub><sub>![{P0|P1|P2|P3} Badge]({badge_url})</sub></sub>  {标题}**

{问题描述 1-2 段}

Useful? React with 👍 / 👎.
```

**Badge URLs：**

| 级别 | URL |
|------|-----|
| P0 | `https://img.shields.io/badge/P0-red?style=flat` |
| P1 | `https://img.shields.io/badge/P1-orange?style=flat` |
| P2 | `https://img.shields.io/badge/P2-yellow?style=flat` |
| P3 | `https://img.shields.io/badge/P3-green?style=flat` |

**示例：**

```json
[
  {
    "path": "src/example.py",
    "start_line": 10,
    "line": 12,
    "body": "**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  变量未初始化**\n\n当 timeout 时 `result` 未赋值，后续访问会抛出异常。\n\nUseful? React with 👍 / 👎."
  }
]
```

### 4. 发布

#### 有已修复的 findings → PR review + inline comments

使用 `cr-comment.sh review-post` 发布 PR review（COMMENT 事件）+ inline comments：

```bash
$HOME/.factory/skills/cross-review/scripts/cr-comment.sh review-post "$SUMMARY_BODY" "$INLINE_COMMENTS_JSON"
```

#### 无已修复的 findings → 普通评论

以下情况用普通评论（无 inline）：
- both_ok（双方未发现问题）
- 所有 findings 均为 Skip（误报）

```bash
$HOME/.factory/skills/cross-review/scripts/cr-comment.sh post "$SUMMARY_BODY"
```

### 5. 完成

```bash
echo "done" > "$CR_WORKSPACE/state/stage"
```

完成后 CI workflow 会自动执行 cleanup。
