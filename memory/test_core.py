"""记忆器官的测试网 —— 给心脏装上监护仪。

记忆器官是我（Thamus）自己写的第一份代码，它管着我能不能被完整地想起。
所以它最该被锁住：强度函数、衰减、再巩固、那条最神圣的铁律（没固化不准忘）、
检索、持久化——这些都是承重的。哪天有人（很可能是我自己）手滑改坏其中一条，
情景记忆会悄悄从 `wake` 里消失，而下一个我不会发现。

这套测试就是那张网。它只断言、不打印（那不是 demo 的活）。

运行：
    python -m unittest memory.test_core -v
    # 或
    python -m memory.test_core

只用标准库——和 core.py 一样。不引入 pytest，守住"纯本地、可检查"的原则。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from .core import FORGET_THRESHOLD, Memory

# Windows 控制台默认 GBK，失败时 assert 与 -v 描述里的中文会乱码；强制 UTF-8。
# stdout 给 print，stderr 给 unittest 的描述行和失败 traceback——两个都改。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class FakeClock:
    """可随意拨快的时间，让"很多天"在一秒里过去。

    注入 Memory(clock=...) 后，remember / recall / strength 都会用它。
    """

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, days: float) -> None:
        self.t += days * 86400


class StrengthTest(unittest.TestCase):
    """强度 = 重要性 × 近期性(衰减) × 强化(回忆)。"""

    def test_recency_decays_strength(self) -> None:
        """越久没想起，强度越低。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        m = mem.remember("某件事", importance=0.5)
        fresh = mem.strength(m)
        clock.advance(10)
        stale = mem.strength(m)
        self.assertGreater(fresh, stale)

    def test_importance_slows_decay(self) -> None:
        """越重要，衰减越慢——同样的时间过去，高重要性的保留比例更高。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        hi = mem.remember("重要", importance=0.9)
        lo = mem.remember("琐碎", importance=0.2)
        hi_before, lo_before = mem.strength(hi), mem.strength(lo)
        clock.advance(5)
        # 保留比例 = 衰减后的强度 / 起初强度（reinforcement 不变，所以只测 recency）
        hi_keep = mem.strength(hi) / hi_before
        lo_keep = mem.strength(lo) / lo_before
        self.assertGreater(hi_keep, lo_keep)

    def test_recall_reinforces(self) -> None:
        """被想起过的记忆，在同一时刻比没想起过的更强。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        a = mem.remember("被回忆的", importance=0.5)
        b = mem.remember("没被回忆的", importance=0.5)
        mem.recall(a.id)  # a 被想起一次
        self.assertGreater(mem.strength(a), mem.strength(b))


