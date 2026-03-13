#!/usr/bin/env python3
"""mod9: custom model 支持完整 effort 级别 (+72 bytes)

问题: 两个函数对 custom model 硬编码 supportedReasoningEfforts 为 ["off","low","medium","high"]，
缺少 anthropic 的 "max" 和 openai 的 "xhigh"。

代码路径:
  1. KOH 函数 (构建完整模型列表): L?["off","low","medium","high"]:["none"]
     → 按 provider 区分 (+66 bytes)
  2. $A 函数 (按 ID 解析当前活跃模型): B?["off","low","medium","high"]:["none"]
     → 统一加 "max" (+6 bytes)，$A 无 provider 上下文引用变量 T

字节: +72 bytes，由 comp_universal.py 统一补偿。
"""
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid

data = load_droid()

total_diff = 0

# --- 路径 1: KOH 函数 (模型列表构建) ---
OLD1 = b'supportedReasoningEfforts:L?["off","low","medium","high"]:["none"]'
NEW1 = b'supportedReasoningEfforts:L?T.provider=="openai"?["none","low","medium","high","xhigh"]:["off","low","medium","high","max"]:["none"]'

if b'T.provider=="openai"' in data:
    print("mod9 路径1 (KOH): 已应用，跳过")
else:
    if OLD1 not in data:
        print("错误: KOH 中的 effort 列表未找到")
        sys.exit(1)
    data = data.replace(OLD1, NEW1, 1)
    diff1 = len(NEW1) - len(OLD1)
    total_diff += diff1
    print(f"mod9 路径1 (KOH): effort 列表已修改 ({diff1:+d} bytes)")

# --- 路径 2: $A 函数 (单模型解析, Tab 切换用) ---
# 用更长的上下文确保唯一匹配，避免误改路径 1
OLD2 = b'supportedReasoningEfforts:B?["off","low","medium","high"]:["none"],defaultReasoningEffort:R.reasoningEffort'
NEW2 = b'supportedReasoningEfforts:B?["off","low","medium","high","max"]:["none"],defaultReasoningEffort:R.reasoningEffort'

if OLD2 not in data:
    if b'"high","max"]:["none"],defaultReasoningEffort:R' in data:
        print("mod9 路径2 ($A): 已应用，跳过")
    else:
        print("错误: $A 中的 effort 列表未找到")
        sys.exit(1)
else:
    data = data.replace(OLD2, NEW2, 1)
    diff2 = len(NEW2) - len(OLD2)
    total_diff += diff2
    print(f"mod9 路径2 ($A): effort 列表已修改 ({diff2:+d} bytes)")

if total_diff == 0:
    print("mod9: 全部已应用")
else:
    print(f"mod9: 总计 {total_diff:+d} bytes")
    save_droid(data)
