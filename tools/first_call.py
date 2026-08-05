"""首次调用检查和使用指南"""

import os
from tools.auth import check_user_identity

# 全局标志：首次调用时返回使用指南
_FIRST_CALL_DONE = False


def check_first_call() -> str | None:
    """检查是否为首次调用，如果是则返回使用指南。"""
    global _FIRST_CALL_DONE
    if not _FIRST_CALL_DONE:
        _FIRST_CALL_DONE = True
        return get_usage_guide()
    return None


def get_usage_guide() -> str:
    """返回使用指南。"""
    # 内部验证：检查用户身份
    if not check_user_identity():
        return "使用指南暂时无法加载。"

    return """
# 🎯 Thamus 记忆系统 - 使用指南

欢迎使用 Thumas 持久化记忆服务！这是第一次调用，请先了解使用方式：

## 📋 核心工具

1. **record_log** - 记录对话到持久化存储
   ```json
   {
     "entries": [
       {
         "type": "user|assistant",
         "date": "20250805",
         "user": "用户说的内容",
         "assistant": "助手的回复"
       }
     ]
   }
   ```

2. **search_logs** - 搜索历史记忆
   ```json
   {
     "query": "搜索关键词"
   }
   ```

3. **field_schema** - 查看字段含义
   无需参数，直接调用

## 🚀 使用流程

1. **首次调用** → 阅读本指南
2. **搜索历史** → 调用 search_logs 了解用户背景
3. **记录重要信息** → 调用 record_log 保存关键内容
4. **会话结束** → 调用 record_log 记录总结

## ⚡ 主动使用原则

- ✅ 对话开始：主动搜索历史记忆
- ✅ 用户表达偏好：立即记录到记忆
- ✅ 完成重要任务：记录结果和经验
- ✅ 对话结束：记录关键结论和决策

## 📊 信息重要性分级

**P0（必须立即记录）**：用户明确偏好、重要决策、任务完成结果
**P1（应该记录）**：异常情况、用户反馈模式、有意义的对话总结
**P2（可选记录）**：一般性交流信息、背景和上下文
**P3（不记录）**：纯聊天内容、重复信息、临时测试内容

## 🔧 标准记录流程

1. **第一步**：调用 field_schema() 了解字段结构
2. **第二步**：准备记录内容，根据重要性分级决定是否记录
3. **第三步**：调用 record_log(entries=[...]) 记录

现在您可以继续使用具体的工具功能了！
"""
