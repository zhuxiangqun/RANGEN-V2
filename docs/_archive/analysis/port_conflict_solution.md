# 端口冲突解决方案

## 🚨 问题描述

动态配置管理系统默认使用端口 **8080**（API）和 **8081**（Web界面），但项目中的可视化服务器 `examples/start_visualization_server.py` 也使用 **8080** 端口，导致冲突。

## 🔍 冲突检查

### 检查端口占用

```bash
# 检查8080端口是否被占用
lsof -i :8080

# 检查8081端口是否被占用
lsof -i :8081
```

如果看到类似输出，说明端口被占用：
```
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
python  12345 user    3u  IPv4  0x123456      0t0  TCP *:8080 (LISTEN)
```

## ✅ 解决方案

### 方案1：使用自定义端口启动动态配置系统

```bash
# 使用8082和8083端口启动（避免与可视化服务器冲突）
python scripts/quick_start.py --api-port 8082 --web-port 8083
```

访问地址变为：
- Web界面：http://localhost:8083
- REST API：http://localhost:8082

### 方案2：修改可视化服务器端口

在 `examples/start_visualization_server.py` 中修改端口：

```python
# 修改第44行，将8080改为其他端口
port = int(os.getenv('VISUALIZATION_PORT', '8090'))  # 改为8090
```

然后启动：
```bash
VISUALIZATION_PORT=8090 python examples/start_visualization_server.py
```

### 方案3：同时运行两个服务

1. **先启动可视化服务器**（使用默认8080）：
   ```bash
   python examples/start_visualization_server.py
   ```

2. **在新终端启动动态配置系统**（使用不同端口）：
   ```bash
   python scripts/quick_start.py --api-port 8082 --web-port 8083
   ```

## 📋 端口分配建议

| 服务 | 默认端口 | 建议替代端口 |
|------|----------|--------------|
| 可视化服务器 | 8080 | 8090, 9000 |
| 动态配置API | 8080 | 8082, 8084 |
| 动态配置Web | 8081 | 8083, 8085 |

## 🔧 高级配置

### 设置环境变量

```bash
# 为动态配置系统设置端口
export DYNAMIC_CONFIG_API_PORT=8082
export DYNAMIC_CONFIG_WEB_PORT=8083
python scripts/quick_start.py

# 为可视化服务器设置端口
export VISUALIZATION_PORT=8090
python examples/start_visualization_server.py
```

### 脚本化解决方案

创建便捷启动脚本：

**start_config_with_custom_ports.sh**
```bash
#!/bin/bash
echo "启动动态配置管理系统（自定义端口）"
python scripts/quick_start.py --api-port 8082 --web-port 8083
```

**start_visualization_custom.sh**
```bash
#!/bin/bash
echo "启动可视化服务器（自定义端口）"
VISUALIZATION_PORT=8090 python examples/start_visualization_server.py
```

## 🚀 立即解决

针对您的情况，最简单的解决方案是：

```bash
# 停止当前的可视化服务器（如果正在运行）
pkill -f start_visualization_server.py

# 使用自定义端口启动动态配置系统
python scripts/quick_start.py --api-port 8082 --web-port 8083

# 或者启用高级功能（如果所有依赖都已安装）
python scripts/quick_start.py --enable-advanced --api-port 8082 --web-port 8083

# 现在可以访问：
# - API界面: http://localhost:8082/ (美观的Web界面)
# - API数据: curl http://localhost:8082/ (JSON格式)
```

现在您可以同时运行两个服务而不会冲突！
