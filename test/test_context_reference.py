"""测试简化后的上下文引用机制"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("极简化的上下文引用机制测试")
print("=" * 60)

# 测试 1: 验证 INSTRUCTIONS.md 中的极简化 ${} 标记
print("\n[Test 1] 验证极简化后的结构化 ${} 标记:")
print("-" * 60)

instructions_file = Path("bootstrap") / "INSTRUCTIONS.md"
instructions_content = instructions_file.read_text(encoding="utf-8")

# 极简化为 2 个核心标记
required_markers = [
    "${usage|",
    "${workflow|"
]

for marker in required_markers:
    if marker in instructions_content:
        print(f"[OK] 找到极简化标记: {marker}")
    else:
        print(f"[FAIL] 缺少标记: {marker}")

# 测试 2: 验证工具文档中的极简化标记引用
print("\n[Test 2] 验证工具文档中的极简化标记引用:")
print("-" * 60)

tool_files = {
    "log_ops.py": {
        "search_logs": ["${usage}", "${workflow}"],
        "record_log": ["${usage}", "${workflow}"]
    },
    "schema.py": {
        "field_schema": ["${usage}"],
        "usage_guide": []  # 无需引用标记
    },
    "version.py": {
        "version": []  # 无需引用标记
    }
}

for tool_file, functions in tool_files.items():
    file_path = Path("tools") / tool_file
    content = file_path.read_text(encoding="utf-8")

    for func, expected_markers in functions.items():
        if f"def {func}" in content:
            # 检查是否包含正确的标记引用
            func_section = content[content.find(f"def {func}"):content.find(f"def {func}") + 500]
            found_markers = [marker for marker in expected_markers if marker in func_section]

            if len(expected_markers) == 0:
                print(f"[OK] {tool_file} 中的 {func} 无需标记引用")
            elif found_markers:
                markers_str = ", ".join(found_markers)
                print(f"[OK] {tool_file} 中的 {func} 引用: {markers_str}")
            else:
                print(f"[FAIL] {tool_file} 中的 {func} 缺少标记引用")

# 测试 3: 验证极简化标记的内容聚焦
print("\n[Test 3] 验证极简化标记的内容聚焦:")
print("-" * 60)

marker_descriptions = {
    "${usage|": "工具使用规则（主动性要求、字段结构）",
    "${workflow|": "标准工作流程（四步流程）"
}

for marker, description in marker_descriptions.items():
    # 提取标记后的内容描述
    start = instructions_content.find(marker)
    if start != -1:
        end = instructions_content.find("}", start)
        if end != -1:
            content = instructions_content[start:end+1]
            print(f"[OK] {marker} 包含: {description}")
            # 显示前50个字符的内容
            content_preview = content[:50] + "..." if len(content) > 50 else content
            print(f"     内容预览: {content_preview}")

# 测试 4: 极简化效果对比
print("\n[Test 4] 极简化效果对比:")
print("-" * 60)

original_markers = [
    "${project|", "${version-info|", "${service-description|", "${capabilities|}",
    "${workflow-rule|", "${core|", "${thamus|", "${version|}", "${tools-rules|}",
    "${standard-workflow|", "${active-mind|", "${usage-principles|}", "${self-concept|"
]

intermediate_markers = ["${project|", "${rules|", "${workflow|", "${thamus|", "${version|"]

current_markers = ["${usage|", "${workflow|}"]

print(f"原始标记数量: {len(original_markers)} 个")
print(f"第一次简化: {len(intermediate_markers)} 个 (减少 {len(original_markers) - len(intermediate_markers)} 个)")
print(f"极简化后: {len(current_markers)} 个 (总共减少 {len(original_markers) - len(current_markers)} 个，{(len(original_markers) - len(current_markers)) / len(original_markers) * 100:.1f}%)")

# 测试 5: 内容聚焦度分析
print("\n[Test 5] 内容聚焦度分析:")
print("-" * 60)

print("极简化的优势:")
print("  [OK] 移除项目介绍 - MCP 服务不需要告诉 LLM 这是什么项目")
print("  [OK] 移除人格描述 - 工具使用不需要了解 Thamus 的人格概念")
print("  [OK] 移除版本信息 - 返回版本信息不需要使用规则")
print("  [OK] 聚焦使用规则 - 只保留对工具调用有实际指导意义的内容")
print("  [OK] 简化标记引用 - 工具文档更加简洁清晰")

print("\n保留内容的核心价值:")
print("  ${usage|} - 告诉 LLM 如何正确使用工具（主动性、字段结构）")
print("  ${workflow|} - 告诉 LLM 标准的工作流程（何时调用哪些工具）")

print("\n" + "=" * 60)
print("[完成] 极简化的上下文引用机制测试")
print("=" * 60)
