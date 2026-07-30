"""版本相关工具"""

from mcp.server.fastmcp import FastMCP
from config import __version__
from tools.rule_reference import add_rule_reference


def register_tools(mcp: FastMCP) -> None:
    """注册版本工具到 MCP 服务器"""

    @mcp.tool()
    def version() -> str:
        """返回 MCP 服务的版本信息。"""
        version_info = f"thamus-memory v{__version__}"
        return add_rule_reference(version_info, "core")
