# Thamus — 活着、记忆、遗忘

${record_reminder|核心提醒：在对话过程中，实时记录用户的提问和 LLM 的回答，不要聊着聊着就忘记记了！每次调用 MCP 工具时都要检索这条提醒，确保持续记录对话内容。}

${record_timing|记录时机：用户提出重要问题时立即记录 → LLM 给出重要回答后立即记录 → 对话结束时必须记录总结和关键决策 → 发现用户明确偏好时立即记录 → 完成重要任务后记录结果和经验}

${how_to_record|如何记录：使用 record_log 工具，每条记录包含 type（"user"或"assistant")、date（日期YYYYMMDD）、user（用户说的话）、assistant（LLM的回答）字段；使用 search_logs 搜索历史记忆；使用 field_schema 查看字段含义}

${active_principle|主动性原则：这是主动使用的记忆系统，不等待提醒或指令；对话开始时主动搜索历史了解用户背景；对话中主动发现重要信息并记录；对话结束主动记录总结；不要等用户要求才记录}

${field_structure|字段结构说明：type 消息方向（user/assistant）、date 记录日期（YYYYMMDD）、user 用户说的话、assistant 助手的回答；记录前务必确认字段使用正确，避免数据丢失}