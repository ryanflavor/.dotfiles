# dotfiles

[English](./README.md)

让 Claude Code、Codex、Droid、Antigravity 共享 commands、skills、droids 和 BMAD 工作流。

## 功能特性

- **36 个 BMAD 工作流命令** - 产品简报、PRD、架构设计、Sprint 规划等
- **10 个 BMAD 代理 (droids)** - PM、架构师、开发者、UX 设计师等
- **bmad-init skill** - 在任意项目中初始化 BMAD

## 安装

```bash
git clone https://github.com/ryanflavor/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles && ./scripts/install.sh
```

## 做了什么

**Commands & Droids:**
```
~/.claude/commands   → ~/.dotfiles/commands (软链)
~/.codex/prompts     → ~/.dotfiles/commands (软链)
~/.factory/commands  → ~/.dotfiles/commands (软链)
~/.factory/droids    → ~/.dotfiles/droids (软链)
~/.gemini/antigravity/global_workflows → ~/.dotfiles/commands (软链)
```

**Skills:**
```
~/.claude/skills                → ~/.dotfiles/skills (软链)
~/.codex/skills                 → ~/.dotfiles/skills (软链)
~/.factory/skills               → ~/.dotfiles/skills (软链)
~/.gemini/antigravity/skills    → ~/.dotfiles/skills (软链)
```

**全局 Agent 配置:**
```
~/.claude/CLAUDE.md  → ~/.dotfiles/agents/AGENTS.md (软链)
~/.factory/AGENTS.md → ~/.dotfiles/agents/AGENTS.md (软链)
~/.codex/AGENTS.md   → ~/.dotfiles/agents/AGENTS.md (软链)
```

**BMAD 源文件 (供 bmad-init 使用):**
```
~/.dotfiles/_bmad/   (BMAD v6.0.0-alpha.23 源文件)
```

## BMAD 使用方法

1. 在项目中初始化 BMAD：
   ```
   bmad init
   ```

2. 使用 BMAD 命令：
   ```
   /bmad__bmm__workflow__create-product-brief
   /bmad__bmm__workflow__prd
   /bmad__bmm__workflow__create-architecture
   ```

3. 使用 BMAD 代理 (droids)：
   ```
   @bmad__bmm__pm
   @bmad__bmm__architect
   @bmad__bmm__dev
   ```

## 支持的 CLI

- Claude Code (`~/.claude/commands`)
- Codex (`~/.codex/prompts`)
- Factory Droid (`~/.factory/commands`, `~/.factory/droids`)
- Antigravity (`~/.gemini/antigravity/global_workflows`)

## 卸载

```bash
~/.dotfiles/scripts/uninstall.sh
```

## 更新

```bash
cd ~/.dotfiles && git pull
```
