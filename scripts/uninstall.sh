#!/bin/bash

set -euo pipefail

resolve_dotfiles_dir() {
    local source="${BASH_SOURCE[0]:-}"
    if [ -n "$source" ] && [ -f "$source" ]; then
        local script_dir
        script_dir="$(cd "$(dirname "$source")" && pwd)"
        local parent_dir
        parent_dir="$(dirname "$script_dir")"
        if [ "$(basename "$parent_dir")" = ".dotfiles" ]; then
            printf "%s\n" "$parent_dir"
            return
        fi
    fi
    printf "%s\n" "$HOME/.dotfiles"
}

DOTFILES_DIR="${DOTFILES_DIR:-$(resolve_dotfiles_dir)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-}")" && pwd)"

# 配置文件仅放在 scripts/ 下，必要时可用环境变量 CONFIG_FILE 覆盖
CONFIG_FILE="${CONFIG_FILE:-$SCRIPT_DIR/config.json}"

COMMANDS_DIR="$DOTFILES_DIR/commands"

DEFAULT_LINK_TARGETS=(
    "~/.claude/commands"
    "~/.codex/prompts"
    "~/.factory/commands"
)

log() { echo "[info] $*"; }
warn() { echo "[warn] $*" >&2; }
err() { echo "[error] $*" >&2; exit 1; }

expand_path() {
    case "$1" in
        "~") echo "$HOME" ;;
        ~/*)  echo "$HOME/${1#~/}" ;;
        *)    echo "$1" ;;
    esac
}

load_targets() {
    LINK_TARGETS=()
    if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
        while IFS= read -r line; do
            [ -n "$line" ] && LINK_TARGETS+=("$line")
        done < <(jq -r '.link_targets[]' "$CONFIG_FILE")

        [ "${#LINK_TARGETS[@]}" -gt 0 ] && return
        warn "config.json 为空，使用默认链接目标"
    elif [ -f "$CONFIG_FILE" ]; then
        warn "未找到 jq，无法读取 config.json，使用默认链接目标"
    else
        warn "未找到 config.json（期望位于 scripts/config.json），使用默认链接目标"
    fi
    LINK_TARGETS=("${DEFAULT_LINK_TARGETS[@]}")
}

load_targets

for raw_dir in "${LINK_TARGETS[@]}"; do
    dir="$(expand_path "$raw_dir")"

    if [ -L "$dir" ]; then
        target="$(readlink "$dir")"
        if [ "$target" = "$COMMANDS_DIR" ]; then
            rm "$dir"
            log "移除软链: $dir"
        else
            warn "跳过：$dir 指向其他位置 ($target)"
            continue
        fi
    elif [ -e "$dir" ]; then
        warn "跳过：$dir 存在但非软链"
        continue
    else
        log "未找到软链: $dir"
    fi

    latest_backup=$(ls -1dt "${dir}.bak-"* 2>/dev/null | head -n 1 || true)
    if [ -n "${latest_backup:-}" ]; then
        mv "$latest_backup" "$dir"
        log "已恢复备份: $latest_backup -> $dir"
    else
        log "无可用备份，未恢复: $dir"
    fi
done

log "卸载完成"
