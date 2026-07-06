---
title: 类型判断与分流
version: 0.4
date: 2026-07-06
status: draft
---

# 类型判断与分流

## 写入时不分类

原始消息写入时不做任何分类，只记录 turn/user/assistant/timestamp/id。

## 简化时分类

简化阶段 LLM 扫描文件内所有记录，按语义判断类型：

| 类型 | 判断标准 | 操作 |
|------|----------|------|
| 事实/知识 | 陈述客观信息、概念定义 | 提升 importance，计算 embedding |
| 观点/信念 | 表达主观判断、价值观 | 提升 importance，建立 linked_ids |
| 经验/经历 | 记录交互结果或教训 | 提升 importance，标记 consolidated |
| 闲聊/噪音 | 寒暄、无信息量 | 降低 importance，可能遗忘 |

分类影响后续简化提纯和遗忘策略，不影响存储位置（所有记录都在同一个文件里）。
