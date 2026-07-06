---
title: 简化触发
version: 0.4
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

1. **扫描**：读取当日所有文件
2. **分类**：LLM 判断每条记录的类型（事实/观点/经验/噪音）
3. **提纯**：压缩冗余内容，保留语义核心
4. **评分**：LLM 评估每条记录的初始 importance [0,1]
5. **建链**：建立 linked_ids 关联（先建链，再算引用加成）
6. **引用加成**：统计每条记录被多少其他记录的 linked_ids 引用，引用越多 importance 越高

| 引用次数 | importance 加成 |
|------|------|
| 0 | 无 |
| 1-2 | +0.1 |
| 3-5 | +0.2 |
| 5+ | +0.3 |

加分后 importance 上限为 1.0。

7. **固化**：标记重要记忆（importance > 0.7 且 consolidated = false → consolidated = true）
8. **向量化**：计算 embedding
9. **检索增强**：检查 recall_count > 5 且 importance < 0.5 → importance + 0.1
10. **删除**：importance < 0.3 且 consolidated = true 的记录直接删除

## 输出

简化后文件内的记录携带完整元数据：importance、consolidated、embedding、linked_ids、recall_count。
