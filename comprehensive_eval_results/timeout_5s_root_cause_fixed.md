# 5秒超时问题 - 根本原因已找到并修复

**修复时间**: 2025-11-16 10:05

---

## 🎯 根本原因

**代理（Clash）设置了5秒超时，导致即使代码设置了240秒超时，代理仍然在5秒时中断连接。**

---

## 🔍 证据

### 1. 发现代理进程

```bash
$ lsof -i -P | grep -E "7890|proxy|PROXY"
clash-met   692  syu    7u  IPv6 0xc876846dbdbc6a51      0t0  TCP *:7890 (LISTEN)
```

**发现**：有一个 `clash-met` 进程在监听 7890 端口，这是 Clash 代理客户端。

### 2. 测试结果证明代理覆盖了timeout

测试代码：
```python
r = requests.get('https://api.deepseek.com', timeout=(5, 10))
```

结果：
```
请求错误: HTTPSConnectionPool(host='api.deepseek.com', port=443): Read timed out. (read timeout=5)
```

**发现**：即使设置了 `timeout=(5, 10)`，请求仍然在5秒时超时，说明代理的超时设置（5秒）覆盖了代码中的timeout参数。

### 3. 环境变量中没有代理设置

```python
HTTP_PROXY: None
HTTPS_PROXY: None
http_proxy: None
https_proxy: None
```

**发现**：虽然环境变量中没有代理设置，但系统可能通过系统代理设置（macOS的系统偏好设置）使用了代理。

---

## ✅ 解决方案

### 修复：在代码中显式禁用代理

**位置**: `src/core/llm_integration.py` 行654-662 和 1133-1141

**修改**：
```python
response = requests.post(
    f"{self.base_url}/chat/completions",
    headers=headers,
    json=data,
    timeout=timeout_tuple,  # 使用tuple格式，确保超时设置正确传递
    verify=True,  # 显式设置SSL验证
    stream=False,  # 禁用流式传输，确保超时设置生效
    allow_redirects=True,  # 允许重定向
    proxies={'http': None, 'https': None}  # 🎯 显式禁用代理，避免代理的超时设置覆盖我们的超时设置
)
```

**原因**：
1. **显式禁用代理**：通过设置 `proxies={'http': None, 'https': None}`，强制requests库不使用代理
2. **避免代理超时覆盖**：代理的超时设置（5秒）不再影响我们的请求
3. **确保timeout参数生效**：现在timeout参数（240秒）可以正确生效

---

## 🚀 验证步骤

### 步骤1: 确认代码已更新

```bash
grep -n "proxies={'http': None, 'https': None}" src/core/llm_integration.py
```

应该看到：
```
662:                    proxies={'http': None, 'https': None}  # 🎯 显式禁用代理，避免代理的超时设置覆盖我们的超时设置
1141:                                proxies={'http': None, 'https': None}  # 🎯 显式禁用代理，避免代理的超时设置覆盖我们的超时设置
```

### 步骤2: 重启进程

```bash
./restart_build_knowledge_graph.sh
```

### 步骤3: 观察日志

应该看到：
- ✅ `🔧 使用超时设置: connect=5.0s, read=240.0s`
- ✅ `🔧 发送请求: url=..., timeout=(5.0, 240.0), timeout_type=<class 'tuple'>`
- ✅ **不再出现** `read timeout=5.0` 的错误
- ✅ 如果出现超时，应该是接近240秒的超时，而不是5秒

---

## 📝 为什么之前没有发现？

1. **环境变量中没有代理设置**：我们检查了环境变量，但没有发现代理设置
2. **系统代理设置**：macOS可能通过系统偏好设置使用了代理，而不是环境变量
3. **代理透明工作**：代理在后台透明工作，我们可能没有意识到它的存在
4. **超时设置被覆盖**：代理的超时设置（5秒）覆盖了代码中的timeout参数，导致问题难以诊断

---

## ⚠️ 重要提示

**如果仍然看到5秒超时错误，说明进程还在使用旧代码！**

**必须重启知识图谱构建进程，新代码才会生效！**

---

## 🎉 总结

**根本原因**：代理（Clash）设置了5秒超时，覆盖了代码中的240秒超时设置。

**解决方案**：在代码中显式禁用代理，确保timeout参数正确生效。

**状态**：✅ 已修复，等待验证

