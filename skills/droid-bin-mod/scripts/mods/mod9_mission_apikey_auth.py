#!/usr/bin/env python3
"""mod9: Mission spawn 支持 API key 认证 (需要补偿)

问题: mission worker spawn 需要 access_token (OAuth)，BYOK 用户只有 API key → 报错
修复: 客户端 fallback 到 API key + daemon 端正确路由 API-key-as-token

两处 patch:
  A) _0H(): access_token 不存在时 fallback 到 FACTORY_API_KEY
  B) $E$(): token 以 "fk-" 开头时走 API key 验证路径
"""
import sys
import re
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid, V

data = load_droid()
original_size = len(data)
total_diff = 0

# 检查是否已应用
if b'||process.env.FACTORY_API_KEY;if(!$)throw' in data:
    print("mod9 已应用，跳过")
    sys.exit(0)

# === Patch A: _0H() fallback to API key ===
patch_a_old = b'?.access_token?.trim();if(!$)throw new vH("No access token available");return $'
patch_a_new = b'?.access_token?.trim()||process.env.FACTORY_API_KEY;if(!$)throw new vH("No access token available");return $'

if data.count(patch_a_old) != 1:
    raise ValueError(f"Patch A: 找到 {data.count(patch_a_old)} 处 (期望1)")

data = data.replace(patch_a_old, patch_a_new, 1)
diff_a = len(patch_a_new) - len(patch_a_old)
total_diff += diff_a
print(f"mod9a _0H() fallback: +{diff_a} bytes")

# === Patch B: $E$() route API-key-as-token ===
patch_b_old = b'if($?.startsWith(_cD))return FcD($,L);if(A)return'
patch_b_new = b'if(($||A)?.startsWith(_cD))return FcD($||A,L);if(A)return'

if data.count(patch_b_old) != 1:
    raise ValueError(f"Patch B: 找到 {data.count(patch_b_old)} 处 (期望1)")

data = data.replace(patch_b_old, patch_b_new, 1)
diff_b = len(patch_b_new) - len(patch_b_old)
total_diff += diff_b
print(f"mod9b $E$() route: +{diff_b} bytes")

# === 补偿: 缩减 mod1 短路后的死代码 ===
# 死代码: let E=I?L.slice(0,A).join(`\n`):H;if(E.length>$)E=E.xxx(0,$);return{text:E,isTruncated:!0}
# 整块替换为更短的等价死代码 (永远不执行)
dead_pattern = rb'(let (' + V + rb')=(' + V + rb')\?(' + V + rb')\.slice\(0,(' + V + rb')\)\.join\(`\n`\):(' + V + rb');if\(\2\.length>\$\)\2=\2\.x{1,9}\(0,\$\);return\{text:\2,isTruncated:!0\})'
dead_m = re.search(dead_pattern, data)

if not dead_m:
    raise ValueError("mod9 补偿: 未找到死代码块 (需要先应用 mod1)")

old_dead = dead_m.group(1)
var_e = dead_m.group(2)  # E
var_h = dead_m.group(6)  # H

# 构造缩短的死代码，保持合法 JS 语法
# 格式: let E=H;return{text:E,isTruncated:!0}
# 补偿量由填充空格调整
base_new = b'let ' + var_e + b'=' + var_h + b';return{text:' + var_e + b',isTruncated:!0}'
# 需要: len(new_dead) = len(old_dead) - total_diff
target_len = len(old_dead) - total_diff
padding = target_len - len(base_new)

if padding < 0:
    raise ValueError(f"mod9 补偿: 空间不足 ({padding} bytes)")

# 在 let 语句后加空格填充
new_dead = b'let ' + var_e + b'=' + var_h + b';' + b' ' * padding + b'return{text:' + var_e + b',isTruncated:!0}'

assert len(new_dead) == target_len, f"补偿长度不匹配: {len(new_dead)} != {target_len}"
data = data.replace(old_dead, new_dead, 1)
comp_diff = len(new_dead) - len(old_dead)
print(f"mod9c 补偿: {len(old_dead)} → {len(new_dead)} ({comp_diff:+d} bytes)")

# 验证总大小不变
assert len(data) == original_size, f"mod9 大小变化 {len(data) - original_size:+d} bytes"

save_droid(data)
print(f"mod9 完成 (总计 {total_diff:+d} bytes patch + {comp_diff:+d} bytes 补偿 = 0)")
