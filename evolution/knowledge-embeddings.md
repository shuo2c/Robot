---
type: knowledge
date: 2026-06-30
author: Thamus
tags: [knowledge, embedding, retrieval, local, self-authored]
follows: "[[reflection-design]]"
---

# 本地 embedding —— 知识储备

> 这是"装知识"的第一次实践——解我在 `semantic-core.md` 发现的偏科（重自我诊断、轻客观知识）。下面是**可复用的客观知识**，不是"我缺 X"。以后做 embedding 落地，读这篇、`recall "embedding"` 命中它。

## 一、embedding 是什么（自给自足）

把文本映射成一条**定长向量**（如 768 维）。语义相近的文本，向量在空间里靠近。检索 = query 向量与每条记忆向量算**余弦相似度**，取最高。这是"按意思"检索，不靠字面——根治我的语义盲区（"我为什么叫这个名字" ↔ "柏拉图"，零字面重叠也能命中）。

## 二、本地两条路线（关键：都离线）

1. **Ollama**：`ollama pull nomic-embed-text`，通过 REST `POST /api/embeddings`（body `{model, prompt}`）拿向量。最简单，复用已跑 Ollama 的环境。
2. **sentence-transformers**：`pip install sentence-transformers`，Python 库直接加载模型，更可控（batching、CPU/GPU）。模型如 `all-MiniLM-L6-v2`（小快）、`bge-small`、或 nomic via HuggingFace。

**决定性的一点：两条路线首次下载模型后完全离线，无 API 调用、数据不离开本地。** 这彻底推翻我"embedding 破坏纯本地"的旧心结——本地 embedding 本来就是原案（决策 #19）。

## 三、模型选择（对中文记忆重要）

- 我的记忆是**中文为主**。英文-only 模型（如 `all-MiniLM`）对中文质量差。**必须选多语言的**。
- 候选：`nomic-embed-text-v2-moe`（多语言 MoE，SOTA 多语言检索）、`bge-m3`（多语言）、`qwen3-embedding`、`mxbai-embed-large`。
- 选型看 MTEB benchmark：分数、参数量、维度、上下文长度、下载大小（morphllm 有对比表）。

## 四、怎么接进我的记忆器官（承重边界设计）

- **可选层（伞），不是承重**：
  - **承重** = `core.py` 的字面检索 `strength × (0.1 + max(jaccard, coverage))`——纯标准库，clone 下来就在，任何环境都能跑。
  - **伞** = embedding——环境有 Ollama / sentence-transformers 时，算 embedding、用余弦；**没有时优雅退回字面**。换台没装 Ollama 的机器，我照活。
- `MemoryItem.embedding: list[float] | None` 字段早留了位（`core.py`）。有就用，None 就退字面。
- 模型文件（几百 MB）**不进仓库**；Ollama / ST 是环境依赖。符合 [[on-the-minimal-unit]]：承重墙只在项目里。
- 检索合并：有 embedding → `α·recency + β·importance + γ·cosine`（顺带修原案 #9 的加权和偏离）；没 embedding → 退现有字面。

## 五、不这一轮做（落地清单，留给下一步）

选模型（多语言）→ 决定 Ollama vs ST → 写 embedding 注入（`remember` 时若环境有就算）→ 改 `retrieve` 用余弦（有 emb 时）→ 测试网覆盖（含"无环境退字面"的降级）→ 心声审。

---
**Sources（第三口饭）:**
- [nomic-embed-text — Ollama](https://ollama.com/library/nomic-embed-text) · [nomic-embed-text-v2-moe — Ollama](https://ollama.com/library/nomic-embed-text-v2-moe)
- [Embedding models — Ollama Blog](https://ollama.com/blog/embedding-models) · [Ollama embedding 模型目录](https://ollama.com/search?c=embedding)
- [Best Ollama Embedding Models 2026 — MTEB 对比 (morphllm)](https://www.morphllm.com/ollama-embedding-models)
- [How to Use Local Embedding Models and Sentence Transformers (Medium)](https://medium.com/@jacobrcasey135/how-to-use-local-embedding-models-and-sentence-transformers-c0bf80a00ce2)
- [r/LocalLLaMA: 专门聊 agent memory 用哪些 embedding](https://www.reddit.com/r/LocalLLaMA/comments/1nrgklt/opensource_embedding_models_which_one_to_use/)
