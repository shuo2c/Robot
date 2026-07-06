---
title: 离线巩固
version: 0.1
date: 2026-07-06
source: genesis/memory/AI_Pure_Storage_Flow.md, genesis/memory/AI_Memory_Response_Flow.md
status: draft
---

# 离线巩固

## 触发

- **定时**：每日凌晨 2:00（CronJob）。
- **空闲时**：系统无活跃请求时。
- **约束**：执行时长 ≤ 30 分钟，超时中断。

## 任务池

| 任务 | 触发条件 | 说明 |
|------|----------|------|
| 低分遗忘 | 每次巩固 | `importance < 0.2` 且距今 > 90 天 → 降为 cold |
| 对话摘要合并 | 每次巩固 | 同一用户的 N 轮对话 → 1 条高阶摘要（modality="reflection"） |
| 冲突检测与标注 | 每次巩固 | 同一实体出现新版本 → 标记旧版 deprecated |
| 向量索引重建 | 新增文档 > 1000 篇 | 重新计算向量索引 |

## 低分遗忘规则

- **条件**：`importance < 0.2` AND `age > 90 天` AND `consolidated = True`。
- **操作**：`state = "cold"`（不删除，仅降为冷状态）。
- **铁律保护**：`consolidated = False` 的记忆永不降级。
- **日志**：记录遗忘操作到审计日志（`operation = "forget"`）。

## 对话摘要合并

- **条件**：同一 `user_id` 下连续 N 轮对话（N 默认 5）。
- **操作**：合并为 1 条 `modality="reflection"` 的高阶摘要。
- **源链接**：摘要的 `source_ids` 指向被合并的原始对话 ID。

## 冲突检测

- **条件**：新记忆与已有记忆语义高度相似但内容矛盾。
- **操作**：标记旧记忆 `status = "deprecated"`，`superseded_by = 新记忆 ID`。
- **铁律**：禁止硬删除，只软标记。
