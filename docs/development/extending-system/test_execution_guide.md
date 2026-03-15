# 测试执行指南

> **创建日期**：2025-12-28
> **目的**：指导如何运行新创建的集成测试和性能基准测试

## 📋 测试文件

### 1. 集成测试
**文件**：`tests/test_langgraph_integration.py`

**测试内容**：
- 简单查询路径（端到端）
- 复杂查询路径（端到端）
- 多查询场景
- 并发查询场景
- 错误恢复机制
- 检查点恢复
- 状态一致性

### 2. 性能基准测试
**文件**：`tests/test_langgraph_performance_benchmark.py`

**测试内容**：
- 简单查询性能
- 复杂查询性能
- 缓存性能（第一次 vs 第二次）
- 节点性能分解
- 并发性能

## 🚀 运行测试

### 运行集成测试

```bash
# 运行所有集成测试
pytest tests/test_langgraph_integration.py -v

# 运行特定测试
pytest tests/test_langgraph_integration.py::TestLangGraphIntegration::test_simple_query_path -v

# 运行并显示详细输出
pytest tests/test_langgraph_integration.py -v -s
```

### 运行性能基准测试

```bash
# 运行所有性能基准测试
pytest tests/test_langgraph_performance_benchmark.py -v

# 运行特定测试
pytest tests/test_langgraph_performance_benchmark.py::TestLangGraphPerformanceBenchmark::test_cache_performance -v

# 运行并显示详细输出
pytest tests/test_langgraph_performance_benchmark.py -v -s
```

### 运行所有测试

```bash
# 运行所有测试（包括集成测试和性能基准测试）
pytest tests/test_langgraph_integration.py tests/test_langgraph_performance_benchmark.py -v
```

## 📊 预期结果

### 集成测试预期结果

- ✅ 所有测试应该通过
- ✅ 简单查询路径应该在几秒内完成
- ✅ 复杂查询路径应该在合理时间内完成（< 5分钟）
- ✅ 并发查询应该成功执行
- ✅ 错误恢复机制应该正确处理错误
- ✅ 检查点恢复应该正常工作

### 性能基准测试预期结果

- ✅ 简单查询平均执行时间 < 60秒
- ✅ 复杂查询平均执行时间 < 300秒
- ✅ 缓存应该提供显著的速度提升（> 10x）
- ✅ 节点性能分解应该显示各节点执行时间
- ✅ 并发性能应该优于顺序执行

## 📝 注意事项

1. **API 密钥**：确保设置了 `DEEPSEEK_API_KEY` 环境变量
2. **网络连接**：测试需要网络连接访问 API
3. **执行时间**：性能测试可能需要较长时间，请耐心等待
4. **资源使用**：性能测试会监控内存和 CPU 使用情况

## 🔍 故障排除

### 测试失败

如果测试失败，检查：
1. API 密钥是否正确设置
2. 网络连接是否正常
3. 查看详细错误信息：`pytest tests/test_langgraph_integration.py -v -s`

### 性能测试异常

如果性能测试显示异常结果：
1. 检查系统资源使用情况
2. 检查 API 响应时间
3. 查看节点执行时间分解

## 📚 相关文档

- [完成总结](./completion_summary.md)
- [完成计划](./completion_plan.md)
- [测试工具使用指南](../../tests/README_TEST_TOOLS.md)

