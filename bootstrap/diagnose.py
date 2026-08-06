#!/usr/bin/env python3
"""MCP服务器启动诊断脚本"""

import sys
import asyncio
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_imports():
    """测试依赖导入"""
    print("测试依赖导入...")
    try:
        import mcp
        print(f"✓ mcp 版本: {mcp.__version__ if hasattr(mcp, '__version__') else '未知'}")
    except ImportError as e:
        print(f"✗ mcp 导入失败: {e}")
        return False

    try:
        from mcp.server.fastmcp import FastMCP
        print("✓ FastMCP 导入成功")
    except ImportError as e:
        print(f"✗ FastMCP 导入失败: {e}")
        return False

    try:
        import config
        print(f"✓ config 导入成功, 版本: {config.__version__}")
    except ImportError as e:
        print(f"✗ config 导入失败: {e}")
        return False

    try:
        from tools import log_ops, version
        print("✓ tools 导入成功")
    except ImportError as e:
        print(f"✗ tools 导入失败: {e}")
        return False

    return True

def test_config():
    """测试配置文件"""
    print("\n测试配置...")
    try:
        from config import LOG_DIR
        print(f"✓ LOG_DIR: {LOG_DIR}")

        # 测试日志目录创建
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if LOG_DIR.is_dir():
            print("✓ 日志目录可以正常创建/访问")
        else:
            print("✗ 日志目录创建失败")
            return False
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

    return True

def test_instructions():
    """测试说明文件"""
    print("\n测试说明文件...")
    try:
        instructions_file = Path(__file__).parent / "INSTRUCTIONS.md"
        if instructions_file.exists():
            content = instructions_file.read_text(encoding="utf-8")
            print(f"✓ INSTRUCTIONS.md 读取成功 (长度: {len(content)} 字符)")
            return True
        else:
            print("✗ INSTRUCTIONS.md 文件不存在")
            return False
    except Exception as e:
        print(f"✗ 说明文件测试失败: {e}")
        return False

def test_server_creation():
    """测试服务器创建"""
    print("\n测试服务器创建...")
    try:
        from mcp.server.fastmcp import FastMCP
        import config
        from tools import log_ops, version

        instructions_file = Path(__file__).parent / "INSTRUCTIONS.md"
        instructions_content = instructions_file.read_text(encoding="utf-8")

        mcp = FastMCP(
            "thamus-memory",
            instructions=instructions_content,
        )
        print("✓ FastMCP 服务器创建成功")

        # 测试工具注册
        version.register_tools(mcp)
        print("✓ version 工具注册成功")

        log_ops.register_tools(mcp)
        print("✓ log_ops 工具注册成功")

        return True
    except Exception as e:
        print(f"✗ 服务器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主诊断流程"""
    print("=" * 50)
    print("Thamus MCP 服务器启动诊断")
    print("=" * 50)

    print(f"\nPython 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")

    tests = [
        ("依赖导入", test_imports),
        ("配置文件", test_config),
        ("说明文件", test_instructions),
        ("服务器创建", test_server_creation),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 50}")
        print(f"测试: {name}")
        print('=' * 50)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print(f"\n{'=' * 50}")
    print("诊断总结")
    print('=' * 50)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✓ 所有测试通过！服务器应该可以正常启动。")
        print("如果仍然出现启动错误，可能是以下原因：")
        print("1. 启动时被外部中断（检查IDE配置）")
        print("2. 端口冲突（如果使用 SSE 模式）")
        print("3. Python 3.13 异步处理问题（考虑降级到 Python 3.11/3.12）")
        return 0
    else:
        print("\n✗ 部分测试失败，请根据上述错误信息修复问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
