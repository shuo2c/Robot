---
title: 记忆存储 — 概要设计
version: 1.0
date: 2026-07-06
status: draft
---

# 记忆存储 — 概要设计

> 基于 `prd/memory/` 三份需求文档，面向 `memory/` 目录现有代码，定义可执行、可验证的设计。

---

## 1. 架构概览

```
memory/
├── core.py          ← 现有记忆引擎（Memory 类、检索、embedding、持久化）
├── __main__.py      ← CLI（wake/note/core/recall/sleep/chat/reflect/link/embed/export-md）
├── thamus.json      ← 运行时记忆数据
└── logs/            ← 新增：按日流水账文件
    ├── 2026070601.json
    ├── 2026070602.json
    └── 2026070701.json
```

**核心变更：** 在现有 `memory/` 包下新增 `logs/` 目录，作为原始对话的写入目标。现有 `thamus.json` 保留作为语义核心导出目标。

---

## 2. 模块划分

| 模块 | 职责 | 对应文件 |
|------|------|---------|
| 写入器 | 对话追加、文件拆分、日期切换 | `memory/log_writer.py`（新增） |
| 简化器 | 扫描→提纯→评分→建链→引用加成→向量化 | `memory/consolidator.py`（新增） |
| 嵌入层 | sentence-transformers 优先，hashing-trick 兜底 | 复用 `core.py` 的 `_st_embed`/`_simple_embed` |
| CLI 集成 | 将写入器和简化器接入现有命令 | 修改 `__main__.py` |

---

## 3. 写入器（log_writer.py）

### 3.1 职责

- 将每轮对话（user + assistant）打包为一条记录，追加到当日日志文件
- 检测文件是否超过 3MB，超过则创建新文件
- 检测日期是否变化，变化则切换到新日期文件

### 3.2 数据结构

每条记录（JSON 对象）：

```json
{
  "turn": 1,
  "user": "用户消息原文",
  "assistant": "助手回复原文",
  "timestamp": 1751836800.0,
  "id": "a1b2c3d4e5f6"
}
```

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| `turn` | int | 是 | 当日递增序号，新文件重置为 1 |
| `user` | str | 是 | 用户消息 |
| `assistant` | str | 是 | 助手回复 |
| `timestamp` | float | 是 | `time.time()` |
| `id` | str | 是 | `uuid.uuid4().hex[:12]` |

简化后追加字段：

| 字段 | 类型 | 来源 |
|------|------|------|
| `importance` | int | 简化时 LLM 评分 |
| `embedding` | list[float] | 简化时向量化 |
| `linked_ids` | list[str] | 简化时建链 |

### 3.3 文件命名

格式：`YYYYMMDDNN.json`

- `YYYYMMDD`：日期
- `NN`：当日序号，从 01 开始，每次文件满 3MB 递增

### 3.4 接口

```python
class LogWriter:
    def append(self, user_msg: str, assistant_msg: str) -> None:
        """追加一轮对话到当日日志文件。自动处理文件拆分和日期切换。"""

    def get_current_file(self) -> str:
        """返回当前正在写入的文件名。"""

    def get_today_files(self) -> list[str]:
        """返回当日所有日志文件路径。"""

    def get_all_files(self) -> list[str]:
        """返回所有日志文件路径（所有日期）。"""
```

### 3.5 验证条件

- [ ] 写入一轮对话后，对应日志文件存在且包含正确的 JSON 记录
- [ ] 单日对话量超过 3MB 时，自动创建新文件（序号 +1）
- [ ] 跨天后自动切换到新日期文件
- [ ] 记录格式与上述数据结构完全一致
- [ ] `turn` 序号在新文件中从 1 重新开始

---

## 4. 简化器（consolidator.py）

### 4.1 职责

在触发条件满足时，对当日所有日志文件执行简化流程：

1. 扫描
2. 提纯
3. 评分
4. 建链
5. 引用加成
6. 向量化

### 4.2 触发条件

