# 5秒超时问题 - 必须重启进程！

**更新时间**: 2025-11-16 02:27

---

## ⚠️ 关键问题

**进程仍在运行旧代码！**

从检查结果看：
- **进程启动时间**: 2:21AM
- **代码最后修改时间**: 02:27
- **进程状态**: 仍在运行（PID 58662）

**Python进程会缓存已加载的模块，必须重启才能加载新代码！**

---

## ✅ 已完成的修复

### 修复1: 主请求路径使用Urllib3Timeout对象

**位置**: `src/core/llm_integration.py` 行621-635

```python
from urllib3.util import Timeout as Urllib3Timeout
urllib3_timeout = Urllib3Timeout(connect=float(connect_timeout), read=float(read_timeout))
response = requests.post(..., timeout=urllib3_timeout, ...)
```

### 修复2: SSL重试路径也使用Urllib3Timeout对象

**位置**: `src/core/llm_integration.py` 行1086-1096

```python
from urllib3.util import Timeout as Urllib3Timeout
urllib3_timeout = Urllib3Timeout(connect=float(connect_timeout), read=read_timeout)
response = requests.post(..., timeout=urllib3_timeout, ...)
```

**所有使用timeout的地方都已修复！**

---

## 🚀 快速重启方法

### 方法1: 使用重启脚本（推荐）

```bash
./restart_build_knowledge_graph.sh
```

这个脚本会：
1. 自动停止当前进程
2. 确认代码已更新
3. 重新启动进程

### 方法2: 手动重启

```bash
# 1. 停止进程
ps aux | grep build_knowledge_graph
# 找到PID后执行：
kill <PID>
# 如果进程不停止，使用强制停止：
kill -9 <PID>

# 2. 确认进程已停止
ps aux | grep build_knowledge_graph
# 应该没有输出（除了grep本身）

# 3. 确认代码已更新
grep -n "Urllib3Timeout" src/core/llm_integration.py
# 应该看到至少2处使用Urllib3Timeout

# 4. 重新启动
./build_knowledge_graph.sh
```

---

## 🔍 验证修复是否生效

重启后，观察日志应该看到：

### ✅ 正常情况

```
🔧 使用超时设置: connect=5.0s, read=240.0s
⏱️ DeepSeek API实际响应时间: XX.XX秒 (attempt 1)
```

### ❌ 如果仍然看到5秒超时

```
Read timed out. (read timeout=5.0)
⚠️ 推理模型在5.0秒时超时，但超时设置是240秒
```

**这说明进程仍然在使用旧代码！**

**解决方法**:
1. 确认进程已完全停止：`ps aux | grep build_knowledge_graph`
2. 确认代码已更新：`grep -n "Urllib3Timeout" src/core/llm_integration.py`
3. 强制停止所有相关进程：`pkill -f build_knowledge_graph`
4. 重新启动

---

## 📊 为什么必须重启？

### Python模块缓存机制

1. **首次导入**: Python加载模块并编译为字节码
2. **缓存**: 字节码缓存在内存中
3. **后续导入**: 直接使用缓存的字节码，不会重新加载文件
4. **文件修改**: 即使文件已修改，已加载的模块不会自动更新

### 解决方案

**必须重启Python进程才能重新加载模块！**

---

## 🎯 修复原理

### 为什么使用Urllib3Timeout对象？

1. **直接控制底层**: Timeout对象直接传递给urllib3，绕过了可能的中间层问题
2. **类型明确**: 明确指定connect和read超时，避免tuple可能被误解
3. **官方推荐**: 这是urllib3库推荐的方式

### 为什么之前的方法不行？

1. **tuple可能被误解**: 某些情况下，tuple可能被解释为单个超时值
2. **中间层问题**: session、HTTPAdapter等中间层可能影响timeout传递
3. **连接池复用**: 复用的连接可能使用旧的超时设置

---

## ⚠️ 重要提示

1. **必须重启进程**: 这是最关键的步骤！
2. **确认进程已停止**: 使用`ps aux | grep build_knowledge_graph`确认
3. **检查日志级别**: 确保能看到INFO级别的日志（`🔧 使用超时设置`）
4. **网络问题**: 如果网络本身有问题，即使修复了timeout设置，仍然可能出现连接问题

---

## 📝 相关文件

- `src/core/llm_integration.py`: 主要修复位置
  - 行621-635: 主请求路径
  - 行1086-1096: SSL重试路径
- `restart_build_knowledge_graph.sh`: 自动重启脚本
- `comprehensive_eval_results/timeout_5s_fix_ultimate.md`: 详细修复说明

