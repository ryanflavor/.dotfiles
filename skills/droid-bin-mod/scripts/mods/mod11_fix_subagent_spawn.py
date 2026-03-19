#!/usr/bin/env python3
"""mod11: 修复 subagent spawn "Premature close" (0 bytes)

问题: 0.77.0+ 将 subagent spawn 的 binary path 从 process.execPath 改为
process.argv[0]，但在 Bun SEA 中 process.argv[0] 无法用于 child_process.spawn,
导致 Task tool 永远失败 ("Premature close")。

修改: ujD() 函数改为使用 process.execPath，匹配 0.76.0 的行为。
  原: function ujD(){let H=process.argv[0],...}
  新: function ujD(){return{binary:process.execPath,baseArgs:[]}/*..*/}
"""
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid

data = load_droid()
original_size = len(data)

if b'process.execPath,baseArgs:[]' in data:
    print("mod11 已应用，跳过")
    sys.exit(0)

# 定位 ujD 函数
old = (
    b'function ujD(){let H=process.argv[0],$=process.argv[1];'
    b'if($&&($.endsWith(".ts")||$.endsWith(".js")))'
    b'return{binary:H,baseArgs:[$]};return{binary:H,baseArgs:[]}}'
)

if old not in data:
    # 尝试 0.77.0 变体 (变量名可能不同但结构相同)
    import re
    V = rb'[A-Za-z_$][A-Za-z0-9_$]*'
    pattern = (
        rb'function ujD\(\)\{let (' + V + rb')=process\.argv\[0\],'
        rb'(' + V + rb')=process\.argv\[1\];'
        rb'if\(\2&&\(\2\.endsWith\("\.ts"\)\|\|\2\.endsWith\("\.js"\)\)\)'
        rb'return\{binary:\1,baseArgs:\[\2\]\};return\{binary:\1,baseArgs:\[\]\}\}'
    )
    m = re.search(pattern, data)
    if m:
        old = m.group(0)
    else:
        # 可能是 0.76.0 或更早版本，不需要此修复
        if b'function sAH' in data or b'process.execPath).includes("droid")' in data:
            print("mod11 不需要 (0.76.0 及更早版本使用 process.execPath)")
            sys.exit(0)
        print("错误: ujD 函数未找到")
        sys.exit(1)

# 构建等长替换
new_core = b'function ujD(){return{binary:process.execPath,baseArgs:[]}}'
pad = len(old) - len(new_core)
if pad < 0:
    print(f"错误: 替换内容比原始长 {-pad} bytes")
    sys.exit(1)
elif pad == 0:
    new = new_core
elif pad >= 4:
    # 用注释填充: /*   */
    new = new_core[:-1] + b'/*' + b' ' * (pad - 4) + b'*/' + b'}'
else:
    # 用空格填充
    new = new_core[:-1] + b' ' * pad + b'}'

assert len(new) == len(old), f"长度不匹配: {len(new)} != {len(old)}"

data = data.replace(old, new, 1)
assert len(data) == original_size, f"大小变化 {len(data) - original_size:+d} bytes"

save_droid(data)
print(f"mod11: ujD() 已修复 (process.argv[0] → process.execPath, 0 bytes)")
