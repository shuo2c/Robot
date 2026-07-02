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
    ascii_words = [w for w in re.findall(r"[a-z9]+", text) if len(w) > 1]
    cjk_chunks = re.findall(r"[一-鿿]+", text)
    bigrams = [s[i : i + 2] for s in cjk_chunks for i in range(len(s) - 1)]
    return ascii_words + bigrams


# —— 轻量 embedding：hashing trick，零依赖，可被替换 ——
EMBED_DIM = 128
_HASH_SALT = "thamus-memory-embedding"  # 第二次 hash 的盐，保证 sign 独立


def _hash_signed(token: str, salt: str, dim: int) -> tuple[int, int]:
    """对单个 token 做双 hash：bucket index + sign。"""
    h1 = hash(token + salt) % dim
    h2 = hash(token + salt + "_sign") % 2
    return h1, 1 if h2 else -1


def _simple_embed(text: str, dim: int = EMBED_DIM) -> list[float] | None:
    """Hashing-trick embedding：文本 → 定长稠密向量。

    算法：
      1. tokenize 文本
      2. 每个 token 双 hash → (bucket_index, sign)
      3. 把 sign 累加到对应 bucket
      4. L2 归一化

    零训练、零依赖、确定性（同进程内）。
    以后换成 sentence-transformers / Ollama 等，只需替换此函数，
    返回格式不变（dim 维 float 列表，L2 归一化）。
    """
    tokens = _tokens(text)
    if not tokens:
        return None
    vec = [0.0] * dim
    for t in tokens:
        idx, sign = _hash_signed(t, _HASH_SALT, dim)
        vec[idx] += sign
    # L2 归一化
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return None
    return [v / norm for v in vec]


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


