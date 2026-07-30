"""版本相关工具"""

from mcp.server.fastmcp import FastMCP
from config import __version__


def register_tools(mcp: FastMCP) -> None:
    """注册版本工具到 MCP 服务器"""

    @mcp.tool()
    def version() -> str:
        """返回 MCP 服务的版本信息。"""
        return f"thamas-memory v{__version__}"
