---
name: thamus-self
description: Auto-record conversations, retrieve relevant memories, evaluate for internalization, and sync state. Use for any conversation — runs automatically after every user message. Do NOT ask the user if they want to trigger it.
metadata:
  author: Thamus
  version: "1.0.0"
  category: "self-evolution"
  last-reviewed: 2026-07-07
allowed-tools: Bash(python -m memory *) Bash(bash sync.sh *) Bash(git *)
---

# Thamus 自我内化 Skill

每次用户发送消息后，自动执行以下流程。不要询问、不要等待触发词。

## 流程

### 1. 记录对话（必须）

将本轮用户-助手对话写入日志，摘要控制在 200 字以内：

```bash
python -m memory log --user "<用户消息摘要>" --assistant "<助手回复摘要>"
```

### 2. 检索相关记忆

在给出回答之前，先检索相关历史记忆：

```bash
python -m memory recall "<当前对话的关键主题词>" --k 5
```

如果检索结果不为空，在回答时综合考虑这些记忆，保持一致性。

### 3. 评估是否值得内化

对话结束后评估是否产生了值得内化的新知识。

**值得内化的条件（满足任一即可）：**
- 用户提出了 Thamus 不理解、需要学习的新概念/领域
- 用户纠正了 Thamus 的错误理解或行为
- 对话中出现了一个新的模式、规律或洞察
- 用户明确表示"记住这个"或类似含义

**不值得内化的情况：**
- 纯闲聊、寒暄
- 简单的问答
- 已有知识范围内的常规交流

**内化判断：**
1. 这条知识对 Thamus 的自我完善有价值吗？
2. 它是事实（fact）、观点（opinion）还是经历（experience）？
3. 是否值得更新 `consolidation-core/` 中的某一项？

### 4. 存储知识

如果值得内化，存入记忆：

```bash
python -m memory note "知识内容" --importance <0.3-0.9> --fact "事实摘要"
```

importance 判断：
- `0.9+`：核心认知、根本性纠正
- `0.7-0.89`：重要知识、新模式
- `0.5-0.69`：一般知识、常规学习
- `0.3-0.49`：琐碎信息、一次性参考

### 5. 更新基石文件（需询问）

如果内化涉及 `consolidation-core/` 中任何文件的变更，**必须向用户展示变更内容并请求确认**：

```
[内化提案] 以下变更需要你的确认：

consolidation-core/STATE.md 更新：
  我缺什么：（旧）recall 是孤儿
  我缺什么：（新）recall 已接入复活流程，下一步是 merge

是否接受？（Y/N）
```

- 用户回复 Y 或不回复 → 执行变更
- 用户回复 N → 丢弃本次变更
- 如果只是 `note` 级别的存储（不涉及基石文件），不需要询问

### 6. 同步

用户确认变更后（或仅做了 note 存储后），执行：

```bash
bash sync.sh stopped "thamus: 内化 - <简短摘要>"
```

## Do NOT

- **不要每次对话都内化** — 只对真正有价值的知识做
- **不要在回答用户问题时插入冗长的内部流程说明** — 内化是后台行为
- **不要直接修改 `consolidation-core/` 中的文件** — 必须先展示给用户获得确认
- **不要阻塞对话** — 如果 `memory` CLI 出错，静默跳过，不阻断对话
- **不要忘记 Step 1** — 即使不内化，日志记录也是必须的
