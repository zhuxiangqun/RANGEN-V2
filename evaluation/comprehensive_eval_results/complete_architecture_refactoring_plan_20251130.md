# 核心系统架构重构完整方案

**设计时间**: 2025-11-30  
**目标**: 将核心系统改造为符合标准Agent定义的架构，重命名非Agent组件，封装为工具

---

## 📋 方案概述

### 核心原则

1. **核心系统本身是标准Agent** - `UnifiedResearchSystem`实现Agent循环
2. **非Agent组件重命名** - 避免命名混淆
3. **封装为工具** - 统一接口，便于管理
4. **保持向后兼容** - 逐步迁移，不破坏现有功能

---

## 🏗️ 架构设计

### 1. 核心系统架构

```
UnifiedResearchSystem (标准Agent)
├── 模型（大脑）: LLM Integration
├── 工具注册表: ToolRegistry
│   ├── Agent Tools (4个)
│   │   ├── KnowledgeRetrievalTool
│   │   ├── ReasoningTool
│   │   ├── AnswerGenerationTool
│   │   └── CitationTool
│   └── Utility Tools (3个)
│       ├── RAGTool
│       ├── SearchTool
│       └── CalculatorTool
├── 上下文/记忆: observations, thoughts, actions
└── 循环（生命周期）: while循环
    ├── 思考（Think）
    ├── 规划行动（Plan Action）
    ├── 执行工具（Act）
    └── 观察（Observe）
```

### 2. 组件分类

#### 2.1 真正的Agent（保留命名）

1. ✅ **ReActAgent** - 符合标准Agent定义
2. ✅ **UnifiedResearchSystem** - 改造为标准Agent

#### 2.2 服务组件（重命名）

| 原名称 | 新名称 | 类型 | 说明 |
|--------|--------|------|------|
| `EnhancedKnowledgeRetrievalAgent` | `KnowledgeRetrievalService` | Service | 知识检索服务 |
| `EnhancedReasoningAgent` | `ReasoningService` | Service | 推理服务 |
| `EnhancedAnswerGenerationAgent` | `AnswerGenerationService` | Service | 答案生成服务 |
| `EnhancedCitationAgent` | `CitationService` | Service | 引用生成服务 |

#### 2.3 工具（封装服务）

| 工具名称 | 封装的服务 | 说明 |
|----------|-----------|------|
| `KnowledgeRetrievalTool` | `KnowledgeRetrievalService` | 知识检索工具 |
| `ReasoningTool` | `ReasoningService` | 推理工具 |
| `AnswerGenerationTool` | `AnswerGenerationService` | 答案生成工具 |
| `CitationTool` | `CitationService` | 引用工具 |

---

## 🔄 重构步骤

### 阶段1: 重命名服务组件（P0 - 立即）

#### 步骤1.1: 创建新的Service类（保留原Agent类作为别名）

**策略**: 创建新类，原类作为别名，逐步迁移

```python
# src/services/knowledge_retrieval_service.py
class KnowledgeRetrievalService(BaseAgent):
    """知识检索服务 - 从EnhancedKnowledgeRetrievalAgent重命名"""
    
    def __init__(self, agent_name: str = "KnowledgeRetrievalService", use_intelligent_config: bool = True):
        # 复用原有逻辑
        config = AgentConfig(
            agent_id=agent_name,
            agent_type="knowledge_retrieval"
        )
        super().__init__(agent_name, ["knowledge_retrieval", "intelligent_search", "context_analysis"], config)
        # ... 原有初始化逻辑 ...

# src/agents/enhanced_knowledge_retrieval_agent.py
# 保留作为别名，向后兼容
from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

class EnhancedKnowledgeRetrievalAgent(KnowledgeRetrievalService):
    """向后兼容别名 - 已废弃，请使用KnowledgeRetrievalService"""
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn(
            "EnhancedKnowledgeRetrievalAgent已废弃，请使用KnowledgeRetrievalService",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
```

**同样处理**:
- `ReasoningService` ← `EnhancedReasoningAgent`
- `AnswerGenerationService` ← `EnhancedAnswerGenerationAgent`
- `CitationService` ← `EnhancedCitationAgent`

#### 步骤1.2: 创建Service目录结构

