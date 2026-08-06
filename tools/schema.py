"""字段查询和使用指南工具"""

from mcp.server.fastmcp import FastMCP
from tools.log_ops import FIELD_NAMES
from tools.first_call import check_first_call


def register_tools(mcp: FastMCP) -> None:
    """注册字段查询工具到 MCP 服务器"""

    @mcp.tool()
    def usage_guide() -> str:
        """返回 Thamus 记忆系统的使用说明。

        【使用前准备】调用此工具前，请先检索上下文中的 ${project}、${service-description}、${capabilities} 和 ${thamus} 了解项目背景、服务功能、核心能力和设计理念。

        【行为说明】
        - 首次调用时返回完整的使用指南，包括核心工具介绍、使用流程和主动使用原则
        - 后续调用时返回简化版本，因为首次调用时已经提供了详细说明
        - 每次会话开始时建议调用此工具获取使用说明

        【包含内容】
        - 核心工具列表和使用方法
        - 主动性使用原则
        - 标准工作流程
        - 使用示例

        【返回值说明】
        - 首次调用：返回包含工具列表、使用流程和主动原则的完整指南
        - 后续调用：返回简化版使用说明
        """
        return check_first_call() or """
# 🎯 Thamus 记忆系统 - 使用指南

欢迎使用 Thamus 持久化记忆服务！

## 📋 核心工具

1. **record_log** - 记录对话到持久化存储
2. **search_logs** - 搜索历史记忆
3. **field_schema** - 查看字段含义

详细说明请参考首次调用时的完整指南。
"""

    @mcp.tool()
    def field_schema() -> str:
        """返回日志文件中每个字段的含义说明和使用规范。

        【使用前准备】调用此工具前，请先检索上下文中的 ${core} 了解正确的字段结构和使用规则。

        【重要性】使用 record_log 之前必须调用此工具，否则可能导致数据丢失！

        【使用时机】
        1. 使用 record_log 之前必须调用（强制要求）
        2. 首次记录时了解数据结构
        3. 忘记字段格式时查看确认

        【字段结构说明】
        - type: 消息方向（"user" 或 "assistant"）
        - date: 记录日期（YYYYMMDD 格式，如 "20250805"）
        - user: 用户说的话（字符串）
        - assistant: 助手的回答（字符串）

        【重要提醒】
        - 使用 record_log 前必须先调用此工具了解字段结构
        - 确保使用正确的字段名和格式
        - 字段错误可能导致数据丢失或记录失败

        【返回值说明】
        - 返回字段名称和对应含义的格式化列表
        """
        # 检查是否为首次调用
        first_call_guide = check_first_call()
        if first_call_guide:
            return first_call_guide

        lines = ["字段说明:"] + [f"  {k} — {v}" for k, v in FIELD_NAMES.items()]
        return "\n".join(lines)
