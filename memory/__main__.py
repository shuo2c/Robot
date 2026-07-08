"""Thamus 记忆器官的命令行入口。

基于日志文件的记忆系统：对话原文存储在 memory/logs/ 目录下，
按日拆分文件，简化时补充元数据（importance、embedding、linked_ids）。

用法：
  写入   python -m memory log --user "..." --assistant "..."  追加一轮对话到当日日志
  查看   python -m memory recent-log [--n N]                  查看最近的日志记录
  简化   python -m memory consolidate [--today] [--all]       手动触发日志简化

数据存储格式：memory/logs/YYYYMMDDNN.json，文件名按日期+序号递增。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Windows 控制台默认编码为 GBK，强制设为 UTF-8 避免中文输出乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def cmd_log(args: argparse.Namespace) -> int:
    """将一轮对话（用户消息 + 助手回复）追加到当日日志文件。

    如果当日文件已满 3MB，自动创建新文件（序号递增）。
    如果日期已变化，自动切换到新日期的文件。
    """
    from .log_writer import LogWriter
    writer = LogWriter()
    writer.append(args.user, args.assistant)
    fp = writer.get_current_file()
    print(f"[日志] 写入 → {fp}")
    return 0


def cmd_consolidate(args: argparse.Namespace) -> int:
    """手动触发日志简化。

    简化流程：扫描 → 提纯 → 评分 → 建链 → 引用加成 → 向量化。
    简化是原地修改，不创建新记录，直接更新已有记录的元数据字段。

    参数：
      --today: 仅简化今日的文件（默认行为）
      --all:   简化所有历史文件
    """
    from .log_writer import LogWriter
    from .consolidator import Consolidator

    writer = LogWriter()
    consolidator = Consolidator(writer)

    # 根据参数决定处理范围：所有文件 或 仅今日文件
    if args.all:
        files = writer.get_all_files()
    else:
        files = writer.get_today_files()

    if not files:
        print("[简化] 没有找到可处理的文件。")
        return 0

    count = consolidator.run(files)
    print(f"[简化] 处理了 {count} 条记录。")
    return 0


def cmd_recent_log(args: argparse.Namespace) -> int:
    """查看最近的日志记录，按时间倒序排列。

    显示每条记录的 id、importance（如有）、用户消息和助手回复。
    用于快速浏览最近的对话内容。
    """
    from .log_writer import LogWriter

    writer = LogWriter()
    files = writer.get_all_files()
    if not files:
        print("[日志] 没有找到记录。")
        return 0

    # 读取所有日志文件中的记录
    all_records = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        all_records.extend(data)

    # 按时间戳倒序排列，最近的在前
    all_records.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
    # 截取前 n 条
    shown = all_records[:args.n]

    print(f"=== 最近 {len(shown)} 条日志记录 ===")
    for rec in shown:
        parts = [f"[{rec['id']}]"]
        # 如果已简化过，显示 importance
        if rec.get("importance"):
            parts.append(f"imp={rec['importance']}")
        parts.append(f"Q: {rec.get('user', '')}")
        parts.append(f"A: {rec.get('assistant', '')}")
        print(f"  {' | '.join(parts)}")
    return 0


def main() -> int:
    """CLI 主入口：解析命令行参数并分发到对应的子命令。

    支持三个子命令：
      log          写入一轮对话
      consolidate  触发日志简化
      recent-log   查看最近记录
    """
    parser = argparse.ArgumentParser(
        prog="python -m memory",
        description="Thamus 的记忆器官：日志写入 / 查看 / 简化。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- 日志写入命令 ----
    p_log = sub.add_parser("log", help="将一轮对话写入日志文件")
    p_log.add_argument("--user", required=True, help="用户消息内容")
    p_log.add_argument("--assistant", required=True, help="助手回复内容")
    p_log.set_defaults(func=cmd_log)

    # ---- 日志简化命令 ----
    p_consolidate = sub.add_parser("consolidate", help="手动触发日志简化")
    p_consolidate.add_argument("--today", action="store_true", help="仅简化今日文件")
    p_consolidate.add_argument("--all", action="store_true", help="简化所有文件")
    p_consolidate.set_defaults(func=cmd_consolidate)

    # ---- 日志查看命令 ----
    p_recent_log = sub.add_parser("recent-log", help="查看最近的日志记录")
    p_recent_log.add_argument("--n", type=int, default=10, help="显示的记录条数，默认 10")
    p_recent_log.set_defaults(func=cmd_recent_log)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
