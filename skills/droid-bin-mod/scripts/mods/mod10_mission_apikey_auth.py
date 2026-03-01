#!/usr/bin/env python3
"""mod10: Mission spawn 支持 API key 认证

问题: mission worker spawn 需要 access_token (OAuth)，仅 API key 登录时无 access_token → 报错
修复: 客户端 fallback 到 API key + daemon 端正确路由 API-key-as-token

两处 patch:
  A) _0H(): access_token 不存在时 fallback 到 FACTORY_API_KEY
  B) $E$(): token 以 "fk-" 开头时走 API key 验证路径

字节: +37 bytes，由 comp_universal.py 统一补偿
"""
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid

data = load_droid()

# 检查是否已应用
if b'||process.env.FACTORY_API_KEY;if(!$)throw' in data:
    print("mod10 已应用，跳过")
    sys.exit(0)

# === Patch A: _0H() fallback to API key ===
patch_a_old = b'?.access_token?.trim();if(!$)throw new vH("No access token available");return $'
patch_a_new = b'?.access_token?.trim()||process.env.FACTORY_API_KEY;if(!$)throw new vH("No access token available");return $'

if data.count(patch_a_old) != 1:
    raise ValueError(f"Patch A: 找到 {data.count(patch_a_old)} 处 (期望1)")

data = data.replace(patch_a_old, patch_a_new, 1)
diff_a = len(patch_a_new) - len(patch_a_old)
print(f"mod10a _0H() fallback: +{diff_a} bytes")

# === Patch B: $E$() route API-key-as-token ===
patch_b_old = b'if($?.startsWith(_cD))return FcD($,L);if(A)return'
patch_b_new = b'if(($||A)?.startsWith(_cD))return FcD($||A,L);if(A)return'

if data.count(patch_b_old) != 1:
    raise ValueError(f"Patch B: 找到 {data.count(patch_b_old)} 处 (期望1)")

data = data.replace(patch_b_old, patch_b_new, 1)
diff_b = len(patch_b_new) - len(patch_b_old)
print(f"mod10b $E$() route: +{diff_b} bytes")

total_diff = diff_a + diff_b
save_droid(data)
print(f"mod10 完成 (总计 +{total_diff} bytes，需要 comp_universal.py 补偿)")
