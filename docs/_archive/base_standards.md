# RANGEN 基盘标准文档

> 基盘核心接口标准定义，用于确保所有组件遵循一致的协议。

## 目录

1. [接口标准](#1-接口标准)
2. [维度标准](#2-维度标准)
3. [适配器层](#3-适配器层)
4. [如何吸收新标准](#4-如何吸收新标准)

---

## 1. 接口标准

### 文件位置

```
src/interfaces/
├── __init__.py      # 统一导出
├── agent.py         # IAgent
├── tool.py          # ITool
├── skill.py         # ISkill
├── coordinator.py   # ICoordinator
└── adapter.py       # IAdapter
```

### 1.1 Agent 标准 (IAgent)

**文件**: `src/interfaces/agent.py`

```python
class IAgent(ABC):
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        pass
```

**配套类**:
- `AgentConfig` - Agent 配置
- `AgentResult` - 执行结果
- `ExecutionStatus` - 状态枚举 (PENDING/RUNNING/COMPLETED/FAILED)

---

### 1.2 Tool 标准 (ITool)

**文件**: `src/interfaces/tool.py`

```python
class ITool(ABC):
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
```

**配套类**:
- `ToolConfig` - Tool 配置
- `ToolResult` - 执行结果
- `ToolCategory` - 类别枚举 (RETRIEVAL/COMPUTE/UTILITY/API)

---

### 1.3 Skill 标准 (ISkill)

**文件**: `src/interfaces/skill.py`

```python
class ISkill(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def version(self) -> str: ...
    
    @property
    def description(self) -> str: ...
    
    @property
    def category(self) -> SkillCategory: ...
    
    @property
    def scope(self) -> SkillScope: ...
    
    @property
    def tools(self) -> Dict[str, Any]: ...
    
    @property
    def prompt_template(self) -> str: ...
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        pass
    
    @abstractmethod
    def get_schemas(self) -> List[ToolSchema]:
        pass
```

**配套类**:
- `SkillMetadata` - 元数据 (name/version/description/author/category/tags/scope/dependencies)
- `SkillResult` - 执行结果
- `SkillScope` - 作用域 (BUNDLED/MANAGED/WORKSPACE)
- `SkillCategory` - 类别 (CODE/DOCUMENT/ANALYSIS/WRITING/REASONING/RETRIEVAL/TOOL/WORKFLOW/GENERAL)
- `ToolSchema` - 工具 Schema

---

### 1.4 Coordinator 标准 (ICoordinator)

**文件**: `src/interfaces/coordinator.py`

```python
class ICoordinator(ABC):
    @abstractmethod
    async def run_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        pass
```

---

## 2. 维度标准

### 文件位置

```
src/ui/dimension_mapping.py
```

### 2.1 维度定义

| 实体类型 | 维度文件 | 典型维度 |
|----------|---------|---------|
| Tool | `TOOL_CATEGORY_DIMENSIONS` | accuracy, precision, recall, latency |
| Agent | `AGENT_CAPABILITY_DIMENSIONS` | reasoning_depth, logic_coherence, accuracy |
| Skill | `SKILL_TRIGGER_DIMENSIONS` | code_quality, security, best_practices |
| Team | `TEAM_TYPE_DIMENSIONS` | coverage, design_quality, coordination |
| Workflow | `WORKFLOW_TYPE_DIMENSIONS` | node_execution, flow_control |
| Service | `SERVICE_TYPE_DIMENSIONS` | availability, response_quality, latency |
| System Module | `SYSTEM_MODULE_DIMENSIONS` | 22 个核心模块维度 |

### 2.2 维度结构

```python
{
    "dimension_key": {
        "name": "维度名称",
        "weight": 0.25,           # 权重
        "test": "测试说明",
        "test_cases": [           # 可选：测试用例
            {"input": "...", "expected": "..."}
        ]
    }
}
```

---

## 3. 适配器层

### 文件位置

```
src/interfaces/adapter.py
```

### 3.1 核心类

```python
class IAdapter(ABC):
    @property
    def metadata(self) -> AdapterMetadata: ...
    
    @abstractmethod
    def adapt(self, source: Any) -> Any: ...
    
    @abstractmethod
    def validate(self, target: Any) -> bool: ...

class AdapterRegistry:
    def register(self, standard_name: str, version: StandardVersion, adapter_class): ...
    def get_adapter(self, standard_name: str, version: StandardVersion = StandardVersion.LATEST): ...
    def list_standards(self) -> List[str]: ...
    def list_versions(self, standard_name: str) -> List[StandardVersion]: ...

class StandardVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    LATEST = "latest"
```

### 3.2 使用方式

```python
from src.interfaces import get_adapter_registry, StandardVersion

registry = get_adapter_registry()
adapter = registry.get_adapter("agent", StandardVersion.V3)
adapted = adapter.adapt(old_implementation)
```

---

## 4. 如何吸收新标准

### 4.1 流程概览

```
新标准出现 → 创建适配器 → 注册到注册中心 → 自动兼容
```

### 4.2 步骤 1：创建适配器

新建文件: `src/interfaces/adapters/xxx_adapter.py`

```python
from src.interfaces import IAdapter, AdapterMetadata, StandardVersion

class NewStandardAdapter(IAdapter):
    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            name="new_standard_adapter",
            version=StandardVersion.V3,
            standard_name="agent",  # 或 tool, skill 等
            description="新标准适配器"
        )
    
    def adapt(self, source: Any) -> Any:
        # 转换逻辑：将新标准转为基盘标准
        return adapted_source
    
    def validate(self, target: Any) -> bool:
        # 验证是否符合基盘标准
        return hasattr(target, 'execute')
```

### 4.3 步骤 2：注册适配器

```python
from src.interfaces import get_adapter_registry, StandardVersion
from src.interfaces.adapters.new_standard_adapter import NewStandardAdapter

registry = get_adapter_registry()
registry.register("agent", StandardVersion.V3, NewStandardAdapter)
```

### 4.4 步骤 3：自动使用

基盘内部自动选择合适的适配器：

```python
adapter = get_adapter_registry().get_adapter("agent")
standard_agent = adapter.adapt(external_agent)
result = await standard_agent.execute(inputs)
```

---

## 附录：统一导入

```python
# 导入所有接口
from src.interfaces import (
    IAgent,
    ITool,
    ISkill,
    ICoordinator,
    IAdapter,
    AdapterRegistry,
    get_adapter_registry,
)

# 导入具体类
from src.interfaces import (
    AgentConfig,
    AgentResult,
    ToolConfig,
    ToolResult,
    SkillMetadata,
    SkillResult,
    SkillCategory,
    SkillScope,
    ToolSchema,
    AdapterMetadata,
    StandardVersion,
)
```

---

## 版本历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-03-15 | v1.0 | 初始版本，包含 IAgent/ITool/ISkill/ICoordinator |
| 2026-03-15 | v1.1 | 新增 IAdapter 适配器层 |
