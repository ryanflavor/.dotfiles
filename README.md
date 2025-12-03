# dotfiles

[中文](./README.zh-CN.md)

Share a single commands directory across Claude CLI, Codex CLI, and Factory CLI.

## What it does

```
~/.claude/commands   → ~/.dotfiles/commands (symlink)
~/.codex/prompts     → ~/.dotfiles/commands (symlink)
~/.factory/commands  → ~/.dotfiles/commands (symlink)
```

Edit once, apply everywhere.

## Install

### Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/notdp/.dotfiles/main/scripts/install.sh | bash
```

Deps: none for the default path. `jq` is only needed when `scripts/config.json` exists; `rsync` is used for migrating existing dirs (falls back to `cp -an`).

### Version Control & Customization

1. Fork & clone:

```bash
git clone https://github.com/<your-username>/.dotfiles.git ~/.dotfiles
```

2. Run installer:

```bash
cd ~/.dotfiles && ./scripts/install.sh
```

## Uninstall

```bash
cd ~/.dotfiles && ./scripts/uninstall.sh
```

## Configuration

Edit `scripts/config.json` to customize link targets:

```json
{
  "link_targets": [
    "~/.claude/commands",
    "~/.codex/prompts",
    "~/.factory/commands"
  ]
}
```

The installer backs up existing directories before creating symlinks.
