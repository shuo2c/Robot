---
title: 核心铁律与审计
version: 0.1
date: 2026-07-06
source: genesis/memory/AI_Memory_Response_Flow.md, genesis/memory/AI_Pure_Storage_Flow.md
status: draft
---

# 核心铁律与审计

## 铁律

| 编号 | 铁律 | 说明 |
|------|------|------|
| **F-1** | 没固化不准忘 | 未 consolidate 的记忆永不降级到 cold |
| **F-2** | 软删除 | 记忆只降状态（active → cold），不硬删除 |
| **F-3** | 元数据 100% 完整 | 任何写入必须带 source_id、timestamp、embedding_model_version |
| **F-4** | 冲突禁止覆盖 | 发现新版本只标记旧版 deprecated，不删除 |
| **F-5** | 情景与语义物理隔离 | 不同记忆类型分属不同存储，严禁混合检索 |
| **F-6** | 提取即再巩固 | 每次召回时记录提取次数，>5 次后优先级自动提升 |
| **F-7** | 工具记忆只增不减 | 程序性记忆中的工具记录只追加不修改 |
| **F-8** | 全链路审计 | 所有写入、修改、提取操作生成结构化日志 |

## 审计日志

所有写入、修改、提取操作生成结构化日志，追加写到 `memory/audit.jsonl`。

### 日志格式

| 字段 | 类型 | 说明 |
|------|------|------|
| `operation` | str | `write` / `update` / `recall` / `consolidate` / `forget` / `conflict` |
| `item_id` | str | 操作的记忆 ID |
| `timestamp` | float | 操作时间 |
| `detail` | dict | 操作详情（JSON） |

### 留存策略

永久。