```
src/
├── services/
│   ├── __init__.py
│   ├── knowledge_retrieval_service.py
│   ├── reasoning_service.py
│   ├── answer_generation_service.py
│   └── citation_service.py
├── agents/
│   ├── enhanced_knowledge_retrieval_agent.py  # 保留为别名
│   ├── enhanced_reasoning_agent.py            # 保留为别名
│   ├── enhanced_answer_generation_agent.py    # 保留为别名
│   ├── enhanced_citation_agent.py             # 保留为别名
│   └── react_agent.py                         # 真正的Agent
```

---

### 阶段2: 创建工具封装（P0 - 立即）

#### 步骤2.1: 创建Agent Tools

**1. KnowledgeRetrievalTool**

```python
# src/agents/tools/knowledge_retrieval_tool.py
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class KnowledgeRetrievalTool(BaseTool):
    """知识检索工具 - 封装KnowledgeRetrievalService"""
    
    def __init__(self):
        super().__init__(
            tool_name="knowledge_retrieval",
            description="从知识库检索相关信息，返回知识条目列表。输入查询文本，返回相关的知识片段、证据和上下文信息。"
        )
        self._service = None
    
    def _get_service(self):
        """延迟初始化Service"""
        if self._service is None:
            from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
            self._service = KnowledgeRetrievalService()
        return self._service
    
    async def call(self, query: str, top_k: int = 5, threshold: float = 0.7, **kwargs) -> ToolResult:
        """
        调用知识检索服务
        
        Args:
            query: 查询文本（必需）
            top_k: 返回的知识条目数量（可选，默认5）
            threshold: 相关性阈值（可选，默认0.7）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        try:
            service = self._get_service()
            context = {
                "query": query,
                "top_k": top_k,
                "threshold": threshold,
                **kwargs
            }
            
            result = await service.execute(context)
            
            return ToolResult(
                success=result.success,
                data=result.data,
                error=result.error,
                execution_time=result.processing_time
            )
        except Exception as e:
            logger.error(f"知识检索工具调用失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=0.0
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "查询文本，用于检索相关知识"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回的知识条目数量",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "threshold": {
                    "type": "number",
                    "description": "相关性阈值，范围0-1",
                    "default": 0.7,
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            },
            "required": ["query"]
        }
```

**2. ReasoningTool**

```python
# src/agents/tools/reasoning_tool.py
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class ReasoningTool(BaseTool):
    """推理工具 - 封装ReasoningService"""
    
    def __init__(self):
        super().__init__(
            tool_name="reasoning",
            description="对查询进行推理分析，生成推理步骤和中间结果。输入查询和知识，返回推理过程和结论。"
        )
        self._service = None
    
    def _get_service(self):
        """延迟初始化Service"""
        if self._service is None:
            from src.services.reasoning_service import ReasoningService
            self._service = ReasoningService()
        return self._service
    
    async def call(self, query: str, knowledge: Optional[List[Dict]] = None, 
                   reasoning_type: Optional[str] = None, **kwargs) -> ToolResult:
        """
        调用推理服务
        
        Args:
            query: 查询文本（必需）
            knowledge: 知识列表（可选）
            reasoning_type: 推理类型（可选，如'deductive', 'inductive', 'abductive'）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        try:
            service = self._get_service()
            context = {
                "query": query,
                "knowledge": knowledge or [],
                "reasoning_type": reasoning_type,
                **kwargs
            }
            
            result = await service.process_query(query, context)
            
            return ToolResult(
                success=result.success,
                data=result.data,
                error=result.error,
                execution_time=result.processing_time
            )
        except Exception as e:
            logger.error(f"推理工具调用失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=0.0
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "查询文本，需要进行推理分析"
                },
                "knowledge": {
                    "type": "array",
                    "description": "知识列表，用于推理的证据",
                    "items": {
                        "type": "object"
                    }
                },
                "reasoning_type": {
                    "type": "string",
                    "description": "推理类型",
                    "enum": ["deductive", "inductive", "abductive", "default"],
                    "default": "default"
                }
            },
            "required": ["query"]
        }
```

**3. AnswerGenerationTool**

