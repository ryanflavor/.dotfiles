#!/usr/bin/env python3
"""通用补偿: 修改截断函数内的 substring 长度

位于截断函数内，被 mod1 短路后永远不执行，可以安全修改。
用 isTruncated:!0 定位（截断函数返回值的唯一特征）

补偿范围: -9 到 +∞ bytes
  - substring (9字符) → 空 (0字符) = -9 bytes (最大缩减)
  - substring (9字符) → 任意长字符串 = +∞ bytes (无限扩展)

用法: python3 comp_substring.py <bytes>
  bytes: 需要补偿的字节数（负数=缩减，正数=扩展）
  
示例:
  python3 comp_substring.py -2   # 补偿 -2 bytes (当前默认)
  python3 comp_substring.py -9   # 最大缩减 -9 bytes
  python3 comp_substring.py +5   # 扩展 +5 bytes
"""
import sys
import re
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from common import load_droid, save_droid, V

# 默认补偿 -2 bytes (配合 mod3+mod5 的 +2)
DEFAULT_COMP = -2

def main():
    # 解析参数
    if len(sys.argv) > 1:
        try:
            comp_bytes = int(sys.argv[1])
        except ValueError:
            print(f"错误: 无效的字节数 '{sys.argv[1]}'")
            sys.exit(1)
    else:
        comp_bytes = DEFAULT_COMP
    
    # 检查范围
    if comp_bytes < -9:
        print(f"错误: 最大只能缩减 -9 bytes，你指定了 {comp_bytes}")
        sys.exit(1)
    
    data = load_droid()
    
    # X.substring(0,Y);return{text:X,isTruncated:!0}
    # 变量名会混淆，用正则匹配
    pattern = rb'(' + V + rb')\.(substring[a-z]*)\(0,(' + V + rb')\);return\{text:\1,isTruncated:!0\}'
    match = re.search(pattern, data)
    
    if not match:
        print("补偿失败: 未找到目标模式")
        print("请检查 droid 版本是否更新了截断函数结构")
        sys.exit(1)
    
    var1 = match.group(1)
    old_func = match.group(2)  # substring 或之前修改过的
    var2 = match.group(3)
    
    # 计算新函数名长度: 原始 substring=9, 目标长度=9+comp_bytes
    new_len = 9 + comp_bytes
    if new_len < 0:
        new_len = 0
    new_func = b'x' * new_len  # 用 x 填充，反正不会执行
    
    old = match.group(0)
    new = var1 + b'.' + new_func + b'(0,' + var2 + b');return{text:' + var1 + b',isTruncated:!0}'
    actual_diff = len(new) - len(old)
    
    # 验证字节变化
    # 注意: 如果之前已经修改过，old_func 可能不是 9 字符
    expected_diff = comp_bytes - (len(old_func) - 9)
    
    data = data.replace(old, new, 1)
    
    save_droid(data)
    print(f"compensation: {old_func.decode()} → {new_func.decode() or '(空)'} ({actual_diff:+d} bytes)")
    print(f"补偿完成 ({actual_diff:+d} bytes)")

if __name__ == '__main__':
    main()
