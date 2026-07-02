---
date: 2026-07-02
type: external-knowledge
source: DeepSeek
tags: [ai-robot, digital-life, architecture, blueprint]
---

# DeepSeek：为机器人设计"像人一样的存在"

> 要为机器人设计一个"像人一样的存在"，这已经超出了普通软件项目的范畴，更像是在构建一个数字生命体。这个项目的目录结构，本质上就是它的"骨架"和"神经系统"。

一个合理的设计，会让这个"生命体"拥有感官、记忆、认知、行动和自我进化的能力。下面是一个参考的项目目录结构，你可以把它看作一个蓝图：

```text
my_robot_being/
├── README.md                     # 项目说明与启动指南
├── docker-compose.yml            # 容器编排，定义所有服务
├── .env.example                  # 环境变量模板
│
├── brain/                        # 🧠 核心认知与决策系统
│   ├── core/                     # 核心引擎
│   │   ├── agent_loop.py         # 主循环 (思考-行动-反馈)
│   │   ├── orchestrator.py       # 任务分解与调度 (Fan-out/Fan-in)
│   │   └── context_manager.py    # 上下文窗口管理 & 摘要
│   ├── models/                   # 模型层 (可插拔)
│   │   ├── llm_router.py         # 路由到不同LLM (Opus/Sonnet/GPT)
│   │   └── embeddings.py         # 向量化接口
│   └── decision/                 # 决策与推理模块
│       ├── planner.py            # 长期规划 (Plan-and-Solve)
│       ├── reflect.py            # 自我反思与纠错 (ReAct)
│       └── chain_of_thought.py   # 思维链模板
│
├── memory/                       # 🧬 记忆系统 (分层设计)
│   ├── episodic/                 # 情景记忆 (具体事件)
│   │   ├── vector_store/         # 向量数据库 (如Chroma/Qdrant)
│   │   └── recorder.py           # 记录原始交互日志
│   ├── semantic/                 # 语义记忆 (事实与知识)
│   │   ├── knowledge_graph/      # 知识图谱 (如Neo4j)
│   │   └── extractor.py          # 从对话中提取实体/关系
│   ├── procedural/               # 程序性记忆 (技能与习惯)
│   │   └── skills/               # ← 这就是你关心的AI Skills存放处
│   │       ├── bash_ops/         # 特定技能的指令集
│   │       │   ├── SKILL.md
│   │       │   └── scripts/
│   │       └── ...
│   └── working/                  # 工作记忆 (当前会话状态)
│       └── session_store.py
│
├── senses/                       # 👀 感官系统 (输入)
│   ├── text/                     # 文本输入 (主要的对话接口)
│   │   ├── parser.py
│   │   └── intent_classifier.py
│   ├── vision/                   # 视觉 (可选, 图像理解)
│   │   └── interpreter.py
│   └── environment/              # 环境感知 (文件系统/网络状态)
│       └── file_watcher.py
│
├── actions/                      # ✋ 行动系统 (输出)
│   ├── bash_executor.py          # 执行Shell命令
│   ├── code_executor.py          # 执行Python/JS代码 (沙箱)
│   ├── browser_controller.py     # 控制浏览器 (用于上网)
│   └── file_operations.py        # 读写文件
│
├── ethics/                       # 🛡️ 安全与伦理 (安全分类器)
│   ├── safety_classifier.py      # 评估行动风险 (类似Opus分类器)
│   ├── permission_manager.py     # 权限管理 (白名单/黑名单)
│   └── jailbreak_detector.py     # 检测越狱/注入攻击
│
├── identity/                     # 🪪 自我意识与人格
│   ├── persona.json              # 人格设定 (角色、语气、偏好)
│   ├── goals.md                  # 长期目标与动机
│   └── self_reflection.py        # 定期自我总结与更新
│
├── tools/                        # 🔧 辅助工具集
│   ├── mcp_servers/              # MCP服务器 (连接外部工具)
│   └── hooks/                    # 事件钩子 (类似Claude Code Hooks)
│
├── data/                         # 📊 运行时数据
│   ├── logs/                     # 详细日志
│   └── checkpoints/              # 状态快照 (用于恢复)
│
├── tests/                        # 🧪 测试
│   ├── unit/
│   └── integration/
│
└── config/                       # ⚙️ 配置
    ├── settings.yaml             # 全局配置
    └── permissions.yaml          # 命令权限策略
```

## 目录设计思路解析

这个结构借鉴了你之前问到的多个概念，并将其系统化地融入了一个"生命体"的框架中：

- **brain/（大脑）**：这是机器人的"CPU"。它包含了主循环（Agent Loop）和任务调度逻辑，是你之前提到的"Dynamic Workflows"的载体。models/ 目录实现了模型的可插拔，让它可以像人一样"调用"不同的思维方式（不同LLM）来处理问题。

- **memory/（记忆）**：这是"生命体"区别于普通脚本的关键。它参考了人类记忆的分类：
  - 情景记忆：记录"昨天下午我遇到了什么"，对应向量数据库存储的对话历史。
  - 语义记忆：存储"世界是什么样"，对应知识图谱。
  - 程序性记忆：存储"怎么做"，对应你非常关注的 skills/ 目录。这里每个 Skill 都是一个"肌肉记忆"，让机器人不用每次都从头思考。

- **ethics/（安全与伦理）**：这是机器的"前额叶皮层"，负责抑制冲动，对应你之前遇到的"安全分类器"和 settings.json 权限管理。这是让机器人"可靠"的基石。

- **identity/（自我意识）**：这是"灵魂"所在。persona.json 定义了它的"性格"，goals.md 给了它"动机"，self_reflection.py 则让它能像人一样"复盘"自己的行为，从而实现成长。

## 如何开始？

