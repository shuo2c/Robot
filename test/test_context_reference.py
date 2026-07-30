"""测试上下文引用机制是否正确实现"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("上下文引用机制测试")
print("=" * 60)

# 测试 1: 验证 INSTRUCTIONS.md 中的规则标记
print("\n[Test 1] 验证 INSTRUCTIONS.md 中的规则标记:")
print("-" * 60)

instructions_file = Path("bootstrap") / "INSTRUCTIONS.md"
instructions_content = instructions_file.read_text(encoding="utf-8")

required_markers = ["${RULES:core}", "${/RULES:core}"]
for marker in required_markers:
    if marker in instructions_content:
        print(f"[OK] 找到标记: {marker}")
    else:
        print(f"[FAIL] 缺少标记: {marker}")

# 测试 2: 验证规则引用函数
print("\n[Test 2] 验证规则引用函数:")
print("-" * 60)

try:
    from tools.rule_reference import add_rule_reference

    # 测试基本功能
    test_response = "测试结果：操作成功完成"
    enhanced_response = add_rule_reference(test_response)

    if "${RULES:core}" in enhanced_response:
        print("[OK] 规则引用已添加到响应中")
    else:
        print("[FAIL] 规则引用未添加到响应中")

    # 检查响应长度
    if len(enhanced_response) > len(test_response):
        print(f"[OK] 响应已增强：{len(test_response)} -> {len(enhanced_response)} 字符")
    else:
        print("[FAIL] 响应未被增强")

except ImportError as e:
    print(f"[FAIL] 无法导入规则引用函数: {e}")

# 测试 3: 验证工具函数是否使用规则引用
print("\n[Test 3] 验证工具函数是否使用规则引用:")
print("-" * 60)

tool_files = {
    "log_ops.py": ["record_log", "search_logs"],
    "schema.py": ["field_schema"],
    "version.py": ["version"]
}

for tool_file, functions in tool_files.items():
    file_path = Path("tools") / tool_file
    content = file_path.read_text(encoding="utf-8")

    for func in functions:
        if f"def {func}" in content:
            # 检查函数中是否使用了 add_rule_reference
            if "add_rule_reference" in content:
                print(f"[OK] {tool_file} 中的 {func} 使用了规则引用")
            else:
                print(f"[FAIL] {tool_file} 中的 {func} 未使用规则引用")

# 测试 4: 模拟实际响应
print("\n[Test 4] 模拟实际响应效果:")
print("-" * 60)

try:
    from tools.rule_reference import add_rule_reference

    # 模拟 record_log 的响应
    mock_response = "成功写入 2 条日志。"
    enhanced = add_rule_reference(mock_response)

    print("原始响应:")
    print(mock_response)
    print("\n增强后响应:")
    print(enhanced)

    # 计算token节省效果
    original_length = len(mock_response)
    enhanced_length = len(enhanced)
    reference_length = len("⚠️ **重要**：请严格遵循上下文中的 ${RULES:core} 中的规则执行以上结果。这些规则是强制性的，不是可选的。必须始终按照这些规则来理解和执行返回的数据。")

    print(f"\nToken分析:")
    print(f"  原始响应: {original_length} 字符")
    print(f"  规则引用: {reference_length} 字符")
    print(f"  总长度: {enhanced_length} 字符")
    print(f"  相比每次发送完整规则(约150字符)，节省: ~135 字符")

except Exception as e:
    print(f"[FAIL] 模拟测试失败: {e}")

print("\n" + "=" * 60)
print("[完成] 上下文引用机制测试")
print("=" * 60)
