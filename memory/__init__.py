"""Thamus 的记忆器官。基于日志文件的对话存储与简化。

记忆系统架构：
  - 对话原文存储在 memory/logs/ 目录下，按日拆分文件
  - 简化时补充 importance、embedding、linked_ids 元数据
  - CLI 命令：log / consolidate / recent-log
"""
