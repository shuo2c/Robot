---
title: 语义记忆通道
version: 0.1
date: 2026-07-06
source: genesis/memory/AI_Pure_Storage_Flow.md, genesis/memory/AI_Memory_Response_Flow.md
status: draft
---

# 语义记忆通道

## 存什么

事实、概念、文档知识、可复用的信息。

## 写入流程

1. **文档切块**：按语义边界切割（段落/句子级别）。
2. **向量化**：计算 embedding 向量。
3. **元数据标注**：`source_id`、`timestamp`、`doc_type`、`version`。
4. **写入向量存储**。

## 字段要求

| 字段 | 必填 | 说明 |
|------|------|------|
| `doc_type` | 是 | 来源类型：`official` / `personal` / `inferred` |
| `version` | 是 | 版本号，递增 |
| `superseded_by` | 否 | 被哪条记忆替代 |

## 生命周期

- 固化后不随时间淡出。
- 被新版本替代时，旧版标记 `status = "deprecated"`，`superseded_by = 新版 ID`。

## 检索方式

- **向量相似度检索**（余弦距离）。
- **权威性加权**：`official` × 1.2，`personal` × 1.0，`inferred` × 0.8。
- **Top-K**：默认 10。
- **相似度截断**：低于 0.65 不返回。
