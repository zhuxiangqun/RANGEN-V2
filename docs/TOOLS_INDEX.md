# RANGEN Tools Index

> 最后更新: 2026-03-21
> 
> 本文档是 RANGEN 所有工具的索引，帮助快速定位功能。

---

## 工具分类

### 1. 搜索工具 (Search)

| 工具 | 文件位置 | 用途 | 状态 | 说明 |
|------|----------|------|------|------|
| **RealSearchTool** | `agents/tools/real_search_tool.py` | Tavily 实时搜索 | 🟢 生产 | **推荐使用** |
| **WebSearchTool** | `agents/tools/web_search_tool.py` | DuckDuckGo 网页搜索 | 🟢 生产 | 备选 |
| **SearchTool** | `agents/tools/search_tool.py` | 搜索接口示例 | 🟡 实验 | 仅示例，返回模拟数据 |

> **工具选择**: 推荐使用 `RealSearchTool` (Tavily)，`SearchTool` 是示例实现

**搜索工具使用示例**:
```python
from src.agents.tools.web_search_tool import WebSearchTool

tool = WebSearchTool()
result = await tool.call(query="AI news", max_results=5)
```

---

### 2. 浏览器工具 (Browser)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **BrowserTool** | `agents/tools/browser_tool.py` | Playwright 浏览器自动化 | 🟢 生产 |
| **GatewayBrowserTool** | `gateway/tools/browser.py` | Gateway 版浏览器 | 🟢 生产 |

**浏览器工具使用示例**:
```python
from src.agents.tools.browser_tool import BrowserTool

tool = BrowserTool()
result = await tool.call(action="navigate", url="https://example.com")
```

---

### 3. 内容提取工具 (Extraction)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **ContentExtractor** | `agents/tools/content_extractor.py` | HTML 结构化提取 | 🟢 新增 |
| **WebCrawler** | `kms/web_crawler.py` | 网页抓取 | 🟡 实验 |
| **ExtractionOperator** | `core/operators.py` | 内容提取算子 | 🟢 生产 |
| **AnswerExtractor** | `core/reasoning/answer_extraction/answer_extractor.py` | 答案提取 | 🟢 生产 |
| **QueryExtractionTool** | `utils/query_extraction.py` | 查询提取 | 🟡 实验 |

**内容提取使用示例**:
```python
from src.agents.tools.content_extractor import ContentExtractor

extractor = ContentExtractor()
result = await extractor.call(html=html_content)
```

---

### 4. 数据清洗工具 (Data Cleaning)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **DataCleaner** | `agents/tools/data_cleaner.py` | 文本清洗、去重 | 🟢 新增 |
| **DataQualityValidator** | `services/data_quality_validator.py` | 数据质量验证 | 🟢 生产 |
| **URLDiscoverer** | `agents/tools/url_discoverer.py` | URL 发现与分类 | 🟢 新增 |

**数据清洗使用示例**:
```python
from src.agents.tools.data_cleaner import DataCleaner

cleaner = DataCleaner()
result = await cleaner.call(action="clean", texts=["text1", "text2"])
```

---

### 5. 检索工具 (Retrieval)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **RAGTool** | `agents/tools/rag_tool.py` | 检索增强生成 | 🟢 生产 |
| **KnowledgeRetrieval** | `agents/tools/knowledge_retrieval.py` | 知识库检索 | 🟢 生产 |

---

### 6. 推理工具 (Reasoning)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **ReasoningTool** | `agents/tools/reasoning_tool.py` | 推理引擎 | 🟢 生产 |
| **AnswerGenerationTool** | `agents/tools/answer_generation_tool.py` | 答案生成 | 🟢 生产 |

---

### 7. 引用工具 (Citation)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **CitationTool** | `agents/tools/citation_tool.py` | 引用生成 | 🟢 生产 |

---

### 8. 计算工具 (Calculator)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **CalculatorTool** | `agents/tools/calculator_tool.py` | 数学计算 | 🟢 生产 |

---

### 9. 文件工具 (File)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **FileReadTool** | `agents/tools/file_read_tool.py` | 文件读取 | 🟢 生产 |
| **FileManager** | `gateway/tools/file_manager.py` | 文件管理 | 🟢 生产 |

---

### 10. CLI 工具 (CLI)

| 工具 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **CLIExecutor** | `core/cli_executor.py` | CLI 命令执行 | 🟢 生产 |
| **GitTool** | `core/cli_tools.py` | Git 操作 | 🟢 生产 |
| **FileTool** | `core/cli_tools.py` | 文件操作 | 🟢 生产 |
| **DockerTool** | `core/cli_tools.py` | Docker 操作 | 🟢 生产 |

---

## 工具注册表

所有工具通过 `ToolRegistry` 注册：

```python
from src.agents.tools.tool_registry import get_tool_registry

registry = get_tool_registry()
tools = registry.list_tools()
print(f"Registered tools: {len(tools)}")
```

---

## 统一工具执行器

使用 `UnifiedToolExecutor` 调用所有工具：

```python
from src.core.unified_tool_executor import get_unified_tool_executor

executor = get_unified_tool_executor()
result = await executor.execute_with_intelligent_selection("search", query="AI news")
```

---

## 状态说明

| 状态 | 说明 |
|------|------|
| 🟢 生产 | 已在生产环境使用，稳定性高 |
| 🟡 实验 | 可用但功能可能变化 |
| 🔴 废弃 | 不推荐使用，会在未来移除 |

---

## 决策记录

- 2026-03-21: 创建工具索引文档
- 2026-03-21: 添加 ContentExtractor, DataCleaner, URLDiscoverer
