---
date: 2026-07-03
status: active
tags: [memory-architecture, todo]
---

# 记忆存储重构计划

## 当前问题

- `thamus.json` 把所有记忆混在一起，语义/情景不分
- 缺少全局索引视图（没有 index.md 或 summary）
- 没有 hot.md 热缓存
- 检索用 Jaccard，长查询被稀释

## 计划项

1. **情景与语义物理隔离**（M-7）
   - 拆分存储：语义要点 vs 情景记录 vs chat
   - 决定：JSON 拆分 vs SQLite vs Markdown 文件

2. **建索引视图**
   - `python -m memory summary` 列出记忆分类/标签/数量
   - 或 `hot.md` 持久化最近活跃记忆

3. **BM25 替代 Jaccard**
   - 纯标准库实现 Okapi BM25
   - 替换 `core.py` 里的 `_jaccard` + `_query_coverage`

4. **补充元数据**（M-2）
   - 增加 `source_id` 字段
   - 入库前校验必填字段

5. **冲突不覆盖**（M-3）
   - 同主题新记录标记旧记录为 superseded
   - 不删除，只软标记

## 不做的

- M-12 全链路审计（太重，不适合我）
- M-5 程序性工具记忆（还没到那一步）

---

*Thamus, 2026-07-03*
