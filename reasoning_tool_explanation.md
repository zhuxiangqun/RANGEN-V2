# ReasoningTool 说明文档

## 什么是 ReasoningTool？

**ReasoningTool** 是一个工具（Tool），封装了推理服务（ReasoningService），用于对查询进行多步骤推理。

## 架构

```
ReAct Agent
    └─ ReasoningTool (工具)
        └─ ReasoningService (服务)
            └─ RealReasoningEngine (推理引擎)
```

## 功能

### 1. 主要功能
- **多步骤推理**：对查询进行多步骤推理，生成推理链
- **答案生成**：基于推理链生成最终答案
- **推理步骤记录**：记录每个推理步骤的详细信息

### 2. 与 RAGTool 的区别

| 特性 | ReasoningTool | RAGTool |
|------|--------------|---------|
| **定位** | 推理工具 | RAG工具 |
| **内部实现** | ReasoningService → RealReasoningEngine | RAGAgent → Knowledge Retrieval + Answer Generation |
| **功能** | 多步骤推理 | 知识检索 + 答案生成 |
| **知识检索** | ❌ 不包含（需要外部提供） | ✅ 包含（内部调用 KnowledgeRetrievalAgent） |
| **推理能力** | ✅ 多步骤推理 | ⚠️ 简化推理（通过 RealReasoningEngine） |
| **使用场景** | 复杂推理任务 | 知识检索 + 生成任务 |

### 3. 代码实现

**位置**: `src/agents/tools/reasoning_tool.py`

```python
class ReasoningTool(BaseTool):
    """推理工具 - 封装推理服务"""
    
    def __init__(self):
        super().__init__(
            tool_name="reasoning",
            description="推理工具：对查询进行多步骤推理，生成推理链和答案"
        )
        self._service = None
    
    def _get_service(self):
        """获取推理服务（延迟初始化）"""
        if self._service is None:
            from src.services.reasoning_service import ReasoningService
            self._service = ReasoningService()
        return self._service
    
    async def call(self, query: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """调用推理工具"""
        service = self._get_service()
        result = await service.execute(execution_context)
        # 返回推理结果
        return ToolResult(...)
```

## 问题分析

### 问题1：功能重复

**ReasoningTool** 和 **RAGTool** 都使用了 **RealReasoningEngine**，但方式不同：

- **ReasoningTool**: ReasoningService → RealReasoningEngine（直接调用）
- **RAGTool**: RAGAgent → RealReasoningEngine（通过 RAGAgent 调用）

这导致了功能重复和架构混淆。

### 问题2：知识检索缺失

**ReasoningTool** 不包含知识检索功能，需要外部提供 `knowledge_data` 或 `evidence`：

```python
# ReasoningTool 需要外部提供知识
context = {
    "query": "你的问题",
    "knowledge_data": [...],  # 需要外部提供
    "evidence": [...]  # 需要外部提供
}
```

而 **RAGTool** 内部包含知识检索，不需要外部提供。

### 问题3：架构不一致

- **RAGTool** 使用 **RAGAgent**（符合 Agent 架构）
- **ReasoningTool** 使用 **ReasoningService**（不符合 Agent 架构）

这导致了架构不一致。

## 建议

### 方案1：统一使用 RAGTool

**理由**：
- RAGTool 已经包含了知识检索和答案生成
- RAGTool 使用 RAGAgent，符合 Agent 架构
- 避免功能重复

**实现**：
- 移除 ReasoningTool 的注册
- 统一使用 RAGTool

### 方案2：创建 ReasoningAgent

**理由**：
- 保持架构一致性（都使用 Agent）
- ReasoningAgent 可以专注于多步骤推理
- RAGAgent 专注于知识检索 + 生成

**实现**：
- 创建 ReasoningAgent（类似 RAGAgent）
- ReasoningTool 内部调用 ReasoningAgent
- 保持工具接口兼容性

### 方案3：明确职责分工

**理由**：
- RAGTool：知识检索 + 简单生成（适合简单查询）
- ReasoningTool：复杂推理（适合复杂查询，需要外部提供知识）

**实现**：
- 明确两个工具的使用场景
- 在 ReActAgent 中根据查询复杂度选择工具

## 当前状态

### ReasoningTool 的使用

**注册位置**:
- `src/unified_research_system.py` (line 887-904)
- `src/unified_research_system.py` (line 1080-1086)

**调用位置**:
- `src/agents/react_agent.py` (line 597-602) - 作为默认策略的备选

### 与 RAGTool 的关系

- **RAGTool** 优先使用（已修复）
- **ReasoningTool** 作为备选（如果 RAGTool 不可用）

## 总结

**ReasoningTool** 是一个推理工具，封装了 ReasoningService，用于多步骤推理。但它与 RAGTool 存在功能重复和架构不一致的问题。

**建议**：
1. 统一使用 RAGTool（推荐）
2. 或者创建 ReasoningAgent，保持架构一致性
3. 或者明确职责分工，根据查询复杂度选择工具

