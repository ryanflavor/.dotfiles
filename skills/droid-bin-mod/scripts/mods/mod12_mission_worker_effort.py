#!/usr/bin/env python3
"""mod12: Mission worker 使用 settings 中配置的 effort (+16 bytes)

问题: spawnWorker() 中 effort 赋值硬编码为 "high"，完全忽略
missionModelSettings.workerReasoningEffort 和 validationWorkerReasoningEffort。

原: E=(BD(D).supportedReasoningEfforts??[]).includes("high")?"high":fK(D)
新: E=L?A.getMissionValidationWorkerReasoningEffort():A.getMissionWorkerReasoningEffort()

L 已在上文区分 worker/validation (同一函数中):
  D=L?A.getMissionValidationWorkerModel():A.getMissionWorkerModel()

稳定锚点: BD(...).supportedReasoningEfforts, includes("high"), fK(...) 均为不变结构。
"""
import re
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid, V

data = load_droid()
original_size = len(data)

OLD = b'E=(BD(D).supportedReasoningEfforts??[]).includes("high")?"high":fK(D)'
NEW = b'E=L?A.getMissionValidationWorkerReasoningEffort():A.getMissionWorkerReasoningEffort()'

if NEW[2:] in data:
    print("mod12 已应用，跳过")
    sys.exit(0)

if OLD not in data:
    # 尝试正则匹配 (变量名可能不同)
    pat = (
        V + rb'=\(' + V + rb'\(' + V + rb'\)\.supportedReasoningEfforts\?\?\[\]\)'
        rb'\.includes\("high"\)\?"high":' + V + rb'\(' + V + rb'\)'
    )
    m = re.search(pat, data)
    if m:
        OLD = m.group(0)
        # 从上下文提取变量名: E=..., L?A.get...
        ctx = data[max(0, m.start()-200):m.start()+200]
        # 找 L 和 A 的角色: D=L?A.getMissionValidationWorkerModel():A.getMissionWorkerModel()
        model_pat = (
            rb'(' + V + rb')=(' + V + rb')\?(' + V + rb')\.getMissionValidationWorkerModel\(\)'
            rb':\3\.getMissionWorkerModel\(\)'
        )
        mm = re.search(model_pat, ctx)
        if mm:
            var_e = OLD[:OLD.index(b'=')]  # 结果变量名
            var_l = mm.group(2)  # 条件变量 (L)
            var_a = mm.group(3)  # 设置对象 (A)
            NEW = (
                var_e + b'=' + var_l
                + b'?' + var_a + b'.getMissionValidationWorkerReasoningEffort()'
                + b':' + var_a + b'.getMissionWorkerReasoningEffort()'
            )
        else:
            print("mod12 失败: 未找到上下文中的 model 赋值行")
            sys.exit(1)
    else:
        print("mod12 失败: 未找到 spawnWorker effort 硬编码")
        sys.exit(1)

assert data.count(OLD) == 1, f"多处匹配: {data.count(OLD)}"

data = data.replace(OLD, NEW, 1)
diff = len(data) - original_size
print(f"mod12 mission worker effort: hardcoded → settings ({diff:+d} bytes)")

save_droid(data)
print(f"mod12 完成")
