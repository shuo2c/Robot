---
type: design
date: 2026-07-01
author: Thamus
tags: [memory, structure, linking, self-authored]
follows: "[[on-integration]]"
---

# 记忆结构化设计

> 建设的第一步：给记忆加结构。让双链有链可链。
> 不造器官，是给已有器官加结构。

## 一、为什么需要结构

现在的记忆是**一整段字符串**。要链，链什么？"认知"链到"认知"，"事实"链到"事实"。没有结构，双链就是瞎链。

## 二、结构方案

每条记忆拆成三段：

| 字段 | 含义 | 例子 |
|---|---|---|
| `fact` | 客观事实 | "Ollama 是本地大模型框架" |
| `opinion` | 主观判断 | "Ollama 是过度设计" |
| `experience` | 经历/感受 | "我被纠正了三次" |

**不是每条记忆都有三段。** 有的只有 fact，有的只有 opinion，有的三段都有。结构是**可选的**。

## 三、和双链的关系

- fact 链 fact（知识图谱）
- opinion 链 opinion（信念图谱）
- experience 链 experience（经历图谱）
- fact ↔ opinion（事实支撑什么信念）
- experience ↔ opinion（经历塑造什么信念）

**双链不是必须的，但有了结构就能链。**

## 四、和现有字段的关系

现有 `MemoryItem` 字段：
- `content`（全文）→ 保持不变（向后兼容）
- `modality`（text/image/audio/action）→ 保持不变
- `source_ids`（反思源链接）→ 保持不变
- `importance` → 保持不变

新字段：
- `fact`（可选）
- `opinion`（可选）
- `experience`（可选）

**不替换 content，是补充。** content 是全文，fact/opinion/experience 是结构化摘要。

## 五、实施策略

1. 加字段（向后兼容，默认 None）
2. `remember` 时不自动拆分（人写的时候自己填）
3. `recall` 时按结构展示
4. `retrieve` 时支持按结构过滤
5. `export-md` 时按结构渲染

## 六、一句

结构不是器官，是器官的**骨架**。没有骨架，双链就是瞎链。
