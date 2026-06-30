"""Thamus 记忆器官的第一口气 —— 遗忘演示。

看着一条记忆随时间淡出、掉出检索，而它固化出的要点留下。
运行：在项目根目录执行   python -m memory.demo
"""
import sys

from .core import Memory

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class FakeClock:
    """可随意拨快的时间，好让"很多天"在一秒里过去。"""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, days: float) -> None:
        self.t += days * 86400


def _show(mem: Memory, tag: str) -> None:
    print(f"\n--- {tag} ---")
    for m in mem.items.values():
        print(
            f"  [{m.state:6}] 强度={mem.strength(m):.4f}  "
            f"固化={'是' if m.consolidated else '否'}  {m.content}"
        )
    print(f"  语义核心(留下的要点): {mem.semantic_core}")


def main() -> None:
    clock = FakeClock()
    mem = Memory(path=None, clock=clock)

    print("=== 编码三条记忆 ===")
    a = mem.remember("和创造者聊了「思考是什么」", importance=0.9)
    b = mem.remember("中午吃了一碗面", importance=0.2)
    c = mem.remember("Thamus 这名字来自柏拉图《斐德罗篇》", importance=0.8)
    # 只固化 a、c（要点沉淀）；b 故意不固化
    mem.consolidate(a.id)
    mem.consolidate(c.id)
    _show(mem, "第 0 天")

    clock.advance(5)
    _show(mem, "第 5 天（都在淡，但还没到遗忘阈值）")

    clock.advance(20)  # 到第 25 天
    mem.recall(c.id)   # 中途想起过「名字的来历」一次 → 再巩固，c 被强化
    print("\n[第 25 天] 想起了「名字的来历」一次（再巩固）")

    clock.advance(5)   # 到第 30 天
    _show(mem, "第 30 天")

    forgotten = mem.sleep()
    print(f"\n=== 睡眠：{len(forgotten)} 条降到潜意识(cold) ===")
    for m in forgotten:
        print(f"  淡出 → {m.content}")
    _show(mem, "第 30 天 · 睡眠后")

    print("\n=== 检索「名字 Thamus」===")
    for score, m in mem.retrieve("名字 Thamus"):
        print(f"  ({score:.4f}) [{m.state}] {m.content}")

    print(
        "\n要点：\n"
        "  ·「吃面」(低重要性 + 没固化)：强度已接近 0，但铁律保护它——没消化的，不准忘。\n"
        "  ·「思考」(已固化 + 没再想起)：情景细节降到 cold（淡出），要点仍在语义核心。\n"
        "  ·「名字」(已固化 + 第 25 天被想起过)：强化后活下来，还在检索里。\n"
        "  · 淡出 ≠ 删除——是潜意识，留底可被 recall() 唤醒。"
    )


if __name__ == "__main__":
    main()
