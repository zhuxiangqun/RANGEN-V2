# 端口占用问题解决方案

## 问题描述

启动可视化服务器时遇到错误：
```
ERROR: [Errno 48] error while attempting to bind on address ('0.0.0.0', 8080): [errno 48] address already in use
```

这表示端口 8080 已被其他进程占用。

## 解决方案

### 方案1：停止占用端口的进程（推荐）

**步骤1：查找占用端口的进程**
```bash
lsof -ti:8080
```

**步骤2：停止这些进程**
```bash
# 方法1：使用 kill 命令（优雅停止）
kill $(lsof -ti:8080)

# 方法2：如果方法1无效，强制停止
kill -9 $(lsof -ti:8080)
```

**步骤3：重新启动服务器**
```bash
python examples/start_visualization_server.py
```

### 方案2：使用其他端口

**方法1：通过环境变量设置**
```bash
export VISUALIZATION_PORT=8081
python examples/start_visualization_server.py
```

**方法2：在 .env 文件中设置**
```env
VISUALIZATION_PORT=8081
```

然后运行：
```bash
python examples/start_visualization_server.py
```

**方法3：修改启动脚本**

编辑 `examples/start_visualization_server.py`，修改第 44 行：
```python
port = int(os.getenv('VISUALIZATION_PORT', '8081'))  # 改为 8081 或其他端口
```

### 方案3：检查是否有其他可视化服务器正在运行

如果之前启动了可视化服务器但没有正确关闭，可能还有进程在运行：

```bash
# 查找所有 Python 进程
ps aux | grep python | grep visualization

# 或查找所有占用 8080 端口的进程
lsof -i:8080
```

## 验证端口是否可用

启动服务器前，可以检查端口是否可用：

```bash
# 检查端口是否被占用
lsof -i:8080

# 如果没有输出，说明端口可用
```

## 常见场景

### 场景1：之前的服务器没有正确关闭

**原因**：按 Ctrl+C 后，服务器进程可能没有完全退出。

**解决**：
1. 查找并停止相关进程
2. 重新启动服务器

### 场景2：多个服务器实例同时运行

**原因**：可能启动了多个服务器实例。

**解决**：
1. 停止所有占用端口的进程
2. 只启动一个服务器实例

### 场景3：其他应用占用了 8080 端口

**原因**：其他应用（如其他 Web 服务器）占用了 8080 端口。

**解决**：
1. 使用方案2，改用其他端口
2. 或停止占用 8080 端口的其他应用

## 预防措施

1. **正确关闭服务器**：使用 Ctrl+C 停止服务器，等待进程完全退出
2. **检查端口占用**：启动前检查端口是否可用
3. **使用环境变量**：通过 `VISUALIZATION_PORT` 环境变量配置端口，避免冲突

## 快速命令

```bash
# 一键停止占用 8080 端口的进程
kill $(lsof -ti:8080) 2>/dev/null || echo "没有进程占用 8080 端口"

# 使用其他端口启动
VISUALIZATION_PORT=8081 python examples/start_visualization_server.py
```

