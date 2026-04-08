#!/usr/bin/env python3
"""检查 droid 当前状态：原版/已修改/部分修改，以及 settings.json 配置"""
import json
import re
from pathlib import Path

droid = Path.home() / '.local/bin/droid'
V = rb'[A-Za-z_$][A-Za-z0-9_$]*'

with open(droid, 'rb') as f:
    data = f.read()

results = {}

# mod1: 截断条件
# 检测 if(!0||! 短路 (mod1 原始形态)
# 或 comp_universal 补偿后的直接 return 形态 (FFH 中原始条件 if(!V&&!V) 被移除)
if b'if(!0||!' in data:
    results['mod1'] = 'modified'
elif b'function FFH(' in data:
    ffh = data.find(b'function FFH(')
    ffh_region = data[ffh:ffh + 300]
    has_orig_cond = re.search(rb'if\(!' + V + rb'&&!' + V + rb'\)', ffh_region)
    has_direct_return = b'return{text:H,isTruncated:!1}' in ffh_region
    if not has_orig_cond and has_direct_return:
        results['mod1'] = 'modified'  # comp_universal 补偿后，原始条件已移除
    elif has_orig_cond:
        results['mod1'] = 'original'
    else:
        results['mod1'] = 'unknown'
else:
    results['mod1'] = 'unknown'

# mod2: 命令阈值
if b'command.length>99' in data:
    results['mod2'] = 'modified'
elif b'command.length>50' in data:
    results['mod2'] = 'original'
else:
    results['mod2'] = 'unknown'

# mod3+mod5: 输出行数
# v0.74+: VAR=(99) , 模式 (0 bytes, 替换 VAR=VAR2?8:4,)
# v0.49+: VAR=99,VAR2=5,VAR3=200 模式 (+1 byte)
if re.search(V + rb'=\(99\) ,', data):
    results['mod3'] = 'modified'
    results['mod5'] = 'modified'
elif re.search(V + rb'=99,' + V + rb'=5,' + V + rb'=200', data):
    results['mod3'] = 'modified'
    results['mod5'] = 'modified'
elif re.search(V + rb'=4,' + V + rb'=5,' + V + rb'=200', data):
    results['mod3'] = 'original'
    results['mod5'] = 'original'
elif re.search(V + rb'=\(?[48]\)? ?,' , data):
    # v0.74 原版: VAR=VAR2?8:4,
    results['mod3'] = 'original'
    results['mod5'] = 'original'
else:
    results['mod3'] = 'unknown'
    results['mod5'] = 'unknown'

# mod4: diff行数
# v0.74+: var V=99,V=2000 (uhf=99,Jhf=2000)
# v0.49+: var V=99,V, 模式
if re.search(rb'var ' + V + rb'=99,' + V + rb'=2000', data):
    results['mod4'] = 'modified'
elif re.search(rb'var ' + V + rb'=99,' + V + rb',', data):
    results['mod4'] = 'modified'
elif re.search(rb'var ' + V + rb'=20,' + V + rb'=2000', data):
    results['mod4'] = 'original'
elif re.search(rb'var ' + V + rb'=20,' + V + rb',', data):
    results['mod4'] = 'original'
else:
    results['mod4'] = 'unknown'

# mod6: custom model cycle
def _mod6_detect():
    targets = [b'peekNextCycleModel', b'peekNextCycleSpecModeModel', b'cycleSpecModeModel']
    modified = original = 0
    for fn in targets:
        for m in re.finditer(fn + rb'\(' + V + rb'\)\{', data):
            region = data[m.start():m.start() + 600]
            if b'=this.customModels.map(m=>m.id)' in region:
                modified += 1
            elif b'validateModelAccess(' in region:
                original += 1
    if modified > 0 and original == 0:
        return 'modified'
    elif original > 0 and modified == 0:
        return 'original'
    return 'unknown'

results['mod6'] = _mod6_detect()

# mod7: mission 门控
# v0.74+: 已移除 statsig 门控，/enter-mission 直接可用，mod7 不再需要
if b'statsigName:"enable_extra_mod0",defaultValue:!0' in data:
    results['mod7'] = 'modified'
elif b'statsigName:"enable_extra_mode",defaultValue:!1' in data:
    results['mod7'] = 'original'
elif b'statsigName:"enable_extra_mode"' not in data:
    results['mod7'] = 'n/a'   # v0.74+: statsig 门控已移除
else:
    results['mod7'] = 'unknown'

