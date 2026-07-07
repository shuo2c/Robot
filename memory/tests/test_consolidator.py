"""Consolidator 的测试网。

运行：
    python -m unittest memory.tests.test_consolidator -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.consolidator import Consolidator, _simple_embed
from memory.log_writer import LogWriter


class TestSimpleEmbed(unittest.TestCase):
    """hashing-trick embedding。"""

    def test_returns_128_dim_vector(self):
        vec = _simple_embed("测试文本")
        self.assertIsNotNone(vec)
        self.assertEqual(len(vec), 128)

    def test_normalization(self):
        vec = _simple_embed("测试文本")
        import math
        norm = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_empty_returns_none(self):
        self.assertIsNone(_simple_embed(""))
        self.assertIsNone(_simple_embed("   "))

    def test_deterministic(self):
        v1 = _simple_embed("hello world")
        v2 = _simple_embed("hello world")
        self.assertEqual(v1, v2)


class TestConsolidatorRun(unittest.TestCase):
    """简化流程基本功能。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_consolidate"
        self.tmp.mkdir()

    def _make_writer(self):
        class PatchedWriter(LogWriter):
            base_dir = self.tmp
        return PatchedWriter()

    def test_run_processes_records(self):
        w = self._make_writer()
        w.append("什么是记忆存储？", "记忆存储以天为单位，每个文件 3MB。")
        w.append("重要决策", "我们决定废弃 thamus.json，改用 logs 目录。")

        cons = Consolidator(w)
        count = cons.run()
        self.assertGreater(count, 0)

    def test_importance_is_integer(self):
        w = self._make_writer()
        w.append("测试评分", "这是一条测试记录")

        cons = Consolidator(w)
        cons.run()

        data = json.loads(w.get_all_files()[0].read_text(encoding="utf-8"))
        for rec in data:
            if "importance" in rec:
                self.assertIsInstance(rec["importance"], int)

    def test_embedding_has_128_dims(self):
        w = self._make_writer()
        w.append("测试向量化", "检查 embedding 维度")

        cons = Consolidator(w)
        cons.run()

        data = json.loads(w.get_all_files()[0].read_text(encoding="utf-8"))
        for rec in data:
            if "embedding" in rec and rec["embedding"]:
                self.assertEqual(len(rec["embedding"]), 128)

    def test_no_records_returns_zero(self):
        w = self._make_writer()
        # 不写入任何记录

        cons = Consolidator(w)
        count = cons.run()
        self.assertEqual(count, 0)

    def test_link_ids_are_valid(self):
        w = self._make_writer()
        w.append("关于检索的设计", "三层检索机制很重要")
        w.append("检索设计讨论", "字面和向量都很关键")

        cons = Consolidator(w)
        cons.run()

        data = json.loads(w.get_all_files()[0].read_text(encoding="utf-8"))
        ids = {r["id"] for r in data}
        for rec in data:
            for lid in rec.get("linked_ids", []):
                self.assertIn(lid, ids)


class TestNoiseFilter(unittest.TestCase):
    """噪音过滤。"""

    def test_short_text_filtered(self):
        self.assertTrue(Consolidator._is_noise("hi"))
        self.assertTrue(Consolidator._is_noise("ok"))

    def test_empty_text_filtered(self):
        self.assertTrue(Consolidator._is_noise(""))

    def test_substantive_text_kept(self):
        self.assertFalse(Consolidator._is_noise("这个 bug 是因为 X 函数的 Y 参数传错了"))
        self.assertFalse(Consolidator._is_noise("我们决定废弃 thamus.json"))

    def test_punctuation_only_filtered(self):
        self.assertTrue(Consolidator._is_noise("！！！"))


class TestRefBonus(unittest.TestCase):
    """引用加成。"""

    def test_zero_refs_no_bonus(self):
        self.assertEqual(Consolidator._ref_bonus(0), 0)

    def test_one_two_refs_plus_one(self):
        self.assertEqual(Consolidator._ref_bonus(1), 1)
        self.assertEqual(Consolidator._ref_bonus(2), 1)

    def test_three_five_refs_plus_two(self):
        self.assertEqual(Consolidator._ref_bonus(3), 2)
        self.assertEqual(Consolidator._ref_bonus(5), 2)

    def test_more_than_five_plus_three(self):
        self.assertEqual(Consolidator._ref_bonus(6), 3)
        self.assertEqual(Consolidator._ref_bonus(10), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
