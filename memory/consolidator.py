"""简化器：扫描→提纯→评分→建链→引用加成→向量化。

简化是原地修改：不创建新记录，直接更新已有记录的元数据字段。
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from .log_writer import LogWriter


# —— Hashing-trick embedding（零依赖，128 维） ——
EMBED_DIM = 128
_HASH_SALT = "thamus-memory-embedding"


def _hash_signed(token: str, salt: str, dim: int) -> tuple[int, int]:
    h1 = hash(token + salt) % dim
    h2 = hash(token + salt + "_sign") % 2
    return h1, 1 if h2 else -1


def _simple_embed(text: str, dim: int = EMBED_DIM) -> list[float] | None:
    if not text:
        return None
    # 朴素分词
    import re
    text_lower = text.lower()
    ascii_words = [w for w in re.findall(r"[a-z9]+", text_lower) if len(w) > 1]
    cjk_chunks = re.findall(r"[一-鿿]+", text_lower)
    bigrams = [s[i:i + 2] for s in cjk_chunks for i in range(len(s) - 1)]
    tokens = ascii_words + bigrams
    if not tokens:
        return None
    vec = [0.0] * dim
    for t in tokens:
        idx, sign = _hash_signed(t, _HASH_SALT, dim)
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return None
    return [v / norm for v in vec]


# ------------------------------------------------------------------
class Consolidator:
    """日志文件简化器。"""

    def __init__(self, log_writer: LogWriter):
        self.writer = log_writer

    def is_triggered(self) -> bool:
        """检查是否满足简化触发条件（文件满 3MB 或跨天）。"""
        if self.writer._current_file is None:
            return False
        from .log_writer import MAX_FILE_SIZE
        if self.writer._file_size(self.writer._current_file) >= MAX_FILE_SIZE:
            return True
        # 跨天检测
        today = __import__("datetime").datetime.now().strftime("%Y%m%d")
        if self.writer._current_date != today:
            return True
        return False

    def run(self, file_paths: Optional[list[Path]] = None) -> int:
        """执行简化流程。返回处理的记录数。

        如果没传 file_paths，默认处理当日所有文件。
        """
        if file_paths is None:
            file_paths = self.writer.get_today_files()

        if not file_paths:
            return 0

        # ---- 1. 扫描 ----
        all_records: list[dict] = []
        for fp in file_paths:
            if not fp.exists():
                continue
            data = json.loads(fp.read_text(encoding="utf-8"))
            all_records.extend(data)

        if not all_records:
            return 0

        # ---- 2. 提纯（原地修改） ----
        kept: list[dict] = []
        for rec in all_records:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            if self._is_noise(text):
                continue  # 丢弃
            kept.append(rec)

        # ---- 3. 评分（LLM 调用点） ----
        for rec in kept:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            rec["importance"] = self._llm_score(text)

        # ---- 4. 建链 ----
        linked_map = self._llm_build_links(kept)
        for rec in kept:
            rec["linked_ids"] = linked_map.get(rec["id"], [])

        # ---- 5. 引用加成 ----
        # 统计每条记录被多少其他记录的 linked_ids 引用
        ref_count: dict[str, int] = {}
        for rec in kept:
            rid = rec["id"]
            for lid in rec.get("linked_ids", []):
                ref_count[lid] = ref_count.get(lid, 0) + 1

        for rec in kept:
            rid = rec["id"]
            cnt = ref_count.get(rid, 0)
            bonus = self._ref_bonus(cnt)
            rec["importance"] += bonus

        # ---- 6. 向量化 ----
        for rec in kept:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            rec["embedding"] = _simple_embed(text)

        # ---- 写回文件 ----
        self._write_back(file_paths, kept)

        return len(kept)

    # ------------------------------------------------------------------
    @staticmethod
    def _is_noise(text: str) -> bool:
        """判断是否为无信息量噪音。"""
        import re
        t = text.strip().lower()
        if not t:
            return True
        # 极短且无实质内容
        if len(t) < 5:
            return True
        # 纯标点/空白
        if not re.search(r"[a-zA-Z一-鿿]", t):
            return True
        return False

    @staticmethod
    def _llm_score(text: str) -> int:
        """LLM 评分占位。

        实际实现应调用 LLM API，此处返回默认值 1。
        """
        # TODO: 接入 LLM 评分
        # 启发式：长文本、含关键词 → 高分
        length_bonus = min(len(text) // 100, 3)
        return max(1, length_bonus + 1)

    @staticmethod
    def _llm_build_links(records: list[dict]) -> dict[str, list[str]]:
        """LLM 建链占位。

        实际实现应调用 LLM 判断语义关联。
        这里用字面重叠做简单启发式。
        """
        import re
        from collections import defaultdict

        # 每条记录的分词集合
        token_sets: dict[str, set[str]] = {}
        for rec in records:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            tokens = set(re.findall(r"[a-z0-9]+|[一-鿿]+", text.lower()))
            token_sets[rec["id"]] = tokens

        # 基于 Jaccard 相似度建链（>0.3 视为有关联）
        links: dict[str, list[str]] = defaultdict(list)
        ids = list(token_sets.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                inter = len(token_sets[a] & token_sets[b])
                union = len(token_sets[a] | token_sets[b])
                if union > 0 and inter / union > 0.3:
                    links[a].append(b)
                    links[b].append(a)

        return dict(links)

    @staticmethod
    def _ref_bonus(count: int) -> int:
        """引用次数 → importance 加成。"""
        if count == 0:
            return 0
        if count <= 2:
            return 1
        if count <= 5:
            return 2
        return 3

    @staticmethod
    def _write_back(file_paths: list[Path], records: list[dict]) -> None:
        """将简化后的记录写回对应文件。"""
        # 按文件分组（根据 id 无法直接映射，简化处理：全部写回第一个文件）
        # 实际应记录每条记录的来源文件
        if not file_paths:
            return
        # 简单策略：按时间戳分配到原文件
        file_groups = [[] for _ in file_paths]
        for rec in records:
            ts = rec.get("timestamp", 0)
            # 粗略分配：按索引
            idx = min(int(ts) % len(file_groups), len(file_groups) - 1)
            file_groups[idx].append(rec)

        for fp, group in zip(file_paths, file_groups):
            if not group:
                continue
            fp.write_text(
                json.dumps(group, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
