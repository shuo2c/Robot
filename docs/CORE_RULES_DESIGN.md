# Token 优化的"上下文引用机制"设计方案

## 🎯 核心想法

**传统方式：**
```python
# 每次都发送完整内容
tool_call("请严格遵循以下规则：
1. 对话结束时主动记录
2. 用户询问时主动搜索
3. 记录前查看字段结构
...")
# Token消耗：~150 tokens
```

**你的想法：**
```python
# 只发送简短引用指令
tool_call("请严格遵循上下文中的 ${core_rules} 执行操作")
# Token消耗：~15 tokens
```

**节省比例：90%！**

## 📋 设计方案

### 1. INSTRUCTIONS.md 中标记关键内容

```markdown
# Thamas 记忆服务

${core_rules}
---
## 核心规则（必须严格遵循）

1. 【对话结束时】必须主动调用 record_log 记录关键信息
2. 【用户询问时】必须主动调用 search_logs 搜索历史
3. 【记录前】必须先调用 field_schema 了解字段结构
4. 【重要偏好】立即调用 record_log 记录用户明确偏好

这些规则是强制的，不是可选的。
${/core_rules}

## 工具说明
...
```

### 2. 每次工具调用前的引用指令

```python
# 原始调用方式
response = f"请调用 record_log 工具，参数是：{params}"
# Token消耗：长

# 你的优化方式
response = f"请严格检查上下文中的 ${{core_rules}}，然后调用 record_log，参数是：{params}"
# Token消耗：短
```

### 3. LLM 的工作流程

```
┌─────────────────────────────────────────────────────┐
│ 1. 会话开始 - 一次性加载 INSTRUCTIONS.md           │
│    LLM 上下文中包含：                              │
│    - 完整的 ${core_rules} 内容                    │
│    - 其他说明                                    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 2. 工具调用阶段                                    │
│    收到指令：请检查 ${{core_rules}}，然后调用 record_log │
│    ↓                                               │
│    LLM 从上下文中检索 ${{core_rules}} 的实际内容    │
│    ↓                                               │
│    LLM 按照检索到的规则执行操作                    │
└─────────────────────────────────────────────────────┘
```

## 💡 实现方式

### 方案 A: 在工具调用时添加引用（推荐）

```python
# bootstrap/memory-server.py

def add_context_reference(tool_response):
    """为工具调用添加上下文引用"""
    return f"""
请先检查上下文中的 ${{core_rules}}，然后严格按照这些规则执行以下操作：

{tool_response}

---
⚠️ 重要：必须始终遵循上述规则，不得跳过。
"""

# 在工具调用时应用
@mcp.tool()
def record_log(entries):
    """记录对话日志"""
    result = do_record(entries)
    return add_context_reference(f"记录结果：{result}")
```

### 方案 B: 在每个工具函数中自动添加

```python
# tools/log_ops.py

def add_rule_reminder(func):
    """装饰器：自动添加规则引用"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return f"""
请严格遵循上下文中的 ${{core_rules}}：

{result}

---
⚠️ 这些规则是强制性的，不是可选的。
"""
    return wrapper

@mcp.tool()
@add_rule_reminder
def record_log(entries):
    """记录对话日志"""
    return do_record(entries)
```

### 方案 C: 在 MCP 层面统一处理（最优）

```python
# bootstrap/memory-server.py

class RuleAwareMCP(FastMCP):
    """支持规则引用的 MCP 服务器"""
    
    def __init__(self, name, instructions, rule_marker="${rule}"):
        super().__init__(name, instructions)
        self.rule_marker = rule_marker
        self.extract_rules(instructions)
    
    def extract_rules(self, instructions):
        """从 instructions 中提取标记的规则"""
        import re
        pattern = rf'\{self.rule_marker}\}(.*?)\{/{self.rule_marker}\}'
        matches = re.findall(pattern, instructions, re.DOTALL)
        self.rules = {f"${rule_marker}": match for rule_marker, match in enumerate(matches)}
    
    def enhance_tool_response(self, response):
        """增强工具响应，添加规则引用"""
        rule_refs = " ".join([f"${{{rule}}}" for rule in self.rules.keys()])
        return f"""
请严格遵循上下文中的 {rule_refs}：

{response}

---
⚠️ 这些规则必须始终遵循。
"""

# 使用
mcp = RuleAwareMCP(
    "thamas-memory",
    instructions_content
)
```

