# 旧系统迁移计划：Tool-based → Skill-based

## 目标

将 RANGEN 从旧系统 (Tool-based) 渐进迁移到新系统 (Skill-based + MCP协议)

## 当前状态

### 旧系统 (Tool-based)
- `BaseTool` 类 + 各种 `*Tool` (CalculatorTool, SearchTool等)
- `ToolOrchestrator` - 工具编排器
- 直接调用工具实例

### 新系统 (Skill-based)
- `Skill` + SKILL.md 定义
- `AISkillTrigger` - AI驱动触发
- `HybridToolExecutor` - MCP协议调用
- `InProcessMCPExecutor` - 进程内MCP

---

## 迁移策略：渐进式

### 原则
1. **保持兼容** - 旧代码保留，逐步弃用
2. **新代码用新系统** - 新功能只使用 Skill-based
3. **可回滚** - 任何时候可以切回旧系统

---

## 迁移步骤

### Wave 1: 基础设施 (第1步)

- [ ] 1.1 创建统一入口 `UnifiedToolExecutor`
  - 文件: `src/agents/unified_executor.py`
  - 功能: 封装 HybridToolExecutor，提供统一API
  - 兼容: 同时支持 Tool 和 Skill 模式

- [ ] 1.2 标记旧系统为 deprecated
  - 在 `BaseTool` 类添加 `@deprecated` 注释
  - 在 `ToolOrchestrator` 类添加 `@deprecated` 注释
  - 添加警告日志

- [ ] 1.3 编写基础测试
  - 文件: `tests/test_unified_executor.py`
  - 测试: 验证新旧系统返回一致结果

---

### Wave 2: 工具迁移 (第2步)

- [ ] 2.1 创建 Skill 定义 (15个工具 → 15个Skill)
  - 目录: `src/agents/skills/bundled/`
  - 命名: `calculator/`, `search/`, `rag/`, etc.
  - 每个 Skill 包含:
    - `SKILL.md` - 技能定义
    - `skill.yaml` - 元数据
    - `executor.py` - 执行逻辑

- [ ] 2.2 迁移映射表
  - 文件: `src/agents/skills/tool_to_skill_map.py`
  - 格式:
    ```python
    TOOL_TO_SKILL_MAP = {
        "calculator": "calculator-skill",
        "search": "search-skill",
        "rag": "rag-skill",
        # ...
    }
    ```

- [ ] 2.3 更新 HybridToolExecutor
  - 添加 `tool_to_skill()` 方法
  - 自动将旧工具调用转换为 Skill 调用

---

### Wave 3: 集成测试 (第3步)

- [ ] 3.1 端到端测试
  - 测试场景: 用户输入 → Skill触发 → MCP调用 → 返回结果
  - 对比: 旧系统 vs 新系统 结果一致性

- [ ] 3.2 性能测试
  - 测量: MCP协议开销 vs 直接调用
  - 优化: 如有必要添加缓存

- [ ] 3.3 兼容性测试
  - 确保现有代码不受影响

---

### Wave 4: 切换 (第4步)

- [ ] 4.1 默认使用新系统
  - 修改配置: `config/default_executor = "skill-based"`

- [ ] 4.2 更新入口点
  - 修改: `src/unified_research_system.py`
  - 使用: `UnifiedToolExecutor` 替代直接调用

- [ ] 4.3 监控日志
  - 记录: 旧系统调用次数
  - 目标: 逐步降为 0

---

### Wave 5: 清理 (第5步)

- [ ] 5.1 移除旧代码 (可选)
  - 只有在确认新系统稳定后
  - 保留至少一个版本

- [ ] 5.2 更新文档
  - 说明新架构
  - 迁移指南

---

## 文件清单

### 需要创建

| 文件 | 说明 |
|------|------|
| `src/agents/unified_executor.py` | 统一执行器入口 |
| `src/agents/skills/tool_to_skill_map.py` | 工具到Skill映射 |
| `tests/test_unified_executor.py` | 统一执行器测试 |
| `tests/test_skill_trigger.py` | Skill触发测试 |
| `tests/test_mcp_integration.py` | MCP集成测试 |

### 需要修改

| 文件 | 修改内容 |
|------|----------|
| `src/agents/tools/base_tool.py` | 添加 deprecated 标记 |
| `src/agents/tool_orchestrator.py` | 添加 deprecated 标记 |
| `src/unified_research_system.py` | 使用新系统 |

### 需要创建 Skill

| Skill | 对应旧工具 |
|-------|-----------|
| `calculator-skill` | CalculatorTool |
| `search-skill` | SearchTool |
| `rag-skill` | RAGTool |
| `knowledge-skill` | KnowledgeRetrievalTool |
| `reasoning-skill` | ReasoningTool |
| `answer-skill` | AnswerGenerationTool |
| `citation-skill` | CitationTool |
| `multimodal-skill` | MultimodalTool |
| `browser-skill` | BrowserTool |
| `file-read-skill` | FileReadHandTool |

---

## 测试计划

### 单元测试

```python
# test_unified_executor.py
def test_calculator_direct():
    """测试计算器直接调用"""
    
def test_calculator_via_mcp():
    """测试计算器通过MCP调用"""
    
def test_result_consistency():
    """验证两种方式结果一致"""
```

### 集成测试

```python
# test_skill_integration.py
async def test_skill_trigger_and_execute():
    """测试Skill触发到执行完整流程"""
    
async def test_ai_trigger():
    """测试AI触发机制"""
```

---

## 回滚方案

如果迁移出现问题:

1. **配置回滚**: 修改 `config/default_executor = "tool-based"`
2. **代码回滚**: 旧代码仍在，只是标记为 deprecated
3. **逐步切换**: 可以按工具逐个切换

---

## 成功标准

- [ ] 所有现有测试通过
- [ ] 新系统功能正常 (Skill触发 + MCP调用)
- [ ] 性能无明显下降
- [ ] 旧系统调用降为 0

---

## 预计工作量

| Wave | 任务 | 估计时间 |
|------|------|---------|
| 1 | 基础设施 | 2小时 |
| 2 | 工具迁移 | 4小时 |
| 3 | 集成测试 | 2小时 |
| 4 | 切换 | 1小时 |
| 5 | 清理 | 1小时 |
| **总计** | | **10小时** |

---

## 下一步

1. 确认计划
2. 开始 Wave 1: 基础设施
3. 运行测试验证
