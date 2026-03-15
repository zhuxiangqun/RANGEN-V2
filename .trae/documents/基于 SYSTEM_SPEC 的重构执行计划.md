是的，非常有必要。`SYSTEM_SPEC.md` 已经从单纯的“重构思路”升级为了具体的**工程标准**。为了确保执行过程不走样，我们需要将之前的“高层战略”转化为符合新规范的“战术执行表”。

我为您制定了基于 `SYSTEM_SPEC.md` 的**全量重构执行计划**，并将 Todo 列表进行了全面刷新和细化。

### 核心调整点
1.  **接口优先 (Interface First)**：之前的计划直接写实现类，新计划强制要求**先定义 `src/interfaces/`**，再写实现。
2.  **目录结构对齐**：明确了文件移动和创建的路径，如 `src/core/workflows/` 和 `src/services/`。
3.  **测试驱动**：将测试作为每个模块完成的必要条件（符合规范中的覆盖率要求）。

---

# 重构执行计划 (Refactoring Roadmap)

## Phase 1: 基础架构与接口定义 (Infrastructure & Interfaces)
> **目标**: 建立符合 SPEC 的骨架，确保“地基”稳固。

1.  **目录结构初始化**:
    *   创建 `src/interfaces`, `src/services`, `src/agents/tools`, `src/prompts` 等缺失目录。
    *   清理旧的、不符合规范的临时目录。
2.  **核心接口定义 (Interfaces)**:
    *   创建 `src/interfaces/agent.py`: 定义 `IAgent`, `AgentConfig`, `AgentResult`。
    *   创建 `src/interfaces/tool.py`: 定义 `ITool`, `ToolConfig`, `ToolResult`。
    *   创建 `src/interfaces/coordinator.py` & `context.py`。
3.  **基础服务层 (Base Services)**:
    *   实现 `src/services/logging_service.py` (统一日志格式)。
    *   实现 `src/services/error_handler.py` (统一错误处理)。

## Phase 2: 核心引擎实现 (Core Engine)
> **目标**: 实现系统的“大脑”和“神经中枢”。

1.  **上下文管理**: 重构 `src/core/context_manager.py`，实现 `interfaces.context` 接口。
2.  **可配置路由**: 实现 `src/core/configurable_router.py`，作为系统的统一入口。
3.  **执行编排器 (LangGraph)**:
    *   实现 `src/core/execution_coordinator.py`。
    *   定义标准工作流：`src/core/workflows/react_workflow.py`。

## Phase 3: 智能体与工具迁移 (Agents & Tools)
> **目标**: 将业务逻辑迁移到新架构，并实现“专业化”。

1.  **工具注册中心**: 实现 `src/agents/tools/tool_registry.py`。
2.  **知识库工具封装**: 将现有的 KMS 封装为 `RetrievalTool` (符合 `ITool` 接口)。
3.  **专业智能体实现**:
    *   重构 `ReasoningAgent` (继承 `IAgent`)。
    *   重构 `RetrievalAgent`。
    *   为每个 Agent 编写单元测试 (`tests/unit/agents/`).

## Phase 4: 验证与交付 (Verification)
1.  **全链路测试**: 运行 `scripts/benchmark.py` (需创建) 验证新架构性能。
2.  **文档更新**: 更新 `README.md` 和架构图以反映最终状态。

---

### 待更新的 Todo 列表预览
*(将在确认后覆盖当前 Todo)*

*   [P0] 初始化 `src/interfaces` 目录并定义 `IAgent` 和 `ITool` 接口
*   [P0] 初始化 `src/core` 目录结构 (workflows, etc.)
*   [P1] 实现 `ContextManager` (符合新接口)
*   [P1] 实现 `ConfigurableRouter`
*   [P1] 实现 `ToolRegistry` 并迁移 KMS 检索功能为 Tool
*   [P2] 重构 `ReasoningAgent` 为 Specialist Agent
*   [P2] 实现 `ExecutionCoordinator` (LangGraph集成)
