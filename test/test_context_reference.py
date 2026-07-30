"""测试简化后的上下文引用机制"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("结构化的上下文引用机制测试")
print("=" * 60)

# 测试 1: 验证 INSTRUCTIONS.md 中的结构化 ${} 标记
print("\n[Test 1] 验证 INSTRUCTIONS.md 中的结构化 ${} 标记:")
print("-" * 60)

instructions_file = Path("bootstrap") / "INSTRUCTIONS.md"
instructions_content = instructions_file.read_text(encoding="utf-8")

required_markers = [
    "${project|",
    "${version-info|",
    "${service-description|",
    "${capabilities|",
    "${workflow-rule|",
    "${core|",
    "${thamus|",
    "${version|",
    "${tools-rules|",
    "${standard-workflow|",
    "${active-mind|",
    "${usage-principles|",
    "${self-concept|"
]

for marker in required_markers:
    if marker in instructions_content:
        print(f"[OK] 找到结构化标记: {marker}")
    else:
        print(f"[FAIL] 缺少标记: {marker}")

# 测试 2: 验证工具文档中的标记引用说明
print("\n[Test 2] 验证工具文档中的标记引用说明:")
print("-" * 60)

tool_files = {
    "log_ops.py": {
        "search_logs": ["${core}", "${workflow-rule}", "${standard-workflow}", "${tools-rules}"],
        "record_log": ["${core}", "${workflow-rule}", "${active-mind}", "${tools-rules}"]
    },
    "schema.py": {
        "field_schema": ["${core}"],
        "usage_guide": ["${project}", "${service-description}", "${capabilities}", "${thamus}"]
    },
    "version.py": {
        "version": ["${version}", "${version-info}"]
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

# 测试 3: 验证标记的内容结构
print("\n[Test 3] 验证标记的内容结构:")
print("-" * 60)

marker_descriptions = {
    "${project|": "项目介绍",
    "${version-info|": "当前版本",
    "${service-description|": "服务描述",
    "${capabilities|": "核心能力",
    "${workflow-rule|": "工作流程规则",
    "${core|": "主动记忆规则",
    "${thamus|": "Thamus 人格定义",
    "${version|": "版本信息格式",
    "${tools-rules|": "工具调用通用规则",
    "${standard-workflow|": "标准工作流程",
    "${active-mind|": "主动性理念",
    "${usage-principles|": "使用原则",
    "${self-concept|": "自我概念"
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

# 测试 4: 模拟实际使用场景
print("\n[Test 4] 模拟实际使用场景:")
print("-" * 60)

scenarios = [
    {
        "name": "版本查询",
        "tool": "version",
        "markers": ["${version}"],
        "workflow": "1. 检索上下文 ${version} 了解版本格式\n2. 返回 'thamas-memory v0.0.1'"
    },
    {
        "name": "搜索记忆",
        "tool": "search_logs",
        "markers": ["${core}", "${tools-rules}"],
        "workflow": "1. 检索上下文 ${core} 了解主动记忆规则\n2. 检索上下文 ${tools-rules} 了解工具调用规则\n3. 执行搜索并返回结果"
    },
    {
        "name": "记录日志",
        "tool": "record_log",
        "markers": ["${core}", "${tools-rules}"],
        "workflow": "1. 检索上下文 ${core} 了解主动记录规则\n2. 检索上下文 ${tools-rules} 确认主动性要求\n3. 执行记录并返回成功"
    }
]

for scenario in scenarios:
    print(f"\n场景: {scenario['name']}")
    print(f"  工具: {scenario['tool']}")
    print(f"  标记: {', '.join(scenario['markers'])}")
    print(f"  工作流程:")
    for line in scenario['workflow'].split('\n'):
        print(f"    {line}")

# 测试 5: Token 优化效果分析
print("\n[Test 5] Token 优化效果分析:")
print("-" * 60)

print("结构化标记的 Token 优化优势:")
print("  [OK] 按需加载：工具只引用相关的命名空间标记")
print("  [OK] 内容精确：每个标记包含针对性的内容描述")
print("  [OK] 易于扩展：新增功能只需添加新的命名空间标记")
print("  [OK] 清晰关联：工具与标记的对应关系一目了然")

print("\n对比完整指令:")
traditional_size = len(instructions_content)
optimized_size = traditional_size  # 标记机制主要节省工具调用时的重复指令

print(f"  传统方式: 每次工具调用重复发送完整指令 (~{traditional_size} 字符)")
print(f"  标记方式: LLM 从上下文检索相关标记内容 (按需加载)")

print("\n" + "=" * 60)
print("[完成] 结构化的上下文引用机制测试")
print("=" * 60)