| 条件 | 检测方式 |
|------|----------|
| 文件满 3MB | `append()` 时检查文件大小 |
| 跨天 | `append()` 时检查当前日期与最后写入日期 |

### 4.3 简化流程

#### 步骤 1：扫描

读取当日所有 `logs/YYYYMMDD*.json` 文件，加载为记录列表。

#### 步骤 2：提纯

对每条记录执行原地修改：

- **保留**：关键事实、决策理由、教训经验、观点信念 → 不改动
- **压缩**：冗长推理过程 → 结论 + 原因，更新 `user`/`assistant` 字段内容为精炼版
- **丢弃**：寒暄、重复、无信息量的过程性废话 → 从文件中删除

**原地修改**：不创建新记录，直接修改已有记录的字段。

#### 步骤 3：评分

LLM 评估每条记录的初始 `importance`（正整数）。

**输入提示词**：将提纯后的 `user` + `assistant` 内容发给 LLM，要求输出一个正整数作为重要性评分。

**评分标准（供 LLM 参考）**：
- 涉及自我认知、关键决策、明确纠正 → 高分
- 技术讨论、问题解决 → 中等
- 闲聊、寒暄 → 低分

#### 步骤 4：建链

LLM 判断哪些记录之间存在语义关联，互相链接。

**输出**：每条记录的 `linked_ids` 列表。

#### 步骤 5：引用加成

统计每条记录被多少其他记录的 `linked_ids` 引用，按规则增加 `importance`：

| 引用次数 | importance 加成 |
|------|------|
| 0 | 无 |
| 1-2 | +1 |
| 3-5 | +2 |
| 5+ | +3 |

#### 步骤 6：向量化

对每条记录计算 embedding 向量。复用 `core.py` 中的 `_st_embed` / `_simple_embed`。

### 4.4 接口

```python
class Consolidator:
    def run(self) -> int:
        """执行简化流程。返回处理的记录数。"""

    def is_triggered(self) -> bool:
        """检查是否满足简化触发条件（文件满 3MB 或跨天）。"""
```

### 4.5 验证条件

- [ ] 简化后所有记录的 `importance` 为正整数
- [ ] 简化后所有记录的 `linked_ids` 指向有效的记录 ID
- [ ] 简化后所有记录的 `embedding` 长度为 128（复用 core.py 的 EMBED_DIM）
- [ ] 提纯后丢弃的记录确实从文件中删除
- [ ] 引用加成计算正确（与被引用次数匹配）
- [ ] 简化是原地修改，不创建新记录

---

## 5. CLI 集成

### 5.1 新增命令

| 命令 | 说明 |
|------|------|
| `python -m memory log` | 将当前对话追加到日志文件 |
| `python -m memory consolidate` | 手动触发简化 |

### 5.2 修改现有命令

- `chat` 命令改为同时写入日志文件
- `sleep` 命令在遗忘前调用 `consolidate()` 简化流程

---

## 6. 与现有代码的关系

| 现有功能 | 是否保留 | 变更 |
|----------|---------|------|
| `Memory.remember()` / `recall()` / `retrieve()` | 保留 | 不变 |
| `Memory.sleep()` 遗忘机制 | 保留 | 当前不启用（待办） |
| `Memory.consolidate()` 语义核心 | 保留 | 不变 |
| `Memory.reflect()` 反思 | 保留 | 不变 |
| `Memory.link()` / `get_linked()` | 保留 | 不变 |
| embedding（st + hashing-trick） | 复用 | 不变 |
| `thamus.json` 持久化 | 保留 | 不变 |
| 新增 `logs/` 目录 | 新增 | 流水账存储 |
| 新增简化流程 | 新增 | `consolidator.py` |

---

## 7. 待办

| 编号 | 内容 | 优先级 |
|------|------|--------|
| T-1 | 遗忘机制：importance 极低且长时间未被引用的记录如何处理 | 中 |
| T-2 | 记忆冲突处理：两条记录语义矛盾时如何处理 | 中 |
| T-3 | 检索机制：BM25 + 向量双路检索（当前不设计） | 低 |
