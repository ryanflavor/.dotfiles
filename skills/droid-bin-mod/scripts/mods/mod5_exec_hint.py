#!/usr/bin/env python3
"""mod5: EXECUTE 输出提示条件 >4 → >99 (+1 byte)

配合 mod3 的 slice(0,99)：显示 99 行，超过 99 行才提示
"""
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid, replace_one, V

data = load_droid()

# D>4&&q1.jsxDEV... (exec-preview 附近)
data, diff = replace_one(
    data,
    rb',(' + V + rb')>4&&(' + V + rb')\.jsxDEV',
    lambda m: b',' + m.group(1) + b'>99&&' + m.group(2) + b'.jsxDEV',
    'mod5 exec提示条件',
    near_marker=b'exec-preview')

save_droid(data)
print(f"mod5 完成 ({diff:+d} bytes)")
