---
title: 记忆存储 — 概要设计
version: 2.0
date: 2026-07-06
status: draft
---

# 记忆存储 — 概要设计

> 基于 `prd/memory/` 三份需求文档，定义可执行、可验证的设计。
> 旧的 `thamus.json` 和 `core.py` 中的 Memory 类不再使用，全部由新模块替代。

---

## 1. 架构概览

```
memory/
├── __init__.py
├── __main__.py      ← CLI（log / consolidate / embed）
├── log_writer.py    ← 新增：对话写入、文件拆分、日期切换
├── consolidator.py  ← 新增：简化流程（6步）
├── token_estimator.py  ← 保留：token 统计
└── logs/            ← 新增：按日流水账文件
    ├── 2026070601.json
    ├── 2026070602.json
    └── 2026070701.json
```

**核心变更：**
- 废弃 `thamus.json`、`core.py`（Memory 类及其所有方法）
- 新增 `log_writer.py`、`consolidator.py`
- 新增 `logs/` 目录存储所有记忆数据

---

## 2. 写入器（log_writer.py）

### 2.1 职责

- 将每轮对话（user + assistant）打包为一条记录，追加到当日日志文件
- 检测文件是否超过 3MB，超过则创建新文件
- 检测日期是否变化，变化则切换到新日期文件

### 2.2 数据结构

每条记录（JSON 对象）：

```json
{
  "turn": 1,
  "user": "用户消息原文",
  "assistant": "助手回复原文",
  "timestamp": 1751836800.0,
  "id": "a1b2c3d4e5f6",
  "importance": 7,
  "embedding": [0.1, -0.2, ...],
  "linked_ids": ["turn_def456"]
}
```

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| `turn` | int | 是 | 当日递增序号，新文件重置为 1 |
| `user` | str | 是 | 用户消息 |
| `assistant` | str | 是 | 助手回复 |
| `timestamp` | float | 是 | `time.time()` |
| `id` | str | 是 | `uuid.uuid4().hex[:12]` |
| `importance` | int | 否 | 简化时 LLM 评分 |
| `embedding` | list[float] | 否 | 简化时向量化 |
| `linked_ids` | list[str] | 否 | 简化时建链 |

### 2.3 文件命名

格式：`YYYYMMDDNN.json`

- `YYYYMMDD`：日期
- `NN`：当日序号，从 01 开始，每次文件满 3MB 递增

### 2.4 接口

```python
class LogWriter:
    def __init__(self, base_dir: Path = None):
        """初始化，base_dir 默认为 memory/logs/"""

    def append(self, user_msg: str, assistant_msg: str) -> None:
        """追加一轮对话到当日日志文件。自动处理文件拆分和日期切换。"""

    def get_current_file(self) -> Path:
        """返回当前正在写入的文件路径。"""

    def get_today_files(self) -> list[Path]:
        """返回当日所有日志文件路径。"""

    def get_all_files(self) -> list[Path]:
        """返回所有日志文件路径（所有日期）。"""
```

### 2.5 验证条件

- [ ] 写入一轮对话后，对应日志文件存在且包含正确的 JSON 记录
- [ ] 单日对话量超过 3MB 时，自动创建新文件（序号 +1）
- [ ] 跨天后自动切换到新日期文件
- [ ] 记录格式与上述数据结构完全一致
- [ ] `turn` 序号在新文件中从 1 重新开始

---

## 3. 简化器（consolidator.py）

### 3.1 职责

在触发条件满足时，对当日所有日志文件执行简化流程：

1. 扫描
2. 提纯
3. 评分
4. 建链
5. 引用加成
6. 向量化

### 3.2 触发条件

| 条件 | 检测方式 |
|------|----------|
| 文件满 3MB | `append()` 时检查文件大小 |
| 跨天 | `append()` 时检查当前日期与最后写入日期 |

### 3.3 简化流程

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

**输入**：提纯后的 `user` + `assistant` 内容。
**输出**：一个正整数。

**评分标准**：
- 涉及自我认知、关键决策、明确纠正 → 高分（5+）
- 技术讨论、问题解决 → 中等（2-4）
- 闲聊、寒暄 → 低分（1）

#### 步骤 4：建链

LLM 判断哪些记录之间存在语义关联，互相链接。

**输入**：文件内所有记录内容。
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

对每条记录计算 embedding 向量。

**实现**：使用 hashing-trick（零依赖，复用 `core.py` 的 `_simple_embed` 逻辑，128 维）。

### 3.4 接口

```python
class Consolidator:
    def __init__(self, log_writer: LogWriter):
        """依赖 LogWriter 获取文件路径。"""

    def run(self) -> int:
        """执行简化流程。返回处理的记录数。"""

    def is_triggered(self) -> bool:
        """检查是否满足简化触发条件（文件满 3MB 或跨天）。"""
```

### 3.5 验证条件

- [ ] 简化后所有记录的 `importance` 为正整数
- [ ] 简化后所有记录的 `linked_ids` 指向有效的记录 ID
- [ ] 简化后所有记录的 `embedding` 长度为 128
- [ ] 提纯后丢弃的记录确实从文件中删除
- [ ] 引用加成计算正确（与被引用次数匹配）
- [ ] 简化是原地修改，不创建新记录

---

## 4. CLI 集成

### 4.1 命令列表

| 命令 | 说明 |
|------|------|
| `python -m memory log` | 将当前对话追加到日志文件（需传入 user/assistant 参数） |
| `python -m memory consolidate` | 手动触发简化 |
| `python -m memory embed` | 批量计算缺失的 embedding |
| `python -m memory recent` | 查看最近的日志记录 |

### 4.2 命令签名

```
python -m memory log --user "用户消息" --assistant "助手回复"
python -m memory consolidate [--today] [--all]
python -m memory embed
python -m memory recent [--n 10]
```

---

## 5. 待办

| 编号 | 内容 | 优先级 |
|------|------|--------|
| T-1 | 遗忘机制：importance 极低且长时间未被引用的记录如何处理 | 中 |
| T-2 | 记忆冲突处理：两条记录语义矛盾时如何处理 | 中 |
| T-3 | 检索机制：BM25 + 向量双路检索 | 低 |
