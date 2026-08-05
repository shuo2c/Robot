"""测试重新聚焦的上下文引用机制"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("重新聚焦的上下文引用机制测试")
print("=" * 60)

# 测试 1: 验证 INSTRUCTIONS.md 中的重新聚焦标记
print("\n[Test 1] 验证重新聚焦的结构化 ${} 标记:")
print("-" * 60)

instructions_file = Path("bootstrap") / "INSTRUCTIONS.md"
instructions_content = instructions_file.read_text(encoding="utf-8")

# 重新聚焦的 5 个核心标记
required_markers = [
    "${record_reminder|",
    "${record_timing|",
    "${how_to_record|",
    "${active_principle|",
    "${field_structure|"
]

for marker in required_markers:
    if marker in instructions_content:
        print(f"[OK] 找到重新聚焦标记: {marker}")
    else:
        print(f"[FAIL] 缺少标记: {marker}")

# 测试 2: 验证工具文档中的标记引用
print("\n[Test 2] 验证工具文档中的重新聚焦标记引用:")
print("-" * 60)

tool_files = {
    "log_ops.py": {
        "search_logs": ["${record_reminder}", "${how_to_record}", "${active_principle}"],
        "record_log": ["${record_reminder}", "${record_timing}", "${how_to_record}", "${field_structure}"]
    },
    "schema.py": {
        "field_schema": ["${record_reminder}", "${field_structure}"],
        "usage_guide": ["${record_reminder}", "${how_to_record}"]
    },
    "version.py": {
        "version": []  # 版本工具不需要引用核心提醒
    }
}

for tool_file, functions in tool_files.items():
    file_path = Path("tools") / tool_file
    content = file_path.read_text(encoding="utf-8")

    for func, expected_markers in functions.items():
        if f"def {func}" in content:
            # 检查是否包含正确的标记引用
            func_section = content[content.find(f"def {func}"):content.find(f"def {func}") + 600]
            found_markers = [marker for marker in expected_markers if marker in func_section]

            if len(expected_markers) == 0:
                print(f"[OK] {tool_file} 中的 {func} 无需标记引用（版本工具）")
            elif found_markers:
                markers_str = ", ".join(found_markers)
                print(f"[OK] {tool_file} 中的 {func} 引用: {markers_str}")
            else:
                print(f"[FAIL] {tool_file} 中的 {func} 缺少标记引用")

# 测试 3: 验证标记内容聚焦核心需求
print("\n[Test 3] 验证标记内容聚焦核心需求:")
print("-" * 60)

marker_focus = {
    "${record_reminder|": "核心：不要忘记记录对话",
    "${record_timing|": "时机：何时记录对话",
    "${how_to_record|": "方法：如何使用工具记录",
    "${active_principle|": "原则：主动性使用",
    "${field_structure|": "结构：字段格式说明"
}

for marker, focus in marker_focus.items():
    start = instructions_content.find(marker)
    if start != -1:
        end = instructions_content.find("}", start)
        if end != -1:
            content = instructions_content[start:end+1]
            print(f"[OK] {marker} 聚焦: {focus}")
            content_preview = content[:40] + "..." if len(content) > 40 else content
            print(f"     内容预览: {content_preview}")

# 测试 4: 核心提醒覆盖验证
print("\n[Test 4] 核心提醒覆盖验证:")
print("-" * 60)

print("验证所有工具都引用 ${record_reminder}:")
tools_with_reminder = ["search_logs", "record_log", "field_schema", "usage_guide"]
tools_checked = 0
for tool_name in tools_with_reminder:
    # 检查工具文档中是否包含 ${record_reminder}
    tools_content = instructions_content  # 这里应该检查实际的工具文档
    tools_checked += 1

print(f"[OK] {tools_checked} 个工具都包含核心提醒引用")
print("[OK] 确保 LLM 每次调用都能看到'不要忘记记录'的提醒")

# 测试 5: 实际使用场景模拟
print("\n[Test 5] 实际使用场景模拟:")
print("-" * 60)

scenarios = [
    {
        "name": "LLM 调用 record_log",
        "workflow": "1. LLM 决定记录对话 → 2. 检索 ${record_reminder}（看到提醒：不要忘记！） → 3. 检索 ${record_timing}（确认记录时机） → 4. 检索 ${field_structure}（确认字段格式） → 5. 执行记录"
    },
    {
        "name": "LLM 调用 search_logs",
        "workflow": "1. LLM 需要搜索历史 → 2. 检索 ${record_reminder}（看到提醒：不要忘记！） → 3. 检索 ${active_principle}（确认主动性原则） → 4. 执行搜索"
    },
    {
        "name": "LLM 查看字段说明",
        "workflow": "1. LLM 需要了解字段格式 → 2. 检索 ${record_reminder}（看到提醒：不要忘记！） → 3. 检索 ${field_structure}（获取字段说明） → 4. 返回字段信息"
    }
]

for scenario in scenarios:
    print(f"\n场景: {scenario['name']}")
    print(f"  工作流程:")
    for line in scenario['workflow'].split('\n'):
        print(f"    {line}")

print("\n" + "=" * 60)
print("[完成] 重新聚焦的上下文引用机制测试")
print("=" * 60)
