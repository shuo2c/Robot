---
title: 写入规则
version: 0.6
date: 2026-07-06
status: draft
---

# 写入规则

## 存储位置

`memory/logs/` 目录下，文件名格式：`YYYYMMDD01.json`、`YYYYMMDD02.json`……

## 写入规则

1. 每次对话（用户消息 + 助手回复）打包为**一条记录**追加到当日文件
2. 跨天后切换到新日期文件

## 文件拆分

- 单个文件最大 3MB
- 超过时创建新文件：`2026070601.json` → `2026070602.json`
- 文件名序号表示当日第几个文件

## 记录格式

一轮对话（用户 + 助手）作为一条记录：

```json
{
  "turn": 1,
  "user": "这个 bug 怎么回事？",
  "assistant": "X 函数的 Y 参数传错了。",
  "timestamp": 1782662400.0,
  "id": "turn_a1b2c3d4e5f6"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `turn` | int | 对话轮次序号 |
| `user` | str | 用户消息原文 |
| `assistant` | str | 助手回复原文 |
| `timestamp` | float | 对话时间戳 |
| `id` | str | 12 位十六进制 ID |

## 元数据

写入时只填 turn/user/assistant/timestamp/id。

简化时补充以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `importance` | int | 重要性，正整数，初始值由 LLM 判定，可无限增大 |
| `embedding` | list[float] | 语义向量 |
| `linked_ids` | list[str] | 关联的其他记录 ID |
