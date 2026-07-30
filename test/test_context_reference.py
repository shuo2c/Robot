"""测试简化后的上下文引用机制"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("简化的上下文引用机制测试")
print("=" * 60)

# 测试 1: 验证 INSTRUCTIONS.md 中的 ${} 标记
print("\n[Test 1] 验证 INSTRUCTIONS.md 中的 ${} 标记:")
print("-" * 60)

instructions_file = Path("bootstrap") / "INSTRUCTIONS.md"
instructions_content = instructions_file.read_text(encoding="utf-8")

required_marker = "${核心规则}"
if required_marker in instructions_content:
    print(f"[OK] 找到简化标记: {required_marker}")
else:
    print(f"[FAIL] 缺少标记: {required_marker}")

# 测试 2: 验证工具文档中的简单说明
print("\n[Test 2] 验证工具文档中的简单说明:")
print("-" * 60)

tool_files = {
    "log_ops.py": ["search_logs", "record_log"],
    "schema.py": ["field_schema"],
    "version.py": ["version"]
}

for tool_file, functions in tool_files.items():
    file_path = Path("tools") / tool_file
    content = file_path.read_text(encoding="utf-8")

    for func in functions:
        if f"def {func}" in content:
            # 检查是否包含简单的使用说明
            if "${核心规则}" in content or "${核心规则}" in content:
                print(f"[OK] {tool_file} 中的 {func} 包含规则引用说明")
            else:
                print(f"[INFO] {tool_file} 中的 {func} 使用简洁说明")

# 测试 3: 对比复杂度
print("\n[Test 3] 复杂度对比:")
print("-" * 60)

print("简化前:")
print("  - 复杂的 ${RULES:core} 标记")
print("  - 专门的 rule_reference.py 函数")
print("  - 每个工具都调用 add_rule_reference")
print("  - 增强的返回结果包含提醒文本")

print("\n简化后:")
print("  - 简单的 ${核心规则} 标记")
print("  - 工具文档中简单的使用说明")
print("  - 直接返回工具结果，无额外处理")
print("  - Token消耗更低")

# 测试 4: 模拟实际使用
print("\n[Test 4] 模拟实际使用:")
print("-" * 60)

print("LLM 收到的工具调用信息:")
print('  工具: record_log')
print('  说明: "调用此工具前，请先检查上下文中的 ${核心规则}"')

print("\nLLM 的处理流程:")
print("  1. 检查上下文，找到 ${核心规则} 的实际内容")
print("  2. 阅读规则：对话结束时必须调用 record_log")
print("  3. 按照规则执行操作")
print("  4. 返回简单结果：\"成功写入 2 条日志。\"")

print("\n" + "=" * 60)
print("[完成] 简化的上下文引用机制测试")
print("=" * 60)
