"""字段查询和使用指南工具"""

from mcp.server.fastmcp import FastMCP
from tools.log_ops import FIELD_NAMES
from tools.first_call import check_first_call


def register_tools(mcp: FastMCP) -> None:
    """注册字段查询工具到 MCP 服务器"""

    @mcp.tool()
    def usage_guide() -> str:
        """返回 Thamus 记忆系统的完整使用手册。

        每次会话开始时应该调用此工具获取使用说明。
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
        """返回日志文件中每个字段的含义说明。

        当用户询问日志结构、字段定义或需要理解记忆系统如何存储数据时调用此工具。
        """
        # 检查是否为首次调用
        first_call_guide = check_first_call()
        if first_call_guide:
            return first_call_guide

        lines = ["字段说明:"] + [f"  {k} — {v}" for k, v in FIELD_NAMES.items()]
        return "\n".join(lines)
