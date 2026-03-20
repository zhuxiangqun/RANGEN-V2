# RANGEN V2 优化学习笔记

## 统一 Agent 接口决策

### 决策日期
2026-03-20

### 问题
两个 `IAgent` 接口冲突：
1. `interfaces/agent.py`: `execute(inputs, context) -> AgentResult`
2. `interfaces/core_interfaces.py`: `process(query, context) -> Dict`, `is_enabled()`

### 选择方案
**统一接口方案**

### 实施内容

#### 1. 创建统一接口
- **文件**: `src/interfaces/unified_agent.py`
- **核心组件**:
  - `UnifiedAgentConfig`: 合并配置（包含 agent_id）
  - `UnifiedAgentResult`: 合并结果（置信度、引用、证据）
  - `IAgent`: 统一抽象接口
    - `agent_id` 属性
    - `is_enabled()` 方法
    - `execute(query, context)` 抽象方法
    - `process(query, context)` 别名
    - `enable()/disable()` 工具方法

#### 2. 保留向后兼容
- `interfaces/agent.py`: 添加 DeprecationWarning
- `interfaces/core_interfaces.py`: 添加 DeprecationWarning
- 现有 8 个 Agent 实现无需修改

#### 3. 统一导出
- `interfaces/__init__.py`: 优先导出统一接口
- 建议: `from src.interfaces import IAgent` (推荐)

### 迁移指南
```python
# 旧 (已弃用)
from src.interfaces.agent import IAgent

# 新 (推荐)
from src.interfaces.unified_agent import IAgent
# 或
from src.interfaces import IAgent
```

### 验证结果
- ✅ 统一接口功能测试通过
- ✅ 向后兼容性测试通过
- ✅ 弃用警告正常显示
- ✅ 现有 Agent 实现正常（CitationAgent, ValidationAgent, ReasoningAgent）

### 技术细节
- Pydantic v2 兼容性: 使用 `model_config = ConfigDict()`
- 枚举序列化: `use_enum_values=True`
- 异步支持: `async def execute()` / `await`

### 后续建议
- 新 Agent 使用统一接口
- 现有 Agent 逐步迁移（可选）
- 更新文档说明
