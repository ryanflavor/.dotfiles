# dotfiles

[中文](./README.zh-CN.md)

Share commands, skills, droids, and BMAD workflows across Claude Code, Codex, Droid, and Antigravity.

## Features

- **36 BMAD workflow commands** - Product brief, PRD, architecture, sprint planning, etc.
- **10 BMAD agent droids** - PM, Architect, Dev, UX Designer, etc.
- **bmad-init skill** - Initialize BMAD in any project

## Install

```bash
git clone https://github.com/ryanflavor/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles && ./scripts/install.sh
```

## What it does

**Commands & Droids:**
```
~/.claude/commands   → ~/.dotfiles/commands (symlink)
~/.codex/prompts     → ~/.dotfiles/commands (symlink)
~/.factory/commands  → ~/.dotfiles/commands (symlink)
~/.factory/droids    → ~/.dotfiles/droids (symlink)
~/.gemini/antigravity/global_workflows → ~/.dotfiles/commands (symlink)
```

**Skills:**
```
~/.claude/skills                → ~/.dotfiles/skills (symlink)
~/.codex/skills                 → ~/.dotfiles/skills (symlink)
~/.factory/skills               → ~/.dotfiles/skills (symlink)
~/.gemini/antigravity/skills    → ~/.dotfiles/skills (symlink)
```

**Global Agent Instructions:**
```
~/.claude/CLAUDE.md  → ~/.dotfiles/agents/AGENTS.md (symlink)
~/.factory/AGENTS.md → ~/.dotfiles/agents/AGENTS.md (symlink)
~/.codex/AGENTS.md   → ~/.dotfiles/agents/AGENTS.md (symlink)
```

**BMAD Source (for bmad-init):**
```
~/.dotfiles/_bmad/   (BMAD v6.0.0-alpha.23 source files)
```

## BMAD Usage

1. Initialize BMAD in your project:
   ```
   bmad init
   ```

2. Use BMAD commands:
   ```
   /bmad__bmm__workflow__create-product-brief
   /bmad__bmm__workflow__prd
   /bmad__bmm__workflow__create-architecture
   ```

3. Use BMAD agents (droids):
   ```
   @bmad__bmm__pm
   @bmad__bmm__architect
   @bmad__bmm__dev
   ```

## Supported CLIs

- Claude Code (`~/.claude/commands`)
- Codex (`~/.codex/prompts`)
- Factory Droid (`~/.factory/commands`, `~/.factory/droids`)
- Antigravity (`~/.gemini/antigravity/global_workflows`)

## Uninstall

```bash
~/.dotfiles/scripts/uninstall.sh
```

## Update

```bash
cd ~/.dotfiles && git pull
```
