---
title: 核心铁律
version: 0.3
date: 2026-07-06
status: draft
---

# 核心铁律

| 编号 | 铁律 | 说明 |
|------|------|------|
| **F-1** | 没固化不准忘 | consolidated = false 的记录永不降级到 cold |
| **F-2** | 遗忘即删除 | importance < 0.3 的记录直接删除，释放空间和检索开销 |
| **F-3** | 元数据完整 | 简化后每条记录必须带 importance、embedding、linked_ids |
| **F-4** | 冲突禁止覆盖 | 发现新版本只标记旧版 deprecated，不删除 |
| **F-5** | 原始数据先行 | 写入时不简化，先存原始对话 |
| **F-6** | 提取即再巩固 | 每次召回时记录提取次数，>5 次后 importance 自动提升 |
