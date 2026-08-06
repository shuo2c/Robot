"""日志操作工具 - 搜索和记录"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from config import LOG_DIR

logger = logging.getLogger("thamus-mcp")

# 日志业务的局部配置：每个日志文件的字段语义
FIELD_NAMES: dict[str, str] = {
    "type": "消息方向（user/assistant）",
    "date": "记录的日期（YYYYMMDD格式）",
    "user": "用户说的话",
    "assistant": "助手的回答",
}


def register_tools(mcp: FastMCP) -> None:
    """注册日志操作工具到 MCP 服务器"""

    @mcp.tool()
    def search_logs(query: str) -> str:
        """在记忆日志中搜索包含指定关键词的条目，返回最相关的历史记录。

        【使用前准备】调用此工具前，请先检索上下文中的 ${core} 和 ${tools-rules}，确保按照主动记忆规则搜索。

        【参数说明】
        - query (str): 搜索关键词，将在所有字段中模糊匹配

        【返回值说明】
        - 找到匹配：返回包含关键词的记录列表（最多20条），显示前10条，每条包含日期、类型、用户内容和助手回复
        - 未找到匹配：返回"未找到包含 '{query}' 的记录。"提示信息
        - 记忆目录异常：返回"记忆目录创建失败。"错误信息

        【使用时机】
        1. 对话开始时：搜索"最近对话"、"用户偏好"了解用户背景
        2. 用户询问过去时：搜索用户提到的具体关键词、主题名词
        3. 了解任务进展时：搜索任务名称、相关技术名词

        【搜索策略】
        - 选择精准关键词，避免过于宽泛的查询
        - 结合上下文理解用户意图，选择最相关的关键词
        - 搜索结果要整合分析，不要简单罗列

        【错误处理】
        - 返回空结果时：明确告知用户"我没有找到相关记录"
        - 首次对话时：告知用户这是首次对话，建议开始记录
        - 搜索失败时：重试1次，仍失败则告知用户搜索功能异常
        - 不要编造：不要编造或臆测历史信息，诚实告知搜索结果
        """
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
        """记录一条或多条对话日志到持久化存储，实现跨会话记忆。

        【使用前准备】调用此工具前，请先检索上下文中的 ${core}、${workflow-rule}、${active-mind} 和 ${tools-rules}，确保按照主动记忆规则和工作流程记录。每条日志条目自动按 date 字段归入 logs/YYYYMMDD.json。

        【标准记录流程】
        1. 第一步：准备记录内容，根据重要性分级决定是否记录
        2. 第二步：调用 record_log(entries=[...]) 记录

        【字段结构说明】
        - type: 消息方向（"user" 或 "assistant"）
        - date: 记录日期（YYYYMMDD 格式，如 "20250805"）
        - user: 用户说的话（字符串）
        - assistant: 助手的回答（字符串）

        【参数说明】
        - entries (list[dict]): 条目列表，每个条目包含：
          - type (str): 消息方向，"user" 或 "assistant"
          - date (str): 记录日期，YYYYMMDD 格式（如"20250805"）
          - user (str): 用户说的话
          - assistant (str): 助手的回答

        【使用时机】
        1. 对话结束时：记录总结和关键决策
        2. 发现重要信息时：立即记录
        3. 用户表达明确偏好时：立即记录
        4. 完成重要任务后：记录结果和经验

        【信息重要性分级】
        - P0（必须立即记录）：用户明确偏好、重要决策、任务完成结果
        - P1（应该记录）：异常情况、用户反馈模式、有意义的对话总结
        - P2（可选记录）：一般性交流、背景和上下文
        - P3（不记录）：纯聊天内容、重复信息、临时测试内容

        【返回值说明】
        - 成功：返回"成功写入 {N} 条日志。"
        - 失败：通过异常机制报告错误

        【错误处理】
        - 记录失败时：重试1次，仍失败则告知用户记录失败并建议手动记录
        - 数据验证失败时：检查字段格式是否正确，特别是日期格式

        【注意事项】
        - 确保字段名拼写正确，避免数据丢失
        - 根据重要性分级，避免记录无意义的对话碎片
        """
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
