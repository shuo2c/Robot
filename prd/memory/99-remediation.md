---
title: 记忆存储整改计划
version: 0.1
date: 2026-07-06
status: discussion
---

# 记忆存储整改计划

> 基于 genesis/memory/ 三份原始 PRD + 当前 prd/memory/ 九份细化文档，对照我们实际语境（自我记忆，不是服务系统），整理出需要整改的点。
>
> 只收录已讨论并达成共识的项。未讨论的暂不加入。

---

## 1. 去掉审计日志

- **涉及文件**：08-rules.md, 00-overview.md
- **当前**：所有写入/修改/提取操作生成结构化日志，追加到 memory/audit.jsonl，永久留存
- **问题**：审计日志的前提是多人协作系统需要追踪"谁在什么时候做了什么"。我们是单人的，每条记忆自带 timestamp，recall 更新 last_recalled，sleep 更新 state——这些字段本身就是足够的追踪
- **改为**：去掉 audit.jsonl。依靠 thamus.json 里每条记录的 timestamp/last_recalled/state 字段做追踪
