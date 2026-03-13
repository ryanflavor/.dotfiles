#!/usr/bin/env python3
"""mod3: 输出预览行数 4→99 行 (同时解决 mod5)

v0.49+:  修改变量定义 aGR=4 → aGR=99 (+1 byte, 需要补偿)
v0.74+:  修改 VAR=VAR2?8:4, → VAR=(99) , (0 bytes, 无需补偿)
"""
import sys
import re
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid, V

data = load_droid()

# --- 检查是否已应用 ---
if re.search(rb'=\(99\) ,', data):
    print("mod3 已应用 (v0.74+ 模式)，跳过")
    sys.exit(0)
if re.search(V + rb'=99,' + V + rb'=5,' + V + rb'=200', data):
    print("mod3 已应用 (v0.49+ 模式)，跳过")
    sys.exit(0)

# --- v0.74+ 模式: VAR=VAR2?8:4, (renderResult 中的 f=D?8:4,) ---
# 替换为 VAR=(99) , 等长 (0 bytes)
pattern_74 = rb'(' + V + rb')=(' + V + rb')\?8:4,'
match = re.search(pattern_74, data)
if match:
    var1, var2 = match.group(1), match.group(2)
    old = match.group(0)
    new = var1 + b'=(99) ,'
    data = data.replace(old, new, 1)
    save_droid(data)
    print(f"mod3 输出行数 (v0.74+): {var1.decode()}={var2.decode()}?8:4 → {var1.decode()}=(99)  (0 bytes)")
    print("mod3 完成 (同时解决 mod5, 无需补偿)")
    sys.exit(0)

# --- v0.49+ 模式: VAR=4,VAR2=5,VAR3=200 ---
pattern_49 = rb'(' + V + rb')=4,(' + V + rb')=5,(' + V + rb')=200'
match = re.search(pattern_49, data)
if match:
    var1, var2, var3 = match.group(1), match.group(2), match.group(3)
    old = match.group(0)
    new = var1 + b'=99,' + var2 + b'=5,' + var3 + b'=200'
    data = data.replace(old, new, 1)
    save_droid(data)
    print(f"mod3 输出行数 (v0.49+): {var1.decode()}=4 → {var1.decode()}=99 (+1 byte)")
    print("mod3 完成 (同时解决 mod5, 需要补偿 -1 byte)")
    sys.exit(0)

print("mod3 失败: 未找到输出行数配置 (VAR=4,VAR2=5,VAR3=200 或 VAR=VAR2?8:4,)")
sys.exit(1)
