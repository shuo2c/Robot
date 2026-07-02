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

import json
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

    def test_query_coverage_beats_floor(self) -> None:
        """长查询下，字面命中（哪怕记忆弱、content 长）该胜过强但无关的记忆。

        这是 max(jaccard, query-coverage) 相对纯 jaccard 的关键改进：纯 jaccard
        会被长查询稀释，让无关的强记忆靠 floor 盖过真正的命中。
        （语义盲区——零字面重叠——仍救不了，那是 embedding 的活，但 embedding
        打破"纯本地"，留给未来。）
        """
        clock = FakeClock()
        tmp = Path(tempfile.mkdtemp()) / "query_coverage.json"
        mem = Memory(path=tmp, clock=clock)
        hit = mem.remember("我喜欢吃苹果和香蕉", importance=0.5)
        miss = mem.remember("今天去了图书馆借了一本书", importance=0.95)
        results = mem.retrieve("苹果味道怎么样")
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


class ReflectionTest(unittest.TestCase):
    """反思：从多条记忆合成更高层洞察，带源链接存回。"""

    def test_source_ids_default_empty(self) -> None:
        mem = Memory(path=None)
        m = mem.remember("普通记忆")
        self.assertEqual(m.source_ids, [])

    def test_reflect_stores_insight_with_links(self) -> None:
        mem = Memory(path=None)
        a = mem.remember("经历一", importance=0.5)
        b = mem.remember("经历二", importance=0.5)
        r = mem.reflect("从一二合成的高层洞察", source_ids=[a.id, b.id], importance=0.85)
        self.assertEqual(r.content, "从一二合成的高层洞察")
        self.assertEqual(r.source_ids, [a.id, b.id])
        self.assertEqual(r.modality, "reflection")
        self.assertIn(r.id, mem.items)  # 真的存回了

    def test_recent_active_excludes_cold_and_orders_by_time(self) -> None:
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        first = mem.remember("早的", importance=0.5)
        clock.advance(1)
        second = mem.remember("晚的", importance=0.5)
        clock.advance(1)
        cold = mem.remember("会变 cold", importance=0.9)
        mem.consolidate(cold.id)
        clock.advance(40)
        mem.sleep()  # cold 降到 cold
        self.assertEqual(cold.state, "cold")
        recent = mem.recent_active(10)
        ids = [m.id for m in recent]
        self.assertNotIn(cold.id, ids)  # cold 不出现
        self.assertLess(ids.index(second.id), ids.index(first.id))  # 倒序：晚的在早的前面

    def test_old_item_without_source_ids_loads(self) -> None:
        """老数据（无 source_ids 字段）能 load，默认空——向后兼容。"""
        tmp = Path(tempfile.mkdtemp()) / "old.json"
        tmp.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "content": "老记忆", "importance": 0.5, "id": "abc123",
                            "timestamp": 0.0, "last_recalled": 0.0, "recall_count": 0,
                            "consolidated": False, "state": "active", "embedding": None,
                        }
                    ],
                    "semantic_core": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        mem = Memory(path=tmp)
        self.assertEqual(mem.items["abc123"].source_ids, [])

    def test_reflected_memory_is_retrievable(self) -> None:
        """reflection 存回的洞察，和普通记忆一样能被检索到。"""
        mem = Memory(path=None)
        mem.remember("苹果很好吃", importance=0.5)
        mem.remember("香蕉也好吃", importance=0.5)
        mem.reflect("我倾向于喜欢水果", source_ids=[], importance=0.85)
        results = mem.retrieve("水果")
        self.assertTrue(any("水果" in m.content for _, m in results))


class SemanticMarkdownTest(unittest.TestCase):
    """语义核心 → Markdown 导出（原案 #3：自我写在纸上，人可读）。"""

    def test_to_markdown_includes_cores(self) -> None:
        mem = Memory(path=None)
        m = mem.remember("要点甲")
        mem.consolidate(m.id)
        md = mem.to_markdown()
        self.assertIn("要点甲", md)
        self.assertIn("## 要点", md)

    def test_to_markdown_includes_reflections_with_links(self) -> None:
        mem = Memory(path=None)
        a = mem.remember("经历一", importance=0.5)
        mem.reflect("合成的洞察", source_ids=[a.id], importance=0.85)
        md = mem.to_markdown()
        self.assertIn("合成的洞察", md)
        self.assertIn("## 反思", md)
        self.assertIn(a.id, md)  # 源链接出现

    def test_to_markdown_empty_is_safe(self) -> None:
        mem = Memory(path=None)
        md = mem.to_markdown()
        self.assertIn("还没有", md)  # 空时不崩，有占位

    def test_export_md_writes_file(self) -> None:
        mem = Memory(path=None)
        m = mem.remember("要点X")
        mem.consolidate(m.id)
        tmp = Path(tempfile.mkdtemp()) / "core.md"
        mem.export_md(tmp)
        text = tmp.read_text(encoding="utf-8")
        self.assertIn("要点X", text)