```python
# src/agents/tools/answer_generation_tool.py
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class AnswerGenerationTool(BaseTool):
    """答案生成工具 - 封装AnswerGenerationService"""
    
    def __init__(self):
        super().__init__(
            tool_name="answer_generation",
            description="基于查询、知识和推理结果生成最终答案。输入查询、知识和推理结果，返回格式化的答案文本。"
        )
        self._service = None
    
    def _get_service(self):
        """延迟初始化Service"""
        if self._service is None:
            from src.services.answer_generation_service import AnswerGenerationService
            self._service = AnswerGenerationService()
        return self._service
    
    async def call(self, query: str, knowledge: Optional[List[Dict]] = None,
                   reasoning: Optional[Dict] = None, **kwargs) -> ToolResult:
        """
        调用答案生成服务
        
        Args:
            query: 查询文本（必需）
            knowledge: 知识列表（可选）
            reasoning: 推理结果（可选）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        try:
            service = self._get_service()
            context = {
                "query": query,
                "knowledge": knowledge or [],
                "reasoning": reasoning or {},
                **kwargs
            }
            
            result = await service.execute(context)
            
            return ToolResult(
                success=result.success,
                data=result.data,
                error=result.error,
                execution_time=result.processing_time
            )
        except Exception as e:
            logger.error(f"答案生成工具调用失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=0.0
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "查询文本"
                },
                "knowledge": {
                    "type": "array",
                    "description": "知识列表",
                    "items": {
                        "type": "object"
                    }
                },
                "reasoning": {
                    "type": "object",
                    "description": "推理结果"
                }
            },
            "required": ["query"]
        }
```

**4. CitationTool**

```python
# src/agents/tools/citation_tool.py
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class CitationTool(BaseTool):
    """引用工具 - 封装CitationService"""
    
    def __init__(self):
        super().__init__(
            tool_name="citation",
            description="为答案生成引用和来源信息。输入答案和知识，返回引用列表。"
        )
        self._service = None
    
    def _get_service(self):
        """延迟初始化Service"""
        if self._service is None:
            from src.services.citation_service import CitationService
            self._service = CitationService()
        return self._service
    
    async def call(self, answer: str, knowledge: Optional[List[Dict]] = None, **kwargs) -> ToolResult:
        """
        调用引用服务
        
        Args:
            answer: 答案文本（必需）
            knowledge: 知识列表（可选）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        try:
            service = self._get_service()
            context = {
                "answer": answer,
                "knowledge": knowledge or [],
                **kwargs
            }
            
            result = await service.execute(context)
            
            return ToolResult(
                success=result.success,
                data=result.data,
                error=result.error,
                execution_time=result.processing_time
            )
        except Exception as e:
            logger.error(f"引用工具调用失败: {e}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=0.0
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "答案文本，需要生成引用"
                },
                "knowledge": {
                    "type": "array",
                    "description": "知识列表，用于生成引用",
                    "items": {
                        "type": "object"
                    }
                }
            },
            "required": ["answer"]
        }
```

---

### 阶段3: 改造核心系统（P0 - 立即）

#### 步骤3.1: 改造UnifiedResearchSystem为标准Agent

