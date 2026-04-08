#!/usr/bin/env python3
"""mod15: 修复 ucM/NcM 部分JSON解析器对 \\uXXXX Unicode 转义的处理

问题根因:
  YcM 的字符串解析器 (ucM = key解析, NcM = value解析) 在处理 \\uXXXX 时，
  switch default case 只取 backslash 后一个字符，导致:
    \\u5de5 → u5de5  (backslash 被吃掉，只留 u + 4位hex作为普通字符)

影响场景:
  - Plan 显示: wU$(buffer) → YcM() → NcM() → 中文显示为 u5de5...
  - 工具执行: 当 JSON.parse 失败时 fallback 到 YcM → 工具参数中文错误

触发条件:
  - 使用 BYOK Claude Opus (provider: "anthropic")
  - 流式输出工具调用参数时 partial_json 包含 \\u5de5 形式的中文
  - wU$(partial_buffer) 中 JSON.parse 因不完整而失败，fallback 到 YcM

修改:
  1. NcM.default: A+=M → M=="u"时解码4位hex为实际Unicode字符
  2. ucM.default: A+=I → I=="u"时同样处理 (key 名若含中文也正确)

补偿:
  利用 mod14 创建的死代码区域 (provider==="openai"&&!1 后的 return 语句)
  从 ~210B 压缩到 90B，释放 ~120B 用于本 mod 的 +120B 增量

字节变化: +120B (由 mod14 死代码区域补偿)
"""
import sys
import re
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid, V

data = load_droid()
original_size = len(data)

# ─── 检查是否已应用 ───────────────────────────────────────────────────────
# 检查 NcM 是否已有 fromCharCode
if b'default:M=="u"?(A+=String.fromCharCode' in data:
    print("mod15 已应用，跳过")
    sys.exit(0)

# ─── Patch 1: NcM value 解析器 ───────────────────────────────────────────
# 定位: 找到 NcM 函数内的 switch default case
# 锚点: default:A+=M;break}}else A+=H[L]  (NcM 中 M 是 value 变量)
NCM_OLD = b'default:A+=M;break}}else A+=H['
NCM_NEW = b'default:M=="u"?(A+=String.fromCharCode(parseInt(H.slice(L+1,L+5),16)),L+=4):A+=M;break}}else A+=H['

# 验证锚点唯一性
ncm_count = data.count(NCM_OLD)
if ncm_count == 0:
    print("mod15 失败: 未找到 NcM default case (NCM_OLD)")
    print(f"  检查: strings ~/.local/bin/droid | grep 'default:A+=M;break'")
    sys.exit(1)
if ncm_count > 1:
    print(f"警告: NcM default case 找到 {ncm_count} 处，预期1处")
    # 需要找到正确的那个 (在 NcM 函数内)
    pos_ncm = data.find(b'function NcM(')
    if pos_ncm < 0:
        print("mod15 失败: 未找到 NcM 函数")
        sys.exit(1)
    # 在 NcM 函数内找
    ncm_region = data[pos_ncm:pos_ncm+600]
    idx = ncm_region.find(NCM_OLD)
    if idx < 0:
        print("mod15 失败: NcM 函数内未找到 default case")
        sys.exit(1)
    ncm_pos = pos_ncm + idx
    data = data[:ncm_pos] + NCM_NEW + data[ncm_pos + len(NCM_OLD):]
    print(f"  NcM patch 应用于 pos {ncm_pos}")
else:
    data = data.replace(NCM_OLD, NCM_NEW, 1)
    print(f"✓ Patch 1 NcM: default:A+=M → Unicode decode (+{len(NCM_NEW)-len(NCM_OLD)}B)")

# ─── Patch 2: ucM key 解析器 ────────────────────────────────────────────
# 锚点: default:A+=I;break}}else A+=H[L]  (ucM 中 I 是 key 变量)
UCM_OLD = b'default:A+=I;break}}else A+=H['
UCM_NEW = b'default:I=="u"?(A+=String.fromCharCode(parseInt(H.slice(L+1,L+5),16)),L+=4):A+=I;break}}else A+=H['

ucm_count = data.count(UCM_OLD)
if ucm_count == 0:
    print("mod15 失败: 未找到 ucM default case (UCM_OLD)")
    sys.exit(1)
