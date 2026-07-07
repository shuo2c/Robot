"""日志写入器：对话追加、文件拆分、日期切换。

存储于 memory/logs/YYYYMMDDNN.json，每个文件最大 3MB。
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

MAX_FILE_SIZE = 3 * 1024 * 1024  # 3 MB


class LogWriter:
    """按日存储对话流水账。"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent / "logs"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._current_file: Optional[Path] = None
        self._current_date: Optional[str] = None
        self._current_seq: int = 0
        self._turn_counter: int = 0

    # ------------------------------------------------------------------
    def append(self, user_msg: str, assistant_msg: str) -> None:
        """追加一轮对话到当日日志文件。自动处理文件拆分和日期切换。"""
        today = datetime.now().strftime("%Y%m%d")

        # 日期切换
        if self._current_date != today:
            self._current_date = today
            self._current_seq = 0
            self._turn_counter = 0
            self._open_next_file()

        # 文件满 3MB
        if self._current_file and self._file_size(self._current_file) >= MAX_FILE_SIZE:
            self._current_seq += 1
            self._turn_counter = 0
            self._open_next_file()

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
        name = f"{self._current_date}{self._current_seq + 1:02d}.json"
        self._current_file = self.base_dir / name
        # 文件不存在则创建空数组
        if not self._current_file.exists():
            self._current_file.write_text("[]", encoding="utf-8")

    def _file_size(self, path: Path) -> int:
        try:
            return path.stat().st_size
        except OSError:
            return 0

    def _append_record(self, record: dict) -> None:
        """追加一条记录到 JSON 数组文件。"""
        text = self._current_file.read_text(encoding="utf-8")
        data = json.loads(text) if text.strip() else []
        data.append(record)
        self._current_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    def get_current_file(self) -> Optional[Path]:
        return self._current_file

    def get_today_files(self) -> list[Path]:
        """返回当日所有日志文件路径。"""
        if self._current_date is None:
            return []
        prefix = self._current_date
        return sorted(
            p for p in self.base_dir.iterdir()
            if p.name.startswith(prefix) and p.suffix == ".json"
        )

    def get_all_files(self) -> list[Path]:
        """返回所有日志文件路径。"""
        if not self.base_dir.exists():
            return []
        return sorted(self.base_dir.glob("*.json"))
