# 测试运行问题帮助

## 🔍 如何确认测试是否在运行

### 方法1: 使用简单检查脚本

```bash
# 运行简单检查脚本
python tests/simple_check_tests.py

# 或使用shell脚本
bash tests/find_test_process.sh
```

### 方法2: 手动检查

```bash
# 查找Python测试进程
ps aux | grep python | grep -E "test|run_optimization"

# 或查看所有Python进程
ps aux | grep python
```

### 方法3: 查看终端输出

如果测试在另一个终端窗口运行，请：
1. 切换到运行测试的终端窗口
2. 查看最新的输出
3. 检查是否有错误信息

## ⚠️ 如果测试卡住

### 立即操作

1. **查看测试输出**:
   - 切换到运行测试的终端
   - 查看最后几行输出
   - 检查是否有错误

2. **检查测试进度**:
   - 查看日志中是否有 "测试X" 的输出
   - 检查是否卡在某个特定测试

3. **中断测试**:
   ```bash
   # 按 Ctrl+C 中断
   # 或查找并终止进程
   pkill -f run_optimization_tests
   ```

## 📋 请提供的信息

如果测试出现问题，请提供：

1. **测试启动命令**:
   ```bash
   # 您是如何启动测试的？
   python tests/run_optimization_tests.py
   # 或其他命令？
   ```

2. **测试输出**:
   - 复制最后50行输出
   - 包含错误信息

3. **测试运行时间**:
   - 测试运行了多长时间？
   - 是否超过预期时间？

4. **当前状态**:
   - 测试是否还在运行？
   - 是否有输出？
   - 是否卡在某个测试？

## 🔧 常见情况

### 情况1: 测试在运行但没有输出

**可能原因**:
- 测试正在执行LLM API调用（需要时间）
- 测试卡在某个节点

**处理**:
- 等待一段时间（每个测试可能需要几分钟）
- 检查网络连接
- 查看日志文件

### 情况2: 测试输出错误

**处理**:
- 复制完整错误堆栈
- 运行单个测试定位问题: `python tests/run_single_test.py <测试编号>`

### 情况3: 测试无限运行

**处理**:
- 使用带超时的测试运行器: `python tests/run_tests_with_timeout.py`
- 如果超时，查看是哪个测试超时

## 💡 建议

1. **使用改进的测试运行器**:
   ```bash
   python tests/run_tests_with_timeout.py
   ```
   这会为每个测试添加超时保护

2. **运行单个测试**:
   ```bash
   python tests/run_single_test.py 1
   ```
   快速定位问题

3. **查看测试文档**:
   - `tests/README_TEST_TOOLS.md` - 工具使用指南
   - `docs/implementation/test_troubleshooting_guide.md` - 排查指南

