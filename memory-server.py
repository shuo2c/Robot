#!/usr/bin/env python3
"""Thamus MCP 服务器 — 提供记忆查询能力。"""

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

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
    instructions="Thamus 的记忆查询服务。通过日志和历史片段回答关于 Thamus 的经历、记忆和对话。",
)


@mcp.tool()
def search_logs(query: str) -> str:
    """在记忆日志中搜索包含 query 的条目。返回最匹配的几条。"""
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
def field_schema() -> str:
    """返回日志文件中每个字段的含义说明。"""
    lines = ["字段说明:"] + [f"  {k} — {v}" for k, v in FIELD_NAMES.items()]
    return "\n".join(lines)


@mcp.tool()
def record_log(
    entries: list[dict[str, str]],
) -> str:
    """记录一条或多条对话日志到 logs/ 目录。

    每条日志条目自动按 date 字段归入 logs/YYYYMMDDHH.json。
    date 格式为 YYYYMMDDHH（年-月-日-时），缺省则自动生成。
    type 为 'user'（用户消息）或 'assistant'（助手回复）。
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


@mcp.resource("memo://about")
def about() -> str:
    """介绍这个 MCP 服务是什么。"""
    return (
        "我是 Thamus 的记忆查询 MCP 服务器。\n"
        "工具: record_log(记录对话), search_logs(搜索记忆), field_schema(查看字段含义).\n"
        "日志存放在 logs/ 目录下，每条日志是一个 JSON 数组条目。"
    )


if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run(transport=transport)  # type: ignore[call-overload]
