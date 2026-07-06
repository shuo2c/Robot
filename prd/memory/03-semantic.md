---
title: 简化提纯
version: 0.4
date: 2026-07-06
status: draft
---

# 简化提纯

## 做什么

扫描文件内所有原始对话记录，压缩冗余内容，保留语义核心。

简化是**原地修改**：不创建新记录，而是补充/更新已有记录的元数据字段（importance、consolidated、embedding、linked_ids、recall_count）。

## 规则

- **保留**：关键事实、决策理由、教训经验、观点信念
- **压缩**：冗长推理过程 → 结论 + 原因（一两句话），更新 user/assistant 字段内容为精炼版
- **丢弃**：寒暄、重复、无信息量的过程性废话 → 直接从文件中删除

## 示例

原始记录：
```json
{
  "turn": 5,
  "user": "这个 bug 怎么回事？",
  "assistant": "让我看看... 第一行不对，第二行也不对... 哦找到了，X 函数里 Y 参数传错了。",
  "timestamp": 1782662400.0,
  "id": "turn_abc123"
}
```

简化后（原地修改）：
```json
{
  "turn": 5,
  "user": "这个 bug 怎么回事？",
  "assistant": "X 函数的 Y 参数传错了。",
  "timestamp": 1782662400.0,
  "id": "turn_abc123",
  "importance": 0.7,
  "consolidated": true,
  "embedding": [0.1, -0.2, ...],
  "linked_ids": ["turn_def456"]
}
```

## 不做的

- 不创建独立的"提炼记忆"文件
- 不迁移到 thamus.json
- 所有操作在原始文件内完成
