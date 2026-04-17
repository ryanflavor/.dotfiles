#!/usr/bin/env python3
"""mod10: Compaction 默认模型 factory-default → current-model (0 bytes)

默认 getCompactionModelMode() fallback 到 "factory-default"，压缩走 Factory 的 Sonnet 4.5
(eaH="claude-sonnet-4-5-20250929")，扣 Factory token，BYOK 用户触发 402。

改为 "current-model" 后压缩使用当前对话模型（BYOK custom model），不再碰 Factory token。

byte-neutral: 19字节原地改写
  原: ??"factory-default"
  新: ??"current-model"<SP><SP>
"""
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid

OLD = b'compactionModelMode??"factory-default"'
NEW = b'compactionModelMode??"current-model"  '
assert len(OLD) == len(NEW), f'length mismatch: {len(OLD)} vs {len(NEW)}'

data = load_droid()
original_size = len(data)

if NEW in data:
    print("mod10 已应用，跳过")
    sys.exit(0)

n = data.count(OLD)
if n == 0:
    raise SystemExit("mod10: 未找到 compactionModelMode??\"factory-default\" 锚点")
if n != 1:
    raise SystemExit(f"mod10: 锚点出现 {n} 次，预期 1 次")

data = data.replace(OLD, NEW)
assert len(data) == original_size

print(f"mod10: {OLD.decode()} → {NEW.decode()} (0 bytes)")
save_droid(data)
print("mod10 完成: 压缩默认使用当前模型 (BYOK)")
