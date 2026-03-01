# Pytest 测试修复说明

> **修复日期**：2025-12-28
> **问题**：异步 fixture 和超时处理

## 🔧 修复内容

### 1. 异步 Fixture 修复

**问题**：
- pytest-asyncio 在严格模式下，异步 fixture 必须使用 `@pytest_asyncio.fixture` 而不是 `@pytest.fixture`
- 错误信息：`pytest.PytestRemovedIn9Warning: 'test_xxx' requested an async fixture 'system', with no plugin or hook that handled it.`

**修复**：
- 将所有异步 fixture 从 `@pytest.fixture` 改为 `@pytest_asyncio.fixture`
- 添加 `import pytest_asyncio`

**影响的文件**：
- `tests/test_langgraph_integration.py`
- `tests/test_langgraph_performance_benchmark.py`
- `tests/test_orchestration_tracking.py`

### 2. 超时处理

**问题**：
- 测试可能因为 LLM API 调用而长时间运行
- 没有超时保护，测试可能无限等待

**修复**：
- 使用 `asyncio.wait_for` 为每个测试添加超时
- 简单查询：5分钟超时
- 复杂查询：10分钟超时
- 多查询/并发：根据查询数量调整超时

**示例**：
```python
result = await asyncio.wait_for(
    workflow.execute(query=query),
    timeout=300.0  # 5分钟超时
)
```

### 3. 日志输出改进

**问题**：
- 测试执行时没有足够的日志输出，难以了解进度

**修复**：
- 添加日志配置
- 在关键步骤添加日志输出
- 显示查询执行进度

**示例**：
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger.info(f"🔍 开始执行查询: {query}")
```

## 📝 测试文件修改详情

### `tests/test_langgraph_integration.py`

1. **Fixture 修复**：
   - `@pytest.fixture` → `@pytest_asyncio.fixture` (system, workflow)

2. **超时添加**：
   - `test_simple_query_path`: 5分钟超时
   - `test_complex_query_path`: 10分钟超时
   - `test_multiple_queries`: 每个查询5分钟超时
   - `test_concurrent_queries`: 10分钟超时（并发）
   - `test_error_recovery`: 5分钟超时
   - `test_checkpoint_recovery`: 每次执行5分钟超时
   - `test_state_consistency`: 5分钟超时

3. **日志改进**：
   - 添加日志配置
   - 在查询执行前添加日志

### `tests/test_langgraph_performance_benchmark.py`

1. **Fixture 修复**：
   - `@pytest.fixture` → `@pytest_asyncio.fixture` (system, workflow)

2. **超时添加**：
   - 所有测试方法都添加了超时保护

3. **日志改进**：
   - 添加日志配置
   - 显示查询执行进度

### `tests/test_orchestration_tracking.py`

1. **Fixture 修复**：
   - `@pytest.fixture` → `@pytest_asyncio.fixture` (system)

2. **日志改进**：
   - 添加日志配置

## ✅ 验证

修复后，测试应该可以正常运行：

```bash
# 运行集成测试
pytest tests/test_langgraph_integration.py -v -s

# 运行性能基准测试
pytest tests/test_langgraph_performance_benchmark.py -v -s

# 运行编排追踪验证测试
pytest tests/test_orchestration_tracking.py -v -s
```

**注意**：`-s` 参数用于显示日志输出

## 📚 相关文档

- [Pytest 安装指南](../../docs/installation/pytest_installation.md)
- [测试执行指南](./test_execution_guide.md)

