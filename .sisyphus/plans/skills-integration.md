# 提示词与上下文工程集成实施计划

## 目标
将 Skills 可插拔系统与现有的提示词工程、上下文工程进行深度集成。

## 任务列表

### Task 1: 修改 Prompt Manager 支持 Skills 注入
- **文件**: `src/prompts/prompt_manager.py`
- **操作**:
  1. 在 `get_prompt` 方法中添加 `skill_context` 占位符
  2. 新增 `get_prompt_with_skills()` 方法 - 自动从 Skills 生成工具描述和提示词
  3. 新增 `get_tools_for_llm()` 方法 - 返回 LLM 兼容的工具定义
- **Agent Profile**: `quick`
- **QA**: 验证 `get_prompt_with_skills("reasoning_agent_system")` 包含 Skills 内容

### Task 2: 修改 Context Manager 支持 Workspace 隔离
- **文件**: `src/core/context_manager.py`
- **操作**:
  1. 在 `SessionContext` 初始化时接收可选的 `workspace` 参数
  2. 关联的 Workspace 的记忆与当前 Session 共享
  3. 当 Workspace 变化时，自动切换上下文
- **Agent Profile**: `quick`
- **QA**: 验证创建带 Workspace 的 SessionContext 可以访问 Workspace 状态

### Task 3: 创建 SkillsAwareAgent 基类
- **新文件**: `src/agents/skills/agent.py`
- **操作**:
  1. 创建 `SkillsAwareAgent` 基类
  2. 集成 PromptManager + SkillPromptBuilder + Workspace
  3. 提供 `execute()` 方法的模板
- **Agent Profile**: `quick`
- **QA**: 验证 SkillsAwareAgent 实例化成功

### Task 4: 创建集成演示
- **新文件**: `demo_skills_integration.py` (在项目根目录)
- **操作**:
  1. 演示如何使用 Skills + Prompt + Context 完整流程
- **Agent Profile**: `quick`
- **QA**: 运行脚本验证输出

## 执行命令
```bash
cd /Users/apple/workdata/person/zy/RANGEN-main\(syu-python\)

# 测试 Prompt Manager
python3 -c "
from src.prompts.prompt_manager import get_prompt_manager
pm = get_prompt_manager()
prompt = pm.get_prompt_with_skills('reasoning_agent_system', skill_names=['research'])
print('Skills integrated prompt length:', len(prompt))
print('Has skill_context:', 'skill_context' in prompt)
"
```
