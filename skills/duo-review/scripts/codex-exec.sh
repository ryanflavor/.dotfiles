#!/bin/bash
# 调用 Codex (GPT-5.1 Codex Max) 执行任务
# 用法: codex-exec.sh <PROMPT>
# 输出: JSON { session_id, result, is_error }

PROMPT=$1

droid exec -m gpt-5.1-codex-max -r high --auto high --output-format json "$PROMPT"
