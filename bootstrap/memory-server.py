#!/usr/bin/env python3
"""Thamus MCP 服务器 — 提供记忆查询能力。"""

import logging
import sys
from pathlib import Path

# 添加父目录到 Python 路径，以便导入项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP

import config
from tools import log_ops, version

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("thamus-mcp")

# 读取服务器说明文档
instructions_file = Path(__file__).parent / "INSTRUCTIONS.md"
instructions_content = instructions_file.read_text(encoding="utf-8")

# 创建 MCP 服务器
mcp = FastMCP(
    "thamus-memory",
    instructions=instructions_content,
)

# 注册所有工具模块
version.register_tools(mcp)
log_ops.register_tools(mcp)

# 注册资源
@mcp.resource("memo://about")
def about() -> str:
    """介绍这个 MCP 服务是什么。"""
    return (
        f"我是 Thamus 的记忆查询 MCP 服务器（版本 {config.__version__}）。\n"
        "工具: record_log(记录对话), search_logs(搜索记忆), version(获取版本).\n"
        "日志存放在 logs/ 目录下，每条日志是一个 JSON 数组条目。"
    )


if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run(transport=transport)  # type: ignore[call-overload]