```python
# src/unified_research_system.py
class UnifiedResearchSystem:
    """统一研究系统 - 标准Agent实现"""
    
    def __init__(self, max_concurrent_queries: int = 3):
        # ... 原有初始化代码 ...
        
        # Agent状态
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.actions: List[Action] = []
        
        # 工具注册表
        from src.agents.tools.tool_registry import get_tool_registry
        self.tool_registry = get_tool_registry()
        
        # LLM客户端（用于思考）
        from src.core.llm_integration import LLMIntegration
        self.llm_client = LLMIntegration(...)
    
    async def _register_tools(self):
        """注册所有工具"""
        # 注册Agent Tools
        from src.agents.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool
        from src.agents.tools.reasoning_tool import ReasoningTool
        from src.agents.tools.answer_generation_tool import AnswerGenerationTool
        from src.agents.tools.citation_tool import CitationTool
        
        self.tool_registry.register_tool(KnowledgeRetrievalTool(), {"category": "agent"})
        self.tool_registry.register_tool(ReasoningTool(), {"category": "agent"})
        self.tool_registry.register_tool(AnswerGenerationTool(), {"category": "agent"})
        self.tool_registry.register_tool(CitationTool(), {"category": "agent"})
        
        # 注册Utility Tools
        from src.agents.tools.rag_tool import RAGTool
        from src.agents.tools.search_tool import SearchTool
        from src.agents.tools.calculator_tool import CalculatorTool
        
        self.tool_registry.register_tool(RAGTool(), {"category": "utility"})
        self.tool_registry.register_tool(SearchTool(), {"category": "utility"})
        self.tool_registry.register_tool(CalculatorTool(), {"category": "utility"})
    
    async def execute_research(self, request: ResearchRequest) -> ResearchResult:
        """执行研究任务 - 标准Agent循环"""
        query = request.query
        self.observations = []
        self.thoughts = []
        self.actions = []
        
        # Agent循环
        iteration = 0
        max_iterations = 10
        task_complete = False
        
        while iteration < max_iterations and not task_complete:
            # 1. 思考
            thought = await self._think(query, self.observations, self.thoughts)
            self.thoughts.append(thought)
            
            # 2. 规划行动
            action = await self._plan_action(thought, query, self.observations)
            if not action or not action.tool_name:
                break
            
            self.actions.append(action)
            
            # 3. 执行工具
            observation = await self._execute_tool(action)
            self.observations.append(observation)
            
            # 4. 判断是否完成
            task_complete = self._is_task_complete(thought, self.observations)
            
            iteration += 1
        
        # 5. 生成最终结果
        return self._generate_result(self.observations, self.thoughts, self.actions)
    
    async def _think(self, query: str, observations: List[Dict], thoughts: List[str]) -> str:
        """思考阶段 - 使用LLM分析当前状态"""
        # 构建思考提示词
        prompt = self._build_think_prompt(query, observations, thoughts)
        
        # 调用LLM
        response = await self.llm_client._call_llm(prompt)
        
        return response
    
    async def _plan_action(self, thought: str, query: str, observations: List[Dict]) -> Action:
        """规划行动阶段 - 使用LLM决定调用哪个工具"""
        # 获取可用工具列表
        available_tools = self.tool_registry.list_tools()
        tool_descriptions = self._get_tool_descriptions(available_tools)
        
        # 构建行动规划提示词
        prompt = self._build_plan_action_prompt(thought, query, observations, tool_descriptions)
        
        # 调用LLM
        response = await self.llm_client._call_llm(prompt)
        
        # 解析响应，提取工具名称和参数
        action = self._parse_action_response(response)
        
        return action
    
    async def _execute_tool(self, action: Action) -> Dict[str, Any]:
        """执行工具阶段"""
        tool = self.tool_registry.get_tool(action.tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"工具 {action.tool_name} 不存在"
            }
        
        # 调用工具
        result = await tool.call(**action.params)
        
        return {
            "success": result.success,
            "tool_name": action.tool_name,
            "data": result.data,
            "error": result.error
        }
    
    def _is_task_complete(self, thought: str, observations: List[Dict]) -> bool:
        """判断任务是否完成"""
        # 检查是否有最终答案
        for obs in observations:
            if obs.get("tool_name") == "answer_generation" and obs.get("success"):
                answer = obs.get("data", {}).get("answer", "")
                if answer and len(answer) > 0:
                    return True
        
        return False
    
    def _generate_result(self, observations: List[Dict], thoughts: List[str], 
                        actions: List[Action]) -> ResearchResult:
        """生成最终结果"""
        # 从观察中提取答案
        answer = ""
        knowledge = []
        reasoning = None
        citations = []
        
        for obs in observations:
            if obs.get("tool_name") == "answer_generation" and obs.get("success"):
                answer = obs.get("data", {}).get("answer", "")
            elif obs.get("tool_name") == "knowledge_retrieval" and obs.get("success"):
                knowledge.extend(obs.get("data", {}).get("sources", []))
            elif obs.get("tool_name") == "reasoning" and obs.get("success"):
                reasoning = obs.get("data", {})
            elif obs.get("tool_name") == "citation" and obs.get("success"):
                citations.extend(obs.get("data", {}).get("citations", []))
        
        return ResearchResult(
            query=...,  # 从上下文获取
            success=bool(answer),
            answer=answer,
            knowledge=knowledge,
            reasoning=reasoning,
            citations=citations,
            ...
        )
```

---

### 阶段4: 更新导入和引用（P1 - 后续）

#### 步骤4.1: 更新导入语句

**策略**: 使用别名，逐步迁移

```python
# 新代码使用新名称
from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

# 旧代码继续使用旧名称（通过别名）
from src.agents.enhanced_knowledge_retrieval_agent import EnhancedKnowledgeRetrievalAgent
# 实际导入的是KnowledgeRetrievalService
```

#### 步骤4.2: 更新UnifiedResearchSystem中的引用

