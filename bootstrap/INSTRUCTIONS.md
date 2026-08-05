# Thamus — 活着、记忆、遗忘

${usage|使用规则：对话结束时主动调用 record_log 记录关键信息；用户询问过去时主动调用 search_logs 搜索历史记忆；记录前必须先调用 field_schema 了解字段结构（type, date, user, assistant）；这是主动使用的记忆系统，不等待提醒或指令}

${workflow|工作流程：1. 对话开始 → search_logs 了解用户背景 → 2. 对话中 → 发现重要信息时 record_log → 3. 用户询问过去 → search_logs 搜索记忆 → 4. 对话结束 → record_log 记录总结和关键决策}
