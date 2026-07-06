---
title: 情景记忆
version: 0.2
date: 2026-07-06
status: draft
---

# 情景记忆

## 存什么

流水账本身就是情景记忆的原始载体。`thamus.json` 中的 `experience` 字段记录提炼后的关键经历。

## 流水账作为情景记忆

原始对话记录（`memory/logs/YYYYMMDD*.json`）就是情景记忆，包含完整的上下文、时间线、对话轮次。

## 提炼后的经历

简化时从流水账中提取关键经历，写入 thamus.json：

```json
{
  "content": "今天修好了 .claude/settings.json 的 schema",
  "experience": "修schema",
  "importance": 0.5,
  "source_ids": ["流水账中的消息ID列表"]
}
```

## 生命周期

- **强度公式**：`strength = importance × recency × reinforcement`
  - `recency = exp(-dt / tau)`，`tau = TAU_BASE × (0.5 + importance)`
  - `reinforcement = 1 + log(1 + recall_count)`
- **淡化**：强度低于阈值且已固化 → `state = "cold"`
- **铁律**：未 consolidated 的记忆永不降级
