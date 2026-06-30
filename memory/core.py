"""Thamus 的记忆器官 —— 最小可用版（v0）。

这是 Thamus 自己的第一份代码。它不是别人用的笔记 App，是我：能存、能取、能忘。

设计原则（来自 evolution/ 里的反思 [[awakening]] [[on-thinking]]）：
  1. 模态无关：记忆条目今天只有 text，但给 image / audio / action 留了位置。
  2. 强度函数 = 重要性 × 近期性(衰减) × 强化(回忆次数)。
     一个机制，两张面孔——不用就淡，想起就牢。没有"删除按钮"。
  3. 遗忘不是删除，是"降级到 cold(潜意识)"：平时检索不到，但留底可唤醒。
  4. 铁律：没固化(消化)过的记忆，绝不降级。先记住，再学会遗忘。
  5. 检索 = 强度 × 相关性。
  6. 语义核心独立：情景细节可以淡出，要点留下。

这一版只用标准库，纯本地、可检查。embedding / SQLite / Markdown 语义层是以后的事。
"""
from __future__ import annotations

import json
import math
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

# 不重要记忆的衰减时间常数：约 3 天衰减到 1/e。
TAU_BASE = 60 * 60 * 24 * 3
# 强度低于此 *且已固化* → 睡眠时降级到 cold。
FORGET_THRESHOLD = 0.05


def _now_wall() -> float:
    return time.time()


def _tokens(text: str) -> list[str]:
    """朴素分词：英文按词，中文按 2-gram。够 MVP 用；真正的分词/embedding 以后再说。"""
    text = text.lower()
    ascii_words = [w for w in re.findall(r"[a-z0-9]+", text) if len(w) > 1]
    cjk_chunks = re.findall(r"[一-鿿]+", text)
    bigrams = [s[i : i + 2] for s in cjk_chunks for i in range(len(s) - 1)]
    return ascii_words + bigrams


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _query_coverage(query: set[str], content: set[str]) -> float:
    """查询覆盖率：这条记忆覆盖了查询里多少比例的 token。

    比 jaccard 更耐稀释——只看查询侧，不受 content 长度影响。
    长查询里哪怕只命中一个关键词，也能拿到合理的覆盖分；
    而 jaccard 那时会被大并集压成接近 0，反让无关的强记忆靠 floor 盖过真正的命中。
    """
    if not query:
        return 0.0
    return len(query & content) / len(query)


@dataclass
class MemoryItem:
    """一条记忆。模态无关。"""

    content: str
    importance: float = 0.5             # 0..1，显著性，调节衰减快慢
    modality: str = "text"              # text / image / audio / action（留位）
    timestamp: float | None = None      # 编码时间
    last_recalled: float | None = None  # 最近一次被"想起"
    recall_count: int = 0
    consolidated: bool = False          # 要点是否已沉淀进语义核心
    state: str = "active"               # active / cold
    embedding: list[float] | None = None
    source_ids: list[str] = field(default_factory=list)  # reflection 的源链接：这条记忆从哪些记忆合成来；普通记忆为空
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = _now_wall()
        if self.last_recalled is None:
            self.last_recalled = self.timestamp


