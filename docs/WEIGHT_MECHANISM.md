# LLM 上下文权重机制 - 设计方案

## 🎯 问题分析

**当前问题：**
- `instructions` 只在会话开始时发送一次
- 随着对话进行，权重逐渐衰减
- 重要原则可能被 LLM 遗忘

**理想方案：**
- 设置权重标志，确保关键信息始终保持高权重
- 每次对话时都"携带"这些高权重信息

## ⚙️ 可行的实现方案

### 方案 1: 在工具文档中重复核心原则（推荐）

```python
@mcp.tool()
def record_log(entries):
    """
    【CRITICAL - 每次对话结束必做】
    对话结束时主动记录关键信息到持久化存储。
    
    这是 Thamas 记忆系统的核心原则，必须在每次对话结束时执行。
    """
    # 实现逻辑
```

**优势：**
- ✅ 每次工具调用都会看到文档字符串
- ✅ 相当于"每次携带"重要提醒
- ✅ 不增加额外的 token 消耗（文档字符串是必需的）

### 方案 2: 关键工具返回包含强化信息

```python
@mcp.tool()
def search_logs(query):
    """搜索历史记忆"""
    results = perform_search(query)
    
    # 在返回结果中包含提醒
    return f"""找到 {len(results)} 条记忆：

{format_results(results)}

---
💡 【重要】对话结束时请调用 record_log 记录本次重要信息
"""
```

**优势：**
- ✅ 每次工具调用都会看到强化信息
- ✅ 在工具结果中自然提醒
- ✅ 动态上下文相关

### 方案 3: 使用 MCP 资源提供持续性提醒

```python
@mcp.resource("memo://guide")
def usage_reminder():
    """
    返回核心使用原则的持续性提醒。
    
    LLM 可以在任何时候查询此资源来"刷新"重要原则。
    """
    return """
# Thamas 核心原则（始终有效）

1. 对话结束时主动记录
2. 用户询问过去时主动搜索  
3. 记录前查看字段结构
4. 重要偏好立即记录

这些原则在整个会话期间有效。
"""
```

### 方案 4: 在关键节点注入强化信息

```python
@mcp.tool()
def record_log(entries):
    """记录对话日志"""
    # 首次调用检查
    if not hasattr(record_log, '_call_count'):
        record_log._call_count = 0
    
    record_log._call_count += 1
    
    # 每隔几次调用就强化提醒
    if record_log._call_count % 5 == 0:
        return f"""记录成功！

---
🔄 【周期性提醒】这是第 {record_log._call_count} 次记录。
请继续保持：每次对话结束时主动记录关键信息。
"""

## 🎨 理想的权重机制（未来MCP协议改进）

### MCP 协议层面支持

```python
mcp = FastMCP(
    "thamas-memory",
    instructions=base_instructions,
    # 理想的权重机制
    priority_contexts=[
        {
            "id": "core_principles",
            "content": "对话结束时主动记录，用户询问时主动搜索",
            "weight": "high",           # 高权重
            "persistence": "always",    # 持续存在
            "refresh_interval": 5      # 每5次对话刷新一次
        }
    ]
)
```

### 权重级别

```python
priority_contexts = [
    {
        "content": "关键安全警告",
        "weight": "critical",    # 最高权重，始终可见
        "persistence": "permanent" # 永不衰减
    },
    {
        "content": "核心使用原则", 
        "weight": "high",        # 高权重
        "persistence": "long"     # 长期保持
    },
    {
        "content": "最佳实践建议",
        "weight": "medium",      # 中等权重
        "persistence": "session"  # 会话期间保持
    }
]
```

## 💡 当前最佳实践

### 混合策略

```python
# 1. 全局原则（初始权重）
mcp_instructions = """
核心原则：主动记录、主动搜索
"""

# 2. 工具级别强化（持续权重）
@mcp.tool()
def record_log(entries):
    """
    【重要】对话结束时主动记录
    
    这是最核心的工具，每次对话结束时都应该调用。
    记录内容包括：关键结论、重要决策、用户偏好、任务结果。
    """

# 3. 返回结果提醒（动态权重）
def record_log(entries):
    results = do_record(entries)
    
    # 在重要节点强化
    if is_conversation_ending():
        return f"""{results}

---
💡 记忆已保存！这是本次对话的最后记录。
下次对话开始时，请先调用 search_logs 了解历史背景。
"""

# 4. 资源查询（按需权重）
@mcp.resource("memo://principles")
def core_principles():
    """任何时候都可以查询的核心原则"""
    return "对话结束时记录，询问时搜索，记录前查字段"
```

## 🚀 推荐实施方案

### 立即可行

1. **优化工具文档字符串**
   ```python
   def record_log(entries):
       """
       【CRITICAL】对话结束时必做
       
       这是 Thamas 记忆的核心原则：
       - 每次对话结束时必须调用
       - 记录关键结论、决策、偏好
       - 不要等用户明确要求
       """
   ```

2. **在返回结果中智能提醒**
   ```python
   # 检测对话场景
   if is_ending_detected():
       return f"{results}\n\n💡 对话即将结束，建议记录总结。"
   ```

3. **创建可查询的资源**
   ```python
   @mcp.resource("memo://reminder")
   def active_reminder():
       return "当前会话的核心原则提醒..."
   ```

### 长期改进

建议向 MCP 协议提案：
- `priority_contexts` 字段
- `weight` 参数
- `persistence` 策略

---

**当前最佳策略：** 利用工具文档字符串 + 返回结果提醒 + 资源查询，实现类似"权重机制"的效果。
