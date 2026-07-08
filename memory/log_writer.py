"""日志写入器：对话追加、文件拆分、日期切换。

将每轮对话（用户消息 + 助手回复）打包为一条记录，追加到当日日志文件。
文件按日拆分，单文件最大 3MB，超出后自动创建新文件（序号递增）。

存储路径：memory/logs/YYYYMMDDNN.json
  - YYYYMMDD：日期
  - NN：当日文件序号，从 01 开始
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# 单个日志文件的最大大小：3 MB
MAX_FILE_SIZE = 3 * 1024 * 1024


class LogWriter:
    """按日存储对话流水账的写入器。

    职责：
      1. 追加对话记录到当日日志文件
      2. 检测文件是否超过 3MB，超过则创建新文件
      3. 检测日期是否变化，变化则切换到新日期文件
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """初始化日志写入器。

        Args:
            base_dir: 日志文件存放目录，默认为 memory/logs/
        """
        self.base_dir = base_dir or Path(__file__).parent / "logs"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # 当前正在写入的文件路径
        self._current_file: Optional[Path] = None
        # 当前写入的日期
        self._current_date: Optional[str] = None
        # 当日文件序号（用于满 3MB 后创建新文件）
        self._current_seq: int = 0
        # 当日对话轮次计数器
        self._turn_counter: int = 0

    # ------------------------------------------------------------------
    def append(self, user_msg: str, assistant_msg: str) -> None:
        """追加一轮对话到当日日志文件。

        自动处理文件拆分和日期切换：
          - 日期变化 → 打开新日期文件，重置 turn 序号
          - 文件满 3MB → 序号 +1，打开新文件

        Args:
            user_msg: 用户发送的消息内容
            assistant_msg: 助手的回复内容
        """
        today = datetime.now().strftime("%Y%m%d")

        # 日期切换：如果当前日期与记录日期不同，打开新文件
        if self._current_date != today:
            self._current_date = today
            self._current_seq = 0
            self._turn_counter = 0
            self._open_next_file()

        # 文件容量检查：超过 3MB 时创建新文件
        if self._current_file and self._file_size(self._current_file) >= MAX_FILE_SIZE:
            self._current_seq += 1
            self._turn_counter = 0
            self._open_next_file()

        # 构建对话记录，包含唯一 ID 和时间戳
        record = {
            "turn": self._turn_counter + 1,
            "user": user_msg,
            "assistant": assistant_msg,
            "timestamp": __import__("time").time(),
            "id": uuid.uuid4().hex[:12],
        }

        self._append_record(record)
        self._turn_counter += 1

    # ------------------------------------------------------------------
    def _open_next_file(self) -> None:
        """打开下一个日志文件。

        文件命名格式：YYYYMMDDNN.json
        如果文件不存在则创建空数组作为初始内容。
        """
        name = f"{self._current_date}{self._current_seq + 1:02d}.json"
        self._current_file = self.base_dir / name
        # 新文件不存在时初始化为空数组
        if not self._current_file.exists():
            self._current_file.write_text("[]", encoding="utf-8")

    def _file_size(self, path: Path) -> int:
        """获取文件的大小（字节）。

        Args:
            path: 文件路径

        Returns:
            文件大小（字节），文件不存在或出错时返回 0
        """
        try:
            return path.stat().st_size
        except OSError:
            return 0

    def _append_record(self, record: dict) -> None:
        """追加一条记录到 JSON 数组文件中。

        读取现有文件内容 → 追加记录 → 写回文件。
        使用 indent=2 格式化 JSON，ensure_ascii=False 保留中文。

        Args:
            record: 要追加的对话记录字典
        """
        text = self._current_file.read_text(encoding="utf-8")
        data = json.loads(text) if text.strip() else []
        data.append(record)
        self._current_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    def get_current_file(self) -> Optional[Path]:
        """返回当前正在写入的日志文件路径。

        Returns:
            当前文件路径，尚未写入任何文件时返回 None
        """
        return self._current_file

    def get_today_files(self) -> list[Path]:
        """返回当日所有日志文件路径。

        按文件名排序，确保按写入顺序遍历。

        Returns:
            当日日志文件路径列表
        """
        if self._current_date is None:
            return []
        prefix = self._current_date
        return sorted(
            p for p in self.base_dir.iterdir()
            if p.name.startswith(prefix) and p.suffix == ".json"
        )

    def get_all_files(self) -> list[Path]:
        """返回所有日志文件路径（所有日期）。

        Returns:
            按文件名排序的所有日志文件路径列表
        """
        if not self.base_dir.exists():
            return []
        return sorted(self.base_dir.glob("*.json"))
