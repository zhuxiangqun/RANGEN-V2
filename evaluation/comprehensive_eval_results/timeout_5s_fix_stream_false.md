# 5秒超时问题 - 添加stream=False修复

**修复时间**: 2025-11-16

---

## 🔍 问题分析

重启后仍然出现5秒超时，可能的原因：

1. **流式传输问题**：如果启用了流式传输（`stream=True`），超时设置可能不被正确应用
2. **连接池复用**：复用的连接可能使用了旧的超时设置
3. **urllib3的默认行为**：即使设置了timeout参数，urllib3在某些情况下可能仍然使用默认的5秒超时

---

## ✅ 修复方案

### 核心修复：添加`stream=False`参数

**位置**: `src/core/llm_integration.py` 行645-652和1120-1127

**修改**:
```python
# 修改前
response = requests.post(
    f"{self.base_url}/chat/completions",
    headers=headers,
    json=data,
    timeout=timeout_tuple,
    verify=True
)

# 修改后
response = requests.post(
    f"{self.base_url}/chat/completions",
    headers=headers,
    json=data,
    timeout=timeout_tuple,
    verify=True,
    stream=False  # 禁用流式传输，确保超时设置生效
)
```

### 为什么这样修复？

1. **确保超时生效**：流式传输可能影响超时设置的正确应用
2. **避免连接复用**：不使用session，每次创建新连接
3. **明确控制**：显式设置`stream=False`，确保超时设置被正确应用

---

## 🚀 必须执行的操作

### 步骤1: 确认代码已更新

```bash
# 检查修复是否已应用
grep -n "stream=False" src/core/llm_integration.py
```

应该看到：
```
651:                    stream=False  # 禁用流式传输，确保超时设置生效
1126:                                stream=False  # 禁用流式传输，确保超时设置生效
```

### 步骤2: 停止当前进程

**这是最关键的一步！**

```bash
# 找到知识图谱构建进程
ps aux | grep build_knowledge_graph

# 停止进程
kill <PID>
# 如果进程不停止，使用强制停止：
kill -9 <PID>
```

### 步骤3: 确认进程已停止

```bash
# 确认没有相关进程在运行
ps aux | grep build_knowledge_graph
# 应该没有输出（除了grep本身）
```

### 步骤4: 重新启动

```bash
./build_knowledge_graph.sh
```

---

## 📊 验证修复

重启后观察日志，应该看到：
- `🔧 使用超时设置: connect=5.0s, read=240.0s`（INFO级别）
- `🔧 发送请求: url=..., timeout=(5.0, 240.0), timeout_type=<class 'tuple'>`（DEBUG级别）
- 不再出现 `read timeout=5.0` 的错误
- 如果出现超时，应该是接近 240 秒的超时，而不是 5 秒

---

## ⚠️ 如果问题仍然存在

如果重启后问题仍然存在，可能的原因：

1. **Python模块缓存**：Python可能缓存了旧的模块
   - 解决：删除`__pycache__`目录：`find . -type d -name __pycache__ -exec rm -r {} +`

2. **urllib3版本问题**：某些版本的urllib3可能有bug
   - 解决：升级urllib3：`pip install --upgrade urllib3`

3. **系统级别的超时设置**：可能有系统级别的超时设置
   - 解决：检查系统防火墙或代理设置