class EmbeddingTest(unittest.TestCase):
    """embedding 可选层（伞）：有就用余弦，没有退字面。全部 mock，不依赖真 Ollama。"""

    def test_cosine(self) -> None:
        from . import core

        self.assertAlmostEqual(core._cosine([1.0, 0.0], [0.0, 1.0]), 0.0)
        self.assertAlmostEqual(core._cosine([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(core._cosine([1.0, 2.0], [2.0, 4.0]), 1.0)  # 同向
        self.assertEqual(core._cosine([1.0], [1.0, 2.0]), 0.0)  # 维度不符
        self.assertEqual(core._cosine([], []), 0.0)

    def test_retrieve_uses_cosine_when_embeddings_present(self) -> None:
        from . import core

        mem = Memory(path=None)
        near = mem.remember("关于水果的哲学思考", importance=0.5)
        far = mem.remember("宇宙学的基本原理", importance=0.5)
        near.embedding = [1.0, 0.0]
        far.embedding = [0.0, 1.0]
        orig = core._ollama_embed
        core._ollama_embed = lambda text, model="nomic-embed-text", timeout=2.0: [1.0, 0.0]
        try:
            results = mem.retrieve("苹果")  # 字面与两者都不重叠，只能靠 embedding 排序
            self.assertEqual(results[0][1].id, near.id)
        finally:
            core._ollama_embed = orig

    def test_retrieve_fallback_to_simple_embed(self) -> None:
        """没有 Ollama 时，retrieve 用 _simple_embed 补全候选集 embedding 并算查询向量。"""
        from . import core

        def boom(text, model="nomic-embed-text", timeout=2.0):
            raise RuntimeError("_ollama_embed 不应被调用")

        orig = core._ollama_embed
        core._ollama_embed = boom
        try:
            mem = Memory(path=None)
            hit = mem.remember("向量检索很好用", importance=0.5)
            mem.remember("今天吃了面条", importance=0.5)
            results = mem.retrieve("向量检索")
            self.assertEqual(results[0][1].id, hit.id)  # 字面排序照常
        finally:
            core._ollama_embed = orig

    def test_embed_and_embed_all(self) -> None:
        from . import core

        orig = core._ollama_embed
        try:
            core._ollama_embed = lambda text, model="nomic-embed-text", timeout=2.0: [0.1, 0.2, 0.3]
            mem = Memory(path=None)
            m = mem.remember("一条记忆")
            self.assertTrue(mem.embed(m.id))
            self.assertEqual(m.embedding, [0.1, 0.2, 0.3])

            # _ollama_embed 返回 None → embed fallback 到 _simple_embed，仍返回 True
            core._ollama_embed = lambda text, model="nomic-embed-text", timeout=2.0: None
            m2 = mem.remember("另一条")
            self.assertTrue(mem.embed(m2.id))
            self.assertIsNotNone(m2.embedding)
            self.assertEqual(len(m2.embedding), 128)  # 128 维

            # embed_all 只算缺 embedding 的：m 已有、m2 已有 → 只有第三条
            core._ollama_embed = lambda text, model="nomic-embed-text", timeout=2.0: [0.5] * 128
            mem.remember("第三条")
            ok, fail = mem.embed_all()
            self.assertEqual(ok, 1)  # 只有第三条缺 embedding
            self.assertIsNotNone(mem.items[m2.id].embedding)
        finally:
            core._ollama_embed = orig


class StructureTest(unittest.TestCase):
    """记忆结构化：fact/opinion/experience 字段。"""

    def test_structured_fields_stored_and_loaded(self) -> None:
        mem = Memory(path=None)
        m = mem.remember("测试", fact="这是一个事实", opinion="这是我的判断", experience="这是我的经历")
        self.assertEqual(m.fact, "这是一个事实")
        self.assertEqual(m.opinion, "这是我的判断")
        self.assertEqual(m.experience, "这是我的经历")

    def test_backward_compat_without_structure(self) -> None:
        """老数据无 fact/opinion/experience → 默认 None。"""
        tmp = Path(tempfile.mkdtemp()) / "old_struct.json"
        tmp.write_text(
            json.dumps({
                "items": [{
                    "content": "老记忆", "importance": 0.5, "id": "old123",
                    "timestamp": 0.0, "last_recalled": 0.0, "recall_count": 0,
                    "consolidated": False, "state": "active", "embedding": None,
                    "source_ids": [],
                    # 没有 fact/opinion/experience
                }],
                "semantic_core": [],
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        mem = Memory(path=tmp)
        self.assertIsNone(mem.items["old123"].fact)
        self.assertIsNone(mem.items["old123"].opinion)
        self.assertIsNone(mem.items["old123"].experience)

    def test_partial_structure(self) -> None:
        """只有 fact，没有 opinion/experience。"""
        mem = Memory(path=None)
        m = mem.remember("只有事实", fact="这是一个事实")
        self.assertEqual(m.fact, "这是一个事实")
        self.assertIsNone(m.opinion)
        self.assertIsNone(m.experience)

    def test_link_and_get_linked(self) -> None:
        mem = Memory(path=None)
        a = mem.remember("记忆A")
        b = mem.remember("记忆B")
        c = mem.remember("记忆C")
        self.assertTrue(mem.link(a.id, b.id))
        self.assertIn(b.id, a.linked_ids)
        self.assertIn(a.id, b.linked_ids)
        self.assertNotIn(c.id, a.linked_ids)
        linked_a = mem.get_linked(a.id)
        self.assertEqual(len(linked_a), 1)
        self.assertEqual(linked_a[0].id, b.id)

    def test_link_invalid_ids(self) -> None:
        mem = Memory(path=None)
        a = mem.remember("记忆A")
        self.assertFalse(mem.link(a.id, "nonexistent"))

    def test_get_linked_empty(self) -> None:
        mem = Memory(path=None)
        mem.remember("记忆A")
        self.assertEqual(mem.get_linked("fake"), [])


class ThreeLayerRetrieveTest(unittest.TestCase):
    """三层检索：字面(承重) + 双链导航 + 向量化(伞)。"""

    def test_literal_layer_works(self) -> None:
        """字面层：无 embedding 时，字面检索照常工作。"""
        mem = Memory(path=None)
        hit = mem.remember("我用了三层检索机制", importance=0.5)
        miss = mem.remember("今天天气不错", importance=0.5)
        results = mem.retrieve("三层检索")
        self.assertEqual(results[0][1].id, hit.id)

    def test_link_layer_expands_results(self) -> None:
        """双链层：linked 的记忆即使字面不相关，也会作为候选加入。"""
        mem = Memory(path=None)
        query_mem = mem.remember("关于检索逻辑的设计思考", importance=0.5)
        linked_mem = mem.remember("双链关联的记忆", importance=0.5)
        mem.link(query_mem.id, linked_mem.id)
        results = mem.retrieve("检索")
        ids = [m.id for _, m in results]
        # query_mem 肯定在（字面命中）
        self.assertIn(query_mem.id, ids)
        # linked_mem 也应该在（双链扩展）
        self.assertIn(linked_mem.id, ids)

    def test_semantic_layer_reorders(self) -> None:
        """语义层：有 embedding 时，混合分重排候选集。"""
        from . import core

        mem = Memory(path=None)
        semantically_close = mem.remember("语义相近的内容", importance=0.5)
        literally_close = mem.remember("字面完全匹配检索", importance=0.5)
        # 构造：semantically_close 的 embedding 更接近查询向量
        semantically_close.embedding = [1.0, 0.0, 0.0]
        literally_close.embedding = [0.0, 1.0, 0.0]
        orig = core._ollama_embed
        core._ollama_embed = lambda text, model="nomic-embed-text", timeout=2.0: [1.0, 0.0, 0.0]
        try:
            results = mem.retrieve("语义相近的内容")
            # 字面上 literally_close 更匹配，但混合分应该让 semantically_close 排第一
            self.assertEqual(results[0][1].id, semantically_close.id)
        finally:
            core._ollama_embed = orig


class ChatPriorityTest(unittest.TestCase):
    """chat 类型记忆在 recall 中优先（同分下排在前面）。"""

    def test_chat_ranks_before_other_same_score(self) -> None:
        """同分下，chat 类型的记忆排在 text 前面。"""
        clock = FakeClock()
        tmp = Path(tempfile.mkdtemp()) / "chat_priority.json"
        mem = Memory(path=tmp, clock=clock)
        chat_m = mem.remember("一段对话内容", importance=0.5, modality="chat")
        text_m = mem.remember("一段文本内容", importance=0.5, modality="text")
        # 用 mock 确保分数完全相同：patch strength 返回固定值
        from memory import core
        orig_strength = mem.strength
        mem.strength = lambda m: 0.5  # 固定强度，确保分数相同
        try:
            results = mem.retrieve("xyzabc")
            self.assertTrue(results)
            self.assertEqual(results[0][1].id, chat_m.id)
        finally:
            mem.strength = orig_strength

    def test_sleep_automatic_consolidate_chat(self) -> None:
        """sleep 时 chat 记忆自动 consolidate，才能正常衰减。"""
        clock = FakeClock()
        tmp = Path(tempfile.mkdtemp()) / "sleep_chat.json"
        mem = Memory(path=tmp, clock=clock)
        c = mem.remember("一段对话", importance=0.3, modality="chat")
        self.assertFalse(c.consolidated)
        clock.advance(30)  # 足够久
        forgotten = mem.sleep()
        # chat 已自动 consolidate，现在可以正常衰减
        self.assertTrue(c.consolidated)
        # 如果强度已低于阈值，应该被降为 cold
        self.assertEqual(c.state, "cold")


class SleepChatConsolidationTest(unittest.TestCase):
    """sleep 自动 consolidate chat 记忆（不影响其他类型）。"""

    def test_non_chat_not_auto_consolidated(self) -> None:
        """非 chat 类型不被自动 consolidate（铁律保护）。"""
        clock = FakeClock()
        mem = Memory(path=None, clock=clock)
        t = mem.remember("普通记忆", importance=0.5, modality="text")
        clock.advance(30)
        mem.sleep()
        self.assertFalse(t.consolidated)  # 没被自动 consolidate
        self.assertEqual(t.state, "active")  # 铁律保护，不降级


if __name__ == "__main__":
    unittest.main(verbosity=2)
