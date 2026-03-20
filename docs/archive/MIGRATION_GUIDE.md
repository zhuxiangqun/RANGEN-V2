"""
统一执行器使用指南
=====================

本文档说明如何使用新的统一执行器(UnifiedExecutor)替换旧的Tool调用。

## 旧方式 (已废弃)

```python
# 方式1: 直接使用Tool类
from src.agents.tools.calculator_tool import CalculatorTool

tool = CalculatorTool()
result = await tool.call(expression="10 + 20")

# 方式2: 使用ToolOrchestrator
from src.agents.tool_orchestrator import ToolOrchestrator

orchestrator = ToolOrchestrator()
result = await orchestrator.execute_tool("calculator", {"expression": "10 + 20"})
```

## 新方式 (推荐)

```python
from src.agents.unified_executor import UnifiedExecutor, get_unified_executor

# 方式1: 创建实例
executor = UnifiedExecutor(default_mode="skill")
result = await executor.execute("calculator", {"expression": "10 + 20"})

# 方式2: 使用单例
executor = get_unified_executor()
result = await executor.execute("calculator", {"expression": "10 + 20"})

# 方式3: 便捷函数
from src.agents.unified_executor import execute_tool
result = await execute_tool("calculator", {"expression": "10 + 20"}, use_mcp=True)
```

## 模式说明

- `default_mode="skill"` (默认): 使用Skill-based + MCP协议
- `default_mode="legacy"`: 使用旧系统 (deprecated，仍可用)

## 执行结果

```python
result = await executor.execute("calculator", {"expression": "10 + 20"})

print(result.success)      # True/False
print(result.result)       # 执行结果
print(result.error)        # 错误信息
print(result.execution_time)  # 执行时间
```

## 工具映射

新系统使用Skill名称映射:

| 旧工具名 | 新Skill名 |
|---------|----------|
| calculator | calculator-skill |
| reasoning | reasoning-chain |
| search | web-search |
| rag | rag-retrieval |
| knowledge_retrieval | knowledge-graph |
| answer_generation | answer-generation |
| citation | citation-generation |
| multimodal | multimodal-skill |
| browser | browser-skill |
| file_read | file-read-skill |

## 迁移步骤

1. 替换导入:
   - 旧: `from src.agents.tools.calculator_tool import CalculatorTool`
   - 新: `from src.agents.unified_executor import UnifiedExecutor`

2. 替换调用:
   - 旧: `tool = CalculatorTool(); result = await tool.call(...)`
   - 新: `executor = UnifiedExecutor(); result = await executor.execute(...)`

3. 移除ToolOrchestrator的使用，改用UnifiedExecutor

## 兼容性

- 旧代码仍可运行，但会显示DeprecationWarning
- 建议尽快迁移到新系统
- 新系统功能更强大，支持AI驱动的Skill触发
"""
