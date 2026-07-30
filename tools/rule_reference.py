"""规则引用机制 - Token 优化的上下文引用"""

from typing import Callable

def add_rule_reference(response: str, rule_name: str = "core") -> str:
    """
    为工具响应添加规则引用，实现 Token 优化的上下文引用机制。

    工作原理：
    1. 不在每次工具调用时重复发送完整规则（节省 ~150 tokens）
    2. 只发送简短的引用指令（~15 tokens）
    3. LLM 从上下文中检索 ${RULES:core} 的实际内容
    4. 确保 LLM 严格按照规则执行操作

    Args:
        response: 工具的原始响应内容
        rule_name: 规则名称，默认为 "core"

    Returns:
        添加了规则引用的增强响应
    """
    rule_reference = f"${{RULES:{rule_name}}}"

    return f"""
{response}

---
⚠️ **重要**：请严格遵循上下文中的 {rule_reference} 中的规则执行以上结果。

这些规则是强制性的，不是可选的。必须始终按照这些规则来理解和执行返回的数据。
"""


def add_conditional_rule_reference(response: str, critical: bool = False) -> str:
    """
    根据操作重要性添加不同级别的规则引用。

    Args:
        response: 工具的原始响应内容
        critical: 是否为关键操作，决定引用规则级别

    Returns:
        添加了条件性规则引用的增强响应
    """
    if critical:
        return add_rule_reference(response, "critical")
    else:
        return add_rule_reference(response, "standard")


def create_rule_reminder(tool_name: str, is_ending_tool: bool = False) -> str:
    """
    为特定工具创建规则提醒。

    Args:
        tool_name: 工具名称
        is_ending_tool: 是否为对话结束类工具（如 record_log）

    Returns:
        规则提醒文本
    """
    if is_ending_tool:
        return f"""
💡 **对话结束提醒**：
- 请在对话结束时主动使用 {tool_name} 记录总结
- 记录内容：关键结论、重要决策、用户偏好
- 不要等待用户明确要求

📍 遵循上下文中的 ${{RULES:core}} 执行以上操作。
"""
    else:
        return f"""
📍 遵循上下文中的 ${{RULES:core}} 执行 {tool_name} 操作。
"""


# 规则级别的默认配置
RULE_LEVELS = {
    "critical": "最高优先级规则（如安全相关）",
    "core": "核心操作规则（当前使用）",
    "standard": "标准操作规则",
    "optional": "最佳实践建议"
}
