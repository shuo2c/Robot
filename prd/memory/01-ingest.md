---
title: 流水账存储
version: 0.3
date: 2026-07-06
status: draft
---

# 流水账存储

## 存储位置

`memory/logs/` 目录下，文件名格式：`YYYYMMDD01.json`、`YYYYMMDD02.json`……

## 写入规则

1. 每次对话追加两条记录：用户消息 + 助手回复
2. 同日对话共享文件组
3. 跨天后切换到新日期文件

## 文件拆分

- 单个文件最大 3MB
- 超过时创建新文件：`2026070601.json` → `2026070602.json`
- 文件名序号表示当日第几个文件

## 记录格式

```json
{
  "role": "user",
  "content": "用户消息原文",
  "timestamp": 1782662400.0,
  "id": "msg_a1b2c3d4e5f6"
}
```

```json
{
  "role": "assistant",
  "content": "助手回复原文",
  "timestamp": 1782662401.5,
  "id": "msg_f6e5d4c3b2a1"
}
```

## 每条记录携带的元数据

每条记录不仅是原始消息，还要携带记忆机制所需字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `role` | str | `user` / `assistant` |
| `content` | str | 原始消息 |
| `timestamp` | float | 时间戳 |
| `id` | str | 12 位十六进制 ID |
| `importance` | float | 重要性 [0,1]，简化时评估 |
| `state` | str | `active` / `cold` |
| `consolidated` | bool | 是否已固化 |
| `embedding` | list[float] | 语义向量，简化时计算 |
| `linked_ids` | list[str] | 关联的其他记录 ID |
| `source_ids` | list[str] | 来源原始消息 ID |

写入时只填 role/content/timestamp/id，其余字段在简化时补充。
