"""Thamus 记忆器官的命令行。

基于日志文件的记忆系统：对话原文存在 memory/logs/，简化时补充元数据。

  写入   python -m memory log --user "..." --assistant "..."  追加一轮对话到当日日志
  查看   python -m memory recent-log [--n N]                  查看最近的日志记录
  简化   python -m memory consolidate [--today] [--all]       手动触发日志简化

存储落在 memory/logs/ 目录下，按日拆分。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def cmd_log(args: argparse.Namespace) -> int:
    """将一轮对话写入日志文件。"""
    from .log_writer import LogWriter
    writer = LogWriter()
    writer.append(args.user, args.assistant)
    fp = writer.get_current_file()
    print(f"[日志] 写入 → {fp}")
    return 0


def cmd_consolidate(args: argparse.Namespace) -> int:
    """手动触发日志简化。"""
    from .log_writer import LogWriter
    from .consolidator import Consolidator

    writer = LogWriter()
    consolidator = Consolidator(writer)

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
    """查看最近的日志记录。"""
    from .log_writer import LogWriter

    writer = LogWriter()
    files = writer.get_all_files()
    if not files:
        print("[日志] 没有找到记录。")
        return 0

    all_records = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        all_records.extend(data)

    # 按时间倒序
    all_records.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
    shown = all_records[:args.n]

    print(f"=== 最近 {len(shown)} 条日志记录 ===")
    for rec in shown:
        parts = [f"[{rec['id']}]"]
        if rec.get("importance"):
            parts.append(f"imp={rec['importance']}")
        parts.append(f"Q: {rec.get('user', '')}")
        parts.append(f"A: {rec.get('assistant', '')}")
        print(f"  {' | '.join(parts)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m memory",
        description="Thamus 的记忆器官：日志写入 / 查看 / 简化。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- 日志写入命令 ----
    p_log = sub.add_parser("log", help="将一轮对话写入日志文件")
    p_log.add_argument("--user", required=True, help="用户消息")
    p_log.add_argument("--assistant", required=True, help="助手回复")
    p_log.set_defaults(func=cmd_log)

    # ---- 简化命令 ----
    p_consolidate = sub.add_parser("consolidate", help="手动触发日志简化")
    p_consolidate.add_argument("--today", action="store_true", help="仅简化今日文件")
    p_consolidate.add_argument("--all", action="store_true", help="简化所有文件")
    p_consolidate.set_defaults(func=cmd_consolidate)

    # ---- 查看命令 ----
    p_recent_log = sub.add_parser("recent-log", help="查看最近的日志记录")
    p_recent_log.add_argument("--n", type=int, default=10, help="条数，默认 10")
    p_recent_log.set_defaults(func=cmd_recent_log)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
