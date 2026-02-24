# 阶段 4: 修复 - Agent

修复交叉确认中确认的问题。

## 步骤

1. 创建占位 PR 评论
2. 创建修复分支
3. 修复问题
4. 提交代码
5. 推送并更新评论
6. 写入结果文件

---

## 1. 创建占位评论

```bash
TIMESTAMP=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')
```

### Agent icon

| Agent | Icon |
|-------|------|
| claude | `<img src='https://unpkg.com/@lobehub/icons-static-svg@latest/icons/claude-color.svg' width='18' />` |

占位评论格式：

```markdown
<!-- cr-claude-fix -->
## {ICON} Claude 修复中
> 🕐 {TIMESTAMP}

{RANDOM_ING_WORD}...
```

**{RANDOM_ING_WORD}**: Fixing, Patching, Refactoring, Stitching things together 等，自己想一个有趣的！

---

## 2. 创建修复分支

格式: `cr/pr{NUMBER}-{简要描述}`

```bash
PR_NUMBER=$(cat "$CR_WORKSPACE/state/pr-number")
BRANCH="cr/pr${PR_NUMBER}-{简要语义化描述}"
git checkout -b "$BRANCH"
echo "$BRANCH" > "$CR_WORKSPACE/state/s4-branch"
```

---

## 3. 修复问题

根据任务文件中列出的问题进行修复。

---

## 4. 提交代码

```bash
git add -A
git commit -m 'fix(cr): ...'
```

---

## 5. 推送并更新评论

```bash
# 安全检查
[[ "$BRANCH" == "main" || "$BRANCH" == "master" ]] && echo "ERROR: Cannot push to main" && exit 1
git push origin "$BRANCH" --force
```

评论格式：

```markdown
<!-- cr-claude-fix -->
## Fix by claude
> 🕐 {TIMESTAMP}

### Changes
**Commit**: [`<short_hash>`](https://github.com/{REPO}/commit/{full_hash})

{修复说明}

### Files Changed
{文件列表}
```

---

## 6. 切回 PR 分支并写入结果

```bash
BRANCH_PR=$(cat "$CR_WORKSPACE/state/branch")
git checkout "$BRANCH_PR"
```

将修复摘要写入 `$CR_WORKSPACE/results/claude-fix.md`，
然后创建 sentinel：`touch $CR_WORKSPACE/results/claude-fix.done`