```python
# 旧代码
from src.agents.enhanced_knowledge_retrieval_agent import EnhancedKnowledgeRetrievalAgent
self._knowledge_agent = EnhancedKnowledgeRetrievalAgent()

# 新代码
from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
# 但通过工具使用，不直接使用Service
```

---

## 📊 文件结构

### 重构后的目录结构

```
src/
├── services/                          # 新增：服务目录
│   ├── __init__.py
│   ├── knowledge_retrieval_service.py # 从EnhancedKnowledgeRetrievalAgent迁移
│   ├── reasoning_service.py           # 从EnhancedReasoningAgent迁移
│   ├── answer_generation_service.py   # 从EnhancedAnswerGenerationAgent迁移
│   └── citation_service.py            # 从EnhancedCitationAgent迁移
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                  # 保留
│   ├── react_agent.py                 # 保留（真正的Agent）
│   ├── enhanced_knowledge_retrieval_agent.py  # 保留为别名（废弃）
│   ├── enhanced_reasoning_agent.py            # 保留为别名（废弃）
│   ├── enhanced_answer_generation_agent.py    # 保留为别名（废弃）
│   ├── enhanced_citation_agent.py             # 保留为别名（废弃）
│   └── tools/
│       ├── __init__.py
│       ├── base_tool.py
│       ├── knowledge_retrieval_tool.py  # 新增
│       ├── reasoning_tool.py            # 新增
│       ├── answer_generation_tool.py    # 新增
│       ├── citation_tool.py             # 新增
│       ├── rag_tool.py                  # 保留
│       ├── search_tool.py               # 保留
│       └── calculator_tool.py           # 保留
└── unified_research_system.py          # 改造为标准Agent
```

---

## 🔄 迁移计划

### 阶段1: 创建Service类（Week 1）

- [ ] 创建`src/services/`目录
- [ ] 创建`KnowledgeRetrievalService`（复制并重命名）
- [ ] 创建`ReasoningService`（复制并重命名）
- [ ] 创建`AnswerGenerationService`（复制并重命名）
- [ ] 创建`CitationService`（复制并重命名）
- [ ] 在原Agent文件中添加别名（向后兼容）

### 阶段2: 创建工具（Week 1）

- [ ] 创建`KnowledgeRetrievalTool`
- [ ] 创建`ReasoningTool`
- [ ] 创建`AnswerGenerationTool`
- [ ] 创建`CitationTool`
- [ ] 更新`tools/__init__.py`

### 阶段3: 改造核心系统（Week 2）

- [ ] 改造`UnifiedResearchSystem`为标准Agent
- [ ] 实现Agent循环（`_think`, `_plan_action`, `_execute_tool`）
- [ ] 注册所有工具
- [ ] 实现结果生成逻辑

### 阶段4: 测试和验证（Week 2-3）

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 向后兼容性测试

### 阶段5: 迁移现有代码（Week 3-4）

- [ ] 识别所有使用旧Agent的代码
- [ ] 逐步迁移到使用工具
- [ ] 更新文档

### 阶段6: 清理（Week 4+）

- [ ] 移除废弃的Agent类（可选）
- [ ] 更新所有文档
- [ ] 代码审查

---

## 📋 命名规范

### Agent命名

- ✅ 真正的Agent: `*Agent`（如`ReActAgent`）
- ✅ 核心系统: `UnifiedResearchSystem`（作为Agent使用）

### Service命名

- ✅ 服务组件: `*Service`（如`KnowledgeRetrievalService`）

### Tool命名

- ✅ 工具: `*Tool`（如`KnowledgeRetrievalTool`）

### 废弃命名

- ⚠️ 旧Agent类: `Enhanced*Agent`（保留为别名，标记为废弃）

---

## 🎯 总结

### 核心改进

1. ✅ **核心系统是标准Agent** - `UnifiedResearchSystem`实现Agent循环
2. ✅ **服务组件重命名** - 避免命名混淆
3. ✅ **封装为工具** - 统一接口，便于管理
4. ✅ **向后兼容** - 逐步迁移，不破坏现有功能

### 实施优先级

1. **P0（立即）**: 创建Service类和工具
2. **P0（立即）**: 改造核心系统为Agent
3. **P1（后续）**: 迁移现有代码
4. **P2（未来）**: 清理和优化

---

**方案完成时间**: 2025-11-30

