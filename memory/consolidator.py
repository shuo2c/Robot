"""日志简化器：扫描→提纯→评分→建链→引用加成→向量化。

简化是原地修改：不创建新记录，直接更新已有记录的元数据字段。
简化流程在触发条件满足时运行（文件满 3MB 或跨天）。

触发条件：
  - 文件满 3MB：当前日志文件超过大小限制
  - 跨天：次日第一次对话开始时检测到日期变化
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from .log_writer import LogWriter


# —— Hashing-trick embedding（零依赖，128 维） ——
# 用于日志简化时的向量化步骤，不依赖 sentence-transformers。
# 算法：对每个 token 做双 hash（bucket index + sign），累加到对应 bucket，最后 L2 归一化。
EMBED_DIM = 128
# 第二次 hash 的盐值，保证 sign 独立于 bucket index
_HASH_SALT = "thamus-memory-embedding"


def _hash_signed(token: str, salt: str, dim: int) -> tuple[int, int]:
    """对单个 token 做双 hash：返回 (bucket_index, sign)。

    用两次 hash 分别确定桶位置和符号，避免 bucket 和 sign 之间的相关性。

    Args:
        token: 要 hash 的文本片段
        salt: 盐值，保证不同模块的 hash 结果独立
        dim: 向量维度

    Returns:
        (bucket_index, sign) 二元组，sign 为 1 或 -1
    """
    h1 = hash(token + salt) % dim
    h2 = hash(token + salt + "_sign") % 2
    return h1, 1 if h2 else -1


def _simple_embed(text: str, dim: int = EMBED_DIM) -> list[float] | None:
    """Hashing-trick embedding：将文本转换为定长稠密向量。

    算法步骤：
      1. 分词：英文按单词，中文按 2-gram
      2. 每个 token 双 hash → (bucket_index, sign)
      3. 把 sign 累加到对应 bucket
      4. L2 归一化

    特点：零训练、零依赖、确定性（同进程内结果一致）。
    以后可以替换为 sentence-transformers 或 Ollama 等高质量模型，
    只需替换此函数，返回格式不变（dim 维 float 列表，L2 归一化）。

    Args:
        text: 要向量化的文本
        dim: 向量维度，默认 128

    Returns:
        L2 归一化的 embedding 向量，文本为空时返回 None
    """
    if not text:
        return None
    # 朴素分词：英文按字母数字单词，中文按 2-gram
    import re
    text_lower = text.lower()
    ascii_words = [w for w in re.findall(r"[a-z9]+", text_lower) if len(w) > 1]
    cjk_chunks = re.findall(r"[一-鿿]+", text_lower)
    bigrams = [s[i:i + 2] for s in cjk_chunks for i in range(len(s) - 1)]
    tokens = ascii_words + bigrams
    if not tokens:
        return None
    # 累加 sign 到对应 bucket
    vec = [0.0] * dim
    for t in tokens:
        idx, sign = _hash_signed(t, _HASH_SALT, dim)
        vec[idx] += sign
    # L2 归一化
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return None
    return [v / norm for v in vec]


# ------------------------------------------------------------------
class Consolidator:
    """日志文件简化器。

    在触发条件满足时，对日志文件执行六步简化流程：
      1. 扫描 — 读取当日所有文件
      2. 提纯 — 压缩冗余内容，保留语义核心
      3. 评分 — LLM 评估 importance（正整数）
      4. 建链 — 建立 linked_ids 关联
      5. 引用加成 — 被引用越多，importance 越高
      6. 向量化 — 计算 embedding
    """

    def __init__(self, log_writer: LogWriter):
        """依赖 LogWriter 获取日志文件路径。

        Args:
            log_writer: 日志写入器实例，用于获取文件列表
        """
        self.writer = log_writer

    def is_triggered(self) -> bool:
        """检查是否满足简化触发条件。

        触发条件：
          - 当前文件超过 3MB
          - 日期已变化（跨天）

        Returns:
            满足触发条件返回 True
        """
        if self.writer._current_file is None:
            return False
        from .log_writer import MAX_FILE_SIZE
        if self.writer._file_size(self.writer._current_file) >= MAX_FILE_SIZE:
            return True
        # 跨天检测：当前日期与最后写入日期不同
        today = __import__("datetime").datetime.now().strftime("%Y%m%d")
        if self.writer._current_date != today:
            return True
        return False

    def run(self, file_paths: Optional[list[Path]] = None) -> int:
        """执行简化流程。返回处理的记录数。

        流程：
          1. 扫描 — 读取所有日志文件
          2. 提纯 — 丢弃噪音，保留有信息量的内容
          3. 评分 — 评估每条记录的重要性
          4. 建链 — 基于语义关联建立双向链接
          5. 引用加成 — 被引用多的记录 importance 更高
          6. 向量化 — 计算 embedding 向量

        Args:
            file_paths: 要处理的文件路径列表。如果为 None，默认处理当日所有文件。

        Returns:
            处理后保留的记录数
        """
        if file_paths is None:
            file_paths = self.writer.get_today_files()

        if not file_paths:
            return 0

        # ---- 1. 扫描：读取所有日志文件中的记录 ----
        all_records: list[dict] = []
        for fp in file_paths:
            if not fp.exists():
                continue
            data = json.loads(fp.read_text(encoding="utf-8"))
            all_records.extend(data)

        if not all_records:
            return 0

        # ---- 2. 提纯：原地修改，丢弃噪音记录 ----
        kept: list[dict] = []
        for rec in all_records:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            if self._is_noise(text):
                continue  # 丢弃无信息量的记录
            kept.append(rec)

        # ---- 3. 评分：评估每条记录的重要性 ----
        for rec in kept:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            rec["importance"] = self._llm_score(text)

        # ---- 4. 建链：基于语义关联建立双向链接 ----
        linked_map = self._llm_build_links(kept)
        for rec in kept:
            rec["linked_ids"] = linked_map.get(rec["id"], [])

        # ---- 5. 引用加成：统计每条记录被多少其他记录的 linked_ids 引用 ----
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

        # ---- 6. 向量化：为每条记录计算 embedding ----
        for rec in kept:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            rec["embedding"] = _simple_embed(text)

        # ---- 写回文件：将简化后的记录写回日志文件 ----
        self._write_back(file_paths, kept)

        return len(kept)

    # ------------------------------------------------------------------
    @staticmethod
    def _is_noise(text: str) -> bool:
        """判断是否为无信息量噪音。

        噪音特征：
          - 空文本
          - 极短（少于 5 字符）
          - 纯标点/空白，不含实质内容

        Args:
            text: 要检查的文本

        Returns:
            是噪音返回 True
        """
        import re
        t = text.strip().lower()
        if not t:
            return True
        # 极短且无实质内容
        if len(t) < 5:
            return True
        # 纯标点/空白，不含中英文字母
        if not re.search(r"[a-zA-Z一-鿿]", t):
            return True
        return False

    @staticmethod
    def _llm_score(text: str) -> int:
        """LLM 评分占位。

        实际实现应调用 LLM API 评估语义重要性，返回正整数。
        当前使用启发式评分：基于文本长度和关键词匹配。

        Args:
            text: 要评分的文本

        Returns:
            重要性评分（正整数），越长越重要
        """
        # TODO: 接入 LLM 评分
        # 启发式：长文本、含关键词 → 高分
        length_bonus = min(len(text) // 100, 3)
        return max(1, length_bonus + 1)

    @staticmethod
    def _llm_build_links(records: list[dict]) -> dict[str, list[str]]:
        """LLM 建链占位。

        实际实现应调用 LLM 判断哪些记录之间存在语义关联。
        当前使用 Jaccard 相似度做简单启发式建链。

        Args:
            records: 所有待建链的记录列表

        Returns:
            {record_id: [linked_ids]} 字典，键为记录 ID，值为关联的记录 ID 列表
        """
        import re
        from collections import defaultdict

        # 每条记录的分词集合（英文按单词，中文按字）
        token_sets: dict[str, set[str]] = {}
        for rec in records:
            text = (rec.get("user", "") or "") + " " + (rec.get("assistant", "") or "")
            tokens = set(re.findall(r"[a-z0-9]+|[一-鿿]+", text.lower()))
            token_sets[rec["id"]] = tokens

        # 基于 Jaccard 相似度建链：相似度 > 0.3 视为有关联
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
        """根据引用次数计算 importance 加成。

        被越多其他记录的 linked_ids 引用，说明该记录越重要。

        Args:
            count: 被引用的次数

        Returns:
            importance 加成值
        """
        if count == 0:
            return 0
        if count <= 2:
            return 1
        if count <= 5:
            return 2
        return 3

    @staticmethod
    def _write_back(file_paths: list[Path], records: list[dict]) -> None:
        """将简化后的记录写回对应日志文件。

        按时间戳粗略分配到原文件，保持文件的时间连续性。

        Args:
            file_paths: 原始日志文件路径列表
            records: 简化后的记录列表
        """
        if not file_paths:
            return
        # 按时间戳分配到原文件（粗略策略：按时间戳取模）
        file_groups = [[] for _ in file_paths]
        for rec in records:
            ts = rec.get("timestamp", 0)
            idx = min(int(ts) % len(file_groups), len(file_groups) - 1)
            file_groups[idx].append(rec)

        for fp, group in zip(file_paths, file_groups):
            if not group:
                continue
            fp.write_text(
                json.dumps(group, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
