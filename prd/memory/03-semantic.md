---
title: 提炼记忆
version: 0.2
date: 2026-07-06
status: draft
---

# 提炼记忆

## 存什么

简化后提炼出的高价值记忆，写入 `memory/thamus.json`。

格式沿用现有 thamus.json 单条 item：

```json
{
  "content": "提炼后的记忆内容",
  "importance": 0.8,
  "modality": "text",
  "timestamp": 1782662400.0,
  "last_recalled": 1782662400.0,
  "recall_count": 0,
  "consolidated": true,
  "state": "active",
  "embedding": [0.1, -0.2, ...],
  "source_ids": ["流水账文件中的消息ID"],
  "fact": "核心事实",
  "opinion": "核心观点",
  "experience": "核心经验",
  "linked_ids": ["关联的其他记忆ID"],
  "id": "消息唯一ID"
}
```

## 提炼规则

简化时 LLM 执行：

1. **筛选**：哪些流水账内容值得长期保留
2. **提炼**：把碎片化内容浓缩成连贯记忆，保留语义核心
3. **评分**：赋予 importance（0-1）
4. **向量化**：计算 embedding
5. **建链**：建立 linked_ids 关联
6. **去重**：语义相似度判断是否与已有记忆重复

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `content` | str | 精炼后的记忆内容 |
| `importance` | float | 重要性 [0,1]，简化时 LLM 判断 |
| `source_ids` | list[str] | 来源流水账消息 ID 列表 |
| `fact` | str \| null | 核心事实（如有） |
| `opinion` | str \| null | 核心观点（如有） |
| `experience` | str \| null | 核心经验（如有） |
| `linked_ids` | list[str] | 关联的其他记忆 ID |
| `embedding` | list[float] | 语义向量 |

## 不存的

- 无意义的闲聊、寒暄
- 已被提炼过的重复内容
- 与已有记忆语义高度重合的内容
