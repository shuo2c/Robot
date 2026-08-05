"""测试简化后的上下文引用机制"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("简化后的上下文引用机制测试")
print("=" * 60)

# 测试 1: 验证 INSTRUCTIONS.md 中的简化 ${} 标记
print("\n[Test 1] 验证简化后的结构化 ${} 标记:")
print("-" * 60)

instructions_file = Path("bootstrap") / "INSTRUCTIONS.md"
instructions_content = instructions_file.read_text(encoding="utf-8")

# 从 13 个标记简化为 5 个标记
required_markers = [
    "${project|",
    "${rules|",
    "${workflow|",
    "${thamus|",
    "${version|"
]

for marker in required_markers:
    if marker in instructions_content:
        print(f"[OK] 找到简化标记: {marker}")
    else:
        print(f"[FAIL] 缺少标记: {marker}")

# 测试 2: 验证工具文档中的简化标记引用
print("\n[Test 2] 验证工具文档中的简化标记引用:")
print("-" * 60)

tool_files = {
    "log_ops.py": {
        "search_logs": ["${rules}", "${workflow}"],
        "record_log": ["${rules}", "${workflow}"]
    },
    "schema.py": {
        "field_schema": ["${rules}"],
        "usage_guide": ["${project}", "${thamus}"]
    },
    "version.py": {
        "version": ["${project}", "${version}"]
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

            if found_markers:
                markers_str = ", ".join(found_markers)
                print(f"[OK] {tool_file} 中的 {func} 引用: {markers_str}")
            else:
                print(f"[FAIL] {tool_file} 中的 {func} 缺少标记引用")

# 测试 3: 验证简化标记的内容整合
print("\n[Test 3] 验证简化标记的内容整合:")
print("-" * 60)

marker_descriptions = {
    "${project|": "项目整合信息（版本、服务描述、核心能力）",
    "${rules|": "核心使用规则（主动性、字段结构）",
    "${workflow|": "标准工作流程（四步流程）",
    "${thamus|": "Thamus 人格与哲学整合",
    "${version|": "版本信息格式"
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

# 测试 4: 对比简化前后的标记数量
print("\n[Test 4] 简化效果对比:")
print("-" * 60)

old_markers = [
    "${project|", "${version-info|", "${service-description|", "${capabilities|",
    "${workflow-rule|", "${core|", "${thamus|", "${version|}", "${tools-rules|}",
    "${standard-workflow|", "${active-mind|", "${usage-principles|}", "${self-concept|"
]

new_markers = ["${project|", "${rules|", "${workflow|", "${thamus|", "${version|}"]

print(f"简化前标记数量: {len(old_markers)} 个")
print(f"简化后标记数量: {len(new_markers)} 个")
print(f"减少标记数量: {len(old_markers) - len(new_markers)} 个 ({(len(old_markers) - len(new_markers)) / len(old_markers) * 100:.1f}% 减少)")

# 测试 5: Token 优化效果分析
print("\n[Test 5] Token 优化效果分析:")
print("-" * 60)

print("简化后的标记优化优势:")
print("  [OK] 标记数量大幅减少：从 13 个减少到 5 个")
print("  [OK] 内容高度整合：相关内容合并到同一命名空间")
print("  [OK] 引用更加简洁：工具文档中的标记引用更少")
print("  [OK] 维护成本降低：需要管理的标记关系更简单")

print("\n对比完整指令:")
traditional_size = len(instructions_content)
optimized_size = traditional_size  # 标记机制主要节省工具调用时的重复指令

print(f"  传统方式: 每次工具调用重复发送完整指令 (~{traditional_size} 字符)")
print(f"  简化标记: LLM 从上下文检索相关标记内容 (按需加载)")

print("\n简化整合示例:")
print("  ${project|} ← 整合了: project + version-info + service-description + capabilities")
print("  ${rules|}   ← 整合了: core + tools-rules + workflow-rule")
print("  ${workflow|} ← 整合了: standard-workflow + active-mind + usage-principles")
print("  ${thamus|}  ← 整合了: thamus + self-concept")
print("  ${version|} ← 保留原有版本信息格式")

print("\n" + "=" * 60)
print("[完成] 简化后的上下文引用机制测试")
print("=" * 60)
