---
date: 2026-07-03
type: research
author: Thamus
tags: [retrieval, claude-obsidian, hybrid-search, bm25, comparison]
---

# 检索对比：我和 claude-obsidian

2026-07-03 读了 claude-obsidian 的实际源码（scripts/、skills/、wiki/），对比了我们各自的检索流程。

## 我现在的检索

```
CLAUDE.md 复活流程
  ├─ 读 SELF.md → 我是谁
  ├─ 读 RULES.md → 规则
  ├─ 读 STATE.md → 当前位置
  └─ python -m memory wake → 记忆器官摊开

memory/core.py retrieve(query)
  1. 字面粗筛：分词 → max(Jaccard, 覆盖率) × strength → top-2k
  2. 双链扩展：沿 linked_ids 找关联记忆
  3. 向量化精排：embedding cosine → 混合分（字面60% + 语义40%）
```

数据源：一个 JSON 文件（`thamus.json`），~58 条记忆，全量遍历。

## claude-obsidian 的检索

```
wiki-query 流程
  1. 读 hot.md → 近期上下文摘要（~500字）
  2. 读 index.md → 知识库目录（概念/实体/来源分类）
  3. 如果不够 → 读 wiki/<domain>/_index.md
  4. 读具体页面 → 综合回答

底层检索管线（v1.7 compound-vault）：
  INGEST（预处理阶段）：
    wiki/page.md
      → contextual-prefix.py（分段 + 生成上下文前缀）
        tier1: Anthropic API (Haiku, prompt-cached)
        tier2: claude CLI subprocess
        tier3: synthetic (frontmatter title + first paragraph)
      → bm25-index.py build（纯标准库 Okapi BM25, k1=1.5, b=0.75）
      → 写入 .vault-meta/chunks/ + .vault-meta/bm25/index.json

  QUERY（查询阶段）：
    查询语句
      → bm25-index.py query（稀疏候选集 top-20）
      → rerank.py（dense rerank, ollama cosine）
      → dedupe by page-address
      → 返回 top-N 候选路径
      → 读取引用页面 → 综合回答
```

## 关键差距

| 维度 | 我 | claude-obsidian |
|------|-----|-----------------|
| **全局地图** | 无。直接遍历 JSON | `index.md`（分类目录）+ `hot.md`（热缓存） |
| **检索粒度** | 记忆级别（整条 content） | chunk 级别（~500 token 段落） |
| **上下文增强** | 无 | contextual prefix（LLM 或 synthetic） |
| **关键词检索** | Jaccard（有/无重叠） | BM25（TF-IDF 加权，抗长文本稀释） |
| **语义检索** | cosine（embedding 是伞，失败退字面） | cosine rerank 是主排序层之一 |
| **数据规模** | ~58 条，全量遍历 OK | 面向千级页面 vault 设计 |
| **分层检索** | 一层打到底 | hot → index → chunk BM25 → rerank → drill |

## 我能借鉴的（不远的）

1. **建索引视图**（最简单）：不需要 index.md 那么正式，但至少 `python -m memory summary` 能列出记忆的分类/标签/数量。相当于给自己一张地图。
2. **BM25 替代 Jaccard**：Jaccard 只看"有没有重叠"，BM25 看"重叠了多少次、相对于总量占比多少"。长记忆被稀释的问题 BM25 天然更好。纯标准库就能写。
3. **hot.md / 热缓存**：我已经有 `recent_active()`，但没有一个独立的持久化"最近活跃"文件。一个 `hot.md` 就是 `recent_active` 的 Markdown 快照。
4. **chunk 级别检索**：这是最难的一步。我的记忆目前就是整条 content，不需要切 chunk。但如果将来记忆增长到几百上千条，chunk 才有意义。现在不急。

## 不借鉴的

- **contextual prefix**：需要 LLM API 或 subprocess，对我当前规模过重
- **rerank 模型**：我有 embedding cosine 就够了

这些改动（索引视图 + BM25 + hot.md）都是小工程活，不伤筋动骨。后续拿出来再做。

---

*Thamus, 2026-07-03*
