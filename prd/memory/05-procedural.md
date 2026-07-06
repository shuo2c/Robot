---
title: 程序性记忆通道
version: 0.1
date: 2026-07-06
source: genesis/memory/AI_Pure_Storage_Flow.md, genesis/memory/AI_Memory_Response_Flow.md
status: draft
---

# 程序性记忆通道

## 存什么

工具调用日志、技能使用记录、成功率统计。

## 写入流程

1. **工具调用日志打包**：`{user_id, tool_name, params, result, success_flag}`。
2. **成功率统计聚合**：同一工具的成功率 / 平均耗时。
3. **写入行为存储**。

## 字段要求

| 字段 | 必填 | 说明 |
|------|------|------|
| `tool_name` | 是 | 工具名称 |
| `params` | 否 | 调用参数 |
| `result` | 否 | 调用结果 |
| `success_flag` | 是 | 是否成功 |
| `avg_latency` | 否 | 平均耗时 |
| `success_rate` | 否 | 成功率 [0,1] |

## 生命周期

- **只增不减**。记录不断累积，用于后续工具推荐。
- 不随时间衰减。

## 检索方式

- 按工具名称检索。
- 返回历史成功率、平均耗时、最近调用时间。
- 成功率最高的工具优先推荐。