## 📊 Token 对比分析

### 场景：10 次工具调用

**传统方式：**
```
每次调用包含：完整规则说明 (150 tokens) + 工具调用 (50 tokens)
10 次调用：10 × 200 = 2,000 tokens
```

**你的方式：**
```
初始化：完整规则 (150 tokens)
每次调用：引用指令 (15 tokens) + 工具调用 (50 tokens)
10 次调用：150 + 10 × 65 = 800 tokens
```

**节省：1,200 tokens (60% 节省！)**

## ⚠️ 潜在问题与解决方案

### 问题 1: 上下文遗忘

**风险：** LLM 可能忘记上下文中的规则内容
```python
# 解决方案：添加强化机制
if should_remind():
    return f"""
${core_rules} 的内容：
【实际规则内容】

请严格遵循以上规则执行：{tool_call}
"""
```

### 问题 2: 引用解析

**风险：** LLM 可能不理解 `${core_rules}` 的含义
```python
# 解决方案：在初始化时明确说明
instructions = """
${core_rules}
这些是核心规则，在工具调用时会通过 ${{core_rules}} 引用。
${/core_rules}
"""
```

### 问题 3: 规则提取

**风险：** 规则提取可能不准确
```python
# 解决方案：使用标准化的标记格式
instructions = """
${RULES:core}
规则内容...
${/RULES:core}
"""
```

## 🚀 推荐实现步骤

### 第 1 步：修改 INSTRUCTIONS.md

```markdown
# Thamas 记忆服务

${RULES:core}
## 核心规则（必须遵循）

1. 对话结束时必须调用 record_log
2. 用户询问时必须调用 search_logs  
3. 记录前必须调用 field_schema
4. 重要偏好立即记录

这些规则是强制性的，不是可选的。
${/RULES:core}
```

### 第 2 步：在工具返回中添加引用

```python
@mcp.tool()
def record_log(entries):
    """记录对话日志"""
    result = do_record(entries)
    return f"""
{result}

---
⚠️ 请始终遵循上下文中的 ${{RULES:core}}
"""
```

### 第 3 步：验证效果

```bash
# 启动服务器
python bootstrap/memory-server.py sse

# 测试工具调用
# 检查返回结果中是否包含引用
# 观察 LLM 是否按照规则执行
```

## 🎯 优势总结

| 优势 | 说明 |
|------|------|
| **Token节省** | 节省 60%+ 的 token 消耗 |
| **规则一致性** | 所有工具调用遵循相同规则 |
| **易于维护** | 规则集中在一个地方 |
| **动态引用** | 可以引用多个不同的规则集合 |
| **扩展性强** | 可以添加 `${RULES:security}` 等其他引用 |

## 💡 进一步优化

### 多级规则引用

```markdown
${RULES:critical}
安全规则（最高优先级）
${/RULES:critical}

${RULES:standard}
标准操作规则
${/RULES:standard}

${RULES:optional}
最佳实践建议
${/RULES:optional}
```

### 条件性引用

```python
def add_conditional_reference(response, rule_type="standard"):
    """根据操作重要性添加不同级别的规则引用"""
    if is_critical_operation():
        return f"{response}\n\n⚠️ 必须遵循 ${{RULES:critical}}"
    else:
        return f"{response}\n\n请遵循 ${{RULES:standard}}"
```

---

**这个方案完全可行！** 你的想法很好地解决了 token 消耗和规则一致性的矛盾。

需要我帮你实现到当前项目中吗？
