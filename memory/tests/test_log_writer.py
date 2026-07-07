"""LogWriter 的测试网。

运行：
    python -m unittest memory.tests.test_log_writer -v
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# 确保可以从项目根目录 import memory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.log_writer import LogWriter, MAX_FILE_SIZE


class TestAppend(unittest.TestCase):
    """基本写入功能。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_logs"
        self.tmp.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp.parent, ignore_errors=True)

    def _make_writer(self):
        w = LogWriter(base_dir=self.tmp)
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

    def tearDown(self):
        shutil.rmtree(self.tmp.parent, ignore_errors=True)

    def test_new_file_when_exceeds_max_size(self):
        """文件超过 3MB 时自动创建新文件。"""
        import sys
        from unittest.mock import patch

        w = LogWriter(base_dir=self.tmp)

        # Mock _file_size to simulate exceeding limit after 3 writes
        original_size = w._file_size
        call_count = [0]

        def mock_size(path):
            call_count[0] += 1
            if call_count[0] > 3:
                return MAX_FILE_SIZE + 100  # 模拟超过 3MB
            return original_size(path)

        with patch.object(w, '_file_size', mock_size):
            w.append("hello", "world")
            w.append("msg1", "reply1")
            w.append("msg2", "reply2")
            # 第 4 次写入时 _file_size 返回 > MAX_FILE_SIZE，触发新文件
            w.append("msg3_big_x" * 20, "reply3_big_y" * 20)

        all_files = w.get_all_files()
        self.assertGreaterEqual(len(all_files), 2)


class TestGetFiles(unittest.TestCase):
    """文件查询。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_getfiles"
        self.tmp.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp.parent, ignore_errors=True)

    def test_get_today_files_returns_matching(self):
        w = LogWriter(base_dir=self.tmp)
        w.append("a", "b")
        today_files = w.get_today_files()
        self.assertEqual(len(today_files), 1)

    def test_get_all_files_returns_all(self):
        w = LogWriter(base_dir=self.tmp)
        w.append("a", "b")
        w.append("c", "d")
        all_files = w.get_all_files()
        self.assertEqual(len(all_files), 1)

    def test_empty_returns_empty_list(self):
        w = LogWriter(base_dir=self.tmp)
        self.assertEqual(len(w.get_today_files()), 0)
        self.assertEqual(len(w.get_all_files()), 0)


class TestPersistence(unittest.TestCase):
    """持久化：文件可被重新加载。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "test_persist"
        self.tmp.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp.parent, ignore_errors=True)

    def test_roundtrip(self):
        w = LogWriter(base_dir=self.tmp)
        w.append("你好世界", "你好！有什么可以帮助你的？")
        w.append("测试持久化", "数据应该保存在文件中")

        # 重新打开同一目录
        w2 = LogWriter(base_dir=self.tmp)
        files = w2.get_all_files()
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(len(data), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
