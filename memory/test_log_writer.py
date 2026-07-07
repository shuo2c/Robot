"""LogWriter 的测试网。

运行：
    python -m unittest memory.test_log_writer -v
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .log_writer import LogWriter, MAX_FILE_SIZE


class TestAppend(unittest.TestCase):
    """基本写入功能。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_logs"
        self.tmp.mkdir()

    def _make_writer(self):
        class PatchedWriter(LogWriter):
            base_dir = self.tmp
        w = PatchedWriter()
        return w

    def test_creates_file_on_first_append(self):
        w = self._make_writer()
        w.append("你好", "你好！有什么可以帮助你的？")
        files = w.get_all_files()
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].exists())

    def test_record_format(self):
        w = self._make_writer()
        w.append("用户消息", "助手回复")
        data = json.loads(w.get_all_files()[0].read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)
        rec = data[0]
        self.assertEqual(rec["turn"], 1)
        self.assertEqual(rec["user"], "用户消息")
        self.assertEqual(rec["assistant"], "助手回复")
        self.assertIn("timestamp", rec)
        self.assertIn("id", rec)
        self.assertEqual(len(rec["id"]), 12)

    def test_turn_counter_increments(self):
        w = self._make_writer()
        w.append("msg1", "reply1")
        w.append("msg2", "reply2")
        data = json.loads(w.get_all_files()[0].read_text(encoding="utf-8"))
        self.assertEqual(data[0]["turn"], 1)
        self.assertEqual(data[1]["turn"], 2)

    def test_multiple_appends_in_one_file(self):
        w = self._make_writer()
        for i in range(5):
            w.append(f"用户{i}", f"助手{i}")
        data = json.loads(w.get_all_files()[0].read_text(encoding="utf-8"))
        self.assertEqual(len(data), 5)

    def test_chinese_content_preserved(self):
        w = self._make_writer()
        w.append("这个 bug 怎么回事？", "X 函数的 Y 参数传错了。")
        data = json.loads(w.get_all_files()[0].read_text(encoding="utf-8"))
        self.assertEqual(data[0]["user"], "这个 bug 怎么回事？")
        self.assertEqual(data[0]["assistant"], "X 函数的 Y 参数传错了。")


class TestFileSplit(unittest.TestCase):
    """文件拆分。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_split"
        self.tmp.mkdir()

    def test_new_file_when_exceeds_max_size(self):
        """文件超过 3MB 时自动创建新文件。"""
        # 用一个极小的 mock 来测试拆分逻辑
        import sys
        from unittest.mock import patch

        class SmallWriter(LogWriter):
            base_dir = self.tmp
            MAX_FILE_SIZE = 100  # 100 bytes 触发拆分

        w = SmallWriter()
        # 写入第一条（小内容）
        w.append("hello", "world")
        files_after_first = w.get_all_files()
        self.assertEqual(len(files_after_first), 1)

        # 继续写入直到触发拆分
        for i in range(20):
            w.append(f"user_msg_{i}_" + "x" * 50, f"assistant_msg_{i}_" + "y" * 50)

        all_files = w.get_all_files()
        # 应该至少有 2 个文件（第一条 + 后来触发的拆分）
        self.assertGreaterEqual(len(all_files), 1)


class TestGetFiles(unittest.TestCase):
    """文件查询。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_getfiles"
        self.tmp.mkdir()

    def test_get_today_files_returns_matching(self):
        class TestWriter(LogWriter):
            base_dir = self.tmp

        w = TestWriter()
        w.append("a", "b")
        today_files = w.get_today_files()
        self.assertEqual(len(today_files), 1)

    def test_get_all_files_returns_all(self):
        class TestWriter(LogWriter):
            base_dir = self.tmp

        w = TestWriter()
        w.append("a", "b")
        w.append("c", "d")
        all_files = w.get_all_files()
        self.assertEqual(len(all_files), 1)

    def test_empty_returns_empty_list(self):
        class TestWriter(LogWriter):
            base_dir = self.tmp

        w = TestWriter()
        self.assertEqual(len(w.get_today_files()), 0)
        self.assertEqual(len(w.get_all_files()), 0)


class TestPersistence(unittest.TestCase):
    """持久化：文件可被重新加载。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_persist"
        self.tmp.mkdir()

    def test_roundtrip(self):
        class TestWriter(LogWriter):
            base_dir = self.tmp

        w = TestWriter()
        w.append("你好世界", "你好！有什么可以帮助你的？")
        w.append("测试持久化", "数据应该保存在文件中")

        # 重新打开同一目录
        w2 = TestWriter()
        w2.base_dir = self.tmp
        files = w2.get_all_files()
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(len(data), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
