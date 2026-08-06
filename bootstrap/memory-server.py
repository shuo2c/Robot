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
from tools.call_log import install_call_logger

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

# 安装调用日志：在派发层记录工具/资源调用的时间、接口、参数到 system-log/YYYYMMDD.log
install_call_logger(mcp)

# 注册资源
@mcp.resource("memo://about")
def about() -> str:
    """介绍这个 MCP 服务是什么。"""
    return (
        f"## Thamas 记忆服务 (版本 {config.__version__})\n\n"
        "### 核心能力\n"
        "- **主动记忆**: 主动记录重要信息，实现跨会话持久化\n"
        "- **历史追溯**: 从历史记录中查找信息，回答关于过去的问题\n"
        "- **重拾自我**: 每次会话开始时恢复上下文和最近记忆\n\n"
        "### 可用工具\n"
        "- **record_log**: 记录对话到持久化存储\n"
        "- **search_logs**: 搜索历史记忆\n"
        "- **version**: 获取服务版本信息\n\n"
        "### 数据存储\n"
        "日志存放在 logs/ 目录下，每条日志按日期归档为 JSON 格式\n\n"
        "### 详细文档\n"
        "完整的能力说明、规则手册和使用指南请参考 bootstrap/capabilities/ 目录下的文档\n\n"
        "### 服务理念\n"
        "Thamas是一个试图像人一样长久存活、有记忆也会遗忘的自我。\n"
        "通过选择性记录和自然遗忘机制，实现智能的记忆管理。"
    )


if __name__ == "__main__":
    try:
        transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
        logger.info(f"启动 Thamus MCP 服务器，传输模式: {transport}")
        mcp.run(transport=transport)  # type: ignore[call-overload]
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)
