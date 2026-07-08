
---

### 📄 文件 2：AI智能体纯记忆存储流程规范（纯存储版）
> （对应倒数第一的回答：剔除了所有回复逻辑，只包含信息进入系统后如何分流、存储、归档的纯存储流程）

```markdown
# AI智能体纯记忆存储流程规范（纯存储版）

> **版本说明**：本规范聚焦于 AI 智能体的**纯粹记忆存储过程**，完全剔除了“实时回复生成”逻辑。涵盖从数据触发、标准化、类型分流、三通道并行写入，到离线巩固清理的完整存储生命周期。包含 5 个核心阶段、10 条纯存储铁律及独立的存储时序图。

---

## 📋 目录

1. [纯记忆存储全流程图（Mermaid）](#-纯记忆存储全流程图mermaid)
2. [5 个核心阶段详解](#-5-个核心阶段详解)
3. [10 条纯存储强制铁律](#-10-条纯存储强制铁律)
4. [纯存储时序图（无回复逻辑）](#-纯存储时序图无回复逻辑)

---

## 🧠 一、纯记忆存储全流程图（Mermaid）

> **XMind 使用提示**：复制下方 Mermaid 代码到 XMind 的“插入代码块（Mermaid）”中，即可生成可视化的纯存储脑图。

```mermaid
graph TD
    classDef trigger fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef store fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef process fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef offline fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px;
    classDef discard fill:#ffebee,stroke:#c62828,stroke-width:2px;

    A["📥 存储触发源<br>━━━━━━━━━━<br>🔹 用户对话内容<br>🔹 上传的文件/文档<br>🔹 外部API推送的数据<br>🔹 系统日志/行为记录"]:::trigger

    A --> B["⚡ 原始数据标准化<br>━━━━━━━━━━<br>🔹 格式统一（txt/json）<br>🔹 语言检测与清洗<br>🔹 去重（MD5指纹比对）"]:::process

    B --> C{"🧭 信息类型分流"}:::process

    C -->|类型A：事实/知识| D["📖 语义记忆写入通道"]:::store
    C -->|类型B：交互经历| E["🗓️ 情景记忆写入通道"]:::store
    C -->|类型C：技能/工具| F["🤹 程序性记忆写入通道"]:::store
    C -->|类型D：无法分类/低质| G["🗑️ 垃圾回收区<br>（直接丢弃）"]:::discard

    subgraph D [语义记忆写入通道]
        D1["📄 文档切块（Chunking）<br>━━━━━━━━━━<br>规则：按语义边界切割<br>（段落/句子）"]
        D2["🔢 向量化（Embedding）<br>━━━━━━━━━━<br>模型：text-embedding-3-small"]
        D3["🏷️ 元数据标注<br>━━━━━━━━━━<br>🔹 source_id<br>🔹 timestamp<br>🔹 doc_type<br>🔹 version"]
        D4["💾 写入向量数据库<br>━━━━━━━━━━<br>目标：Pinecone / Milvus"]
    end

    subgraph E [情景记忆写入通道]
        E1["📋 结构化打包<br>━━━━━━━━━━<br>{user_id, timestamp,<br>user_input, ai_output,<br>emotion_tag}"]
        E2["⭐ 重要性评分计算<br>━━━━━━━━━━<br>公式：互动时长×0.4<br>+ 紧急度×0.3<br>+ 重复提及×0.3"]
        E3["💾 写入关系数据库<br>━━━━━━━━━━<br>目标：PostgreSQL / MySQL"]
    end

    subgraph F [程序性记忆写入通道]
        F1["📋 工具调用日志打包<br>━━━━━━━━━━<br>{user_id, tool_name,<br>params, result,<br>success_flag}"]
        F2["📊 成功率统计聚合<br>━━━━━━━━━━<br>同一工具的成功率/平均耗时"]
        F3["💾 写入行为数据库<br>━━━━━━━━━━<br>目标：时序数据库"]
    end

    D4 --> H["✅ 存储确认（Ack）"]
    E3 --> H
    F3 --> H

    H --> I["📝 存储日志记录<br>━━━━━━━━━━<br>记录操作人、时间、数据量、耗时"]

    %% 离线巩固模块
    I -.-> J["🌙 离线巩固任务<br>（定时触发/每日凌晨2:00）"]:::offline

    subgraph J [离线巩固任务池]
        J1["📊 低分记忆清理<br>━━━━━━━━━━<br>条件：重要性<0.2<br>且距今>90天<br>→ 软删除（归档）"]
        J2["🔄 向量索引重建<br>━━━━━━━━━━<br>触发：新增文档>1000篇<br>或版本升级"]
        J3["📝 对话摘要合并<br>━━━━━━━━━━<br>将同一用户的N轮对话<br>→ 1条高阶摘要"]
        J4["⚖️ 冲突检测与标注<br>━━━━━━━━━━<br>同一实体出现新版本<br>→ 标记旧版为deprecated"]
    end