# mod8: mission 模型白名单
def _mod8_detect():
    has_orig1 = bool(re.search(V + rb'\.includes\(' + V + rb'\)\)\{if\(!' + V, data))
    has_orig2 = bool(re.search(rb'if\(!\(' + V + rb'\.includes\(' + V + rb'\)&&' + V + rb'\.includes\(', data))
    has_mod1 = bool(re.search(rb'!0\s+\)\{if\(!' + V, data))
    has_mod2 = bool(re.search(rb'if\(!\(!0\s+&&' + V + rb'\.includes\(', data))
    if has_mod1 and has_mod2:
        return 'modified'
    elif has_orig1 and has_orig2:
        return 'original'
    elif has_mod1 or has_mod2:
        return 'partial'
    return 'unknown'

results['mod8'] = _mod8_detect()

# mod9: custom model effort 级别
if b'.provider=="openai"' in data and b'["off","low","medium","high","max"]' in data:
    results['mod9'] = 'modified'
elif re.search(rb'supportedReasoningEfforts:' + V + rb'\?\["off","low","medium","high"\]:\["none"\]', data):
    results['mod9'] = 'original'
else:
    results['mod9'] = 'unknown'

# mod10: 禁用内置模型 (validateModelAccess non-custom return)
OLD_BUILTIN = b'isCustomModel:!1};return{allowed:!0,isCustomModel:!1}}'
NEW_BUILTIN = b'isCustomModel:!1};return{allowed:!1,isCustomModel:!1}}'
if NEW_BUILTIN in data and OLD_BUILTIN not in data:
    results['mod10'] = 'modified'
elif OLD_BUILTIN in data:
    results['mod10'] = 'original'
else:
    results['mod10'] = 'unknown'

# mod11: subagent spawn 修复 (process.argv[0] → process.execPath)
if b'process.execPath,baseArgs:[]' in data:
    results['mod11'] = 'modified'
elif b'function ujD(){let' in data and b'process.argv[0]' in data:
    results['mod11'] = 'original'
elif b'process.execPath).includes("droid")' in data:
    results['mod11'] = 'n/a'  # 0.76.0 及更早版本不需要
else:
    results['mod11'] = 'unknown'

# mod12: mission worker effort 从 settings 读取 (不再硬编码 "high")
# 修改后特征: ...WorkerModel(),E=L?A.getMissionValidationWorkerReasoningEffort():A.getMissionWorkerReasoningEffort()
MOD12_SIG = b'getMissionValidationWorkerReasoningEffort():' + V.replace(rb'[', b'').replace(rb']', b'').encode() if isinstance(V, str) else b''
# 直接用完整特征匹配
if b'WorkerModel(),E=L?A.getMissionValidationWorkerReasoningEffort():A.getMissionWorkerReasoningEffort()' in data:
    results['mod12'] = 'modified'
elif re.search(rb'WorkerModel\(\),' + V + rb'=\(BD\(' + V + rb'\)\.supportedReasoningEfforts', data):
    results['mod12'] = 'original'
else:
    results['mod12'] = 'unknown'

# mod14: summarizer OpenAI → ChatCompletions fallback
# mod15 会将死代码区 return(...) 替换为 return null;，需同时兼容
if (b'provider==="openai"&&!1)return(' in data or b'provider==="openai"&&!1)return null;' in data) and b'N.provider==="generic-chat-completion-api"||' in data:
    results['mod14'] = 'modified'
elif b'provider==="openai")return(' in data and b'responses.create' in data:
    results['mod14'] = 'original'
else:
    results['mod14'] = 'unknown'

# mod15: YcM partial JSON parser Unicode escape fix
if b'default:M=="u"?(A+=String.fromCharCode' in data and b'default:I=="u"?(A+=String.fromCharCode' in data:
    results['mod15'] = 'modified'
elif b'default:A+=M;break}}else A+=H[' in data and b'default:A+=I;break}}else A+=H[' in data:
    results['mod15'] = 'original'
else:
    results['mod15'] = 'unknown'

# mod16: wU$ 预处理修复 proxy 发送无反斜杠 uXXXX 的 bug
if b'H=H.replace(/(?<!\\\\)u([0-9a-fA-F]{4})/g,' in data:
    results['mod16'] = 'modified'
elif b'function wU$(H){if(!H.trim())return{data:{},isComplete:!1};try{' in data:
    results['mod16'] = 'original'
else:
    results['mod16'] = 'unknown'

# 输出
total = 15
mod_count = sum(1 for v in results.values() if v == 'modified')
orig_count = sum(1 for v in results.values() if v == 'original')
na_count   = sum(1 for v in results.values() if v == 'n/a')
applicable = total - na_count

