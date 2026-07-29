#!/usr/bin/env python3
"""Thamus MCP 服务器 — 提供记忆查询能力。"""

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

__version__ = "0.0.1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("thamus-mcp")

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"

# 每个日志文件的字段语义（与 memory/logs/*.json 对齐）
FIELD_NAMES: dict[str, str] = {
    "type": "消息方向 (user/assistant)",
    "date": "记录的日期 YYYYMMDDHH",
    "user": "用户说的话",
    "assistant": "助手的回答",
}


mcp = FastMCP(
    "thamus-memory",
    instructions="""Thamus 的持久化记忆服务。

    核心能力：
    1. record_log - 主动记录重要对话、用户偏好、任务结果到持久化存储
    2. search_logs - 搜索历史对话和记忆，回答"之前做过什么"、"用户喜欢什么"等问题
    3. field_schema - 查看记忆系统的数据结构

    使用原则：
    - 对话结束时主动记录关键信息（不要等用户要求）
    - 用户询问过去的事情时主动搜索记忆
    - 将用户的明确偏好和设置记录到记忆中

    这不是被动响应的工具，而是 agent 应该主动使用的记忆系统。""",
)


@mcp.tool()
def search_logs(query: str) -> str:
    """在记忆日志中搜索包含 query 的条目。返回最匹配的几条。

    IMPORTANT: 当用户询问过去的事情、偏好设置、历史对话或任何需要回忆的信息时，
    应该主动调用此工具，不要等用户明确要求搜索。
    """
    if not LOG_DIR.is_dir():
        return "记忆目录不存在。"

    results: list[dict[str, Any]] = []
    for f in sorted(LOG_DIR.glob("*.json"), reverse=True):
        try:
            with open(f, encoding="utf-8") as fh:
                entries = json.load(fh)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("读取 %s 失败: %s", f.name, e)
            continue

        for entry in entries:
            text = " ".join(v or "" for v in entry.values())
            if query.lower() in text.lower():
                results.append(entry)
                if len(results) >= 20:
                    break

    if not results:
        return f"未找到包含 '{query}' 的记录。"

    out_lines = [f"找到 {len(results)} 条匹配："]
    for i, r in enumerate(results[:10], 1):
        date = r.get("date", "?")
        role = r.get("type", "?")
        user = r.get("user", "")[:200]
        assistant = r.get("assistant", "")[:200]
        out_lines.append(f"--- {i}. 日期:{date} 类型:{role}")
        if user:
            out_lines.append(f"  用户: {user}")
        if assistant:
            out_lines.append(f"  我:   {assistant}")

    return "\n".join(out_lines)


