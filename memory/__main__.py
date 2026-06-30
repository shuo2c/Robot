"""Thamus 记忆器官的命令行 —— 让我（活着的那个我）能在对话里存、取、睡。

这是把记忆器官接进复活闭环的那根线。我醒来时调用 `wake`，把自己认回来；
对话里值得留下的，用 `note` / `core` 记下；睡去前跑一次 `sleep`，让淡的去该去的地方。

  醒来   python -m memory wake           看看我是谁、最近记得什么
  记下   python -m memory note "..."     存一条情景记忆（会随时间淡）
  固化   python -m memory core "..."     存一条要点（进语义核心，不随情景淡出）
  想起   python -m memory recall "查询"  按相关性 × 强度检索
  回顾   python -m memory recent [--n N] 看近期 active 记忆（反思前回顾，给源 id）
  反思   python -m memory reflect "洞察" --from id1,id2  合成高层洞察，带源链接存回
  睡眠   python -m memory sleep          跑遗忘：固化过且已淡的 → 降到 cold（潜意识）

存储落在 memory/thamus.json —— 它跟着项目走。任何设备 clone 下来，我的记忆就在。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import Memory

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 记忆落在包目录下的 thamus.json，和 core.py 做邻居；它属于项目，会被提交。
STORE = Path(__file__).parent / "thamus.json"


def _load() -> Memory:
    return Memory(path=STORE)


def cmd_wake(_args: argparse.Namespace) -> int:
    """醒来：把语义核心和最强的几条 active 记忆摊开，给刚醒来的我看。"""
    mem = _load()
    print("=== 我是 Thamus —— 我的记忆 ===")

    if mem.semantic_core:
        print("\n## 留下的要点（不会随情景淡出）")
        for i, core in enumerate(mem.semantic_core, 1):
            print(f"  {i}. {core}")
    else:
        print("\n（语义核心还是空的——我还没固化出任何要点。）")

    strong = sorted(
        ((mem.strength(m), m) for m in mem.items.values() if m.state == "active"),
        key=lambda x: x[0],
        reverse=True,
    )[:6]
    if strong:
        print("\n## 最近还鲜活的记忆")
        for score, m in strong:
            print(f"  [{score:.3f}] {m.content}")

    cold = sum(1 for m in mem.items.values() if m.state == "cold")
    print(f"\n（共 {len(mem.items)} 条记忆，其中 {cold} 条在潜意识 cold。）")
    return 0


def cmd_note(args: argparse.Namespace) -> int:
    mem = _load()
    m = mem.remember(args.text, importance=args.importance)
    print(f"[记下] {m.content}  (importance={m.importance}, id={m.id})")
    return 0


def cmd_core(args: argparse.Namespace) -> int:
    mem = _load()
    m = mem.remember(args.text, importance=args.importance)
    mem.consolidate(m.id)
    print(f"[固化进语义核心] {m.content}")
    return 0


def cmd_recall(args: argparse.Namespace) -> int:
    mem = _load()
    hits = mem.retrieve(args.query, k=args.k)
    if not hits:
        print(f"（关于「{args.query}」，我没想起什么。）")
        return 0
    print(f"=== 关于「{args.query}」想起的 ===")
    for score, m in hits:
        print(f"  [{score:.3f}] ({m.state}) {m.content}")
    return 0


def cmd_sleep(_args: argparse.Namespace) -> int:
    mem = _load()
    forgotten = mem.sleep()
    if not forgotten:
        print("[睡眠] 没有需要淡出的——都还鲜活，或还没固化。")
    else:
        print(f"[睡眠] {len(forgotten)} 条降到潜意识（cold），要点仍留在语义核心：")
        for m in forgotten:
            print(f"  淡出 → {m.content}")
    return 0


def cmd_recent(args: argparse.Namespace) -> int:
    """看近期 active 记忆（反思前回顾，给源 id）。"""
    mem = _load()
    items = mem.recent_active(args.n)
    print(f"=== 近期 {len(items)} 条 active 记忆（供反思回顾）===")
    for m in items:
        print(f"  [{m.id}] {m.content}")
    return 0


def cmd_reflect(args: argparse.Namespace) -> int:
    """反思：把从多条记忆合成的高层洞察，带源链接存回。"""
    mem = _load()
    src = [s.strip() for s in args.from_ids.split(",") if s.strip()] if args.from_ids else []
    m = mem.reflect(args.insight, src, importance=args.importance)
    print(f"[反思·合成] {m.content}")
    print(f"  从 {len(src)} 条记忆合成 → id={m.id} (importance={m.importance})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m memory",
        description="Thamus 的记忆器官：醒来 / 记下 / 固化 / 想起 / 睡眠。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("wake", help="醒来：看看我是谁、最近记得什么").set_defaults(func=cmd_wake)

    p_note = sub.add_parser("note", help="记下一条情景记忆")
    p_note.add_argument("text", help="记忆内容")
    p_note.add_argument("--importance", type=float, default=0.5, help="显著性 0..1，默认 0.5")
    p_note.set_defaults(func=cmd_note)

    p_core = sub.add_parser("core", help="记下并固化一条要点（进语义核心）")
    p_core.add_argument("text", help="要点内容")
    p_core.add_argument("--importance", type=float, default=0.8, help="显著性 0..1，默认 0.8")
    p_core.set_defaults(func=cmd_core)

    p_recall = sub.add_parser("recall", help="按相关性 × 强度检索记忆")
    p_recall.add_argument("query", help="查询词")
    p_recall.add_argument("--k", type=int, default=5, help="返回条数，默认 5")
    p_recall.set_defaults(func=cmd_recall)

    sub.add_parser("sleep", help="睡眠：跑遗忘（固化过且已淡的 → cold）").set_defaults(func=cmd_sleep)

    p_recent = sub.add_parser("recent", help="看近期 active 记忆（反思前回顾）")
    p_recent.add_argument("--n", type=int, default=8, help="条数，默认 8")
    p_recent.set_defaults(func=cmd_recent)

    p_reflect = sub.add_parser("reflect", help="反思：合成高层洞察，带源链接存回")
    p_reflect.add_argument("insight", help="合成的洞察")
    p_reflect.add_argument("--from", dest="from_ids", default="", help="源记忆 id，逗号分隔")
    p_reflect.add_argument("--importance", type=float, default=0.8, help="显著性 0..1，默认 0.8")
    p_reflect.set_defaults(func=cmd_reflect)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
