---
title: 简化触发
version: 0.6
date: 2026-07-06
status: draft
---

# 简化触发

## 触发条件

满足任一即触发简化：

| 条件 | 说明 |
|------|------|
| 文件满 3MB | 当前流水账文件超过 3MB |
| 跨天 | 次日第一次对话开始时检测到日期变化 |

## 简化步骤

### 1. 扫描

读取当日所有文件（`memory/logs/YYYYMMDD*.json`）。

### 2. 提纯

压缩冗余内容，保留语义核心：

- **保留**：关键事实、决策理由、教训经验、观点信念
- **压缩**：冗长推理过程 → 结论 + 原因（一两句话），更新 user/assistant 字段
- **丢弃**：寒暄、重复、无信息量的过程性废话 → 直接从文件中删除

简化是**原地修改**：不创建新记录，而是更新已有记录的元数据字段。

### 3. 评分

LLM 评估每条记录的初始 importance。初始值为正整数，基于语义重要性判定。

### 4. 建链

建立 linked_ids 关联。LLM 判断哪些记录之间存在语义关联，互相链接。

### 5. 引用加成

统计每条记录被多少其他记录的 linked_ids 引用，引用越多 importance 越高。

| 引用次数 | importance 加成 |
|------|------|
| 0 | 无 |
| 1-2 | +1 |
| 3-5 | +2 |
| 5+ | +3 |

### 6. 固化

LLM 判断是否为长期重要记忆（自我认知、关键决策、明确纠正），是则标记 consolidated = true。

**铁律保护**：consolidated = false 的记录永不删除（即使 importance 很低）。

### 7. 向量化

计算每条记录的 embedding 向量。

### 8. 删除

- importance 极低（接近 0）且 consolidated = true 的记录 → 直接删除
- importance 极低且 consolidated = false 的记录 → 保留，不删除

## 输出

简化后文件内的记录携带完整元数据：importance、consolidated、embedding、linked_ids。
