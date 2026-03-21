# RANGEN Tools Index

> 最后更新: 2026-03-22
> 
> 本文档是 RANGEN 所有工具的索引，帮助快速定位功能。

---

## 工具分类

### 1. 搜索工具 (Search)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **RealSearchTool** | `src/agents/execution_tools/agents/real_search_tool.py` | Tavily 实时搜索 | 🟢 生产 |
| **WebSearchTool** | `src/agents/execution_tools/agents/web_search_tool.py` | DuckDuckGo 网页搜索 | 🟢 生产 |
| **SearchTool** | `src/agents/execution_tools/agents/search_tool.py` | 搜索接口 | 🟢 生产 |

**使用示例**:
```python
from src.agents.execution_tools.agents.web_search_tool import WebSearchTool

tool = WebSearchTool()
result = await tool.call(query="AI news", max_results=5)
```

---

### 2. 浏览器工具 (Browser)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **BrowserTool** | `src/agents/execution_tools/agents/browser_tool.py` | Playwright 浏览器自动化 | 🟢 生产 |

**浏览器工具使用示例**:
```python
from src.agents.execution_tools.agents.browser_tool import BrowserTool

tool = BrowserTool()
result = await tool.call(action="navigate", url="https://example.com")
```

---

### 3. 检索工具 (Retrieval)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **RetrievalTool** | `src/agents/execution_tools/agents/retrieval_tool.py` | 知识检索 | 🟢 生产 |
| **RAGTool** | `src/agents/execution_tools/agents/rag_tool.py` | RAG检索 | 🟢 生产 |
| **KnowledgeRetrievalTool** | `src/agents/execution_tools/agents/knowledge_retrieval_tool.py` | 知识库检索 | 🟢 生产 |

---

### 4. 推理工具 (Reasoning)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **ReasoningTool** | `src/agents/execution_tools/agents/reasoning_tool.py` | 推理执行 | 🟢 生产 |

---

### 5. 基础工具 (Base)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **BaseTool** | `src/agents/execution_tools/base_tool.py` | 工具基类 | 🟢 生产 |
| **CalculatorTool** | `src/agents/execution_tools/agents/calculator_tool.py` | 计算器 | 🟢 生产 |
| **MultimodalTool** | `src/agents/execution_tools/agents/multimodal_tool.py` | 多模态 | 🟡 实验 |
| **FileHandTool** | `src/agents/execution_tools/agents/file_hand_tool.py` | 文件处理 | 🟢 生产 |

---

### 6. 工具注册与管理

| 组件 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **ToolRegistry** | `src/agents/execution_tools/tool_registry.py` | 工具注册表 | 🟢 生产 |
| **ToolOrchestrator** | `src/agents/execution/tool_orchestrator.py` | 工具编排 | 🟢 生产 |
| **IntelligentToolSelector** | `src/agents/execution/intelligent_tool_selector.py` | 智能选择 | 🟢 生产 |

---

## 目录结构

```
src/agents/
├── execution_tools/              # 执行工具目录
│   ├── tool_registry.py         # 工具注册表
│   ├── base_tool.py            # 工具基类
│   ├── agents/                 # 具体工具实现
│   │   ├── real_search_tool.py
│   │   ├── web_search_tool.py
│   │   ├── browser_tool.py
│   │   ├── retrieval_tool.py
│   │   ├── rag_tool.py
│   │   ├── reasoning_tool.py
│   │   ├── calculator_tool.py
│   │   └── ...
│   └── core/                   # 核心工具
└── execution/                   # 执行层
    ├── tool_orchestrator.py
    └── intelligent_tool_selector.py
```

---

*最后更新: 2026-03-22*
