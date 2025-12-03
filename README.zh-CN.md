# dotfiles

[English](./README.md)

让 Claude CLI、Codex CLI、Factory CLI 共享同一个 commands 目录。

## 做了什么

```
~/.claude/commands   → ~/.dotfiles/commands (软链)
~/.codex/prompts     → ~/.dotfiles/commands (软链)
~/.factory/commands  → ~/.dotfiles/commands (软链)
```

改一处，全生效。

## 安装

### 快速安装

```bash
curl -fsSL https://raw.githubusercontent.com/notdp/.dotfiles/main/scripts/install.sh | bash
```

依赖：默认场景无需额外依赖；若存在 `scripts/config.json` 需用 `jq` 读取配置；迁移已有目录优先用 `rsync`，缺失时退化为 `cp -an`。

### 版本管理 & 自定义配置

1. Fork 并 clone：

```bash
git clone https://github.com/<your-username>/.dotfiles.git ~/.dotfiles
```

2. 运行安装脚本：

```bash
cd ~/.dotfiles && ./scripts/install.sh
```

## 卸载

```bash
cd ~/.dotfiles && ./scripts/uninstall.sh
```

## 配置

编辑 `scripts/config.json` 自定义链接目标：

```json
{
  "link_targets": [
    "~/.claude/commands",
    "~/.codex/prompts",
    "~/.factory/commands"
  ]
}
```

安装时会自动备份已存在的目录。