if ucm_count > 1:
    print(f"警告: ucM default case 找到 {ucm_count} 处，预期1处")
    pos_ucm = data.find(b'function ucM(')
    if pos_ucm < 0:
        print("mod15 失败: 未找到 ucM 函数")
        sys.exit(1)
    ucm_region = data[pos_ucm:pos_ucm+500]
    idx = ucm_region.find(UCM_OLD)
    if idx < 0:
        print("mod15 失败: ucM 函数内未找到 default case")
        sys.exit(1)
    ucm_pos = pos_ucm + idx
    data = data[:ucm_pos] + UCM_NEW + data[ucm_pos + len(UCM_OLD):]
    print(f"  ucM patch 应用于 pos {ucm_pos}")
else:
    data = data.replace(UCM_OLD, UCM_NEW, 1)
    print(f"✓ Patch 2 ucM: default:A+=I → Unicode decode (+{len(UCM_NEW)-len(UCM_OLD)}B)")

# ─── 计算增量 ────────────────────────────────────────────────────────────
delta = len(data) - original_size
print(f"  当前总增量: {delta:+d}B (需要补偿)")

# ─── 补偿: 压缩 mod14 死代码区域 ─────────────────────────────────────────
# mod14 把 provider==="openai"&&!1) 后面的 return(...).output_text 变成死代码
# 原始死代码约 210B，压缩为 "return null;/* ... */" (90B)
# 净补偿: 210 - 90 = 120B

# 定位死代码: provider==="openai"&&!1)return( ... ).output_text
DEAD_ANCHOR = b'provider==="openai"&&!1)return('
dead_pos = data.find(DEAD_ANCHOR)
if dead_pos < 0:
    print("mod15 补偿失败: 未找到 mod14 死代码锚点 (provider===\"openai\"&&!1)return()")
    print("  需要先应用 mod14，或检查二进制版本")
    # 回滚已应用的 patch
    sys.exit(1)

# 找到死代码的结尾: .output_text;
dead_start = dead_pos + len(DEAD_ANCHOR) - len(b'return(')  # 包括 return(
dead_end_marker = b'.output_text;'
dead_end = data.find(dead_end_marker, dead_start)
if dead_end < 0:
    print("mod15 补偿失败: 未找到死代码结尾 .output_text;")
    sys.exit(1)
dead_end += len(dead_end_marker)

dead_code = data[dead_start:dead_end]
dead_size = len(dead_code)
print(f"  死代码区域: pos {dead_start}-{dead_end}, {dead_size}B")

# 新的死代码: return null; + 注释填充到 (dead_size - delta) 字节
target_size = dead_size - delta  # 补偿 delta 字节
min_dead = b'return null;'  # 12B 最小有效替换
if target_size < len(min_dead):
    print(f"mod15 失败: 补偿空间不足 (需要 {delta}B, 最多可补偿 {dead_size - len(min_dead)}B)")
    sys.exit(1)

# 生成替换: "return null;/* <spaces> */"
pad_size = target_size - len(min_dead) - 4  # 4 = len("/**/")
if pad_size < 0:
    new_dead = min_dead + b' ' * (target_size - len(min_dead))
else:
    new_dead = min_dead + b'/*' + b' ' * pad_size + b'*/'
assert len(new_dead) == target_size, f"补偿长度错误: {len(new_dead)} != {target_size}"

data = data[:dead_start] + new_dead + data[dead_end:]
print(f"✓ 补偿: 死代码 {dead_size}B → {target_size}B (节省 {dead_size - target_size}B)")

# ─── 验证文件大小 ──────────────────────────────────────────────────────────
final_size = len(data)
if final_size != original_size:
    print(f"✗ 文件大小变化: {original_size} → {final_size} ({final_size - original_size:+d}B)")
    print("  请检查补偿逻辑")
    sys.exit(1)

save_droid(data)
print(f"✓ mod15 完成，文件大小不变 ({final_size}B)")
print()
print("效果:")
print("  - YcM 解析器正确处理 \\uXXXX → 实际Unicode字符")
print("  - Plan 显示中文不再出现 u5de5 格式")
print("  - 工具参数 fallback 到 YcM 时中文也正确")
