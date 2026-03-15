# 创建系统规范文档 SYSTEM_SPEC.md

我将参照 `AGENTS.md` 的结构，为您编写本系统的规范文档 `SYSTEM_SPEC.md`。该文档将作为 RANGEN 系统的开发指南，定义各类组件（Agents, Tools, Core）的标准和组织方式。

## 文档大纲

### 1. 项目定义 (Project Definition)
*   **名称**: RANGEN (Research Agent Generation Engine)
*   **描述**: 一个自主化研究与推理的多智能体系统。
*   **核心能力**: 深度推理 (Reasoning), 知识检索 (RAG), 任务编排 (Orchestration)。

### 2. 资源组织结构 (Repository Structure)
定义代码库的标准目录布局，对应 `AGENTS.md` 中的 Resources 部分：
*   `src/agents/`: **Agents** (智能体实现)
*   `src/agents/tools/`: **Skills/Tools** (工具与技能)
*   `src/core/`: **Core Kernel** (核心引擎与路由)
*   `src/knowledge_management_system/`: **Knowledge** (知识库管理)

### 3. 开发规范 (Development Standards)
仿照 `AGENTS.md` 的规范部分，定义 Python 风格的标准：

*   **Agents (智能体)**:
    *   **基类**: 必须继承自 `src.agents.base_agent.BaseAgent`。
    *   **命名**: 文件名使用 `snake_case` (如 `reasoning_expert.py`)，类名使用 `PascalCase` (如 `ReasoningExpert`)。
    *   **元数据**: 必须包含文档字符串 (Docstrings) 描述智能体职责。

*   **Skills/Tools (技能/工具)**:
    *   **基类**: 必须继承自 `src.agents.tools.base_tool.BaseTool`。
    *   **注册**: 必须在 `src.agents.tools.tool_registry.ToolRegistry` 中注册。
    *   **接口**: 必须实现 `run` 方法。

*   **Prompts (提示词)**:
    *   *现状*: 目前内嵌于代码中。
    *   *规范*: 建议提取至 `src/prompts/` (规划中) 或在类常量中统一定义。

### 4. 工作流 (Workflow)
*   **添加新智能体**: 创建文件 -> 继承基类 -> 实现 execute -> 注册到 Coordinator。
*   **添加新工具**: 创建工具类 -> 定义参数 Schema -> 注册到 ToolRegistry。

## 执行步骤
1.  在根目录创建 `SYSTEM_SPEC.md` 文件。
2.  写入上述规范内容。
