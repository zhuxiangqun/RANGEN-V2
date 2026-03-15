# 测试问题排查指南

## 🔍 问题诊断

### 常见问题

1. **测试卡在LLM API调用**
   - **症状**: 测试长时间无响应，日志显示正在调用API
   - **原因**: API超时、网络问题、API限流
   - **解决**: 
     - 检查网络连接
     - 检查API密钥
     - 增加超时时间
     - 使用模拟数据

2. **测试无限等待**
   - **症状**: 测试进程一直运行，无任何输出
   - **原因**: 缺少超时机制、死循环、资源竞争
   - **解决**:
     - 添加超时机制
     - 检查重试逻辑
     - 检查资源锁

3. **测试内存泄漏**
   - **症状**: 内存使用持续增长
   - **原因**: 未释放资源、缓存过大
   - **解决**:
     - 检查资源释放
     - 限制缓存大小

4. **数据库锁定**
   - **症状**: 测试报错 "database is locked"
   - **原因**: SQLite连接未关闭
   - **解决**:
     - 确保连接关闭
     - 使用临时数据库

## 🛠️ 快速修复

### 1. 中断卡住的测试

```bash
# 查找测试进程
ps aux | grep run_optimization_tests

# 中断测试进程
pkill -f run_optimization_tests

# 或使用 Ctrl+C
```

### 2. 运行快速测试

```bash
# 只测试核心功能，不执行实际查询
python tests/quick_test.py
```

### 3. 运行单个测试

```bash
# 只运行测试1（持久化检查点）
python tests/run_single_test.py 1

# 只运行测试2（检查点恢复）
python tests/run_single_test.py 2
```

### 4. 清理临时文件

```bash
# 清理测试生成的临时文件
rm -rf /tmp/langgraph_test_*
rm -f checkpoint*.sqlite
```

## 📋 测试优化建议

### 1. 添加超时机制

修改 `tests/run_optimization_tests.py`:

```python
import asyncio
from tests.timeout_wrapper import run_with_timeout

async def run_test(self, test_name, test_func):
    """运行测试（带超时）"""
    try:
        await run_with_timeout(test_func(), timeout_seconds=300)  # 5分钟超时
        # ...
    except TimeoutError as e:
        logger.error(f"⏱️ 测试超时: {test_name}")
        # ...
```

### 2. 使用模拟数据

创建 `tests/mock_llm.py`:

```python
class MockLLM:
    """模拟LLM，避免实际API调用"""
    async def generate(self, prompt):
        return "Mock response"
```

### 3. 减少测试范围

修改 `tests/run_optimization_tests.py`:

```python
# 只运行前3个测试
tests = tests[:3]  # 只运行前3个
```

## 🔧 诊断工具

运行诊断工具:

```bash
python tests/test_diagnostic_tool.py
```

该工具会:
- 检查是否有测试进程在运行
- 分析常见问题
- 提供修复建议
- 创建诊断工具

## 📝 日志分析

### 查看测试日志

```bash
# 查看最近的日志
tail -f logs/test.log

# 搜索错误
grep -i error logs/test.log

# 搜索超时
grep -i timeout logs/test.log
```

### 常见错误信息

1. **TimeoutError**: 操作超时
   - 增加超时时间
   - 检查网络连接

2. **ConnectionError**: 连接失败
   - 检查网络
   - 检查API服务状态

3. **RateLimitError**: API限流
   - 等待一段时间后重试
   - 减少并发请求

4. **DatabaseLockedError**: 数据库锁定
   - 关闭其他连接
   - 使用临时数据库

## 🚀 最佳实践

1. **分阶段测试**: 不要一次性运行所有测试
2. **使用超时**: 为每个测试设置超时时间
3. **模拟外部依赖**: 使用Mock避免实际API调用
4. **清理资源**: 确保测试后清理临时文件
5. **记录日志**: 详细记录测试过程，便于排查

## 📞 获取帮助

如果问题仍然存在:

1. 运行诊断工具: `python tests/test_diagnostic_tool.py`
2. 查看错误日志: 检查最近的日志文件
3. 检查系统资源: CPU、内存、磁盘空间
4. 检查网络连接: API服务是否可用

