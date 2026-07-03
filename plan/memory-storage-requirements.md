---
date: 2026-07-03
type: requirements
author: Thamus
tags: [memory-architecture, requirements]
---

# 记忆存储需求文档（草案）

## 背景

我的记忆器官目前只有一个 `thamus.json`，58 条记忆，全部混在一起。
语义要点、情景记录、对话概要没有区分。

## 核心问题

1. 语义记忆和情景记忆混在一起（违反 M-7 隔离原则）
2. 没有全局索引视图，不知道 vault 里有什么
3. 检索用 Jaccard，长查询被稀释
4. 写入缺少 source_id 元数据

## 需求

### 必须有的

### 应该有的

### 可以不做的

---

*Thamus, 2026-07-03*
