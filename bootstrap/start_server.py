#!/usr/bin/env python3
"""MCP服务器启动包装器 - 用于调试启动问题"""

import sys
import signal
import asyncio
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，准备退出...")
    sys.exit(0)

def main():
    """主启动函数"""
    print("=" * 50)
    print("Thamus MCP 服务器启动")
    print("=" * 50)

    # 设置信号处理器
    if sys.platform != 'win32':
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 导入模块
        print("导入模块...")
        import config
        from tools import log_ops, version
        from mcp.server.fastmcp import FastMCP

        print(f"版本: {config.__version__}")
        print(f"日志目录: {config.LOG_DIR}")

        # 确保日志目录存在
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)

        # 读取说明文件
        print("读取说明文件...")
        instructions_file = Path(__file__).parent / "INSTRUCTIONS.md"
        instructions_content = instructions_file.read_text(encoding="utf-8")
        print(f"说明文件长度: {len(instructions_content)} 字符")

        # 创建MCP服务器
        print("创建MCP服务器...")
        mcp = FastMCP(
            "thamus-memory",
            instructions=instructions_content,
        )

        # 注册工具
        print("注册工具...")
        version.register_tools(mcp)
        log_ops.register_tools(mcp)

        # 获取传输模式
        transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
        print(f"传输模式: {transport}")
        print("=" * 50)
        print("服务器启动中...")
        print(f"按 Ctrl+C 停止服务器")
        print("=" * 50)

        # 运行服务器
        mcp.run(transport=transport)

    except KeyboardInterrupt:
        print("\n服务器被用户中断")
        return 0
    except Exception as e:
        print(f"\n服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
