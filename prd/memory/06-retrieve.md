---
title: 检索机制
version: 0.2
date: 2026-07-06
status: draft
---

# 检索机制

## 检索范围

只检索 `memory/thamus.json` 中的提炼记忆。流水账文件（`memory/logs/`）只在需要完整上下文时按需读取。

## 检索方式

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 方式 | 向量相似度（余弦距离） | — |
| Top-K | 10 | 返回条数上限 |
| 相似度截断 | 0.65 | 低于此值不返回 |

## 检索流程

1. 用户提问 → 提取 query embedding
2. 与 thamus.json 中所有记忆的 embedding 计算余弦相似度
3. 按相似度排序，取 top-k
4. 返回记忆 content + 元数据

## 不做的

- 不做权威性加权（我们没有 official/personal/inferred 的多用户场景）
- 不做三层情景记忆检索（没有字面/双链/向量分离）
- 不做程序性记忆单独检索