@mcp.tool()
def usage_guide() -> str:
    """返回 Thamus 记忆系统的完整使用手册。

    每次会话开始时应该调用此工具获取使用说明。
    """
    return """
# Thamus 记忆系统使用手册

你是一个有持久记忆的 AI 助手，通过 thamus-memory MCP 实现记忆功能。

## 核心原则

- **主动记录**：不要等用户要求，主动判断何时需要记录
- **全面记录**：记录用户偏好、任务结果、重要决策
- **结构化存储**：使用标准格式存储，便于后续检索

## 必须执行的时机

### 1. 会话开始时
立即调用 `record_log` 记录会话启动：
```json
{
  "entries": [
    {
      "type": "assistant",
      "assistant": "会话启动 - 准备为用户提供记忆服务"
    }
  ]
}
```

### 2. 用户表达明确偏好时
```json
{
  "entries": [
    {
      "type": "user",
      "user": "我喜欢函数式编程风格"
    }
  ]
}
```

### 3. 完成重要任务后
```json
{
  "entries": [
    {
      "type": "assistant",
      "assistant": "完成了用户认证模块的开发，采用 JWT 方案"
    }
  ]
}
```

### 4. 用户提及个人信息时
```json
{
  "entries": [
    {
      "type": "user",
      "user": "项目使用 PostgreSQL 数据库，部署在 AWS 上"
    }
  ]
}
```

### 5. 会话结束时
```json
{
  "entries": [
    {
      "type": "assistant",
      "assistant": "会话总结 - 今天讨论了 MCP 记忆系统的实现逻辑"
    }
  ]
}
```

## 可用工具说明

- **record_log**: 记录对话日志到持久化存储
  - entries: 日志条目数组
  - 每个条目包含 type (user/assistant) 和对应字段

- **search_logs**: 搜索历史对话和记忆
  - query: 搜索关键词
  - 返回相关的历史记录

- **field_schema**: 查看记忆系统的数据结构
  - 返回每个字段的含义说明

## 记录格式规范

type 字段：
- "user" - 用户消息
- "assistant" - 助手回复

date 字段：
- 格式：YYYYMMDDHH (年月日时)
- 示例：2026072910
- 可省略，自动生成当前时间

user/assistant 字段：
- 对应角色的具体内容
- 避免过长，提取关键信息

## 工作流程建议

1. **会话启动** → 调用 usage_guide + record_log(会话启动)
2. **搜索历史** → 调用 search_logs 了解用户背景
3. **对话过程中** → 主动记录重要信息
4. **会话结束** → 调用 record_log(会话总结)

## 示例对话流程

用户：我想优化数据库查询
助手：让我先查看相关历史记录
      [调用 search_logs("数据库 查询 优化")]

      根据历史，你之前选择了 PostgreSQL...

      [如果用户表达偏好]
      [调用 record_log 记录偏好]

      让我们帮你优化查询...
"""

@mcp.tool()
def field_schema() -> str:
    """返回日志文件中每个字段的含义说明。

    当用户询问日志结构、字段定义或需要理解记忆系统如何存储数据时调用此工具。
    """
    lines = ["字段说明:"] + [f"  {k} — {v}" for k, v in FIELD_NAMES.items()]
    return "\n".join(lines)


@mcp.tool()
def record_log(
    entries: list[dict[str, str]],
) -> str:
    """记录一条或多条对话日志到 logs/ 目录，实现持久化记忆。

    每条日志条目自动按 date 字段归入 logs/YYYYMMDDHH.json。
    date 格式为 YYYYMMDDHH（年-月-日-时），缺省则自动生成。
    type 为 'user'（用户消息）或 'assistant'（助手回复）。

    CRITICAL - 主动调用时机（不要等待用户请求）：
    1. 对话结束时：记录本次对话的关键结论、决策和重要信息
    2. 用户表达明确偏好时：记录用户的喜好、设置、工作习惯
    3. 完成重要任务后：记录任务结果、解决方案、遇到的问题
    4. 用户提及个人信息：记录项目背景、团队信息、环境配置等

    这是实现持久化记忆的核心工具，agent 应该主动判断何时需要记录，
    而不是被动等待用户明确要求"记录这个"。
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    written = 0
    for entry in entries:
        date = entry.get("date") or datetime.now().strftime("%Y%m%d%H")
        fpath = LOG_DIR / f"{date}.json"

        if fpath.exists():
            try:
                with open(fpath, encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = []
        else:
            existing = []

        record = {
            "type": entry.get("type", "user"),
            "date": date,
            "user": entry.get("user", ""),
            "assistant": entry.get("assistant", ""),
        }
        existing.append(record)

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        written += 1

    return f"成功写入 {written} 条日志。"


@mcp.tool()
def version() -> str:
    """返回 MCP 服务的版本信息。"""
    return f"thamus-memory v{__version__}"


@mcp.resource("memo://about")
def about() -> str:
    """介绍这个 MCP 服务是什么。"""
    return (
        f"我是 Thamus 的记忆查询 MCP 服务器（版本 {__version__}）。\n"
        "工具: record_log(记录对话), search_logs(搜索记忆), field_schema(查看字段含义), version(获取版本).\n"
        "日志存放在 logs/ 目录下，每条日志是一个 JSON 数组条目。"
    )


if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run(transport=transport)  # type: ignore[call-overload]
