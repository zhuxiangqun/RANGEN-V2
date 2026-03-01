# 从单体架构迁移到模块化架构

## 概述

本文档指导如何从旧的单体 `BrowserVisualizationServer` 架构迁移到新的模块化服务器架构。

## 迁移背景

### 旧架构问题

1. **单一职责违反**: `BrowserVisualizationServer` 类承担了7种不同的职责
2. **代码复杂度高**: `_register_routes` 方法超过1000行
3. **维护困难**: 修改一个功能可能影响其他功能
4. **测试困难**: 难以单独测试某个功能
5. **语法错误频发**: 复杂的代码结构导致大量语法错误

### 新架构优势

1. **模块化设计**: 每个服务独立开发和部署
2. **单一职责**: 每个模块只负责一种类型的服务
3. **易于维护**: 修改一个模块不会影响其他模块
4. **便于测试**: 可以独立测试每个服务
5. **高可用性**: 一个服务故障不会影响其他服务

## 迁移步骤

### 第一阶段：准备工作

#### 1. 备份现有代码

```bash
# 备份当前的单体服务器文件
cp src/visualization/browser_server.py src/visualization/browser_server.py.backup
```

#### 2. 安装新架构

新架构的文件结构：

```
src/visualization/servers/
├── __init__.py
├── base_server.py          # 基础服务器抽象类
├── api_server.py           # 基础API服务
├── visualization_server.py # 可视化服务
├── config_server.py        # 配置管理服务
├── websocket_server.py     # WebSocket服务
└── unified_server_manager.py # 统一服务管理器
```

#### 3. 验证依赖

确保以下依赖已安装：

```bash
pip install fastapi uvicorn websockets
```

### 第二阶段：渐进式迁移

#### 方案A：并行运行（推荐）

1. **保持旧系统运行**: 继续使用现有的 `BrowserVisualizationServer`
2. **部署新系统**: 在不同端口部署新的模块化服务器
3. **逐步迁移功能**: 一个功能一个功能地迁移
4. **验证兼容性**: 确保新系统完全兼容旧系统的功能
5. **切换流量**: 验证无误后切换到新系统

#### 方案B：逐步替换

1. **功能映射**: 将旧系统的功能映射到新模块

| 旧系统功能 | 新系统模块 | 说明 |
|-----------|-----------|------|
| 工作流执行API | APIServer | `/api/workflow/execute` |
| 执行状态查询 | APIServer | `/api/execution/{id}` |
| 工作流可视化 | VisualizationServer | `/api/workflow/graph` |
| 配置管理界面 | ConfigServer | `/config` |
| WebSocket通信 | WebSocketServer | `/ws/{execution_id}` |
| 监控和诊断 | APIServer | `/api/workflow/health` |

2. **逐个迁移路由**: 将路由从旧系统逐步迁移到新系统

### 第三阶段：配置和部署

#### 1. 配置文件

创建新的配置文件 `config/modular_server.yaml`：

```yaml
# 统一服务器配置
server:
  host: "0.0.0.0"
  port: 8080
  debug: false

# 子服务配置
services:
  api_server:
    enabled: true
    port: 8081
    host: "0.0.0.0"

  visualization_server:
    enabled: true
    port: 8082
    host: "0.0.0.0"

  config_server:
    enabled: true
    port: 8083
    host: "0.0.0.0"

  websocket_server:
    enabled: true
    port: 8084
    host: "0.0.0.0"

# 工作流系统配置
workflow:
  max_concurrent_executions: 5
  timeout_seconds: 300

# 监控配置
monitoring:
  enabled: true
  metrics_interval: 30
```

#### 2. 启动脚本

使用新的启动脚本：

```bash
# 启动模块化服务器
python scripts/start_modular_server.py --port 8080 --config config/modular_server.yaml
```

#### 3. 环境变量

设置必要的环境变量：

```bash
export RANGEN_SERVER_MODE=modular
export RANGEN_CONFIG_PATH=config/modular_server.yaml
```

## API兼容性保证

### 端点兼容性

新架构完全兼容旧系统的API端点：

| 端点 | 旧系统 | 新系统 | 状态 |
|------|--------|--------|------|
| `GET /` | ✅ | ✅ | 兼容 |
| `GET /api/workflow/graph` | ✅ | ✅ | 兼容 |
| `POST /api/workflow/execute` | ✅ | ✅ | 兼容 |
| `GET /api/execution/{id}` | ✅ | ✅ | 兼容 |
| `GET /config` | ✅ | ✅ | 兼容 |
| `WebSocket /ws/{execution_id}` | ✅ | ✅ | 兼容 |

### 数据格式兼容性

- **请求格式**: 新系统完全兼容旧系统的请求格式
- **响应格式**: 新系统完全兼容旧系统的响应格式
- **错误处理**: 新系统保持相同的错误响应格式

## 测试策略

### 功能测试

1. **单元测试**: 为每个模块编写独立的单元测试
2. **集成测试**: 测试模块间的交互
3. **端到端测试**: 验证完整的功能流程

### 兼容性测试

1. **API兼容性**: 验证所有API端点的工作正常
2. **前端兼容性**: 确保前端应用能正常工作
3. **第三方集成**: 验证与其他系统的集成

### 性能测试

1. **基准测试**: 对比新旧系统的性能
2. **负载测试**: 验证新系统在高负载下的表现
3. **内存使用**: 监控内存使用情况

## 回滚计划

### 快速回滚

如果新系统出现问题，可以快速回滚到旧系统：

1. **停止新系统**:
   ```bash
   pkill -f "start_modular_server.py"
   ```

2. **启动旧系统**:
   ```bash
   python scripts/start_unified_server.py --port 8080
   ```

3. **恢复配置**:
   - 恢复原始的配置文件
   - 恢复环境变量设置

### 渐进式回滚

如果需要更平滑的回滚：

1. **并行运行**: 保持两个系统同时运行
2. **逐步切换**: 将流量逐步从新系统切换回旧系统
3. **监控验证**: 确保回滚过程中功能正常

## 监控和维护

### 健康检查

新架构提供了更细粒度的健康检查：

```bash
# 检查主服务器健康状态
curl http://localhost:8080/health

# 检查子服务健康状态
curl http://localhost:8080/api/health
curl http://localhost:8081/health  # API服务
curl http://localhost:8082/health  # 可视化服务
```

### 日志管理

新架构提供了分层的日志系统：

- **主服务器日志**: 统一服务管理器的日志
- **子服务日志**: 每个服务的独立日志
- **聚合日志**: 可以通过配置将所有日志聚合到一起

### 性能监控

新架构支持更详细的性能监控：

- **服务级别监控**: 每个服务的性能指标
- **跨服务监控**: 服务间的调用性能
- **资源使用监控**: CPU、内存、磁盘使用情况

## 总结

通过这次迁移，我们将：

1. **提高代码质量**: 消除语法错误，提高代码可维护性
2. **提升系统可用性**: 服务模块化部署，单个服务故障不影响整体
3. **便于扩展**: 新功能可以独立开发和部署
4. **简化测试**: 每个模块可以独立测试
5. **优化性能**: 可以针对不同服务进行专门的性能优化

迁移过程虽然需要一定的工作量，但长期来看会带来显著的收益。建议按照本文档的步骤逐步进行迁移，确保每个步骤都经过充分测试。
