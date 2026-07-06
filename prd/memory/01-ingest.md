---
title: 流水账存储
version: 0.2
date: 2026-07-06
status: draft
---

# 流水账存储

## 存储位置

`memory/logs/` 目录下，文件名格式：`YYYYMMDD01.json`、`YYYYMMDD02.json`……

## 写入规则

1. 每次对话（用户消息 + 助手回复）作为两条记录追加到当日文件。
2. 同日对话共享同一文件组（01、02、03……按 10MB 拆分）。
3. 跨天后自动切换到新日期文件。

## 文件拆分

- 单个文件最大 10MB（按字节估算，JSON 文本大小）。
- 超过时创建新文件：`2026070601.json` → `2026070602.json`。
- 文件名中的序号表示当日第几个文件。

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

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `role` | str | 是 | `user` 或 `assistant` |
| `content` | str | 是 | 原始消息，不做任何修改 |
| `timestamp` | float | 是 | Unix 时间戳 |
| `id` | str | 是 | 12 位十六进制随机 ID |

## 不做的处理

- 不做统一格式转换（上游已做好）
- 不做 MD5 去重
- 不做语音/OCR 处理
- 不做信息简化

简化在 sleep 时异步执行，不在写入时做。