def _cosine(a: list[float], b: list[float]) -> float:
    """余弦相似度（语义检索用）。维度不符或零向量返回 0。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _ollama_embed(
    text: str, model: str = "nomic-embed-text", timeout: float = 2.0
) -> list[float] | None:
    """尝试用本地 Ollama 算 embedding。失败（没装/没跑/没模型）返回 None → 退字面。

    可选层（伞）：用纯标准库 urllib 调本地 Ollama，不引入 pip 依赖。环境没有 Ollama
    时它返回 None，core.py 照样跑（字面检索承重）。模型文件不进仓库。
    """
    try:
        import json as _json
        import urllib.request

        req = urllib.request.Request(
            "http://localhost:11434/api/embeddings",
            data=_json.dumps({"model": model, "prompt": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return list(_json.loads(r.read().decode("utf-8"))["embedding"])
    except Exception:
        return None


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
    source_ids: list[str] = field(default_factory=list)  # reflection 的源链接
    # 结构化记忆：不是替换 content，是补充。content 是全文，fact/opinion/experience 是结构化摘要。
    fact: str | None = None
    opinion: str | None = None
    experience: str | None = None
    linked_ids: list[str] = field(default_factory=list)  # 双链：这条记忆链到哪些其他记忆
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
        self, content: str, importance: float = 0.5, modality: str = "text",
        fact: str | None = None, opinion: str | None = None, experience: str | None = None,
    ) -> MemoryItem:
        now = self.clock()
        m = MemoryItem(content=content, importance=importance, modality=modality,
                       fact=fact, opinion=opinion, experience=experience)
        m.timestamp = now
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

    def link(self, id1: str, id2: str) -> bool:
        """双向双链：id1 链到 id2，id2 链到 id1。"""
        m1 = self.items.get(id1)
        m2 = self.items.get(id2)
        if m1 is None or m2 is None:
            return False
        if id2 not in m1.linked_ids:
            m1.linked_ids.append(id2)
        if id1 not in m2.linked_ids:
            m2.linked_ids.append(id1)
        self._save()
        return True

    def get_linked(self, item_id: str) -> list[MemoryItem]:
        """获取一条记忆链到的所有记忆。"""
        m = self.items.get(item_id)
        if m is None:
            return []
        return [self.items[lid] for lid in m.linked_ids if lid in self.items]

    # —— 检索：三层机制协同 ——
    def retrieve(self, query: str, k: int = 5) -> list[tuple[float, MemoryItem]]:
        """三层检索：字面(承重) + 双链导航 + 向量化(伞)。

        流程：
          1. 字面检索：max(jaccard, 覆盖率) × strength → 粗筛 top-2k
          2. 双链扩展：对 top-2k 的每条，链入 linked_ids 中的 active 记忆
          3. 向量化精排：若有 embedding，对候选集重排，取 top-k

        没有 embedding 时，1+2 生效，3 跳过。

        chat 优先：在同等相关性分数下，chat 类型的记忆排在前面
        （chat 是"刚刚发生的生活"，core 是"过去的沉淀"）。
        """
        q = set(_tokens(query))

        # --- 第1层：字面粗筛 ---
        literal_candidates: list[tuple[float, MemoryItem]] = []
        for m in self.items.values():
            if m.state != "active":
                continue
            ct = set(_tokens(m.content))
            rel = max(_jaccard(q, ct), _query_coverage(q, ct))
            s = self.strength(m)
            literal_candidates.append((s * (0.1 + rel), m, rel, s))

        if not literal_candidates:
            return []

        # 取字面前 expand_factor 做候选（至少 k*2，但不能超过总数）
        expand_factor = max(2, min(2 * k, len(literal_candidates)))
        literal_candidates.sort(key=lambda x: x[0], reverse=True)
        top_literal = literal_candidates[:expand_factor]

        # --- 第2层：双链扩展 ---
        linked_candidates: list[tuple[float, MemoryItem, float, float]] = []
        linked_ids_seen: set[str] = set()
        for _, m, _, _ in top_literal:
            for lid in m.linked_ids:
                if lid in linked_ids_seen:
                    continue
                linked_ids_seen.add(lid)
                linked_m = self.items.get(lid)
                if linked_m is None or linked_m.state != "active":
                    continue
                linked_candidates.append(
                    (self.strength(linked_m) * 0.5, linked_m, 0.0, self.strength(linked_m))
                )

        # 合并：字面候选 + 双链扩展
        seen_ids: set[str] = {item[1].id for item in top_literal}
        for item in linked_candidates:
            if item[1].id not in seen_ids:
                seen_ids.add(item[1].id)
                top_literal.append(item)

        # --- 第3层：向量化精排（伞） ---
        # 先补全候选集中缺 embedding 的条目（用 _simple_embed fallback）
        for i, (score, m, literal_rel, strength_val) in enumerate(top_literal):
            if m.embedding is None:
                vec = _simple_embed(m.content)
                if vec is not None:
                    m.embedding = vec
                    self._save()
        # 重新检查是否有 embedding
        has_emb = any(m.embedding is not None for _, m, _, _ in top_literal)
        if has_emb:
            try:
                q_emb = _ollama_embed(query)
            except Exception:
                q_emb = None
            if q_emb is None:
                q_emb = _simple_embed(query)
            if q_emb is not None:
                scored_with_semantic: list[tuple[float, MemoryItem]] = []
                for score, m, literal_rel, strength_val in top_literal:
                    if m.embedding is not None:
                        semantic_rel = _cosine(q_emb, m.embedding)
                        # 混合分：字面 60% + 语义 40%
                        hybrid = 0.6 * (0.1 + literal_rel) + 0.4 * max(0, semantic_rel)
                        final = strength_val * hybrid
                    else:
                        final = score  # 没 embedding 的保持原分
                    scored_with_semantic.append((final, m))
                scored_with_semantic.sort(key=lambda x: x[0], reverse=True)
                # chat 优先：同分下，chat 类型的排在前面
                scored_with_semantic.sort(key=lambda x: (-x[0], 0 if x[1].modality == "chat" else 1))
                return scored_with_semantic[:k]

        # 没有语义层：返回字面+双链的 top-k
        top_literal.sort(key=lambda x: x[0], reverse=True)
        # chat 优先：同分下，chat 类型的排在前面
        results = [(s, m) for s, m, _, _ in top_literal[:k]]
        results.sort(key=lambda x: (-x[0], 0 if x[1].modality == "chat" else 1))
        return results

    # —— 睡眠 / 固化循环：遗忘在这里发生（固化的副产品）——
    def sleep(self) -> list[MemoryItem]:
        """铁律：没固化的，不准降级。先记住，再学会遗忘。

        特殊处理：chat 类型的记忆（对话概要）在 sleep 时自动 consolidate，
        让它们能正常衰减——对话是情景记忆，该淡就该淡，但 consolidate 后才能淡。
        """
        # 先自动 consolidate 所有未固化的 chat 记忆
        for m in self.items.values():
            if m.state == "active" and m.modality == "chat" and not m.consolidated:
                self.consolidate(m.id)

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

    # —— embedding 可选层（伞）：Ollama 优先，失败退本地 hashing trick ——
    def embed(self, item_id: str, model: str = "nomic-embed-text") -> bool:
        """给一条记忆算 embedding。先试 Ollama（质量更高），失败退本地 hashing trick。
        成功设字段返回 True。"""
        m = self.items.get(item_id)
        if m is None:
            return False
        vec = _ollama_embed(m.content, model=model)
        if vec is None:
            vec = _simple_embed(m.content)
        if vec is None:
            return False
        m.embedding = vec
        self._save()
        return True

    def embed_all(self, model: str = "nomic-embed-text") -> tuple[int, int]:
        """批量给缺 embedding 的 active 记忆算。
        先试 Ollama，失败退本地 hashing trick（不会完全失败，除非内容为空）。
        返回 (成功数, 失败数)。"""
        targets = [m for m in self.items.values() if m.state == "active" and m.embedding is None]
        if not targets:
            return 0, 0
        ok, fail = 0, 0
        for m in targets:
            if self.embed(m.id, model=model):
                ok += 1
            else:
                fail += 1
        return ok, fail

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