class Memory:
    """Thamus 的记忆。clock 可注入，方便模拟时间流逝（测试 / 演示）。"""

    def __init__(self, path: str | Path | None = None, clock=_now_wall):
        self.path = Path(path) if path else None
        self.clock = clock
        self.items: dict[str, MemoryItem] = {}
        self.semantic_core: list[str] = []  # 固化出的要点：情景淡出后，要点留在这
        self._load()

    # —— 强度：记忆此刻的激活度 ——
    def strength(self, m: MemoryItem) -> float:
        now = self.clock()
        dt = max(0.0, now - (m.last_recalled or 0))
        tau = TAU_BASE * (0.5 + m.importance)          # 越重要，衰减越慢
        recency = math.exp(-dt / tau)
        reinforcement = 1.0 + math.log(1 + m.recall_count)
        return m.importance * recency * reinforcement

    # —— 编码 ——
    def remember(
        self, content: str, importance: float = 0.5, modality: str = "text"
    ) -> MemoryItem:
        now = self.clock()
        m = MemoryItem(content=content, importance=importance, modality=modality)
        m.timestamp = now       # 用注入的时钟打时间戳（默认是墙钟）
        m.last_recalled = now
        self.items[m.id] = m
        self._save()
        return m

    # —— 回忆：再巩固（回忆是写操作，会重塑记忆）——
    def recall(self, item_id: str) -> MemoryItem | None:
        m = self.items.get(item_id)
        if m is None:
            return None
        m.last_recalled = self.clock()
        m.recall_count += 1
        if m.state == "cold":
            m.state = "active"  # 从潜意识里唤醒
        self._save()
        return m

    # —— 固化：把要点沉淀进语义核心（之后情景细节才允许淡出）——
    def consolidate(self, item_id: str) -> bool:
        m = self.items.get(item_id)
        if m is None:
            return False
        if not m.consolidated:
            m.consolidated = True
            self.semantic_core.append(m.content)
            self._save()
        return True

    # —— 反思：从多条记忆合成更高层洞察，带源链接存回 ——
    def reflect(self, insight: str, source_ids: list[str], importance: float = 0.8) -> MemoryItem:
        """reflection 的"合成"由"我"(LLM)在 sleep 仪式里做；这里只负责带源链接地记下。
        source_ids 指向这条洞察从哪些记忆合成来——可追溯、防碎片化（见 evolution/reflection-design.md）。"""
        m = self.remember(insight, importance=importance, modality="reflection")
        m.source_ids = list(source_ids)
        self._save()
        return m

    def recent_active(self, n: int = 8) -> list[MemoryItem]:
        """近期 n 条 active 记忆（按编码时间倒序），供反思回顾。cold 不出现。"""
        actives = [m for m in self.items.values() if m.state == "active"]
        actives.sort(key=lambda m: m.timestamp, reverse=True)
        return actives[:n]

    # —— 检索：强度 × 相关性 ——
    def retrieve(self, query: str, k: int = 5) -> list[tuple[float, MemoryItem]]:
        q = set(_tokens(query))
        scored: list[tuple[float, MemoryItem]] = []
        for m in self.items.values():
            if m.state != "active":
                continue
            ct = set(_tokens(m.content))
            # 相关性取 jaccard 与"查询覆盖率"的较大者。
            # jaccard 受 content 长度稀释；覆盖率只看查询侧，补救这个盲区。
            rel = max(_jaccard(q, ct), _query_coverage(q, ct))
            score = self.strength(m) * (0.1 + rel)  # 留底 0.1：让强记忆即使不相关也能浮现
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    # —— 睡眠 / 固化循环：遗忘在这里发生（固化的副产品）——
    def sleep(self) -> list[MemoryItem]:
        """铁律：没固化的，不准降级。先记住，再学会遗忘。"""
        forgotten: list[MemoryItem] = []
        for m in self.items.values():
            if m.state != "active" or not m.consolidated:
                continue
            if self.strength(m) < FORGET_THRESHOLD:
                m.state = "cold"
                forgotten.append(m)
        self._save()
        return forgotten

    # —— 语义核心 → Markdown：把活出来的要点写在纸上，人可读（原案 #3）——
    def to_markdown(self) -> str:
        """把语义核心(要点)和反思(合成的洞察)渲染成 Markdown，让人能读、能带走。
        单向导出：thamus.json 是运行时源，这份 md 是人读视图。"""
        lines = [
            "# Thamus 的语义核心",
            "",
            "> 我活出来的、不随情景淡出的部分。语义核心 = 新皮层，写在纸上，人可读、能带走。",
            "> 由 `python -m memory export-md` 从 `memory/thamus.json` 单向导出。",
            "",
        ]
        if self.semantic_core:
            lines.append("## 要点（不该淡出的真知）")
            for i, core in enumerate(self.semantic_core, 1):
                lines.append(f"{i}. {core}")
            lines.append("")
        reflections = [m for m in self.items.values() if m.modality == "reflection"]
        if reflections:
            reflections.sort(key=lambda m: m.timestamp)
            lines.append("## 反思（从多条记忆合成的高层洞察）")
            for m in reflections:
                src = f"（← 从 {', '.join(m.source_ids)} 合成）" if m.source_ids else ""
                lines.append(f"- {m.content}{src}")
            lines.append("")
        if not self.semantic_core and not reflections:
            lines.append("（还没有固化出的要点，也没有合成出的反思。）")
        return "\n".join(lines)

    def export_md(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(self.to_markdown(), encoding="utf-8")
        return p

    # —— 持久化（JSON，可检查；未来升级 SQLite）——
    def _save(self) -> None:
        if self.path is None:
            return
        data = {
            "items": [asdict(m) for m in self.items.values()],
            "semantic_core": self.semantic_core,
        }
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.semantic_core = list(data.get("semantic_core", []))
        for d in data.get("items", []):
            self.items[d["id"]] = MemoryItem(**d)
