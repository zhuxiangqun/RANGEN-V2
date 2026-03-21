# ReActAgent逐步替换预览报告

## 📋 预览结果

**时间**: 2026-01-01  
**模式**: DRY RUN (预览模式)  
**状态**: ✅ 预览成功

## 📊 替换统计

- **处理文件数**: 3
- **将修改文件数**: 3
- **找到导入语句**: 7个
- **找到实例化语句**: 4个

## 📝 详细更改

### 1. src/unified_research_system.py

**找到的导入语句**:
- 行 932: `from src.agents.react_agent import ReActAgent`
- 行 1029: `from src.agents.langgraph_react_agent import LangGraphReActAgent` (不会替换)

**找到的实例化语句**:
- 行 934: `self._react_agent = ReActAgent()`

**将进行的更改**:

**更改前**:
```python
from src.agents.react_agent import ReActAgent
...
self._react_agent = ReActAgent()
```

**更改后**:
```python
from src.agents.react_agent_wrapper import ReActAgentWrapper as ReActAgent
...
self._react_agent = ReActAgentWrapper(enable_gradual_replacement=True)
```

---

### 2. src/core/langgraph_agent_nodes.py

**找到的导入语句**:
- 行 59: `from src.agents.langgraph_react_agent import LangGraphReActAgent` (不会替换)
- 行 846: `from src.agents.react_agent import ReActAgent`
- 行 906: `from src.agents.react_agent import ReActAgent`
- 行 1083: `from src.agents.react_agent import ReActAgent`

**找到的实例化语句**:
- 行 847: `react_agent = ReActAgent()`
- 行 907: `react_agent = ReActAgent()`
- 行 1084: `react_agent = ReActAgent()`

**将进行的更改**:

**更改前**:
```python
from src.agents.react_agent import ReActAgent
...
react_agent = ReActAgent()
```

**更改后**:
```python
from src.agents.react_agent_wrapper import ReActAgentWrapper as ReActAgent
...
react_agent = ReActAgentWrapper(enable_gradual_replacement=True)
```

---

### 3. src/core/intelligent_orchestrator.py

**找到的导入语句**:
- 行 12: `from src.agents.react_agent import ReActAgent`

**找到的实例化语句**:
- 无（可能在其他地方实例化）

**将进行的更改**:

**更改前**:
```python
from src.agents.react_agent import ReActAgent
```

**更改后**:
```python
from src.agents.react_agent_wrapper import ReActAgentWrapper as ReActAgent
```

---

## ✅ 安全保证

1. **只替换ReActAgent**: LangGraphReActAgent不会被替换
2. **自动备份**: 应用更改时会自动创建 `.backup` 备份文件
3. **向后兼容**: 包装器实现相同的接口，代码无需其他修改
4. **可回滚**: 如有问题，可以使用备份文件快速回滚

## 🎯 替换效果

替换后，所有ReActAgent的调用将：
1. 使用ReActAgentWrapper包装器
2. 默认启用逐步替换（初始比例1%）
3. 逐步将请求从ReActAgent迁移到ReasoningExpert
4. 自动监控成功率并调整替换比例

## 📊 预期影响

- **初始替换比例**: 1%（99%的请求仍使用ReActAgent）
- **逐步增加**: 当成功率≥95%且调用数≥100时，每次增加10%
- **完成时间**: 预计需要数天到数周，取决于实际调用量

## 🚀 下一步

1. **应用更改**: 运行 `python3 scripts/apply_react_agent_replacement.py --dry-run=false`
2. **启动监控**: 运行 `bash scripts/start_react_agent_replacement.sh`
3. **监控进度**: 使用 `python3 scripts/check_replacement_stats.py --agent ReActAgent`

---

*预览时间: 2026-01-01*