print(f"droid 状态:\n")
for name, status in results.items():
    icon  = '✓' if status == 'modified' else '○' if status == 'original' else '△' if status == 'partial' else '-' if status == 'n/a' else '?'
    label = {'modified': '已修改', 'original': '原版', 'partial': '部分', 'unknown': '未知', 'n/a': '不适用'}[status]
    note  = ' (由 mod3 控制)' if name == 'mod5' else ' (v0.74+: 门控已移除，/enter-mission 直接可用)' if status == 'n/a' and name == 'mod7' else ' (0.76.0 及更早: 不需要)' if status == 'n/a' and name == 'mod11' else ''
    print(f"  {icon} {name}: {label}{note}")

print()
if mod_count == applicable:
    print("结论: 已修改")
elif orig_count == applicable:
    print("结论: 原版")
else:
    print(f"结论: 部分修改 ({mod_count}/{applicable})")

# === settings.json 配置检查 ===
settings_path = Path.home() / '.factory/settings.json'
if not settings_path.exists():
    print(f"\n⚠ settings.json 不存在: {settings_path}")
else:
    try:
        cfg = json.loads(settings_path.read_text())
    except Exception as e:
        print(f"\n⚠ settings.json 解析失败: {e}")
        cfg = None

    if cfg:
        print(f"\nsettings.json 配置检查:\n")
        models = cfg.get('customModels', [])
        if not models:
            print("  ⚠ customModels 为空，未配置任何自定义模型")
        else:
            warnings = []
            for m in models:
                mid = m.get('id', '?')
                name = m.get('displayName', mid)
                provider = m.get('provider', '?')
                effort = m.get('reasoningEffort')
                extra = m.get('extraArgs', {})

                issues = []
                has_mod9 = results.get('mod9') == 'modified'

                # reasoningEffort 优先级:
                #   有值 (low/medium/high/max/xhigh) → Droid 控制，extraArgs 中的 effort 被忽略
                #   none/off → Droid 不发送 thinking/reasoning，extraArgs 接管
                # 后果: extraArgs 有 effort 时，Tab 切到 off/none 本想关闭思考，
                #       但 extraArgs 会接管并重新开启

                if provider == 'anthropic':
                    if not effort:
                        issues.append('缺少 reasoningEffort (建议 "high")')
                    thinking = extra.get('thinking', {})
                    oc = extra.get('output_config', {})
                    removable = []
                    if thinking:
                        removable.append('thinking')
                    if oc.get('effort'):
                        removable.append('output_config.effort')
                    if removable:
                        issues.append(
                            f'extraArgs 中的 {" 和 ".join(removable)} 已不需要'
                            '（Droid 内置 reasoningEffort 已接管）。'
                            '不删后果: Tab 切到 off 时 extraArgs 会接管，思考不会真正关闭')
                elif provider == 'openai':
                    if not effort:
                        issues.append('缺少 reasoningEffort (建议 "high")')
                    reasoning = extra.get('reasoning', {})
                    if reasoning:
                        keep_parts = []
                        if extra.get('text', {}).get('verbosity'):
                            keep_parts.append('text.verbosity')
                        keep_note = '，' + '、'.join(keep_parts) + ' 可保留' if keep_parts else ''
                        issues.append(
                            f'extraArgs 中的整个 reasoning 对象必须移除（包括 summary）'
                            '（responses.create 中 extraArgs 浅展开会覆盖 requestParams.reasoning，'
                            '导致 effort 字段丢失，Tab 切换 Thinking Level 完全无效'
                            + (f'；mod9 已解锁 xhigh' if has_mod9 else '') + '）'
                            + keep_note)

                icon = '✓' if not issues else '⚠'
                print(f"  {icon} {name} [{provider}]")
                if effort:
                    print(f"    reasoningEffort: {effort}")
                if extra:
                    print(f"    extraArgs: {json.dumps(extra, ensure_ascii=False)}")
                for issue in issues:
                    print(f"    ⚠ {issue}")
                    warnings.append((name, issue))

            # missionModelSettings 检查
            mission = cfg.get('missionModelSettings', {})
            model_ids = [m.get('id', '') for m in models]
            if mission:
                print(f"\n  missionModelSettings:")
                wm = mission.get('workerModel', '')
                vm = mission.get('validationWorkerModel', '')
                we = mission.get('workerReasoningEffort', '')
                ve = mission.get('validationWorkerReasoningEffort', '')
                print(f"    Worker:    {wm} ({we})" + (" ⚠ 不在 customModels 中" if wm and wm not in model_ids else ""))
                print(f"    Validator: {vm} ({ve})" + (" ⚠ 不在 customModels 中" if vm and vm not in model_ids else ""))
            elif results.get('mod7') == 'modified' or results.get('mod8') == 'modified':
                print(f"\n  ⚠ mod7/mod8 已启用但缺少 missionModelSettings")
                print(f"    → 建议配置 workerModel / validationWorkerModel 指向 custom model")

            if not warnings:
                print("\n  配置正常 ✓")
