---
title: 情景记忆通道
version: 0.1
date: 2026-07-06
source: genesis/memory/AI_Pure_Storage_Flow.md, genesis/memory/AI_Memory_Response_Flow.md
status: draft
---

# 情景记忆通道

## 存什么

对话历史、交互片段、个人经历。

## 写入流程

1. **结构化打包**：`{user_id, timestamp, user_input, ai_output, emotion_tag}`。
2. **重要性评分**：`importance = duration × 0.4 + urgency × 0.3 + repetition × 0.3`。
3. **写入关系存储**。

## 重要性评分细则

| 分量 | 计算方式 | 范围 |
|------|----------|------|
| 互动时长 | 对话轮数/时长归一化 | [0,1] |
| 紧急度 | 含"立刻""紧急"等关键词加权 | [0,1] |
| 重复提及 | 跨会话重复提及频率归一化 | [0,1] |

## 字段要求

| 字段 | 必填 | 说明 |
|------|------|------|
| `user_id` | 否 | 交互用户标识 |
| `user_input` | 是 | 用户原始输入 |
| `ai_output` | 是 | AI 原始回复 |
| `emotion_tag` | 否 | 情绪标签：`neutral` / `happy` / `fear` / `corrected` / ... |
| `urgency_level` | 否 | 紧急度 [0,1] |

## 生命周期

- **强度公式**：`strength = importance × recency × reinforcement`
  - `recency = exp(-dt / tau)`，`tau = TAU_BASE × (0.5 + importance)`
  - `reinforcement = 1 + log(1 + recall_count)`
- **淡化**：强度低于阈值（0.05）且已固化 → 降为 `state = "cold"`（冷状态/潜意识）。
- **铁律保护**：未 consolidate 的记忆永不降级。

## 检索方式

见 `06-retrieve.md`。
