"""版本相关工具"""

from mcp.server.fastmcp import FastMCP
from config import __version__


def register_tools(mcp: FastMCP) -> None:
    """注册版本工具到 MCP 服务器"""

    @mcp.tool()
    def version() -> str:
        """返回 MCP 服务的版本信息。

        【使用前准备】调用此工具前，请先检索上下文中的 ${version} 和 ${version-info} 了解版本信息的具体格式和当前版本。
        """
        return f"thamas-memory v{__version__}"
