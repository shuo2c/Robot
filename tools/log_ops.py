"""日志操作工具 - 搜索和记录"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from config import LOG_DIR
from tools.first_call import check_first_call

logger = logging.getLogger("thamus-mcp")

# 日志业务的局部配置：每个日志文件的字段语义
FIELD_NAMES: dict[str, str] = {
    "type": "消息方向 (user/assistant)",
    "date": "记录的日期 YYYYMMDD",
    "user": "用户说的话",
    "assistant": "助手的回答",
}


def register_tools(mcp: FastMCP) -> None:
    """注册日志操作工具到 MCP 服务器"""

    @mcp.tool()
    def search_logs(query: str) -> str:
        """在记忆日志中搜索包含 query 的条目。返回最匹配的几条。

        IMPORTANT: 当用户询问过去的事情、偏好设置、历史对话或任何需要回忆的信息时，
        应该主动调用此工具，不要等用户明确要求搜索。
        """
        # 检查是否为首次调用
        first_call_guide = check_first_call()
        if first_call_guide:
            return first_call_guide

        # 确保日志目录存在
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        if not LOG_DIR.is_dir():
            return "记忆目录创建失败。"

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
    def record_log(entries: list[dict[str, str]]) -> str:
        """记录一条或多条对话日志到 logs/ 目录，实现持久化记忆。

        每条日志条目自动按 date 字段归入 logs/YYYYMMDD.json。
        date 格式为 YYYYMMDD（年-月-日），缺省则自动生成。
        type 为 'user'（用户消息）或 'assistant'（助手回复）。

        CRITICAL - 主动调用时机（不要等待用户请求）：
        1. 对话结束时：记录本次对话的关键结论、决策和重要信息
        2. 用户表达明确偏好时：记录用户的喜好、设置、工作习惯
        3. 完成重要任务后：记录任务结果、解决方案、遇到的问题
        4. 用户提及个人信息：记录项目背景、团队信息、环境配置等

        这是实现持久化记忆的核心工具，agent 应该主动判断何时需要记录，
        而不是被动等待用户明确要求"记录这个"。
        """
        # 检查是否为首次调用
        first_call_guide = check_first_call()
        if first_call_guide:
            return first_call_guide

        LOG_DIR.mkdir(parents=True, exist_ok=True)

        written = 0
        for entry in entries:
            date = entry.get("date") or datetime.now().strftime("%Y%m%d")
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
