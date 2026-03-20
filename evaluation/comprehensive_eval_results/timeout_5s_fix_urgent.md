# 5秒超时问题紧急修复说明

**修复时间**: 2025-11-16

---

## ⚠️ 重要提示

**如果仍然看到5秒超时错误，说明进程还在使用旧代码！**

**必须重启知识图谱构建进程，新代码才会生效！**

---

## 🔍 问题确认

日志显示：
```
ReadTimeoutError("HTTPSConnectionPool(host='api.deepseek.com', port=443): Read timed out. (read timeout=5.0)")
⚠️ 推理模型在5.0秒时超时，但超时设置是240秒。这可能是外层超时或其他问题，尝试重试（attempt 1/3）
```

这说明：
1. ✅ 代码已经检测到问题（实际超时5秒 vs 设置240秒）
2. ❌ 但timeout参数仍然没有正确传递到底层

---

## ✅ 已实施的修复

### 修复1: 从`session.post()`改为`requests.post()`

**位置**: `src/core/llm_integration.py` 行628-638

**原因**: `session.post()`可能没有正确传递timeout参数，直接使用`requests.post()`可以避免这个问题。

### 修复2: 确保timeout参数是float类型

**位置**: `src/core/llm_integration.py` 行636

**修改**:
```python
# 修改前
timeout=timeout_tuple

# 修改后
timeout=(float(connect_timeout), float(read_timeout))
```

**原因**: 确保timeout参数是明确的float类型，避免类型转换问题。

---

## 🚀 必须执行的操作

### 步骤1: 停止当前进程

如果知识图谱构建进程正在运行：
```bash
# 找到进程ID
ps aux | grep build_knowledge_graph

# 停止进程（使用Ctrl+C或kill命令）
kill <PID>
```

### 步骤2: 确认代码已更新

检查代码是否包含修复：
```bash
grep -n "timeout=(float(connect_timeout), float(read_timeout))" src/core/llm_integration.py
```

应该看到类似输出：
```
636:                    timeout=(float(connect_timeout), float(read_timeout)),
```

### 步骤3: 重新启动进程

```bash
./build_knowledge_graph.sh
```

### 步骤4: 验证修复

观察日志，应该看到：
- ✅ `使用超时设置: connect=5.0s, read=240.0s`
- ✅ 不再出现`read timeout=5.0`的错误
- ✅ 如果出现超时，应该是接近240秒的超时

---

## 🔍 如果问题仍然存在

### 检查1: 确认进程使用的是新代码

```bash
# 检查Python进程加载的模块
ps aux | grep python | grep build_knowledge_graph
```

### 检查2: 检查是否有其他timeout设置

```bash
# 搜索所有可能的timeout设置
grep -r "timeout.*5" src/ --include="*.py"
grep -r "5.*timeout" src/ --include="*.py"
```

### 检查3: 检查urllib3版本

```bash
python3 -c "import urllib3; print(urllib3.__version__)"
```

如果版本过旧，可能需要升级：
```bash
pip install --upgrade urllib3 requests
```

### 检查4: 检查环境变量

```bash
# 检查是否有环境变量覆盖了timeout设置
env | grep -i timeout
```

---

## 📊 预期结果

修复后，应该看到：

1. **正常情况**:
   - API调用成功，没有超时错误
   - 日志显示正确的超时设置

2. **如果真的超时**:
   - 超时时间应该是接近240秒（或配置的值）
   - 不应该再出现5秒超时

3. **重试逻辑**:
   - 如果出现接近240秒的超时，会重试
   - 如果出现5秒超时，会检测到问题并重试

---

## ⚠️ 注意事项

1. **必须重启进程**：Python进程会缓存已加载的模块，必须重启才能加载新代码。

2. **检查日志级别**：确保日志级别设置为DEBUG，才能看到详细的超时设置信息。

3. **网络问题**：如果网络本身有问题（如防火墙、代理），即使修复了timeout设置，仍然可能出现连接问题。

---

## 📝 相关文件

- `src/core/llm_integration.py`: 主要修复位置
- `comprehensive_eval_results/timeout_5s_fix_final.md`: 详细修复说明
- `comprehensive_eval_results/timeout_and_truncation_fix_summary.md`: 之前的修复总结