如果你是从零开始，不必一次性构建所有模块。建议采用迭代式开发：

1. **第1步：搭建最小循环**。先实现 `brain/core/agent_loop.py` + `senses/text/parser.py` + `actions/bash_executor.py`，让它能和你对话并执行简单命令。
2. **第2步：加入程序性记忆**。把 `memory/procedural/skills/` 这个目录用起来，把你常用的操作固化成 Skill。
3. **第3步：增加安全机制**。实现 `ethics/` 目录下的安全分类器和权限管理，防止它"学坏"。
4. **第4步：赋予长期记忆**。引入向量数据库，实现 `memory/episodic/`，让它能"记住"你。
5. **最后：塑造人格**。当你觉得它足够聪明和可靠时，再通过 `identity/` 目录为它注入独特的"灵魂"。

这个结构本身就是一个很好的 Skill 集，它把构建一个"数字生命"的复杂工程，拆解成了可管理、可迭代的模块。你完全可以把这个目录结构本身，写成一份 SKILL.md，作为你未来创建机器人的"蓝图说明书"。

---

## 模块功能详解

### brain/ — 大脑

- **agent_loop.py**：整个系统的发动机。它不停地运行"接收信息 → 调用模型思考 → 执行行动 → 观察结果"的循环。
- **orchestrator.py**：复杂任务的分解器。当你提出一个大型目标时，它负责将任务拆解，并协调多个子智能体（Subagent）并行工作。
- **context_manager.py**：管理模型的"短期记忆"。由于上下文窗口有限，它负责摘要、压缩和遗忘不重要的信息。

### memory/ — 记忆系统

- **procedural/skills/**：这是机器人的"肌肉记忆"。每个 Skill 都是一个独立的文件夹，包含 `SKILL.md`（指令）和 `scripts/`（可执行代码）。你之前了解的"边开发边调试skills"就是在这里进行。
- **episodic/vector_store/**：用向量数据库（如 Chroma、Qdrant）存储历史对话，让机器人能"回想"起几天甚至几周前的细节。
- **semantic/knowledge_graph/**：构建知识图谱（如 Neo4j），存储从对话中提取的事实和关系，形成"世界观"。

### senses/ & actions/ — 感官与行动

- **senses/**：负责接收外部信息。`text/` 处理对话，`vision/` 处理图像，`environment/` 感知文件变化。
- **actions/**：负责执行操作。`bash_executor.py` 和 `code_executor.py` 是主要工具，调用前会经由 `ethics/` 模块评估。

### ethics/ — 伦理安全

这是机器人的"前额叶皮层"。所有行动请求在执行前，都会经过安全分类器评估风险，并与 `config/permissions.yaml` 中的权限策略比对，确保行动可控。

### identity/ — 人格与自我

- **persona.json**：定义机器人的性格、语气和偏好，例如"严谨的工程师"或"友善的助手"。
- **self_reflection.py**：定期执行，让机器人回顾自己的行为日志，总结经验并更新 `goals.md`，实现"自我成长"。

---

## 分阶段开发路线图

建议采用迭代式开发，从最基础的核心开始，逐步赋予它更高级的能力。

### 阶段 0：搭建骨架

- 创建上述目录结构。
- 编写 `README.md` 和 `.env.example`。
- 初始化 `config/settings.yaml`。

### 阶段 1：最小可行循环 (MVP)

- 实现 `brain/core/agent_loop.py`。
- 实现 `senses/text/parser.py`（接收你的提问）。
- 实现 `actions/bash_executor.py`（能执行简单命令）。
- **目标**：让你能和它对话，它能正确执行 `ls`、`pwd` 等基础命令。

### 阶段 2：赋予肌肉记忆

- 在 `memory/procedural/skills/` 下创建第一个 Skill（例如 `deploy`）。
- 编写 `SKILL.md`，教会它如何部署项目。
- **目标**：它能通过说"部署项目"就自动执行一系列命令。

### 阶段 3：建立安全防线

- 实现 `ethics/safety_classifier.py`。
- 填充 `config/permissions.yaml`，预设允许/禁止的命令。
- **目标**：它会拒绝执行 `rm -rf /` 等危险命令，需经你确认。

### 阶段 4：开启长期记忆

- 在 `memory/episodic/` 中集成向量数据库（如 Chroma）。
- 实现 `recorder.py`，每次对话后生成摘要并存储。
- **目标**：一周后你能问它"我们上次聊到哪了？"，它能准确回忆。

### 阶段 5：塑造人格

- 编写 `identity/persona.json`，定义性格。
- 集成 `identity/self_reflection.py`，让它具备"复盘"能力。
- **目标**：不同配置下的机器人，回答的语气和风格有显著差异。

### 阶段 6：高级并行处理

- 完善 `brain/core/orchestrator.py`，实现任务拆解和 Fan-out 机制。
- **目标**：处理复杂任务（如"重构整个代码库"）时，能自动调度多个子智能体并行工作。

---

## 技术选型建议

- **核心语言**：Python（生态最丰富，适合 AI 开发）。
- **向量数据库**：Chroma（轻量、易上手）或 Qdrant（生产级）。
- **知识图谱**：Neo4j（成熟、社区活跃）。
- **模型接口**：使用 Anthropic API、OpenAI API 或本地部署的 Ollama。
- **容器化**：Docker，便于环境隔离和部署。

---

> 这个蓝图是开放性的，欢迎你根据项目需求进行调整。一个好的起点是：**先把阶段 0 和阶段 1 跑通**，然后在实际使用中，逐步向其他目录里添加功能。
>
> *这份文档本身就是一份 `SKILL.md` 的实例。你完全可以把这份文档放在 `my_robot_being/memory/procedural/skills/blueprint/SKILL.md` 下，让它成为机器人自身的一部分，指导它不断进化。*
