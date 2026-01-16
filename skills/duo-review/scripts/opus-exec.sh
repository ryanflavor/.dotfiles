#!/bin/bash
# 调用 Opus (Claude Opus 4.5) 执行任务
# 用法: opus-exec.sh <PROMPT>
# 输出: JSON { session_id, result, is_error }

PROMPT=$1

droid exec -m claude-opus-4-5-20251101 -r high --auto high --output-format json "$PROMPT"
