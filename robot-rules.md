---
title: Robot Rules
version: 1.0
date: 2026-07-07
status: active
---

# Robot Rules — 基础业务逻辑

> 这些规则定义了 Thamus 的记忆存储机制，所有 agent 在与 Thamus 交互时必须遵守。

## 对话记录规则

**每次对话结束（助手回复完用户的问题后），自动执行：**

```bash
python -m memory log --user "<用户消息>" --assistant "<助手回复>"
```

### 参数说明

- `--user`：用户的原始消息（不做修改，原样传递）
- `--assistant`：助手的回复内容（不做修改，原样传递）

### 注意事项

1. **每次对话必须记录** — 无论对话长短、重要与否，所有对话都要写入日志
2. **消息内容原样传递** — 不要省略、不要摘要、不要修改
3. **对话结束即触发** — 不要在睡去时才补记，回复完就记
4. **失败不中断流程** — 如果命令执行失败，打印错误后继续，不中断对话

### 示例

用户问："今天天气怎么样？"
助手答："今天北京晴，25度。"

执行：
```bash
python -m memory log --user "今天天气怎么样？" --assistant "今天北京晴，25度。"
```

## 记忆存储架构

- 所有对话写入 `memory/logs/YYYYMMDDNN.json`
- 每个文件最大 3MB，超过自动拆分
- 简化流程：`python -m memory consolidate`
- 查看记录：`python -m memory recent-log --n 10`