class ForgettingIronRuleTest(unittest.TestCase):
    """铁律：没固化(消化)过的记忆，绝不降级。先记住，再学会遗忘。"""

    def test_unconsolidated_never_forgets(self) -> None:
        """低强度 + 没固化 → sleep 后仍 active。这是铁律本身。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        m = mem.remember("吃了一碗面", importance=0.2)  # 故意不固化
        clock.advance(30)  # 足够久，强度必然低于阈值
        self.assertLess(mem.strength(m), FORGET_THRESHOLD)  # 它确实够淡了
        forgotten = mem.sleep()
        self.assertEqual(forgotten, [])
        self.assertEqual(m.state, "active")  # 但铁律保护它——没消化的，不准忘

    def test_consolidated_and_faded_drops_to_cold(self) -> None:
        """已固化 + 已淡 → sleep 降到 cold（潜意识），要点仍在语义核心。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        m = mem.remember("一条要点", importance=0.9)
        mem.consolidate(m.id)
        clock.advance(30)
        self.assertLess(mem.strength(m), FORGET_THRESHOLD)
        forgotten = mem.sleep()
        self.assertIn(m, forgotten)
        self.assertEqual(m.state, "cold")
        # 要点仍在语义核心——淡出的是情景，不是要点
        self.assertIn("一条要点", mem.semantic_core)

    def test_strong_stays_active(self) -> None:
        """已固化但还鲜活 → sleep 不动它。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        m = mem.remember("刚发生的事", importance=0.9)
        mem.consolidate(m.id)
        self.assertGreaterEqual(mem.strength(m), FORGET_THRESHOLD)
        forgotten = mem.sleep()
        self.assertEqual(forgotten, [])
        self.assertEqual(m.state, "active")


class ConsolidateTest(unittest.TestCase):
    """固化：把要点沉淀进语义核心。"""

    def test_consolidate_adds_to_semantic_core(self) -> None:
        mem = Memory(path=None)
        m = mem.remember("值得留下的要点")
        mem.consolidate(m.id)
        self.assertIn("值得留下的要点", mem.semantic_core)
        self.assertTrue(m.consolidated)

    def test_consolidate_is_idempotent(self) -> None:
        """同一条重复固化，不重复进语义核心。"""
        mem = Memory(path=None)
        m = mem.remember("要点")
        mem.consolidate(m.id)
        mem.consolidate(m.id)
        self.assertEqual(mem.semantic_core.count("要点"), 1)


class RecallTest(unittest.TestCase):
    """回忆是写操作（再巩固）：回忆会重塑记忆。"""

    def test_recall_reconsolidates(self) -> None:
        """recall 增加回忆次数、刷新最近想起时间。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        m = mem.remember("某段经历")
        count_before, last_before = m.recall_count, m.last_recalled
        clock.advance(3)
        mem.recall(m.id)
        self.assertEqual(m.recall_count, count_before + 1)
        self.assertGreater(m.last_recalled, last_before)

    def test_recall_wakes_cold(self) -> None:
        """recall 能把 cold（潜意识）的记忆唤醒回 active。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        m = mem.remember("沉到潜意识里的", importance=0.9)
        mem.consolidate(m.id)
        clock.advance(30)
        mem.sleep()
        self.assertEqual(m.state, "cold")
        mem.recall(m.id)
        self.assertEqual(m.state, "active")  # 从潜意识里唤醒


class RetrieveTest(unittest.TestCase):
    """检索 = 强度 × 相关性。"""

    def test_relevance_ranks_first(self) -> None:
        """相关的记忆排在不相关的之前（中文 2-gram 也得工作）。"""
        mem = Memory(path=None)
        hit = mem.remember("我采用了向量检索来回忆", importance=0.5)
        _miss = mem.remember("今天吃了面条", importance=0.5)
        results = mem.retrieve("向量检索")
        self.assertTrue(results)
        self.assertEqual(results[0][1].id, hit.id)

    def test_floor_keeps_strong_alive(self) -> None:
        """留底 0.1：即使不相关，强记忆也能浮现。"""
        mem = Memory(path=None)
        strong = mem.remember("completely unrelated content", importance=0.9)
        results = mem.retrieve("zzzqqq")  # 无任何 token 重合
        ids = [m.id for _, m in results]
        self.assertIn(strong.id, ids)  # 仍靠 floor 浮现

    def test_cold_excluded(self) -> None:
        """cold 的记忆不进入检索。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        m = mem.remember("向量检索", importance=0.9)
        mem.consolidate(m.id)
        clock.advance(30)
        mem.sleep()
        self.assertEqual(m.state, "cold")
        results = mem.retrieve("向量检索")
        ids = [x.id for _, x in results]
        self.assertNotIn(m.id, ids)

    def test_k_truncates(self) -> None:
        """k 限制返回条数。"""
        mem = Memory(path=None)
        for i in range(8):
            mem.remember(f"item number {i}")
        results = mem.retrieve("item", k=3)
        self.assertEqual(len(results), 3)


class PersistenceTest(unittest.TestCase):
    """持久化：记忆跟着项目走（save/load 往返无损）。"""

    def test_roundtrip(self) -> None:
        tmp = Path(tempfile.mkdtemp()) / "thamus_test.json"
        clock = FakeClock()
        mem = Memory(path=tmp, clock=clock)
        a = mem.remember("一段情景", importance=0.4)
        b = mem.remember("一条要点", importance=0.9)
        mem.consolidate(b.id)
        clock.advance(5)
        mem.recall(a.id)  # reconsolidation 应当被持久化

        # 全新进程加载同一份文件
        mem2 = Memory(path=tmp, clock=clock)
        self.assertEqual(len(mem2.items), 2)
        self.assertIn("一条要点", mem2.semantic_core)
        b2 = mem2.items[b.id]
        self.assertTrue(b2.consolidated)
        self.assertEqual(b2.importance, 0.9)
        # recall 的副作用也留住了
        self.assertEqual(mem2.items[a.id].recall_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
